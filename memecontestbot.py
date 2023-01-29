#!/usr/bin/env python

"""
Simple Bot to analyze telegram post reactions and create a ranking.
Can be configured for daily or weekly rankings (get_chat_history has a limit of posts to return from chat).

Usage:
Start bot to create a nice ranking.
"""

from datetime import datetime
from os import path, listdir, remove
from argparse import ArgumentParser

import sys
import importlib
import csv
import re
import locale

from pyrogram import Client, enums

locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')

app = Client("my_account")

# import config
parser = ArgumentParser()
parser.add_argument("-c", "--config", dest="configfile",
                    help="path to file with your config", metavar="FILE")
args = parser.parse_args()

if args.configfile:
    configfile = args.configfile
else:
    configfile = "config.py"

# import config file
config = importlib.import_module(configfile.replace('.py',''))

# verify config exists
try:
    config.CHAT_ID
    config.CONTEST_DATE
    config.CONTEST_DAYS
    config.CONTEST_MAX_RANKS
    config.EXCLUDE_PATTERN
    config.FINAL_MESSAGE_FOOTER
    config.FINAL_MESSAGE_CHAT_ID
    config.PARTITICPANTS_FROM_CSV
    config.CREATE_CSV
    config.CSV_CHAT_ID
    config.POST_LINK
    config.POST_WINNER_PHOTO
    config.SIGN_MESSAGES
    config.RANK_MEMES
    config.POST_PARTICIPANTS_CHAT_ID
except Exception:
    print(f"Can not read from config file '{configfile}', please checkout config.py")
    print(Exception)
    sys.exit()

# global vars
participants = []
contest_time = datetime.strptime(config.CONTEST_DATE, "%Y-%m-%d %H:%M:%S")

