import trolly
import convert
import settings
import pyfscache
import collections

# Enabling a tiny bit of cache so Trello doesn't block us
cache = pyfscache.FSCache('cache', minutes=2)


class Client(trolly.Client):
    def __init__(self):
        print settings.API_KEY
        print settings.TOKEN
        super(Client, self).__init__(settings.API_KEY, settings.TOKEN)


@cache
def get_bugs(board):
    bug_ids = {}
    for card in board.get_cards():
        bug_id = convert.get_bug_id(card)
        if bug_id:
            bug_ids[bug_id] = card

    return bug_ids


def main():
    #boards = convert.list_boards()
    #bug_ids = collections.Counter()
    #names = collections.Counter()

    #for board in boards:
    #    print board

    #    for card in convert.get_cards(board):
    #        if card.closed:
    #            print 'Deleting archived card', card
    #            card.delete()
    #            continue

    #        bug_ids[convert.get_bug_id(card)] += 1
    #        names[card.name] += 1

    # for k, v in bug_ids.most_common():
    #     if v == 1:
    #         break

    #     print k, v

    # for k, v in names.most_common():
    #     if v == 1:
    #         break

    #     print k, v

        #for list_ in board.all_lists():
        #    if list_.id == '557f35934155810f1206f07f':
        #        print list_, list_.id
        #        for card in list_.list_cards():
        #            print 'removing card', card
        #            card.delete()

    client = Client()
    organisation = client.get_organisation('54e4761f3f2a6c0b12ddad86')

    for board in organisation.get_boards():
        print board
        for list_ in board.get_lists():
            print '\t', list_
            if list_.id == '557f35934155810f1206f07f':
                print '\t\t', list_
                for card in list_.get_cards():
                    print '\t\t\t', card
    #                 card.remove_member()

if __name__ == '__main__':
    main()

