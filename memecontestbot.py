#!/usr/bin/env python
"""
Bot to analyze telegram post reactions and create a ranking.
Can be configured for daily and weekly rankings,
collect and repost messages, log results to CSV or
update a highscore message.

Usage:
Start bot to create a ranking message
or set some configurations for advanced usage
"""

# default imports
import os
import sys
import logging
import copy
import csv
import re
import time
import random

from datetime import datetime, timedelta

# telegram api
import asyncio
from pyrogram import Client, enums
from pyrogram.types import InputMediaPhoto
from pyrogram.errors import FloodWait, MessageNotModified

# image manipulation api
from PIL import Image, ImageDraw, ImageFont

# own modules
import settings

VERSION_NUMBER = "v1.4.1"

config = settings.load_config()
api = settings.load_api()

app = Client("my_account", api_id=api.ID, api_hash=api.HASH)

async def main():
    """This function will run the bot"""
    contest_time = build_strptime(config.CONTEST_DATE)
    formatted_date = contest_time.strftime("%d.%m.%Y %H:%M")
    logging.info("Start meme contest bot version '%s' at %s", VERSION_NUMBER, formatted_date)

    if config.PARTICIPANTS_LIST:
        yellow_cards, orange_cards = get_inactivities_from_csv()

    async with app:

        if config.PARTICIPANTS_LIST:
            await send_inactivity_message(yellow_cards, orange_cards)
            sys.exit()

        if config.CONTEST_POLL:
            # Poll mode: Create a voting poll for winners
            await create_poll()

            sys.exit()

        if config.PARTICIPANTS_FROM_CSV:
            # CSV Mode: Create a ranking message from CSV data
            await create_ranking_from_csv()

            sys.exit()

        participants = await get_participants()

        if config.CONTEST_POLL_RESULT:
            # Poll mode: Evaluate last open poll found
            await evaluate_poll(participants)

            sys.exit()

        # create final message with ranking
        if not config.POST_PARTICIPANTS_CHAT_ID:

            if config.CREATE_CSV:

                rows_count = write_rows_to_csv(participants)

                if rows_count > 0 and config.CSV_CHAT_ID and config.CSV_FILE:
                    header_message = build_ranking_caption()
                    await app.send_document(config.CSV_CHAT_ID, config.CSV_FILE,
                            caption=header_message)

            final_message, winner = create_ranking(participants)

            if config.FINAL_MESSAGE_CHAT_ID:

                if winner['photo'] != "" and config.POST_WINNER_PHOTO:
                    await send_photo_caption(
                        config.FINAL_MESSAGE_CHAT_ID,
                        winner['photo'],
                        final_message
                    )

                elif winner['photo'] != "" and not config.POST_WINNER_PHOTO:
                    await app.send_message(config.FINAL_MESSAGE_CHAT_ID, final_message,
                            parse_mode=enums.ParseMode.MARKDOWN)

                else:
                    log_msg = ("Something went wrong!"
                            " Can not find winner photo for final ranking message")
                    logging.warning(log_msg)

            if config.CONTEST_HIGHSCORE:
                await update_highscore(winner['display_name'])

async def send_collected_photo(message, message_author):
    """send collected photo from message to POST_PARTICIPANTS_CHAT_ID"""
    if not config.SIGN_MESSAGES:
        message_author = "@" + message_author
    logging.info("Collect %s (message id: %s, unique id: %s)",
            message_author,
            message.id,
            message.photo.file_unique_id
    )

    # extract hashtag from caption
    message_hashtags = get_caption_pattern(message.caption, "#")
    if message_hashtags:
        photo_caption = message_author + "\n\n" + message_hashtags
        logging.info("Hashtags: %s", message_hashtags)
    else:
        photo_caption = message_author

    # add footer
    if config.FINAL_MESSAGE_FOOTER != "":
        photo_caption = photo_caption + "\n\n" + config.FINAL_MESSAGE_FOOTER

    # send the photo
    if config.POST_PARTICIPANTS_CHAT_ID != "TEST":
        try:
            await app.send_photo(config.POST_PARTICIPANTS_CHAT_ID,
                    message.photo.file_id,
                    photo_caption, parse_mode=enums.ParseMode.MARKDOWN)
        except FloodWait as ex_flood:
            logging.warning("Wait %s seconds to send more photos...", ex_flood.value)
            await asyncio.sleep(ex_flood.value)
            # retry
            await app.send_photo(config.POST_PARTICIPANTS_CHAT_ID,
                    message.photo.file_id,
                    photo_caption, parse_mode=enums.ParseMode.MARKDOWN)