async def main():
    winner_photo = ""
    header_message = build_message_header()

    if config.PARTITICPANTS_FROM_CSV:
        # collect contest data from CSV files and only winner photo from config.CHAT_ID
        csv_filename = ("contest_" + str(config.CHAT_ID) + "_overall_" +
            contest_time.strftime("%Y-%m-%d_%H-%M-%S") + ".csv")

        # create overall CSV and ranking message
        csv_success = write_overall_csv(csv_filename)

        # send CSV file
        if config.CSV_CHAT_ID and csv_success:

            async with app:
                await app.send_document(config.CSV_CHAT_ID, csv_filename,
                        caption=header_message)

        # Get winners from participants and create final message
        csvparticipants = get_csv_participants(csv_filename)
        final_message, winner_photo = create_overall_ranking(csvparticipants, header_message)

        # send ranking message to given chat
        if config.FINAL_MESSAGE_CHAT_ID:

            if not final_message:
                print("Can not create final message from CSV participants (file: " + str(csv_filename) + ")")
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
                    if config.CONTEST_DAYS == 1:
                        print("Something went wrong! Can not find winner photo for final overall ranking message")
                    else:
                        print("Can not find best meme photo overall, please fix me")

        # skip everything else
        sys.exit()

    async with app:
        async for message in app.get_chat_history(config.CHAT_ID):
            skip = 0
            # check excludes
            for exclude in config.EXCLUDE_PATTERN:
                if exclude in str(message.caption):
                    # skip this message
                    skip = 1

            if not config.SIGN_MESSAGES:
                # force to set author from caption
                message.author_signature = ""
                if "@" in str(message.caption):
                    # extract telegram handle from caption
                    message_caption_array = message.caption.split()
                    for caption_word in message_caption_array:
                        if caption_word.startswith("@"):
                            # make sure nobody can inject commands here
                            message.author_signature = re.sub(r"[^a-zA-Z0-9\_]", "", caption_word)
                if ( message.author_signature == ""
                        or "httpstme" in message.author_signature ):
                    skip = 1

            if skip:
                continue

            # check if message is a photo
            if str(message.media) != "MessageMediaType.PHOTO":
                continue

            # check if message was in desired timeframe
            message_time = datetime.strptime(str(message.date), "%Y-%m-%d %H:%M:%S")
            message_difftime = contest_time - message_time

            if ( (message_difftime.days <= config.CONTEST_DAYS-1)
                    and not message_difftime.days < 0 ):

                if not config.POST_PARTICIPANTS_CHAT_ID:
                    # verify reactions for ranking message
                    reaction_counter = 0
                    try:
                        reaction_counter = message.reactions.reactions[0].count
                    except Exception:
                        continue     

                # check if participant has more than one post
                duplicate = 0
                highest_count = 0
                for participant in participants:

                    try:
                        # group author
                        message_author = message.from_user.id
                        participant_author = participant.from_user.id
                    except:
                        # channel author
                        message_author = message.author_signature
                        participant_author = participant.author_signature

                    if participant_author == message_author:
                        duplicate = 1

                        if config.POST_PARTICIPANTS_CHAT_ID:
                            participant_time = datetime.strptime(str(participant.date),
                                    "%Y-%m-%d %H:%M:%S")

                            if participant_time < message_time:
                                # remember only the newest meme
                                participant = message
                            continue

                        if config.RANK_MEMES:
                            # already exist in participants array, only one post allowed (prefer best)
                            if participant.reactions.reactions[0].count > message.reactions.reactions[0].count:
                                # update existent meme data
                                participant.photo.file_id = message.photo.file_id
                                participant.photo.file_unique_id = message.photo.file_unique_id
                                participant.caption = message.caption
                                participant.id = message.id
                                participant.views = message.views
                                participant.reactions.reactions[0].count = message.reactions.reactions[0].count
                        else:
                            post_count = participant.reactions.reactions[0].count

                            # remember the best meme of current participant
                            if post_count > highest_count:
                                highest_count = post_count

                            if highest_count < message.reactions.reactions[0].count:
                                # replace existent meme data
                                participant.photo.file_id = message.photo.file_id
                                participant.photo.file_unique_id = message.photo.file_unique_id
                                participant.caption = message.caption
                                participant.id = message.id

                            # update reaction counter and views
                            participant.reactions.reactions[0].count += message.reactions.reactions[0].count
                            participant.views += message.views

                    elif str(message.author_signature) == "None":
                        duplicate = 1

                if duplicate == 0:
                    # append to participants array
                    participants.append(message)
                    if config.POST_PARTICIPANTS_CHAT_ID:
                        if not config.SIGN_MESSAGES:
                            message_author = "@" + message.author_signature
                        else:
                            try:
                                message_author = "//" + message.from_user.first_name
                            except:
                                message_author = "//" + message.author_signature

                        await app.send_photo(config.POST_PARTICIPANTS_CHAT_ID, message.photo.file_id,
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
            csv_file = write_rows_to_csv( 
                    "contest_" + str(config.CHAT_ID) + "_" + str(config.CONTEST_DAYS))

            if config.CSV_CHAT_ID and csv_file:
                async with app:
                    await app.send_document(config.CSV_CHAT_ID, csv_file,
                            caption=header_message)

        final_message, winner_photo = create_ranking(header_message)

        if config.FINAL_MESSAGE_CHAT_ID:
            async with app:
                if winner_photo != "" and config.POST_WINNER_PHOTO:
                    await app.send_photo(config.FINAL_MESSAGE_CHAT_ID, winner_photo,
                            final_message, parse_mode=enums.ParseMode.MARKDOWN)
                elif winner_photo != "" and not config.POST_WINNER_PHOTO:
                    await app.send_message(config.FINAL_MESSAGE_CHAT_ID, final_message,
                            parse_mode=enums.ParseMode.MARKDOWN)
                else:
                    if config.CONTEST_DAYS == 1:
                        print("Something went wrong! Can not find winner photo for final ranking message")
                    else:
                        print("Can not find best meme photo, please fix me")

def build_message_header():
    """"Create header of final message"""

    if config.RANK_MEMES:
        header_contest_type = "Memes"
    else:
        header_contest_type = "Contest Lords"

    formatted_date = contest_time.strftime("%d.%m.%Y %H:%M")

    if not config.PARTITICPANTS_FROM_CSV:
        header_message = f"Top {config.CONTEST_MAX_RANKS} {header_contest_type} (Stand: {formatted_date})"

        if config.CONTEST_DAYS == 1:
            header_message = "Rangliste 24-Stunden " + header_message
        else:
            header_message = f"Rangliste {config.CONTEST_DAYS}-Tage " + header_message
    else:
        # get the month and year for header message
        ranking_time = contest_time.strftime("%Y-%m")
        # get the months name for header_message
        ranking_message = contest_time.strftime("%B")
        header_message = f"Rangliste {ranking_message}"
        header_message += f" Top {config.CONTEST_MAX_RANKS} {header_contest_type} (Stand: {ranking_time} cache)"

    return header_message

def write_rows_to_csv(pattern):
    """Write participants data to CSV file"""
    csv_rows = []

    for participant in participants:
        participant_postlink = build_postlink(participant)
        csv_rows.append([participant.author_signature, participant_postlink,
            participant.date, participant.reactions.reactions[0].count, participant.views])

    # clean up, only keep 3 csv files
    filecount = 0
    files = listdir()
    files = sorted(files, key = path.getmtime, reverse=True)
    for filename in files:
        if ( filename.endswith('.csv')
                and pattern in filename ):
            filecount += 1
            if filecount >= 4:
                remove(filename)

    # CSV header and filename
    csv_fields = ['Username', 'Postlink', 'Timestamp', 'Count', 'Views']
    csv_file = ("contest_" + str(config.CHAT_ID) + "_" + 
            str(config.CONTEST_DAYS) + "d_" + contest_time.strftime("%Y-%m-%d_%H-%M-%S") + ".csv")

    # open file an write rows
    with open(csv_file, mode='w', encoding="utf-8") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(csv_fields)
        csvwriter.writerows(csv_rows)

    print(f"CSV created: {csv_file}")
    return csv_file

def get_winner():
    """Extracts the best post from participants and returns the winner"""
    best_count = 0
    winner = []
    winner_id = -1

    i = 0
    for participant in participants:
        if participant.reactions.reactions[0].count >= best_count:
            best_count = participant.reactions.reactions[0].count
            winner = participant
            winner_id = i
        i += 1

    # remove winner from participants array
    if winner_id != -1 and len(participants) >= 0:
        participants.pop(winner_id)

    return winner

def get_winners():
    """Get all winners and return winners array"""
    winners = []

    i = 1
    while i <= config.CONTEST_MAX_RANKS:
        current_winner = get_winner()
        if current_winner:
            winners.append(current_winner)
        i += 1

    return winners

def build_postlink(message):
    """Builds link to given message"""
    message_id = str(message.id)
    message_chat_id = str(message.chat.id).replace("-100","")
    postlink = "https://t.me/c/" + message_chat_id + "/" + message_id
    return postlink

def create_ranking(header_message):
    """Build the final ranking message"""

    # get winners
    winners = get_winners()

    # init vars
    rank = 0
    last_count = 0
    winner_photo = ""
    final_message = ""

    i = 1
    for winner in winners:

        winner_count = winner.reactions.reactions[0].count

        # update rank, same rank with same count
        if last_count != winner_count:
            rank += 1
        last_count = winner_count

        # set rank 1 winner photo
        if rank == 1 and winner_photo == "":
            winner_photo = winner.photo.file_id

        # check for telegram handles in caption
        winner_display_name = str(winner.author_signature)
        if not winner_display_name:
            winner_display_name = "None"

        if "@" in str(winner.caption):
            # extract telegram handle from caption
            winner_caption_array = winner.caption.split()
            for caption_word in winner_caption_array:
                if caption_word.startswith("@"):
                    # make sure nobody can inject commands here
                    winner_display_name = re.sub(r"@[^a-zA-Z0-9 ]", "", caption_word)

        # add post link
        if config.POST_LINK:
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
    print(final_message)   

    return final_message, winner_photo

###########################
# CSV based ranking methods
###########################

def write_overall_csv(csvname):
    """Read single CSV files and write data to new overall CSV file"""
    csv_overall_rows = []
    csv_header = 0
    csv_pattern = "contest_" + str(config.CHAT_ID) + "_" + str(config.CONTEST_DAYS) + "d_"
    check = False

    for filename in listdir():
        if ( filename.endswith('.csv') 
                and not csvname in filename 
                and not "_overall_" in filename
                and csv_pattern in filename ):

            print(f"Collect data from CSV: {filename}")
            with open(filename, mode = 'r', newline='', encoding="utf-8") as csvfile:
                csvreader = csv.reader(csvfile, delimiter=',')
                for row in csvreader:
                    # skip header if already written
                    if "Username" in row and csv_header:
                        continue
                    else:
                        csv_header = 1

                        # remember csv data found
                        check = True
                        try:
                            csv_overall_rows.append([str(row[0]), str(row[1]),
                                    str(row[2]), int(row[3]), int(row[4])])
                        except:
                            # add header
                            csv_overall_rows.append(row)

    # clean up
    if path.exists(csvname):
        remove(csvname)

    with open(csvname, mode='w', encoding="utf-8") as csvfile_overall:
        csvwriter = csv.writer(csvfile_overall)
        csvwriter.writerows(csv_overall_rows)

    return check

def get_csv_participants(csvfile):
    """Collect participants from CSV file"""
    csvparticipants = []
    with open(csvfile, mode='r', encoding="utf-8") as csvfile:

        csv_dict = csv.DictReader(csvfile)

        for row in csv_dict:
            duplicate = 0
            # check if winner was already found
            for participant in csvparticipants:
                if row['Username'] == participant[0]:
                    participant[3] += int(row['Count'])
                    participant[4] += int(row['Views'])
                    duplicate = 1

            # add participant to array
            if not duplicate:
                # check if row was in desired timeframe
                participant_time = datetime.strptime(str(row['Timestamp']), "%Y-%m-%d %H:%M:%S")
                participant_difftime = contest_time - participant_time

                if ( (participant_difftime.days <= config.CONTEST_DAYS-1) 
                        and not participant_difftime.days < 0 ):
                    csvparticipants.append([str(row['Username']),str(row['Postlink']),
                            str(row['Timestamp']), int(row['Count']),int(row['Views'])])

    return csvparticipants

def get_csv_winner(csvparticipants):
    """Extracts the best post from participants and returns the winner"""
    best_count = 0
    winner = []
    winner_id = -1

    i = 0
    for participant in csvparticipants:
        if participant[3] >= best_count:
            best_count = participant[3]
            winner = participant
            winner_id = i
        i += 1

    # remove winner from participants array
    if winner_id != -1 and len(csvparticipants) >= 0:
        csvparticipants.pop(winner_id)

    return winner

def get_csv_winners(csvparticipants):
    """Get all winners and return winners array"""
    winners = []

    i = 1
    while i <= config.CONTEST_MAX_RANKS:
        current_winner = get_csv_winner(csvparticipants)
        if current_winner:
            #print("Add Winner %s %s" % (current_winner.author_signature, str(current_winner.reactions.reactions[0].count)))
            winners.append(current_winner)
        i += 1

    return winners

def create_overall_ranking(csvparticipants, header_message):
    """Build the final ranking message based on a winners array"""
    winner_photo = ""

    # get winners
    winners = get_csv_winners(csvparticipants)

    # init vars
    rank = 0
    last_count = 0
    final_message = ""

    i = 1
    for winner in winners:
        winner_count = winner[3]

        # update rank, same rank with same count
        if last_count != winner_count:
            rank += 1
        last_count = winner_count

        # set rank 1 winner photo as message link
        if rank == 1 and winner_photo == "":
            winner_photo = winner[1]

        if not config.SIGN_MESSAGES:
            winner_display_name = "@" + winner[0]
        else:
            winner_display_name = winner[0]

        # add post link
        if config.POST_LINK:
            winner_postlink = winner[1]
            winner_count = f"[{winner_count}]({winner_postlink})"

        final_message = final_message + "#" + str(rank) \
                + " " + winner_display_name \
                + " " + str(winner_count) \
                + " 🏆 \n"

        i += 1
        if i > config.CONTEST_MAX_RANKS:
            break
    
    final_message = header_message + ":\n\n" + final_message + "\n" + config.FINAL_MESSAGE_FOOTER
    print(final_message)   

    return final_message, winner_photo

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
    else:
        return False

app.run(main())
