import re
import trello
import requests
import settings
import pyfscache
import pyjsonrpc


client = trello.TrelloClient(
    api_key=settings.API_KEY,
    api_secret=settings.API_SECRET,
    token=settings.TOKEN,
    token_secret=settings.TOKEN_SECRET,
)

trac = pyjsonrpc.HttpClient(
    settings.TRAC_JSONRPC_URL,
    username=settings.TRAC_JSONRPC_USER,
    password=settings.TRAC_JSONRPC_PASS,
)

long_cache = pyfscache.FSCache('cache', days=1)
cache = pyfscache.FSCache('cache', minutes=2)


@long_cache
def get_boards():
    return client.get_organization('4tu').all_boards()


@long_cache
def get_lists(board):
    return board.all_lists()


@cache
def get_cards(list_):
    return list_.list_cards()


@long_cache
def get_labels(board):
    return board.get_labels()


# def trac(method, params):
#     response = requests.post(settings.TRAC_JSONRPC_URL, json=dict(
#         method=method,
#         params=params,
#     )).json()
#
#     return response['result']


@cache
def get_trac_bug(bug_id):
    return trac.call('ticket.get', bug_id)[3]


def query_trac_bugs(query):
    return trac.call('ticket.query', query)


def get_bug_id(name):
    match = re.match('^#(\d{4}) ', name)
    if match:
        return int(match.group(1))
