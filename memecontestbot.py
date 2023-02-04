#!/usr/bin/env python

"""
Simple Bot to analyze telegram post reactions and create a ranking.
Can be configured for daily or weekly rankings
(get_chat_history has a limit of posts to return from chat).

Usage:
Start bot to create a nice ranking.
"""

from datetime import datetime
from os import path
from argparse import ArgumentParser

import sys
import importlib
import csv
import re
import logging

from pyrogram import Client, enums

# configure logging
logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("memecontestbot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# check config arguments
parser = ArgumentParser()
parser.add_argument("-c", "--config", dest="CONFIGFILE",
                    help="path to file with your config", metavar="FILE")
args = parser.parse_args()

if args.CONFIGFILE:
    config_path = path.dirname(path.abspath(args.CONFIGFILE))
    try:
        CONFIG = path.basename(args.CONFIGFILE)
    except AttributeError:
        CONFIG = args.CONFIGFILE

    if CONFIG == "config.py":
        logging.warning("Please rename your config file (config.py not allowed): %s",
                args.CONFIGFILE)
        sys.exit()
    else:
        sys.path.append(config_path)
else:
    # Default config file
    CONFIG = "config.py"

# start import config file
try:
    config = importlib.import_module(CONFIG.replace('.py',''))
    TESTCONFIG = ""
    TESTCONFIG += '\nCHAT_ID: ' + str(config.CHAT_ID) + '\n'
    TESTCONFIG += 'CONTEST_DATE: ' + str(config.CONTEST_DATE) + '\n'
    TESTCONFIG += 'CONTEST_DAYS: ' + str(config.CONTEST_DAYS) + '\n'
    TESTCONFIG += 'CONTEST_MAX_RANKS: ' + str(config.CONTEST_MAX_RANKS) + '\n'
    TESTCONFIG += 'EXCLUDE_PATTERN: ' + str(config.EXCLUDE_PATTERN) + '\n'
    TESTCONFIG += 'FINAL_MESSAGE_FOOTER: ' + str(config.FINAL_MESSAGE_FOOTER) + '\n'
    TESTCONFIG += 'FINAL_MESSAGE_CHAT_ID: ' + str(config.FINAL_MESSAGE_CHAT_ID) + '\n'
    TESTCONFIG += 'PARTITICPANTS_FROM_CSV: ' + str(config.PARTITICPANTS_FROM_CSV) + '\n'
    TESTCONFIG += 'CREATE_CSV: ' + str(config.CREATE_CSV) + '\n'
    TESTCONFIG += 'CSV_CHAT_ID: ' + str(config.CSV_CHAT_ID) + '\n'
    TESTCONFIG += 'POST_LINK: ' + str(config.POST_LINK) + '\n'
    TESTCONFIG += 'POST_WINNER_PHOTO: ' + str(config.POST_WINNER_PHOTO) + '\n'
    TESTCONFIG += 'SIGN_MESSAGES: ' + str(config.SIGN_MESSAGES) + '\n'
    TESTCONFIG += 'RANK_MEMES: ' + str(config.RANK_MEMES) + '\n'
    TESTCONFIG += 'POST_PARTICIPANTS_CHAT_ID: ' + str(config.POST_PARTICIPANTS_CHAT_ID)
except AttributeError as ex:
    logging.error("Read config file '%s' failed!", CONFIG)
    logging.error(TESTCONFIG)
    logging.error(ex)
    sys.exit()
except ModuleNotFoundError as ex:
    logging.error("Import '%s' failed!", CONFIG)
    logging.error(ex)
    sys.exit()

API_FILE = "config_api.py"
try:
    api = importlib.import_module(API_FILE.replace('.py',''))
    TESTAPI = ""
    TESTAPI += '\nID: ' + str(api.ID) + '\n'
    TESTAPI += 'HASH: ' + str(api.HASH)
except AttributeError as ex:
    logging.error("Read api file '%s' failed!", API_FILE)
    logging.error(TESTCONFIG)
    logging.error(ex)
    sys.exit()
except ModuleNotFoundError as ex:
    logging.error("Import'%s' failed!", API_FILE)
    logging.error(ex)
    sys.exit()   

app = Client("my_account", api_id=api.ID, api_hash=api.HASH)

# global vars
contest_time = datetime.strptime(config.CONTEST_DATE, "%Y-%m-%d %H:%M:%S")

async def main():
    """This function will run the bot"""

    if config.PARTITICPANTS_FROM_CSV:
        # create a ranking message from CSV data
        await create_csv_ranking()

        # do not walk through chat history
        sys.exit()

    header_message = build_ranking_caption()
    participants = []

    async with app:
        async for message in app.get_chat_history(config.CHAT_ID):

            # check excludes in message caption
            if check_excludes(message.caption):
                continue

            # check if message is a photo
            if str(message.media) != "MessageMediaType.PHOTO":
                continue

            # check for valid author in message caption
            message_author = get_author(message)
            if not message_author:
                continue

            # check if message was in desired timeframe
            message_time = datetime.strptime(
                    str(message.date),
                    "%Y-%m-%d %H:%M:%S")
            message_difftime = contest_time - message_time

            if ( (message_difftime.days <= config.CONTEST_DAYS-1)
                    and not message_difftime.days < 0 ):

                message_reactions = 0
                if not config.POST_PARTICIPANTS_CHAT_ID:
                    # verify reactions for ranking message
                    try:
                        message_reactions = message.reactions.reactions[0].count
                    except AttributeError:
                        # skip this message for missing reactions
                        continue

                # check if participant was already found
                duplicate = False
                highest_count = 0
                for participant in participants:

                    if participant["author"] == message_author:
                        duplicate = True

                        if config.POST_PARTICIPANTS_CHAT_ID:
                            participant_time = datetime.strptime(
                                    str(participant["date"]),
                                    "%Y-%m-%d %H:%M:%S")

                            if participant_time < message_time:
                                # remember only the newest meme
                                participant = create_participant(message, message_author)
                            continue

                        if config.RANK_MEMES:
                            # already exist in participants array,
                            # only one post allowed (prefer best)
                            if participant["count"] < message_reactions:
                                # update existent meme data
                                participant = update_participant(participant, message)

                                # update stats
                                participant["views"] = message.views
                                participant["count"] = message_reactions
                            else:
                                # nothing to do, keep this
                                continue
                        else:
                            post_count = participant["count"]

                            # remember the best meme of current participant
                            if post_count > highest_count:
                                highest_count = post_count

                            if highest_count < message_reactions:
                                # replace existent meme data
                                participant = update_participant(participant, message)

                            # update reaction counter and views, sum up
                            participant["count"] += message_reactions
                            participant["views"] += message.views

                    elif message_author == "None":
                        duplicate = True

                if not duplicate:
                    # append to participants array
                    new_participant = create_participant(message, message_author)
                    participants.append(new_participant)

                    if config.POST_PARTICIPANTS_CHAT_ID:

                        if not config.SIGN_MESSAGES:
                            message_author = "@" + message_author
                        logging.info("Repost %s (message id: %s)", message_author, message.id)

                        await app.send_photo(config.POST_PARTICIPANTS_CHAT_ID,
                                message.photo.file_id,
                                message_author, parse_mode=enums.ParseMode.MARKDOWN)

            elif message_difftime.days < 0:
                # message newer than expected or excluded, keep searching messages
                continue

            else:
                # message too old from here, stop loop
                break

        # create final message with ranking
        if not config.POST_PARTICIPANTS_CHAT_ID:

            if config.CREATE_CSV:

                csv_file = write_rows_to_csv(participants)

                if config.CSV_CHAT_ID and csv_file:
                    await app.send_document(config.CSV_CHAT_ID, csv_file,
                            caption=header_message)

            final_message, winner_photo = create_ranking(participants, header_message)

            if config.FINAL_MESSAGE_CHAT_ID:

                if winner_photo != "" and config.POST_WINNER_PHOTO:
                    await app.send_photo(config.FINAL_MESSAGE_CHAT_ID, winner_photo,
                            final_message, parse_mode=enums.ParseMode.MARKDOWN)

                elif winner_photo != "" and not config.POST_WINNER_PHOTO:
                    await app.send_message(config.FINAL_MESSAGE_CHAT_ID, final_message,
                            parse_mode=enums.ParseMode.MARKDOWN)

                else:
                    log_msg = ("Something went wrong!"
                            " Can not find winner photo for final ranking message")
                    logging.warning(log_msg)

def create_participant(message, author):
    """Return new participant as dict from message object"""
    try:
        message_counter = int(message.reactions.reactions[0].count)
    except:
        message_counter = 0

    try:
        message_views = int(message.views)
    except:
        message_views = 0

    participant = {
        "count": message_counter,
        "views": message_views,
        "photo_id": message.photo.file_id,
        "author": author,
        "date": str(message.date),
        "id": message.id,
        "chat_id": message.chat.id
    }

    logging.info(participant)
    return participant

def update_participant(participant, message):
    """Update existent participant without stats"""
    participant["photo_id"] = message.photo.file_id
    participant["date"] = str(message.date)
    participant["id"] = message.id

    return participant

def get_author(message):
    """Return author from message object"""
    message_author = False

    if not config.SIGN_MESSAGES:
        # force to set author from caption
        # and not from channel signature
        if "@" in str(message.caption):
            # extract telegram handle from caption
            message_caption_array = message.caption.split()
            for caption_word in message_caption_array:
                if caption_word.startswith("@"):
                    # make sure nobody can inject commands here
                    message_author = re.sub(r"[^a-zA-Z0-9\_]", "", caption_word)

        # filter bad authors
        if ( message_author
                and "httpstme" in message_author ):
            message_author = False

    else:
        try:
            # group author
            message_author = message.from_user.id
        except AttributeError:
            # channel author
            message_author = message.author_signature

    return message_author

def build_ranking_caption():
    """"Create header of final message"""

    if config.RANK_MEMES:
        header_contest_type = "Memes"
    else:
        header_contest_type = "Contest Lords"

    formatted_date = contest_time.strftime("%d.%m.%Y %H:%M")

    header_message = (f"Top {config.CONTEST_MAX_RANKS} "
            f"{header_contest_type} (Stand: {formatted_date})")

    if config.CONTEST_DAYS == 1:
        header_message = "Rangliste 24-Stunden " + header_message
    else:
        header_message = f"Rangliste {config.CONTEST_DAYS}-Tage " + header_message

    return header_message

def write_rows_to_csv(participants):
    """Write participants data to CSV file"""
    csv_rows = []

    for participant in participants:
        participant_postlink = build_postlink(participant)
        csv_rows.append([
            participant["author"],
            participant_postlink,
            participant["date"],
            participant["count"],
            participant["views"],
            config.CONTEST_DAYS
        ])

    # open file an append rows
    csv_file = "contest_" + str(config.CHAT_ID) + ".csv"
    write_header = False
    if not path.isfile(csv_file):
        write_header = True

    with open(csv_file, mode='a', encoding="utf-8") as csvfile:
        csvwriter = csv.writer(csvfile)

        # write header if file is new
        if write_header:
            csv_fields = ['Username', 'Postlink', 'Timestamp', 'Count', 'Views', 'Mode']
            csvwriter.writerow(csv_fields)
            logging.info("CSV created: %s", csv_file)

        csvwriter.writerows(csv_rows)
        logging.info("CSV update: %s", csv_file)

    return csv_file

def get_winner(participants):
    """Extracts the best post from participants and returns the winner"""
    best_count = 0
    winner = []
    winner_id = -1

    i = 0
    for participant in participants:

        if participant["count"] >= best_count:
            best_count = participant["count"]
            winner = participant
            winner_id = i

        i += 1

    # remove winner from participants array
    if winner_id != -1 and len(participants) >= 0:
        participants.pop(winner_id)

    return winner, participants

def get_winners(participants):
    """Get all winners and return winners array"""
    winners = []

    i = 1
    while i <= config.CONTEST_MAX_RANKS:
        current_winner, participants = get_winner(participants)

        if current_winner:
            winners.append(current_winner)

        i += 1

    return winners

def create_ranking(participants, header_message):
    """Build the final ranking message"""

    # get winners
    winners = get_winners(participants)

    # init vars
    rank = 0
    last_count = 0
    winner_photo = ""
    final_message = ""

    i = 1
    for winner in winners:

        winner_count = winner["count"]

        # update rank, same rank with same count
        if last_count != winner_count:
            rank += 1
        last_count = winner_count

        # set rank 1 winner photo
        if rank == 1 and winner_photo == "":
            try:
                # chat mode
                winner_photo = winner["photo_id"]
            except KeyError:
                # csv mode
                winner_photo = winner["postlink"]

        # author prefix for telegram handle
        if not config.SIGN_MESSAGES:
            winner_display_name = "@" + winner["author"]
        else:
            winner_display_name = winner["author"]

        # add post link
        if config.POST_LINK:
            try:
                # csv mode
                winner_postlink = winner["postlink"]
            except KeyError:
                # chat mode
                winner_postlink = build_postlink(winner)

            winner_count = f"[{winner_count}]({winner_postlink})"

        final_message = final_message + "#" + str(rank) \
                + " " + winner_display_name \
                + " " + str(winner_count) \
                + " 🏆 \n"

        i += 1
        if i > config.CONTEST_MAX_RANKS:
            break

    final_message = header_message + ":\n\n" + final_message + "\n" + config.FINAL_MESSAGE_FOOTER
    logging.info("\n%s", final_message)

    return final_message, winner_photo


###########################
# CSV based ranking methods
###########################

async def create_csv_ranking():
    """Run collect data from CSV files mode"""

    header_message = build_ranking_caption()

    # Get winners from participants and create final message
    csv_file = "contest_" + str(config.CHAT_ID) + ".csv"

    csv_participants = get_csv_participants(csv_file)

    final_message, winner_photo = create_ranking(csv_participants, header_message)

    # send ranking message to given chat
    if config.FINAL_MESSAGE_CHAT_ID:

        if not final_message:
            logging.warning("Can not create final message from CSV participants (file: %s)",
                    str(csv_file))
            sys.exit()

        async with app:
            if winner_photo != "" and config.POST_WINNER_PHOTO:

                # get photo id from winner photo url
                if "https://t.me/c/" in winner_photo:
                    msg_id = get_message_id_from_postlink(winner_photo)
                    message = await app.get_messages(config.CHAT_ID, msg_id)
                    if message:
                        photo_id = get_photo_id_from_msg(message)
                        if photo_id:
                            winner_photo = photo_id

                await app.send_photo(config.FINAL_MESSAGE_CHAT_ID, winner_photo,
                        final_message, parse_mode=enums.ParseMode.MARKDOWN)

            elif winner_photo != "" and not config.POST_WINNER_PHOTO:
                await app.send_message(config.FINAL_MESSAGE_CHAT_ID, final_message,
                        parse_mode=enums.ParseMode.MARKDOWN)

            else:
                log_msg = ("Something went wrong!"
                        " Can not find winner photo for final overall ranking message")
                logging.warning(log_msg)

def create_csv_participant(csv_row):
    """Create a participant dict from CSV data"""

    participant = {
        "author": csv_row["Username"],
        "postlink": csv_row["Postlink"],
        "date": str(csv_row["Timestamp"]),
        "count": int(csv_row["Count"]),
        "views": int(csv_row["Views"])
    }

    return participant

def get_csv_participants(csvfile):
    """Collect participants from CSV file"""

    csv_participants = []
    with open(csvfile, mode='r', encoding="utf-8") as csvfile_single:

        csv_dict = csv.DictReader(csvfile_single)

        for row in csv_dict:
            duplicate = False

            # check if winner was already found
            for participant in csv_participants:

                # check for same post in different CSV files
                if row['Postlink'] == participant["postlink"]:
                    duplicate = True

                # check if User already found and add stats
                elif row['Username'] == participant["author"]:
                    participant["count"] += int(row['Count'])
                    participant["views"] += int(row['Views'])
                    duplicate = True

            if not duplicate:
                # check if row was in desired timeframe
                participant_time = datetime.strptime(str(row['Timestamp']), "%Y-%m-%d %H:%M:%S")
                participant_difftime = contest_time - participant_time

                if ( (participant_difftime.days <= config.CONTEST_DAYS-1)
                        and not participant_difftime.days < 0 ):
                    # add participant to array
                    csv_participant = create_csv_participant(row)
                    csv_participants.append(csv_participant)

    return csv_participants


##################
# Common methods
##################

def get_message_id_from_postlink(postlink):
    """return message id from postlink"""
    arrpostlink = str(postlink).split("/")
    return int(arrpostlink[-1])

def get_photo_id_from_msg(message):
    """return photo id from message object"""
    if str(message.media) == "MessageMediaType.PHOTO":
        return message.photo.file_id

    return False

def check_excludes(caption):
    """Check for excludes in message caption"""
    for exclude in config.EXCLUDE_PATTERN:
        if exclude in str(caption):
            return True

    return False

def build_postlink(participant):
    """Builds link to given message"""
    participant_id = str(participant["id"])
    participant_chat_id = str(participant["chat_id"]).replace("-100","")
    postlink = "https://t.me/c/" + participant_chat_id + "/" + participant_id
    return postlink

app.run(main())
