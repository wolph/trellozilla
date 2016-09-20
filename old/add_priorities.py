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


def main():
    client = Client()
    organisation = client.get_organisation('54e4761f3f2a6c0b12ddad86')

    for board in organisation.get_boards():
        print board
        print board.get_labels()

if __name__ == '__main__':
    main()

