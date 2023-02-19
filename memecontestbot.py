#!/usr/bin/env python
"""
Simple Bot to analyze telegram post reactions and create a ranking.
Can be configured for daily or weekly rankings
(get_chat_history has a limit of posts to return from chat).

Usage:
Start bot to create a nice ranking.
"""

# default imports
import os
import sys
import logging
import copy
import csv
import re

from datetime import datetime, timedelta

# telegram api
from pyrogram import Client, enums
from pyrogram.types import InputMediaPhoto

# image manipulation api
from PIL import Image, ImageDraw, ImageFont

# own modules
import settings

VERSION_NUMBER = "v1.2.1"

config = settings.load_config()
api = settings.load_api()

app = Client("my_account", api_id=api.ID, api_hash=api.HASH)

# global vars
contest_time = datetime.strptime(config.CONTEST_DATE, "%Y-%m-%d %H:%M:%S")
contest_year = contest_time.strftime("%Y")

# set csv file name
CSV_FILE = (
    "contest_"
    + str(config.CHAT_ID)
    + "_"
    + contest_year
    + ".csv"
)
if isinstance(config.CREATE_CSV, str):
    CSV_FILE = config.CREATE_CSV

async def main():
    """This function will run the bot"""
    logging.info("Start meme contest bot version %s", VERSION_NUMBER)

    if config.PARTITICPANTS_FROM_CSV:
        # create a ranking message from CSV data
        await create_csv_ranking()

        # do not walk through chat history
        sys.exit()

    if config.CONTEST_POLL_RESULT:
        await evaluate_poll()

        sys.exit()

    participants = []

    if config.POST_PARTICIPANTS_CHAT_ID:
        # get all unique file ids from CSV
        unique_ids = get_csv_unique_ids()
        # init senders array to prevent abuse
        message_senders = []
    else:
        # need a header message if not in collect mode
        header_message = build_ranking_caption()

    async with app:
        async for message in app.get_chat_history(config.CHAT_ID):

            # check excludes in message caption
            if check_excludes(message.caption):
                continue

            # check if message is a photo
            if str(message.media) != "MessageMediaType.PHOTO":
                continue

            # check for valid author in message
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
                else:
                    # prevent from caption abuse, check sender
                    message_sender = get_sender(message)
                    if message_sender in message_senders:
                        logging.info(
                            "Skip duplicate from '%s' as '%s' (message id: %s)",
                            message_sender,
                            message_author,
                            message.id
                        )
                        continue

                    message_senders.append(message_sender)

                # no views in groups
                message_views = 0
                if message.views:
                    message_views = message.views

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
                                participant["count"] = message_reactions
                                participant["views"] = message_views
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
                            participant["views"] += message_views

                    elif message_author == "None":
                        duplicate = True

                if not duplicate:
                    # Ranking mode: append to participants array to create ranking
                    new_participant = create_participant(message, message_author)
                    participants.append(new_participant)

                    if config.POST_PARTICIPANTS_CHAT_ID:

                        # check unique file id
                        unique_check = False
                        for unique_id in unique_ids:
                            if unique_id[1] == message.photo.file_unique_id:

                                # send repost message
                                repost_msg = (
                                    "Dieses Meme ist bereits bekannt, "
                                    + f"[schau hier]({unique_id[0]})"
                                )
                                logging.info("%s (reply to msg id %s)",
                                    repost_msg,
                                    str(message.id)
                                )

                                if config.POST_PARTICIPANTS_CHAT_ID != "TEST":
                                    await app.send_message(config.CHAT_ID, repost_msg,
                                            reply_to_message_id=message.id,
                                            parse_mode=enums.ParseMode.MARKDOWN)

                                unique_check = True
                                break

                        # skip this message if it is a repost
                        if unique_check:
                            continue

                        # Collect mode: post message to given chat
                        if not config.SIGN_MESSAGES:
                            message_author = "@" + message_author
                        logging.info("Collect %s (message id: %s)",
                                message_author,
                                message.id
                        )

                        # extract hashtag from caption
                        message_hashtags = get_caption_pattern(message.caption, "#")

                        if message_hashtags:
                            photo_caption = message_author + "\n\n" + message_hashtags
                            logging.info("Hashtags: %s", message_hashtags)
                        else:
                            photo_caption = message_author

                        if config.POST_PARTICIPANTS_CHAT_ID != "TEST":
                            await app.send_photo(config.POST_PARTICIPANTS_CHAT_ID,
                                    message.photo.file_id,
                                    photo_caption, parse_mode=enums.ParseMode.MARKDOWN)

            elif message_difftime.days < 0:
                # message newer than expected or excluded, keep searching messages
                continue

            else:
                # message too old from here, stop loop
                break

        # create final message with ranking
        if not config.POST_PARTICIPANTS_CHAT_ID:

            if config.CREATE_CSV:

                write_rows_to_csv(participants)

                if config.CSV_CHAT_ID and CSV_FILE:
                    await app.send_document(config.CSV_CHAT_ID, CSV_FILE,
                            caption=header_message)

            if config.CONTEST_POLL:
                # Poll mode: Create a voting poll for winners
                await create_poll(participants)

                sys.exit()

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
    # initialize defaults
    message_counter = 0
    message_views = 0

    if not config.POST_PARTICIPANTS_CHAT_ID:
        try:
            message_counter = int(message.reactions.reactions[0].count)
            message_views = int(message.views)
        except AttributeError as ex_attr:
            logging.error(ex_attr)
        except TypeError as ex_type:
            logging.error(ex_type)

    participant = {
        "count": message_counter,
        "views": message_views,
        "photo_id": message.photo.file_id,
        "unique_id": message.photo.file_unique_id,
        "author": author,
        "date": str(message.date),
        "id": message.id,
        "chat_id": message.chat.id
    }

    return participant