async def send_photo_caption(chatid, photo, caption):
    """split the photo caption into chunks if too long"""
    chunks = get_chunks(caption, 2048)
    i = 0
    for chunk in chunks:
        if i == 0 and photo:
            await app.send_photo(chatid, photo,
                    chunk, parse_mode=enums.ParseMode.MARKDOWN)
        else:
            await app.send_message(chatid, chunk,
                    parse_mode=enums.ParseMode.MARKDOWN)
        i += 1

async def check_repost(message, unique_ids):
    """check unique file id"""
    unique_check = False
    for unique_id in unique_ids:
        if unique_id[1] == message.photo.file_unique_id:

            # send repost message
            repost_msg = (
                "Dieses Meme ist bereits bekannt, "
                + f"[schau hier]({unique_id[0]})"
            )
            logging.info("%s (reply to msg id %s, photo id %s)",
                repost_msg,
                str(message.id),
                str(message.photo.file_unique_id)
            )

            if config.FINAL_MESSAGE_CHAT_ID:
                await app.send_message(config.FINAL_MESSAGE_CHAT_ID, repost_msg,
                        reply_to_message_id=message.id,
                        parse_mode=enums.ParseMode.MARKDOWN)

            unique_check = True
            break

    return unique_check

async def get_participants():
    """read chat history and return participants"""
    contest_time = build_strptime(config.CONTEST_DATE)
    participants = []

    if config.POST_PARTICIPANTS_CHAT_ID:
        # get all unique file ids from CSV
        unique_ids = get_unique_ids_from_csv()
        # init senders array to prevent abuse
        message_senders = []

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
        message_time = build_strptime(str(message.date))
        message_difftime = contest_time - message_time

        if ( (message_difftime.days < config.CONTEST_DAYS+1)
                and not message_difftime.days < 0 ):

            # prevent from caption abuse, check sender
            if config.POST_PARTICIPANTS_CHAT_ID:
                message_sender = get_sender(message)
                if message_sender in message_senders:
                    logging.info(
                        "Skip duplicate from '%s' (message id: %s)",
                        message_author,
                        message.id
                    )
                    continue
                message_senders.append(message_sender)

            if not config.PARTICIPANT_DUPLICATES:
                participants, duplicate = check_participant_duplicates(
                    participants,
                    message,
                    message_author
                )

            if config.PARTICIPANT_DUPLICATES or not duplicate:
                # Ranking mode: append to participants array to create ranking
                new_participant = create_participant(message, message_author)
                participants.append(new_participant)

                # Collect mode
                if config.POST_PARTICIPANTS_CHAT_ID:
                    # skip this message if it is a repost
                    unique_check = await check_repost(message, unique_ids)
                    if unique_check:
                        continue

                    await send_collected_photo(message, message_author)

        elif message_difftime.days < 0:
            # message newer than expected or excluded, keep searching messages
            continue

        else:
            # message too old from here, stop loop
            break

    return participants

def create_participant(message, author):
    """Return new participant as dict from message object"""
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
        except IndexError as ex_index:
            logging.error(ex_index)

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
    logging.info("Create Participant %s (%d votes from %s)",
            participant['author'],
            participant['count'],
            participant['date'])

    return participant

def check_participant_duplicates(participants, message, message_author):
    """check if participant was already found"""
    message_reactions = get_reactions(message)
    if not message_reactions:
        return participants, True

    # no views in groups
    message_views = 0
    if hasattr(message, 'views'):
        message_views = message.views

    duplicate = False
    highest_count = 0
    for participant in participants:

        if participant["author"].lower() == message_author.lower():
            duplicate = True

            if config.POST_PARTICIPANTS_CHAT_ID:
                participant_time = datetime.strptime(
                        str(participant["date"]),
                        "%Y-%m-%d %H:%M:%S")

                message_time = build_strptime(str(message.date))
                if participant_time < message_time:
                    # remember only the newest meme
                    participant = create_participant(message, message_author)
                continue

            if config.RANK_MEMES:
                # already exist in participants array,
                # only one post allowed (prefer best)
                if participant["count"] < message_reactions:
                    # update existent meme data
                    participant["photo_id"] = message.photo.file_id
                    participant["unique_id"] = message.photo.file_unique_id
                    participant["date"] = str(message.date)
                    participant["id"] = message.id

                    logging.info("Update Participant %s (%d < %d votes from %s)",
                            participant["author"],
                            participant["count"],
                            message_reactions,
                            participant["date"])

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
                    # replace existent meme data with best meme data
                    participant["photo_id"] = message.photo.file_id
                    participant["unique_id"] = message.photo.file_unique_id
                    participant["id"] = message.id

                participant["date"] = str(message.date)

                logging.info("Update Participant %s (%d + %d = %d votes from %s)",
                        participant["author"],
                        participant["count"],
                        message_reactions,
                        (participant["count"] + message_reactions),
                        participant["date"])

                # update reaction counter and views, sum up
                participant["count"] += message_reactions
                participant["views"] += message_views

        elif message_author == "None":
            duplicate = True

    return participants, duplicate

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
    """Return sender from message object"""
    message_sender = False

    try:
        # group sender
        message_sender = message.from_user.id
    except AttributeError:
        # channel sender with sign messages enabled
        message_sender = message.author_signature

    return message_sender

