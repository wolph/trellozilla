import os
import requests

try:
    import cPickle as pickle
except ImportError:
    import pickle

COOKIES_FILE = 'cookies.pickle'


def get_session():
    session = requests.session()
    if os.path.isfile(COOKIES_FILE):
        with open(COOKIES_FILE, 'rb') as fh:
            session.cookies = requests.utils.cookiejar_from_dict(
                pickle.load(fh))

    return session


def save_session(session):
    with open(COOKIES_FILE, 'wb') as fh:
        pickle.dump(requests.utils.dict_from_cookiejar(session.cookies), fh)
