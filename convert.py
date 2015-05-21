#!/usr/bin/env python

import re
import trello
import pprint
import requests

BUGZILLA_URL = 'http://bugzilla.3xo.eu/show_bug.cgi?id=%(id)s'

try:
    from client import client
except ImportError:
    print '''You need to create a trello client in `client.py`, it should look
    something like this:

    .. highlight:: python

        import trello

        client = trello.TrelloClient(
            api_key='your-key',
            api_secret='your-secret',
            token='your-oauth-token-key',
            token_secret='your-oauth-token-secret',
        )

    :api_key: API key generated at https://trello.com/1/appKey/generate
    :api_secret: the secret component of api_key
    :token_key: OAuth token generated by the user in
                trello.util.create_oauth_token
    :token_secret: the OAuth client secret for the given OAuth token

    You can get the actual input using the `trello_authenticate.py` script with
    the `api_key` and `api_secret` parameters.
    '''

# for board in client.list_boards():
#     print board, board.__dict__

board = client.get_board('54e476a396124a3eec92625a')

for card in board.all_cards():
    match = re.search('(\d+)', card.name)
    if match and 1000 < int(match.group(1)) < 3000:
        bug_id = match.group(1)
        print 'Bug ID: %s' % bug_id
        assert bug_id.isdigit()

        url = BUGZILLA_URL % dict(id=bug_id)
        request = requests.get(url)
        match = re.search('<title>Bug %s - ([^<]+)</title>' % bug_id,
                          request.text)
        if match:
            title = match.group(1)
            new_name = '#%(bug_id)s %(title)s' % locals()
            print 'setting name from %s to %s' % (card.name, new_name)
            if card.name != new_name:
                card.set_name(new_name)
        else:
            print 'Unable to get bugzilla info from: %s' % url

    else:
        print 'Unable to match %r' % card
        pprint.pprint(card.__dict__)

