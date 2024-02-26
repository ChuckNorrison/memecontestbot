#!/usr/bin/env python

"""
Import config files
"""

import sys
import logging
import importlib
from os import path
from argparse import ArgumentParser
from datetime import datetime

# configure logging
logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def get_file_from_args(filetype):
    '''check config arguments'''
    parser = ArgumentParser()
    parser.add_argument("-c", "--config", dest="configfile",
                        help="path to file with your config", metavar="FILE")
    parser.add_argument("-a", "--auth", dest="authfile",
                        help="path to file with your authentication", metavar="FILE")

    # parse args and ignore unknown args
    args, _unknown = parser.parse_known_args()

    file = False
    if filetype == "config":
        if args.configfile:
            file = args.configfile
            add_path(file)
        else:
            # default file
            file = "config.py"

    elif filetype == "auth":
        if args.authfile:
            file = args.authfile
            add_path(file)
        else:
            # default file
            file = "config_api.py"

    return file

def add_path(file):
    '''append path to environment if out of scope'''
    file_path = path.dirname(path.abspath(file))
    if path.exists(file_path):
        sys.path.append(file_path)

    # check file
    file = path.basename(file)
    file_path = path.join(file_path, file)
    if not path.exists(file_path):
        logging.info("File not found: %s", file_path)
        sys.exit()

    return True

def import_module(file):
    '''check if file exist and import'''
    config_module = importlib.import_module(file.replace('.py',''))
    logging.info("importlib import_module %s", file)
    return config_module

def load_config():
    '''import and check contest configuration'''
    filename = get_file_from_args("config")
    config = import_module(filename)

    # load and set defaults for missing configurations
    config.CHAT_ID                      = getattr(config, 'CHAT_ID', "mychannelname")
    config.CONTEST_DATE                 = getattr(
        config, 'CONTEST_DATE', datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    config.CONTEST_DAYS                 = getattr(config, 'CONTEST_DAYS', 1)
    config.CONTEST_MAX_RANKS            = getattr(config, 'CONTEST_MAX_RANKS', 10)
    config.CONTEST_RANKING_BY_VIEWS     = getattr(config, 'CONTEST_RANKING_BY_VIEWS', False)
    config.CONTEST_POLL                 = getattr(config, 'CONTEST_POLL', False)
    config.CONTEST_POLL_HEADER          = getattr(config, 'CONTEST_POLL_HEADER', (
        "Community voting for Meme of the week\n"
        "from {TEMPLATE_START_DATE} - {TEMPLATE_END_DATE} (24h voting)")
    )
    config.CONTEST_POLL_RESULT          = getattr(config, 'CONTEST_POLL_RESULT', False)
    config.CONTEST_POLL_RESULT_RANKING  = getattr(config, 'CONTEST_POLL_RESULT_RANKING', False)
    config.CONTEST_POLL_COLOR           = getattr(config, 'CONTEST_POLL_COLOR', False)
    config.CONTEST_POLL_FROM_POLLS      = getattr(config, 'CONTEST_POLL_FROM_POLLS', False)
    config.CONTEST_POLL_PATTERN         = getattr(
        config, 'CONTEST_POLL_PATTERN', ["Meme of the week", "The Community has voted"]
    )
    config.CONTEST_HIGHSCORE            = getattr(config, 'CONTEST_HIGHSCORE', False)
    config.EXCLUDE_PATTERN              = getattr(
        config, 'EXCLUDE_PATTERN', ["My funny Contest", "Ranking"]
    )
    config.FINAL_MESSAGE_HEADER         = getattr(config, 'FINAL_MESSAGE_HEADER', "")
    config.FINAL_MESSAGE_HEADER_DRAW    = getattr(config, 'FINAL_MESSAGE_HEADER_DRAW', "")
    config.FINAL_MESSAGE_FOOTER         = getattr(
        config, 'FINAL_MESSAGE_FOOTER',
        f"🏆 [{config.EXCLUDE_PATTERN[0]}](https://t.me/mychannelname) 🏆"
    )
    config.FINAL_MESSAGE_CHAT_ID        = getattr(config, 'FINAL_MESSAGE_CHAT_ID', False)
    config.PARTICIPANTS_FROM_CSV        = getattr(config, 'PARTICIPANTS_FROM_CSV', False)
    config.POST_LINK                    = getattr(config, 'POST_LINK', True)
    config.CREATE_CSV                   = getattr(config, 'CREATE_CSV', False)
    config.CSV_CHAT_ID                  = getattr(config, 'CSV_CHAT_ID', False)
    config.POST_WINNER_PHOTO            = getattr(config, 'POST_WINNER_PHOTO', True)
    config.SIGN_MESSAGES                = getattr(config, 'SIGN_MESSAGES', False)
    config.RANK_MEMES                   = getattr(config, 'RANK_MEMES', True)
    config.POST_PARTICIPANTS_CHAT_ID    = getattr(config, 'POST_PARTICIPANTS_CHAT_ID', False)
    config.LIMIT_SENDERS                = getattr(config, 'LIMIT_SENDERS', True)
    config.CSV_FILE                     = getattr(config, 'CSV_FILE', "contest.csv")
    config.RANKING_WINNER_SUFFIX        = getattr(config, 'RANKING_WINNER_SUFFIX', "🏅")
    config.PARTICIPANTS_LIST            = getattr(config, 'PARTICIPANTS_LIST', False)
    config.PARTICIPANT_DUPLICATES       = getattr(config, 'PARTICIPANT_DUPLICATES', False)

    return config

def load_api():
    '''import and check api configuration'''
    filename = get_file_from_args("auth")
    api = import_module(filename)

    api.ID      = getattr(api, 'ID', 12345)
    api.HASH    = getattr(api, 'HASH', "myhashstring")

    return api
