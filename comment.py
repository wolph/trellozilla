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


def add_comment(session, card, data):
    comments = convert.get_bugzilla_comments(card, from_trello=True)
    for url, comment in comments.iteritems():
        text = comment['comment'].split('\n', 1)[-1].strip()
        if simple_compare(text, data['data']['text'].strip()):
            return

    page = html.fromstring(convert.get_bugzilla_page(card.bug_id))

    for form in page.forms:
        if form.get('name') == 'changeform':
            break
    else:
        raise RuntimeError('cant find changeform')

    post_data = dict(form.form_values())
    post_data['comment'] = settings.BUGZILLA_COMMENT_PATTERN % dict(
        short_link=data['data']['card']['shortLink'],
        comment=data['data']['text'],
        name=data['memberCreator']['fullName'],
    )

    convert.cache.expire(('bugzilla_page', card.bug_id))
    session.post(settings.BUGZILLA_BUG_POST_URL, data=post_data)
    print 'Posting comment to %r: %r' % (card, post_data['comment'])


def main(session, *bug_ids):
    client = Client()
    bugzilla_login(session)

    organisation = client.get_organisation('54e4761f3f2a6c0b12ddad86')

    if bug_ids:
        bug_ids = [int(b) for b in bug_ids]

    for board in get_boards(organisation, actions='commentCard'):
        for comment in board.actions:
            data = comment['data']
            card = client.create_card(data['card'])
            if not BUGZILLA_COMMENT_RE.match(data['text']):
                card.bug_id = convert.get_bug_id(card)
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
