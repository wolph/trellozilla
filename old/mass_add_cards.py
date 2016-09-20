import re
import sys
import trolly
import convert
import settings
import pyfscache

# Enabling a tiny bit of cache so Trello doesn't block us
cache = pyfscache.FSCache('cache', minutes=2)


class Client(trolly.Client):
    def __init__(self):
        super(Client, self).__init__(settings.API_KEY, settings.TOKEN)


@cache
def get_bugs(board):
    bug_ids = {}
    for card in board.get_cards():
        bug_id = convert.get_bug_id(card)
        if bug_id:
            bug_ids[bug_id] = card

    return bug_ids


def main(board_id, filename):
    client = Client()
    organisation = client.get_organisation('54e4761f3f2a6c0b12ddad86')

    bugs = {}
    for board in organisation.get_boards():
        bugs.update(get_bugs(board))

    board = client.get_board(board_id, 'Backlog %s' % filename)
    backlog = None
    for list_ in board.get_lists():
        if list_.name.lower() == 'backlog':
            backlog = list_
            break
    else:
        backlog = board.add_list(dict(name='Backlog'))

    print 'Adding items to %r from %r' % (board, filename)

    bug_ids = re.findall('^(\d+)', open(filename).read(), re.MULTILINE)
    for bug_id in bug_ids:
        bug_id = int(bug_id)
        if bug_id not in bugs:
            print 'Adding card for %r' % bug_id
            backlog.add_card(dict(name='#%d' % bug_id))


if __name__ == '__main__':
    if len(sys.argv) == 3:
        main(*sys.argv[1:])
    else:
        print 'Please run like this: %s <board_id> <filename>' % sys.argv[0]