def update_participant(participant, message):
    """Update existent participant without stats"""
    participant["photo_id"] = message.photo.file_id
    participant["unique_id"] = message.photo.file_unique_id
    participant["date"] = str(message.date)
    participant["id"] = message.id

    return participant

def get_caption_pattern(caption, pattern, count = 1):
    """Return findings from message caption as string"""
    caption_findings = []
    caption_new = False

    if pattern in str(caption):
        message_caption_array = caption.split()
        i = 1
        for caption_word in message_caption_array:
            if caption_word.startswith(pattern):
                # make sure nobody can inject commands here
                if count >= i:
                    caption_findings.append(re.sub(r"[^a-zA-Z0-9äöüÄÖÜß\_]", "", caption_word))
                    i += 1

        # add finding to new caption string
        for finding in caption_findings:
            if finding == "":
                continue

            if not caption_new:
                caption_new = pattern + finding
            else:
                caption_new = caption_new + " " + pattern + finding

    return caption_new

def get_author(message):
    """Return author from message object"""
    message_author = False

    if not config.SIGN_MESSAGES:
        # # force to set author from caption
        # # and not from channel signature
        message_author = get_caption_pattern(message.caption, "@")
        if message_author:
            message_author = message_author.replace("@","")

        # filter bad authors
        if ( message_author
                and "httpstme" in message_author ):
            message_author = False

    else:
        message_author = get_sender(message)

    return message_author

def get_sender(message):
    '''Return sender from message object'''
    message_sender = False

    try:
        # group sender
        message_sender = message.from_user.id
    except AttributeError:
        # channel sender with sign messages enabled
        message_sender = message.author_signature

    return message_sender

def build_ranking_caption():
    """"Create header of final message"""

    if config.RANK_MEMES:
        header_contest_type = "Memes"
    else:
        header_contest_type = "Contest Lords"

    formatted_date = contest_time.strftime("%d.%m.%Y %H:%M")

    header_message = (
        f"{config.FINAL_MESSAGE_HEADER}"
        f"Top {config.CONTEST_MAX_RANKS} "
        f"{header_contest_type} (Stand: {formatted_date})"
    )

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
            config.CONTEST_DAYS,
            participant["unique_id"]
        ])

    # open file an append rows
    write_header = False
    if not os.path.isfile(CSV_FILE):
        write_header = True

    with open(CSV_FILE, mode='a', encoding="utf-8") as csvfile:
        csvwriter = csv.writer(csvfile)

        # write header if file is new
        if write_header:
            csv_fields = [
                'Username',
                'Postlink',
                'Timestamp',
                'Count',
                'Views',
                'Mode',
                'Unique ID'
            ]

            csvwriter.writerow(csv_fields)
            logging.info("CSV created: %s", CSV_FILE)

        csvwriter.writerows(csv_rows)
        logging.info("CSV update: %s", CSV_FILE)

    return CSV_FILE

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

