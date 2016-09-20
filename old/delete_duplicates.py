#!/usr/bin/env python

import re
import sys
import pyfscache
import HTMLParser
from datetime import datetime

try:
    from collections import OrderedDict
except:
    from ordereddict import OrderedDict

import utils
import trello
import settings

# Enabling a tiny bit of cache so Trello doesn't block us
cache = pyfscache.FSCache('cache', minutes=2)
long_cache = pyfscache.FSCache('cache', days=1)

# HTML parser for unescaping of html stuff
parser = HTMLParser.HTMLParser()

session = utils.get_session()


client = trello.TrelloClient(
    api_key=settings.API_KEY,
    api_secret=settings.API_SECRET,
    token=settings.TOKEN,
    token_secret=settings.TOKEN_SECRET,
)


from convert import list_boards, get_cards, get_bug_id, get_board


if __name__ == '__main__':
    active_bugs = set()
    print 'Processing active bugs'
    for card in get_cards(get_board(settings.ACTIVE_BOARD)):
        bug_id = get_bug_id(card)
        if not bug_id:
            continue

        if bug_id in active_bugs:
            print 'Deleting duplicate card %r (in active)' % card

        active_bugs.add(bug_id)

    archived_bugs = set()
    # print 'Processing archived bugs'
    # for card in get_cards(get_board(settings.ARCHIVE_BOARD)):
    #     bug_id = get_bug_id(card)
    #     if not bug_id:
    #         continue

    #     if bug_id in active_bugs or bug_id in archived_bugs:
    #         print 'Deleting duplicate card %r (in archive)' % card
    #         card.delete()

    #     archived_bugs.add(bug_id)

    backlog_bugs = set()
    for board in list_boards():
        if board.id in (settings.ARCHIVE_BOARD, settings.ACTIVE_BOARD):
            print 'Skipping', board
            continue

        print 'Processing', board
        for card in get_cards(board):
            bug_id = get_bug_id(card)
            if not bug_id:
                continue

            if bug_id in (active_bugs | archived_bugs | backlog_bugs):
                print 'Deleting duplicate card %r (in archive)' % card
                card.delete()

            backlog_bugs.add(bug_id)
