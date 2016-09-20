import re
import utils
import requests
import collections


def get_sprints():
    by_sprint = collections.defaultdict(set)
    by_bug = collections.defaultdict(set)
    with open('sprints.txt') as fh:
        for line in fh:
            if line.strip():
                k, v = line.split()
                k = int(k)
                v = int(v)
                by_bug[k].add(v)
                by_sprint[v].add(k)

    return by_sprint, by_bug


def get_unplanned():
    unplanned = set()
    with open('unplanned.txt') as fh:
        for line in fh:
            if line.strip():
                unplanned.add(int(line.strip()))

    return unplanned


def process_sprint(unplanned, sprint, list_, bugs):
    missing = set(sprint)
    for card in utils.get_cards(list_):
        match = re.match('#(\d{4})', card.name)
        if match:
            bug_id = int(match.group(1))
            if bug_id in missing:
                missing.remove(bug_id)
            else:
                print 4 * ' ', bug_id, card.name

    for bug_id in sorted(missing):
        if bug_id in bugs:
            bug = bugs[bug_id]
        else:
            bug_data = utils.get_trac_bug(bug_id)
            bug = bug_data['summary']
            if not bug.startswith('#%04d' % bug_id):
                bug = '#%04d %s' % (bug_id, bug)

        print 4 * ' ', 'GOING TO insert', bug
        list_.add_card(bug)
        # import sys
        # print(dir(list_))
        # sys.exit(0)

    # for bug_id, bug in bugs.items():
    #     if bug_id in missing:
    #         print 4 * ' ', 'GOING TO insert', bug
    #         list_.add_card(bug)
    #         # import sys
    #         # print(dir(list_))
    #         # sys.exit(0)


def get_bugs(board):
    bugs = dict()
    if '2015' in board.name:
        filename = 'archive_2015.txt'
    elif '2016' in board.name:
        filename = 'archive_2016.txt'
    else:
        raise IOError()

    with open(filename) as fh:
        for line in fh:
            title = line[13:].strip()
            bug_id = int(title[1:5])
            bugs[bug_id] = title

    return bugs


def main():
    unplanned = get_unplanned()
    by_sprint, by_bug = get_sprints()

    for board in utils.get_boards():
        if 'archive' not in board.name.lower():
            continue
        print board
        bugs = get_bugs(board)
        for list_ in utils.get_lists(board):
            sprint_id = int(list_.name.split()[2])
            if sprint_id in by_sprint:
                print 2 * ' ', list_
                sprint = by_sprint[sprint_id]
                process_sprint(unplanned, sprint, list_, bugs)


if __name__ == '__main__':
    main()