def create_ranking(participants, header_message, unique_ranks = False):
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

        # update rank
        if not unique_ranks:
            # same rank with same count
            if last_count != winner_count:
                rank += 1
            last_count = winner_count
        else:
            # unique ranks
            rank += 1

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
# Poll mode methods
###########################

async def find_poll():
    '''search for the last open poll'''
    poll_message = False

    async with app:
        async for message in app.get_chat_history(config.CHAT_ID):

            if str(message.media) != "MessageMediaType.POLL":
                continue

            # the first poll we find needs to be open to evaluate
            if message.poll.is_closed:
                logging.info(
                    "Last poll found is already closed, "
                    "nothing to evaluate! (message id: %s)",
                    message.id
                )
            else:
                poll_message = message

            break

    return poll_message

async def evaluate_poll():
    '''search for the last open poll and evaluate'''
    poll_message = await find_poll()

    if not poll_message:
        return False

    # remember the reply message id
    poll_reply_message_id = poll_message.reply_to_message_id

    async with app:
        # stop the poll and update poll message with results
        logging.info("Stop poll now (message id: %s)", poll_message.id)
        poll_message = await app.stop_poll(config.CHAT_ID, poll_message.id)

        # find the best answer
        best_vote_count = 0
        best_option = False
        second_best_vote_count = 0
        second_best_option = False

        for option in poll_message.options:
            if option.voter_count > best_vote_count:
                best_vote_count = option.voter_count
                best_option = option.text
            elif ( option.voter_count > 0
                    and option.voter_count == best_vote_count ):
                second_best_option = option.text

        if not best_option:
            logging.info("Was not able to find the best vote!")
            return False

        if best_vote_count == second_best_vote_count:
            logging.info("Draw in poll found: %s vs %s", best_option, second_best_option)

        # check the caption of poll based ranking message
        ranking_message = await app.get_messages(
            config.CHAT_ID,
            poll_reply_message_id
        )

        if not ranking_message:
            logging.info(
                "No message '%s' found in '%s)",
                poll_reply_message_id,
                config.CHAT_ID
            )
            return False

        i = 1
        postlink = False
        for entity in ranking_message.caption_entities:
            if entity.url:
                if i <= config.CONTEST_MAX_RANKS and i == int(best_option[0]):
                    postlink = entity.url
                    break
                i += 1

        if postlink:
            message = await get_message_from_postlink(postlink)
            if message:
                photo_id = get_photo_id_from_msg(message)

                if photo_id:
                    poll_time = build_timeframe(contest_time, config.CONTEST_DAYS)
                    message_author = get_author(message)

                    final_message = (
                        f"{config.FINAL_MESSAGE_HEADER}"
                        f"{poll_time}\n\n"
                        f"@{message_author}\n\n"
                        f"{config.FINAL_MESSAGE_FOOTER}"
                    )

                    await app.send_photo(config.FINAL_MESSAGE_CHAT_ID, photo_id,
                        final_message, parse_mode=enums.ParseMode.MARKDOWN,
                        reply_to_message_id=poll_reply_message_id)

                    return True
        else:
            return False

async def create_poll(participants):
    '''Create a poll to vote a winner from'''

    # get winners and do not touch the main participants array
    media_participants = copy.deepcopy(participants)
    winners = get_winners(media_participants)

    # create the ranking message
    header_message = build_ranking_caption()
    final_message, _winner_photo = create_ranking(participants, header_message, True)

    # create numbered photos from winners
    media_group = []
    poll_answers = []
    rank = 1
    for winner in winners:

        logging.info("Create numbered image %s (message id: %s)", rank, winner["id"])
        await create_numbered_photo(winner["photo_id"], rank)

        poll_answers.append(f"{rank}. Meme")

        if rank == 1:
            media_group.append(InputMediaPhoto("images/image_" + str(rank) + ".jpg", final_message))
        else:
            media_group.append(InputMediaPhoto("images/image_" + str(rank) + ".jpg"))

        rank += 1
        if rank > config.CONTEST_MAX_RANKS:
            break

    if config.FINAL_MESSAGE_CHAT_ID:

        media_group_message = await app.send_media_group(
            config.FINAL_MESSAGE_CHAT_ID,
            media_group
        )

        # create question message
        poll_time = build_timeframe(contest_time, config.CONTEST_DAYS)
        poll_question = (
            "Die Wahl zum Meme der Woche\n"
            f"vom {poll_time} (24h Abstimmung)"
        )

        await app.send_poll(
            config.FINAL_MESSAGE_CHAT_ID,
            poll_question,
            poll_answers,
            reply_to_message_id=media_group_message[0].id
        )