def get_reactions(message):
    """get reactions from given message"""
    message_reactions = 1

    if not config.POST_PARTICIPANTS_CHAT_ID:
        # verify reactions for ranking message
        try:
            message_reactions = message.reactions.reactions[0].count
        except AttributeError:
            # skip this message for missing reactions
            return False

    return message_reactions

def build_ranking_caption():
    """Create header of final message"""
    if config.RANK_MEMES:
        header_contest_type = "Memes"
    else:
        header_contest_type = "Contest Lords"

    header_message = (
        f"{config.FINAL_MESSAGE_HEADER}"
        f"Top {config.CONTEST_MAX_RANKS} "
        f"{header_contest_type}"
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
    if not os.path.isfile(config.CSV_FILE):
        write_header = True

    with open(config.CSV_FILE, mode='a', encoding="utf-8") as csvfile:
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
            logging.info("CSV created: %s", config.CSV_FILE)

        csvwriter.writerows(csv_rows)
        logging.info("CSV update %d rows in %s", len(csv_rows), config.CSV_FILE)

    return len(csv_rows)

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

async def get_daily_winners():
    """get daily based winners, only one winner each day"""
    daily_winners = []
    contest_time = build_strptime(config.CONTEST_DATE)

    if config.PARTICIPANTS_FROM_CSV:
        participants = get_participants_from_csv()
    else:
        participants = await get_participants()

    # find a winner for each contest day
    i = 1
    while i <= config.CONTEST_DAYS+1:
        daily_ranking_time = contest_time-timedelta(days=i)
        daily_participants = []

        for participant in participants:
            participant_time = build_strptime(str(participant['date']))
            participant_diff_time = contest_time - participant_time

            if ( (participant_time - daily_ranking_time).days == 0
                    and (participant_diff_time.days > 0) ):
                daily_participants.append(participant)

        winner, _participants = get_winner(daily_participants)
        if winner:
            logging.info("Add Winner %s from %s", winner['author'], winner['date'])
            daily_winners.append(winner)

        i += 1

    return daily_winners

def create_ranking(participants, unique_ranks = False, sort = True):
    """Build the final ranking message"""
    logging.info("Create ranking (%d Participants)", len(participants))

    # clean up participants, keep only CONTEST_DAYS for ranking
    contest_time = build_strptime(config.CONTEST_DATE)
    participants_ranking = []
    for participant in participants:
        # check if message was in desired timeframe
        participant_time = build_strptime(str(participant['date']))
        participant_difftime = contest_time - participant_time

        if ( (participant_difftime.days < config.CONTEST_DAYS)
                and not participant_difftime.days < 0 ):
            participants_ranking.append(participant)

    # get winners
    if sort:
        # sort participants by views
        participants_ranking = sorted(participants_ranking,
                key=lambda x: x['views'], reverse = True)
        winners = get_winners(participants_ranking)
    else:
        # ranking in poll mode
        winners = participants_ranking

    # init vars
    rank = 0
    last_count = 0
    winner = { "display_name": "", "photo": "" }
    final_message = ""
    templ_winner = "Unbekannt"
    templ_count = 0

    i = 1
    for participant in winners:

        winner_count = participant["count"]

        # update rank
        if not unique_ranks:
            # same rank with same count
            if last_count != winner_count:
                rank += 1
            last_count = winner_count
        else:
            # unique ranks
            rank += 1

        # set rank 1 participant photo
        if rank == 1 and winner['photo'] == "":
            if "photo_id" in participant:
                # chat mode
                winner['photo'] = participant["photo_id"]
            elif "postlink" in participant:
                # csv mode
                winner['photo'] = participant["postlink"]

        # author prefix for telegram handle
        if not config.SIGN_MESSAGES:
            display_name = "@" + participant["author"]
        else:
            display_name = participant["author"]

        # add post link
        if config.POST_LINK:
            if "postlink" in participant:
                # csv mode
                winner_postlink = participant["postlink"]
            else:
                # chat mode
                winner_postlink = build_postlink(participant)

            winner_count = f"[{winner_count}]({winner_postlink})"

        final_message = final_message + "#" + str(rank) \
                + " " + display_name \
                + " (" + str(winner_count) \
                + ")"

        if rank == 1 and templ_winner == "Unbekannt":
            final_message = final_message + config.RANKING_WINNER_SUFFIX + "\n"
            templ_winner = display_name
            templ_count = winner_count
        else:
            final_message = final_message + "\n"

        i += 1
        if i > config.CONTEST_MAX_RANKS:
            break

    header_message = build_ranking_caption()

    # update placeholder
    if "TEMPLATE_WINNER" in header_message:
        header_message = header_message.replace(
            r"{TEMPLATE_WINNER}",
            templ_winner
        )
    if "TEMPLATE_VOTES" in header_message:
        header_message = header_message.replace(
            r"{TEMPLATE_VOTES}",
            str(templ_count)
        )
    winner['display_name'] = templ_winner

    # build final message
    final_message = (
        header_message
        + ":\n\n"
        + final_message
        + "\n"
        + config.FINAL_MESSAGE_FOOTER
    )

    logging.info("\n%s", final_message)

    return final_message, winner

###########################
# Highscore methods
###########################

async def update_highscore(winner_name):
    """Update the highscore message"""
    message = await get_message_from_postlink(config.CONTEST_HIGHSCORE)
    if hasattr(message, 'text'):
        highscore = message.text
        if highscore:
            # find and edit the winner
            new_highscore = ""
            highscore_lines = highscore.split("\n")
            new_highscore_lines = []
            found_winner = False

            count_ranks = 0
            count_lines = 0
            next_line = 0
            rank_prefix = ""
            for line in highscore_lines:
                count_lines += 1
                if len(line) >= 2:
                    if line[0].isdigit() or line[1].isdigit():
                        # remember rank prefix like # if used
                        if not line[0].isdigit():
                            rank_prefix = line[0]
                        count_ranks += 1
                        next_line = count_lines

                        if line.lower().find(winner_name.lower()) > 0:
                            found_winner = True
                            logging.info("Update highscore for %s (ranks: %d)",
                                winner_name,
                                count_ranks
                            )
                            line, highscore_lines[next_line] = update_highscore_line(
                                line,
                                highscore_lines[next_line],
                                winner_name
                            )
                # remember the line and modifications in a new array
                new_highscore_lines.append(line)

            if not found_winner:
                # append winner to highscore
                if new_highscore_lines[next_line] == "":
                    found_winner = True
                    new_line = (str(rank_prefix)
                        + str(count_ranks+1)
                        + "  "
                        + str(winner_name)
                        + " "
                        + str(config.RANKING_WINNER_SUFFIX)
                        + "\n")
                    new_highscore_lines[next_line] += new_line
                    logging.info("Update highscore append new %s",
                        new_highscore_lines[next_line]
                    )

            # rebuild the highscore message from modified lines
            new_highscore = "\n".join(new_highscore_lines)

            # finally update highscore message
            if found_winner:
                chat_id = get_chat_id_from_postlink(config.CONTEST_HIGHSCORE)
                message_id = get_message_id_from_postlink(config.CONTEST_HIGHSCORE)
                if chat_id and message_id:
                    try:
                        await app.edit_message_text(chat_id, message_id, new_highscore)
                    except MessageNotModified as ex_modified:
                        logging.warning(ex_modified)
                else:
                    logging.error("Update highscore failed, "
                        "chat id and/or message id was not found in %s",
                        config.CONTEST_HIGHSCORE
                    )
            else:
                logging.warning("Update highscore: winner %s was not found in highscore (%s)",
                    winner_name,
                    config.CONTEST_HIGHSCORE
                )
        else:
            logging.error("Update highscore failed, message text was missing in %s",
                config.CONTEST_HIGHSCORE
            )
            return False
    else:
        logging.error("Update highscore failed, "
            "message not found from %s ('Copy Post Link' "
            "in Telegram for valid link)",
            config.CONTEST_HIGHSCORE
        )

def update_highscore_line(line, next_line, winner_name):
    """Update the line in highscore"""
    medal_pos = line.find(config.RANKING_WINNER_SUFFIX)
    if medal_pos > 0 or re.findall("[a-zA-Z]", next_line):
        if not line[medal_pos-1] == "x":
            if re.findall(config.RANKING_WINNER_SUFFIX, line):
                # medal already exist, increase medal counter
                line = line.replace(config.RANKING_WINNER_SUFFIX,
                    "2x"+config.RANKING_WINNER_SUFFIX,
                    1
                )
                logging.info("Update highscore medals 2x%s", config.RANKING_WINNER_SUFFIX)
            else:
                # user without medal found
                line = line + config.RANKING_WINNER_SUFFIX

                logging.info("Update highscore medal, append new %s", config.RANKING_WINNER_SUFFIX)
        else:
            # medal counter found, increase
            line = update_highscore_medal_counter(line)
    else:
        # check next line for medals
        medal_pos = next_line.find(config.RANKING_WINNER_SUFFIX)
        if medal_pos > 0:
            if not next_line[medal_pos-1] == "x":
                # medal already exist, add medal counter
                next_line = next_line.replace(config.RANKING_WINNER_SUFFIX,
                    " 2x"+config.RANKING_WINNER_SUFFIX,
                    1
                )
                logging.info("Update highscore medals 2x%s", config.RANKING_WINNER_SUFFIX)
            else:
                # medal counter found, increase
                next_line = update_highscore_medal_counter(next_line)
        else:
            # first medal, just append
            if line.endswith(winner_name):
                line += " "
            line += config.RANKING_WINNER_SUFFIX

    return line, next_line

def update_highscore_medal_counter(line):
    """Find and update the medal counter"""
    found_medal = False
    found_counter = False
    num_string = ""

    for char in reversed(line):
        if char == config.RANKING_WINNER_SUFFIX:
            found_medal = True

        if found_medal and char.isdigit():
            found_counter = True

        if found_counter and char.isdigit():
            num_string += char

        if found_counter and not char.isdigit():
            break

    medal_counter = ""
    for num_char in reversed(num_string):
        medal_counter = medal_counter + num_char

    if medal_counter != "":
        search_string = medal_counter + "x" + config.RANKING_WINNER_SUFFIX
        replace_string = str(int(medal_counter) + 1) + "x" + config.RANKING_WINNER_SUFFIX
        line = line.replace(search_string, replace_string)
        logging.info("Update highscore medals %s -> %s", search_string, replace_string)

    return line

###########################
# Poll mode methods
###########################

async def find_open_poll():
    """search for the last open poll"""
    poll_message = False

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

async def evaluate_poll(participants):
    """search for the last open poll and evaluate"""
    poll_message = await find_open_poll()

    if not poll_message:
        return False

    # remember the reply message id
    if hasattr(poll_message, 'reply_to_message_id'):
        poll_reply_message_id = poll_message.reply_to_message_id
    else:
        logging.error("Reply to message ID was missing from poll")
        return False

    # stop the poll and update poll message with results
    logging.info("Stop poll now (message id: %s)", poll_message.id)
    poll_message = await app.stop_poll(config.CHAT_ID, poll_message.id)

    if not hasattr(poll_message, 'options'):
        logging.error("Poll message is missing results, stop first")
        return False

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
        logging.warning("Was not able to find the best vote!")
        return False

    logging.info("Best option found as %s with %d votes", best_option, best_vote_count)

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
            # search for winner postlink in caption
            if i <= config.CONTEST_MAX_RANKS and i == int(best_option[0]):
                if hasattr(entity, 'url'):
                    postlink = entity.url
                else:
                    logging.error("best option is missing postlink (%s)", best_option[0])
                break
            i += 1

    if postlink:
        message = await get_message_from_postlink(postlink)
        if message:
            photo_id = get_photo_id_from_msg(message)
            if photo_id:
                contest_time = build_strptime(config.CONTEST_DATE)
                poll_time = build_timeframe(contest_time-timedelta(days=1), config.CONTEST_DAYS+1)
                message_author = get_author(message)


                # update placeholder
                if "TEMPLATE_VOTES" in config.FINAL_MESSAGE_HEADER:
                    config.FINAL_MESSAGE_HEADER = config.FINAL_MESSAGE_HEADER.replace(
                        r"{TEMPLATE_VOTES}",
                        str(best_vote_count)
                    )
                if "TEMPLATE_TIME" in config.FINAL_MESSAGE_HEADER:
                    config.FINAL_MESSAGE_HEADER = config.FINAL_MESSAGE_HEADER.replace(
                        r"{TEMPLATE_TIME}",
                        str(poll_time)
                    )

                poll_winner = "@" + message_author + config.RANKING_WINNER_SUFFIX
                if "TEMPLATE_POLL_WINNER" in config.FINAL_MESSAGE_HEADER:
                    config.FINAL_MESSAGE_HEADER = config.FINAL_MESSAGE_HEADER.replace(
                        r"{TEMPLATE_POLL_WINNER}",
                        str(poll_winner)
                    )

                # add ranking to poll message
                if config.CONTEST_POLL_RESULT_RANKING:
                    final_message, winner = create_ranking(participants)
                    if config.CONTEST_HIGHSCORE:
                        await update_highscore(winner['display_name'])
                else:
                    final_message = (
                        f"{config.FINAL_MESSAGE_HEADER}"
                        f"{config.FINAL_MESSAGE_FOOTER}"
                    )

                logging.info("\n%s", final_message)

                if len(final_message) > 2048:
                    logging.warning("Message too long (%d chars)", len(final_message))

                await app.send_photo(config.FINAL_MESSAGE_CHAT_ID, photo_id,
                    final_message, parse_mode=enums.ParseMode.MARKDOWN,
                    reply_to_message_id=poll_reply_message_id)

                if config.CONTEST_HIGHSCORE:
                    winner_name = "@"+message_author
                    await update_highscore(winner_name)

                return True
        else:
            logging.error("Message not found in %s", postlink)
    else:
        logging.error("postlink not found in caption_entities")

    return False

async def create_poll():
    """Create a poll to vote a winner from"""
    winners = await get_daily_winners()

    # create the ranking message
    ranking_winners = copy.deepcopy(winners)
    final_message, _winner = create_ranking(ranking_winners, True, False)

    # create numbered photos from winners
    media_group = []
    poll_answers = []
    poll_start_date = ""
    poll_end_date = ""
    contest_time = build_strptime(config.CONTEST_DATE)

    # create color
    color = []
    for _ in range(3):
        color.append(random.randint(0, 255))

    rank = 1
    for winner in winners:
        winner_date = build_strptime(winner['date'])
        winner_date_formatted = winner_date.strftime("%d.%m.%Y")

        if not "postlink" in winner:
            winner["postlink"] = build_postlink(winner)

        logging.info("Create numbered image %s from %s", rank, winner["postlink"])

        # get photo id
        winner_photo_id = await get_photo_id_from_postlink(winner["postlink"])
        if winner_photo_id:

            media = await download_media(winner_photo_id)

            image_path = create_numbered_photo(media, rank, color)
            if not image_path:
                logging.error(
                    "Create numbered photo failed for rank %d (%s)",
                    rank,
                    winner["postlink"]
                )
                sys.exit()

            if rank == 1:
                poll_end_date = winner_date_formatted
                poll_start_date = contest_time-timedelta(days=config.CONTEST_DAYS)
                poll_start_date = poll_start_date.strftime("%d.%m.%Y")
                logging.info("poll start date found: %s", poll_start_date)

                media_group.append(InputMediaPhoto(image_path, final_message))
            else:
                media_group.append(InputMediaPhoto(image_path))

            poll_answers.append(f"{rank}. Meme ({winner_date_formatted})")
        else:
            logging.warning("Winner photo not found from %s", winner["postlink"])

        rank += 1
        if rank > config.CONTEST_MAX_RANKS:
            break

    if config.FINAL_MESSAGE_CHAT_ID:

        media_group_message = await app.send_media_group(
            config.FINAL_MESSAGE_CHAT_ID,
            media_group
        )

        # create question message
        poll_question = (
            "Die Wahl zum Meme der Woche\n"
            f"vom {poll_start_date} - {poll_end_date} (24h Abstimmung)"
        )

        if len(media_group_message) > 0:
            await app.send_poll(
                config.FINAL_MESSAGE_CHAT_ID,
                poll_question,
                poll_answers,
                reply_to_message_id=media_group_message[0].id
            )
        else:
            logging.error("No media found to create poll")

async def download_media(photo_id):
    """Download media and retry on failure"""
    media = False

    i = 0
    max_loop = 3
    while i <= max_loop:
        media = await app.download_media(photo_id, in_memory=True)
        if media:
            break
        # wait some time and retry download
        logging.warning("Retry download media (%d/%d), sleep 60s ...", i, max_loop)
        time.sleep(60)
        i += 1

    if not media:
        logging.error("Download media failed with %s", photo_id)
        sys.exit()

    return media

def save_image_as_png(photo, number):
    '''Save image as png'''
    result = False

    if not os.path.exists('images'):
        os.makedirs('images')

    image = Image.open(photo)

    # scale image down
    maxsize = (500, 500)
    image.thumbnail(maxsize)

    img_name = 'images/image_' + str(number) + '_temp.png'

    image.save(img_name, "PNG")

    if os.path.exists(img_name):
        result = img_name

    return result

def create_numbered_photo(photo, number, color):
    '''Returns path to the manipulated numbered photo as 500px thumbnail'''
    if not photo:
        return False

    # save image as png for transparency
    img_temp_name = save_image_as_png(photo, number)
    if not img_temp_name:
        return False

    image = Image.open(img_temp_name).convert("RGBA")

    # Create text layer
    txt = Image.new('RGBA', image.size, (255, 255, 255, 0))

    # get image size
    width, height = image.size

    # create a draw object from image
    draw = ImageDraw.Draw(txt)

    # define the font
    if os.name == 'nt':
        font = ImageFont.truetype('arialbd.ttf', 136)
    else:
        font = ImageFont.truetype('DejaVuSans-Bold.ttf', 136)

    # draw the number
    draw.text(
        (width/2, height/2),
        str(number),
        align="center",
        font=font,
        fill=(color[0], color[1], color[2], 120),
        #fill=(153, 101, 21, 120),
        #fill=(255, 255, 255, 120),
        #fill=(255, 223, 0, 120),
        #fill=(212, 175, 55, 120),
        #fill="#f27600",
        stroke_width=3,
        stroke_fill=(0, 0, 0, 255),
        anchor="mm"
    )
    # combine image and text
    combined = Image.alpha_composite(image, txt)

    # save the new numbered image
    img_name = 'images/image_' + str(number) + '.png'
    combined.save(img_name, "PNG")
    logging.info("Image saved as '%s'", img_name)

    return img_name

###########################
# CSV based ranking methods
###########################

async def create_ranking_from_csv():
    """Run collect data from CSV files mode"""
    csv_participants = get_participants_from_csv()

    final_message, winner = create_ranking(csv_participants)

    # send ranking message to given chat
    if config.FINAL_MESSAGE_CHAT_ID:

        if not final_message:
            logging.warning("Can not create final message from CSV participants (file: %s)",
                    str(config.CSV_FILE))
            sys.exit()

        if winner['photo'] != "" and config.POST_WINNER_PHOTO:

            # check if photo is a postlink
            if "https://t.me/" in winner['photo']:
                photo_id = await get_photo_id_from_postlink(winner['photo'])
                if photo_id:
                    # set photo id
                    winner['photo'] = photo_id

            await send_photo_caption(
                config.FINAL_MESSAGE_CHAT_ID,
                winner['photo'],
                final_message
            )

        elif winner['photo'] != "" and not config.POST_WINNER_PHOTO:
            await app.send_message(config.FINAL_MESSAGE_CHAT_ID, final_message,
                    parse_mode=enums.ParseMode.MARKDOWN)

        else:
            log_msg = ("Something went wrong!"
                    " Can not find winner photo for final overall ranking message")
            logging.warning(log_msg)

    if config.CONTEST_HIGHSCORE:
        await update_highscore(winner['display_name'])

def create_participant_from_csv(csv_row):
    """Create a participant dict from CSV data"""
    participant = {
        "author": csv_row["Username"],
        "postlink": csv_row["Postlink"],
        "date": str(csv_row["Timestamp"]),
        "count": int(csv_row["Count"]),
        "views": int(csv_row["Views"])
    }

    return participant

def get_participants_from_csv():
    """Collect participants from CSV file"""
    csv_participants = []
    contest_time = build_strptime(config.CONTEST_DATE)

    with open(config.CSV_FILE, mode='r', encoding="utf-8") as csvfile_single:

        csv_dict = csv.DictReader(csvfile_single)

        i = 0
        for row in csv_dict:
            i += 1
            # check if row was in desired timeframe
            row_time = build_strptime(str(row['Timestamp']))
            row_difftime = contest_time - row_time

            if ( row_difftime.days < config.CONTEST_DAYS+1
                    and not row_difftime.days < 0 ):

                duplicate = False

                # check if winner was already found
                for participant in csv_participants:

                    if config.RANK_MEMES:
                        if row['Postlink'] == participant["postlink"]:
                            duplicate = True
                    else:
                        # check if User already found and add stats
                        if row['Username'].lower() == participant["author"].lower():
                            duplicate = True
                            participant["count"] += int(row['Count'])
                            participant["views"] += int(row['Views'])

                            participant_time = build_strptime(str(participant["date"]))
                            if participant_time < row_time:
                                participant["date"] = row['Timestamp']

                if not duplicate:
                    # add participant to array
                    csv_participant = create_participant_from_csv(row)
                    csv_participants.append(csv_participant)

        logging.info("Read %d rows from %s", i, config.CSV_FILE)

    return csv_participants

def get_unique_ids_from_csv():
    """Collect unique file ids from CSV file"""
    csv_unique_ids = []

    if os.path.isfile(config.CSV_FILE):

        with open(config.CSV_FILE, mode='r', encoding="utf-8") as csvfile_single:

            csv_dict = csv.DictReader(csvfile_single)

            i = 0
            for row in csv_dict:
                if "Unique ID" in row:
                    if row['Unique ID'] != "":
                        if "Postlink" in row:
                            csv_unique_ids.append([row['Postlink'], row['Unique ID'],])
                            i += 1
                else:
                    logging.info("Unique ID is missing in CSV. Skip repost check!")
                    continue

            logging.info("Load %d unique IDs from CSV %s", i, config.CSV_FILE)
    else:
        logging.warning("No CSV to recheck known unique IDs (%s)", config.CSV_FILE)

    return csv_unique_ids

def get_inactivities_from_csv():
    """Return cards to mark inactive participants"""
    csv_participants = get_participants_from_csv()
    csv_participants = sorted(csv_participants,
            key=lambda x: x['date'], reverse = True)

    logging.info("Found CSV data: %d rows", len(csv_participants))
    contest_time = build_strptime(config.CONTEST_DATE)
    yellow_cards = []
    orange_cards = []
    good_participants = []

    for participant in csv_participants:
        participant_time = build_strptime(str(participant['date']))
        participant_difftime = contest_time - participant_time

        duplicate = False
        for good_participant in good_participants:
            if participant['author'].lower() in good_participant['author'].lower():
                duplicate = True
        for yellow_card in yellow_cards:
            if participant['author'].lower() in yellow_card['author'].lower():
                duplicate = True
        for orange_card in orange_cards:
            if participant['author'].lower() in orange_card['author'].lower():
                duplicate = True

        if not duplicate:
            if participant_difftime.days > 7 and participant_difftime.days <= 28:
                participant['lastmemedays'] = participant_difftime.days
                yellow_cards.append(participant)

            elif participant_difftime.days >= 29:
                participant['lastmemedays'] = participant_difftime.days
                orange_cards.append(participant)
            else:
                good_participants.append(participant)

    return yellow_cards, orange_cards

async def send_inactivity_message(yellow_cards, orange_cards):
    """Create inactivity list from cards and send the message"""
    msg = ""
    for card in yellow_cards:
        msg += (f"yellow card 🟨 for @{card['author']} "
                f"cause of {card['lastmemedays']} days of inactivity\n")

    for card in orange_cards:
        msg += (f"orange card 🟧 for @{card['author']} "
                        f"cause of {card['lastmemedays']} days of inactivity\n")

    print(msg)
    if config.FINAL_MESSAGE_CHAT_ID:
        await app.send_message(config.FINAL_MESSAGE_CHAT_ID, msg,
                        parse_mode=enums.ParseMode.MARKDOWN)

##################
# Common methods
##################

async def get_message_from_postlink(postlink):
    """return message from postlink"""
    message = False
    msg_id = get_message_id_from_postlink(postlink)
    chat_id = get_chat_id_from_postlink(postlink)
    if chat_id and msg_id:
        message = await app.get_messages(chat_id, msg_id)
    else:
        logging.error("Cant find message from postlink: %s", postlink)

    return message

async def get_photo_id_from_postlink(postlink):
    """return photo id from CSV data or from chat history"""
    photo_id = False

    message = await get_message_from_postlink(postlink)
    if message:
        photo_id = get_photo_id_from_msg(message)
    else:
        logging.error("Cant find photo id from postlink: %s", postlink)

    return photo_id

def get_chat_id_from_postlink(postlink):
    """return chat id from postlink"""
    arrpostlink = str(postlink).split("/")
    chat_id = False

    if len(arrpostlink) >= 4:
        chat_id = str(arrpostlink[-2]).replace("-100","")

        if chat_id.isnumeric():
            chat_id = -int(f"{100}{int(chat_id)}")
    else:
        logging.error("Cant find valid chat id from postlink: %s", postlink)

    return chat_id

def get_message_id_from_postlink(postlink):
    """return message id from postlink"""
    arrpostlink = str(postlink).split("/")
    message_id = False

    if len(arrpostlink) >= 4:
        message_id = int(arrpostlink[-1])
    else:
        logging.error("Cant find message id from postlink: %s", postlink)

    return message_id

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

def build_strptime(time_string):
    """Return time as strptime object"""
    return datetime.strptime(time_string, "%Y-%m-%d %H:%M:%S")

def build_postlink(participant):
    """Builds link to given message"""
    participant_id = str(participant["id"])
    participant_chat_id = str(participant["chat_id"]).replace("-100","")
    if participant_chat_id.isnumeric():
        # private chat
        baseurl = "https://t.me/c/"
    else:
        # public channel
        baseurl = "https://t.me/"
    postlink = baseurl + participant_chat_id + "/" + participant_id

    return postlink

def build_timeframe(current_time, days):
    """Calculate start and end date and return string"""
    date_list = [current_time - timedelta(days=x) for x in range(days)]
    date_start = ""
    date_end = ""
    date_message = ""

    i = 0
    for date in reversed(date_list):
        if i == 0:
            date_start = date.strftime("%d.%m")
        elif i == len(date_list)-2:
            date_end = date.strftime("%d.%m.%Y")
        i += 1

    if date_start != "" and date_end != "":
        date_message = f"{date_start} - {date_end}"

    return date_message

def get_chunks(wrapstring, maxlength, pattern = "#"):
    """return wrapped string as yield"""
    start = 0
    end = 0
    while start + maxlength  < len(wrapstring) and end != -1:
        end = wrapstring.rfind(pattern, start, start + maxlength + 1)
        yield wrapstring[start:end]
        start = end
    yield wrapstring[start:]

if __name__ == "__main__":
    app.run(main())
