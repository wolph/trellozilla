import sys
import utils
import pprint
import mass_add

bugs = True

# while bugs:
#     bugs = utils.query_trac_bugs('&'.join((
#         'component=Buildserver',
#         # 'component=!Datacentrum',
#         # 'component=!Datacite',
#         # 'component=!Zandmotor',
#         # 'component=!',
#         'desc=1',
#         'order=id',
#     )))
#
#     for bug_id in bugs:
#         bug = utils.get_trac_bug(bug_id)
#         pprint.pprint(bug)
# print utils.get_trac_bug(2345)
#
# sys.exit()
#
# import pprint

components = dict(
    datacentrum='4TU.ResearchData',
    zandmotor='Zandmotor',
    build='Buildserver',
    datacite='Datacite',
)


def main():
    unplanned = mass_add.get_unplanned()
    for board in utils.get_boards():
        print board

        labels = dict((l.name, l) for l in utils.get_labels(board))
        # print labels
        # return

        for list_ in utils.get_lists(board):
            print 2 * ' ', list_
            for card in utils.get_cards(list_):
                bug_id = utils.get_bug_id(card.name)
                if bug_id:
                    trac_card = utils.get_trac_bug(bug_id)
                    print trac_card
                    label = labels[components[trac_card['component'].lower()]]
                    print label
                    if label and label not in card.labels:
                        print 'missing label', label
                        print card.labels
                        print trac_card
                        card.add_label(label)
                else:
                    print 'No bug id for', card

                if bug_id in unplanned:
                    trac_card = utils.get_trac_bug(bug_id)
                    print trac_card
                    label = labels['Unplanned']
                    print label
                    if label and label not in card.labels:
                        print 'missing label', label
                        print card.labels
                        print trac_card
                        try:
                            card.add_label(label)
                        except Exception:
                            print '%r already has label %r' % (card, label)
                else:
                    print 'No bug id for', card

        #     sprint_id = int(list_.name.split()[2])
        #     if sprint_id in by_sprint:
        #         sprint = by_sprint[sprint_id]
        #         process_sprint(unplanned, sprint, list_, bugs)


if __name__ == '__main__':
    main()