async def create_numbered_photo(photo_id, number):
    '''Returns a photo with a watermark as number'''
    media = await app.download_media(photo_id, in_memory=True)

    if not media:
        return False

    #Create an Image Object from an Image
    image = Image.open(media)

    # scale down the image
    maxsize = (500, 500)
    image.thumbnail(maxsize, Image.ANTIALIAS)

    # get image size
    width, height = image.size

    # create a draw object from image
    draw = ImageDraw.Draw(image)

    # define the font
    if os.name == 'nt':
        font = ImageFont.truetype('arial.ttf', 136)
    else:
        font = ImageFont.truetype('DejaVuSans.ttf', 136)
    textwidth, textheight = draw.textsize(str(number), font)

    # calculate the x,y coordinates of the text
    dim_x = width/2 - textwidth/2
    dim_y = height/2 - textheight/2

    # draw the number
    draw.text(
        (dim_x, dim_y),
        str(number),
        align="center",
        font=font,
        fill="#f27600",
        stroke_width=4,
        stroke_fill='black'
    )

    # DEBUG
    # image.show()

    #Save watermarked image
    if not os.path.exists('images'):
        os.makedirs('images')

    img_name = 'images/image_' + str(number) + '.jpg'
    image.save(img_name)
    logging.info("Save image as %s", img_name)

###########################
# CSV based ranking methods
###########################

async def create_csv_ranking():
    """Run collect data from CSV files mode"""
    header_message = build_ranking_caption()

    # Get winners from participants and create final message
    csv_participants = get_csv_participants()

    final_message, winner_photo = create_ranking(csv_participants, header_message)

    # send ranking message to given chat
    if config.FINAL_MESSAGE_CHAT_ID:

        if not final_message:
            logging.warning("Can not create final message from CSV participants (file: %s)",
                    str(CSV_FILE))
            sys.exit()

        async with app:
            if winner_photo != "" and config.POST_WINNER_PHOTO:

                # check if winner_photo is a postlink
                if "https://t.me/c/" in winner_photo:
                    message = await get_message_from_postlink(winner_photo)
                    if message:
                        photo_id = get_photo_id_from_msg(message)
                        if photo_id:
                            # set photo id
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

def get_csv_participants():
    """Collect participants from CSV file"""
    csv_participants = []
    with open(CSV_FILE, mode='r', encoding="utf-8") as csvfile_single:

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

def get_csv_unique_ids():
    """Collect unique file ids from CSV file"""
    csv_unique_ids = []

    if os.path.isfile(CSV_FILE):

        with open(CSV_FILE, mode='r', encoding="utf-8") as csvfile_single:

            csv_dict = csv.DictReader(csvfile_single)

            logging.info("Load unique IDs from CSV %s", CSV_FILE)

            i = 0
            for row in csv_dict:
                try:
                    if row['Unique ID'] != "":
                        csv_unique_ids.append([row['Postlink'], row['Unique ID'],])
                        i += 1
                except KeyError:
                    logging.info("Unique ID is missing in CSV. Skip repost check!")
                    continue

            logging.info("Unique IDs found: %d", i)
    else:
        logging.warning("No CSV to recheck known unique IDs (%s)", CSV_FILE)

    return csv_unique_ids

##################
# Common methods
##################

async def get_message_from_postlink(postlink):
    """return message from postlink"""
    msg_id = get_message_id_from_postlink(postlink)
    chat_id = get_chat_id_from_postlink(postlink)

    message = await app.get_messages(chat_id, msg_id)

    return message

def get_chat_id_from_postlink(postlink):
    """return chat id from postlink"""
    arrpostlink = str(postlink).split("/")
    chat_id = -int(f"{100}{int(arrpostlink[-2])}")
    return chat_id

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

def build_timeframe(current_time, days):
    '''Calculate start and end date and return string'''
    date_list = [current_time - timedelta(days=x) for x in range(days)]
    date_start = ""
    date_end = ""
    date_message = ""

    i = 0
    for date in reversed(date_list):
        if i == 0:
            date_start = date.strftime("%d.%m")
        elif i == len(date_list)-1:
            date_end = date.strftime("%d.%m.%Y")
        i += 1

    if date_start != "" and date_end != "":
        date_message = f"{date_start} - {date_end}"

    return date_message

app.run(main())
