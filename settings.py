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

def get_file_from_args():
    '''check config arguments'''
    parser = ArgumentParser()
    parser.add_argument("-c", "--config", dest="configfile",
                        help="path to file with your config", metavar="FILE")

    # parse args and ignore unknown args
    args, _unknown = parser.parse_known_args()

    file = False

    if args.configfile:
        # append path to environment if out of scope
        config_path = path.dirname(path.abspath(args.configfile))
        if path.exists(config_path):
            sys.path.append(config_path)

        # check file
        file = path.basename(args.configfile)
        file_path = path.join(config_path, args.configfile)
        if not path.exists(file_path):
            logging.info("Config file not found: %s", file_path)
            sys.exit()
    else:
        # Default config file
        file = "config.py"

    return file

def import_module(file):
    '''check if file exist and import'''
    config_module = importlib.import_module(file.replace('.py',''))
    logging.info("Load config %s successful", file)
    return config_module

def load_config():
    '''import and check contest configuration'''
    filename = get_file_from_args()
    config = import_module(filename)

    # load and set defaults for missing configurations
    config.CHAT_ID                      = getattr(config, 'CHAT_ID', "mychannelname")
    config.CONTEST_DATE                 = getattr(
        config, 'CONTEST_DATE', datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    config.CONTEST_DAYS                 = getattr(config, 'CONTEST_DAYS', 1)
    config.CONTEST_MAX_RANKS            = getattr(config, 'CONTEST_MAX_RANKS', 10)
    config.CONTEST_POLL                 = getattr(config, 'CONTEST_POLL', False)
    config.CONTEST_POLL_RESULT          = getattr(config, 'CONTEST_POLL_RESULT', False)
    config.EXCLUDE_PATTERN              = getattr(
        config, 'EXCLUDE_PATTERN', ["Meme Contest", "Tagessieger", "Rangliste"]
    )
    config.FINAL_MESSAGE_HEADER         = getattr(config, 'FINAL_MESSAGE_HEADER', "")
    config.FINAL_MESSAGE_FOOTER         = getattr(
        config, 'FINAL_MESSAGE_FOOTER',
        f"🏆 [{config.EXCLUDE_PATTERN[0]}](https://t.me/mychannelname) 🏆"
    )
    config.FINAL_MESSAGE_CHAT_ID        = getattr(config, 'FINAL_MESSAGE_CHAT_ID', False)
    config.PARTITICPANTS_FROM_CSV       = getattr(config, 'PARTITICPANTS_FROM_CSV', False)
    config.POST_LINK                    = getattr(config, 'POST_LINK', True)
    config.CREATE_CSV                   = getattr(config, 'CREATE_CSV', False)
    config.CSV_CHAT_ID                  = getattr(
        config, 'CSV_CHAT_ID', config.FINAL_MESSAGE_CHAT_ID
    )
    config.POST_WINNER_PHOTO            = getattr(config, 'POST_WINNER_PHOTO', True)
    config.SIGN_MESSAGES                = getattr(config, 'SIGN_MESSAGES', False)
    config.RANK_MEMES                   = getattr(config, 'RANK_MEMES', True)
    config.POST_PARTICIPANTS_CHAT_ID    = getattr(config, 'POST_PARTICIPANTS_CHAT_ID', False)

    return config

def load_api():
    '''import and check api configuration'''
    api = import_module("config_api.py")

    api.ID      = getattr(api, 'ID', 12345)
    api.HASH    = getattr(api, 'HASH', "myhashstring")

    return api
