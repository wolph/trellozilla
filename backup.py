import re
import py
import json
import utils
from datetime import date


def format(data):
    return json.dumps(data, sort_keys=True, indent=4)


def slugify(name):
    name = name.replace(' ', '_')
    name = name.replace('/', '-')
    name = re.sub('[^A-Za-z0-9_-]+', '', name)
    return name


def main():
    backup_dir = py.path.local('backups/%s' % date.today())

    # organisation = client.get_organization('4tu').all_boards()
    # return
    for board in utils.get_boards():
        slug = board.url.split('/')[-1]
        board_dir = backup_dir.join(slug)
        board_json = format(utils.client.fetch_json(
            '/boards/%s' % board.id,
            query_params=dict(
                fields='all',
                actions='all',
                cards='all',
                lists='all',
                labels='all',
                memberships='all',
                members='all',
                checklists='all',
            ),
        ))
        board_path = board_dir.join('board.json')
        board_path.write(board_json, ensure=True)

        for list_ in utils.get_lists(board):
            list_json = format(utils.client.fetch_json(
                '/lists/%s' % list_.id,
                query_params=dict(
                    cards='all',
                    card_fields='all',
                    fields='all',
                ),
            ))
            list_path = board_dir.join('list_%s.json' % slugify(list_.name))
            list_path.write(list_json, ensure=True)


if __name__ == '__main__':
    main()
