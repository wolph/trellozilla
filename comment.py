import re
import sys
from lxml import html
import pprint
import trolly
import requests
import pyfscache

import utils
import convert
import settings

BUGZILLA_COMMENT_RE = re.compile(r'^\[By .+? at .+?\]\(https?://[^)]+\)')

# Enabling a tiny bit of cache so Trello doesn't block us
cache = pyfscache.FSCache('cache', minutes=120)


class Client(trolly.Client):
    def __init__(self):
        super(Client, self).__init__(settings.API_KEY, settings.TOKEN)


@cache
def get_boards(organisation, **kwargs):
    return organisation.get_boards(**kwargs)


@cache
def get_lists(board, **kwargs):
    return board.get_lists(**kwargs)


@cache
def get_cards(list_, **kwargs):
    return list_.get_cards(**kwargs)


@cache
def get_bugs(board):
    bug_ids = {}
    for card in board.get_cards():
        bug_id = convert.get_bug_id(card)
        if bug_id:
            bug_ids[bug_id] = card

    return bug_ids


@cache
def get_comments(list_):
    return list_.get_comments()


def simple_compare(a, b):
    a = convert.strip_tags(a).strip()
    b = convert.strip_tags(b).strip()
    return a == b


def get_form(card):
    page = html.fromstring(convert.get_bugzilla_page(card.bug_id))
    for form in page.forms:
        if form.get('name') == 'changeform':
            break
    else:
        raise RuntimeError('cant find changeform')

    return form


def add_comment(session, card, data):
    simple_text = data['data']['text'].strip()
    comments = convert.get_bugzilla_comments(card, from_trello=True)
    non_matching = []
    for url, comment in comments.iteritems():
        text = comment['comment'].split('\n', 1)[-1].strip()
        non_matching.append(text)
        if simple_compare(text, simple_text):
            return

    form = get_form(card)
    post_data = dict(form.form_values())
    post_data['comment'] = settings.BUGZILLA_COMMENT_PATTERN % dict(
        short_link=data['data']['card']['shortLink'],
        comment=data['data']['text'],
        name=data['memberCreator']['fullName'],
    )

    convert.cache.expire(('bugzilla_page', card.bug_id))
    print 'Found comment: %r' % simple_text
    for text in non_matching:
        print ' - %r' % text
    session.post(settings.BUGZILLA_BUG_POST_URL, data=post_data)
    print 'Posting comment to %r: %r' % (card, post_data['comment'])


def set_status(session, card, data):
    page = convert.get_bugzilla_page(card.bug_id).lower()
    list_name = data['listAfter']['name'].lower()
    knob = None
    resolution = None
    if list_name.startswith('done sprint '):
        status = 'verified fixed'
        # if 'knob-verify' in page:
        #     knob = 'verify'
        # elif '<td>resolved</td>' not in page:
        #     knob = 'resolve'
        #     resolution = 'FIXED'
    elif list_name == 'to do':
        status = 'new'
    elif list_name == 'testing':
        status = 'resolved fixed'
        # if '<td>resolved</td>' not in page:
        #     knob = 'resolve'
        #     resolution = 'FIXED'
    elif list_name == 'doing':
        status = 'assigned'
        # if '<td>assigned</td>' not in page:
        #     knob = 'accept'
    else:
        print 'Unknown list %r, skipping %r' % (list_name, card)
        return

    if 'leave as <b>resolved&nbsp;fixed</b>' in page:
        current_status = 'resolved fixed'
    elif 'leave as <b>verified&nbsp;fixed</b>' in page:
        current_status = 'verified fixed'
    elif 'leave as <b>new&nbsp;</b>' in page:
        current_status = 'new'
    elif 'leave as <b>assigned&nbsp;</b>' in page:
        current_status = 'assigned'
    else:
        print 'Unknown status', card.bug_id, status
        return

    if status == current_status:
        return

    form = get_form(card)
    post_data = dict(form.form_values())

    # verified fixed resolved fixed
    if status == 'verified fixed':
        if 'resolved' not in current_status:
            post_data['knob'] = 'resolve'
            post_data['resolution'] = 'fixed'
            _set_status(session, card, data, post_data, 'resolved fixed')
            del post_data['resolution']

        post_data['knob'] = 'verify'
        _set_status(session, card, data, post_data, status)
    elif status == 'resolved fixed':
        if current_status == 'verified fixed':
            post_data['knob'] = 'verify'
            _set_status(session, card, data, post_data, status)
        else:
            post_data['knob'] = 'resolve'
            post_data['resolution'] = 'fixed'
            _set_status(session, card, data, post_data, status)
    elif status == 'accepted':
        post_data['knob'] = 'accept'
        _set_status(session, card, data, post_data, status)
    else:
        print 'status %r unsupported' % status


def _set_status(session, card, data, post_data, status):
    post_data['comment'] = settings.BUGZILLA_STATUS_PATTERN.format(
        status=status, **data)

    print 'Changing status for %r to %r' % (card, status)

    try:
        convert.cache.expire(('bugzilla_page', card.bug_id))
    except pyfscache.CacheError:
        pass
    session.post(settings.BUGZILLA_BUG_POST_URL, data=post_data)


@cache
def get_moved_cards(organisation):
    return get_boards(organisation, actions='updateCard:idList')


def main(session, *bug_ids):
    client = Client()
    bugzilla_login(session)

    organisation = client.get_organisation('54e4761f3f2a6c0b12ddad86')

    if bug_ids:
        bug_ids = [int(b) for b in bug_ids]

    skip = set()
    for board in get_moved_cards(organisation):
        if board.id != '54e476a396124a3eec92625a':
            continue

        # get_boards(organisation, actions='updateCard:idList'):
        for action in board.actions:
            data = action['data']
            card = client.create_card(data['card'])
            card.bug_id = convert.get_bug_id(card)

            if not card.bug_id:
                continue
            elif card.bug_id in skip:
                continue
            else:
                skip.add(card.bug_id)

            if bug_ids and card.bug_id not in bug_ids:
                continue

            set_status(session, card, data)

    for board in get_boards(organisation, actions='commentCard'):
        for comment in board.actions:
            data = comment['data']
            card = client.create_card(data['card'])
            card.bug_id = convert.get_bug_id(card)
            if bug_ids and card.bug_id not in bug_ids:
                continue
            elif not card.bug_id:
                continue

            if not BUGZILLA_COMMENT_RE.match(data['text']):
                add_comment(session, card, comment)


# curl 'http://bugzilla.dev-ict.tudelft.nl/process_bug.cgi

#     delta_ts='2015-09-17+14%3A19%3A21',
#     longdesclength='1',
#     id='2151',
#     rep_platform='Macintosh',
#     product='3TU+Datacentrum',
#     op_sys='Mac+OS+X+10.0',
#     newcc='',
#     component='Systeem',
#     version='3.0',
#     cc='',
#     priority='P1',
#     bug_severity='normal',
#     target_milestone='---',
#     bug_file_loc='',
#     flag_type-2='X',
#     flag_type-1='X',
#     short_desc='Fedora+user+ID',
#     dependson='',
#     blocked='',
#     comment='',
#     knob='none',
#     resolution='FIXED',
#     dup_id='',
#     assigned_to='a.e.nonhebel%40tudelft.nl',
#     form_name='process_bug,

def bugzilla_login(session):
    request = session.post(settings.BUGZILLA_LOGIN_URL,
                           data=settings.BUGZILLA_LOGIN_DATA)

if __name__ == '__main__':
    try:
        main(convert.session, *sys.argv[1:])
    finally:
        utils.save_session(convert.session)
