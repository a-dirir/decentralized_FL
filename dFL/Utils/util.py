from binascii import hexlify, unhexlify
from time import time
from hashlib import sha256
import colorlog
import logging


def get_logger(name):
    stream_handler = colorlog.StreamHandler()

    formatter = colorlog.ColoredFormatter(
        '%(log_color)s [%(asctime)s]  - [%(message)s] - [%(name)s %(levelname)s]',
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green,bold',
            'WARNING': 'yellow',
            'ERROR': 'red,bold',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )

    stream_handler.setFormatter(formatter)

    logger = colorlog.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler('logs.log')
    file_handler.setLevel(logging.INFO)

    file_formatter = logging.Formatter('%(asctime)s;%(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


def find_element(element, arr):
    for idx, val in enumerate(arr):
        if val == element:
            return idx
    return -1


def c2s(msg):
    return str(hexlify(msg), encoding='utf8')


def c2b(msg):
    return unhexlify(bytes(msg, encoding='utf8'))


def get_current_time():
    return int(time())


def get_time_difference(given_time):
    return int(given_time - time())


def hash_msg(msg):
    return sha256(msg).digest()





