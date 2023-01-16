#!/usr/bin/env python

"""
Simple Bot to analyze telegram post reactions and create a ranking.
Can be configured for daily or weekly rankings (get_chat_history has a limit of posts to return from chat).

Usage:
Start bot to create a nice ranking.
"""

from pyrogram import Client, enums
from datetime import datetime
from os import path
from argparse import ArgumentParser
import csv
import re

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

if path.exists(configfile): 
    exec(compile(open(configfile).read(), configfile, 'exec'))
    try:
        CHAT_ID
        CONTEST_DATE
        CONTEST_DAYS
        CONTEST_MAX_RANKS
        EXCLUDE_PATTERN
        FINAL_MESSAGE_FOOTER
        FINAL_MESSAGE_CHAT_ID
        POST_LINK
        CREATE_CSV
        CSV_CHAT_ID
        POST_WINNER_PHOTO
        SIGN_MESSAGES
        RANK_MEMES
        POST_PARTICIPANTS_CHAT_ID
    except:
        print(f"Can not read from config file '{configfile}', please checkout config.py")
        quit()
else:
    print(f"No config file found as '{configfile}', please checkout config.py as reference")
    quit()

# global vars
participants = []
winner_photo = ""
contest_time = datetime.strptime(CONTEST_DATE, "%Y-%m-%d %H:%M:%S")

# Create header of final message
if RANK_MEMES:
    header_contest_type = "Memes"
else:
    header_contest_type = "Contest Lords"

formatted_date = contest_time.strftime("%d.%m.%Y %H:%M")

header_message = f"Top {CONTEST_MAX_RANKS} {header_contest_type} (Stand: {formatted_date})"

if CONTEST_DAYS == 1:
    header_message = "Rangliste 24-Stunden " + header_message
else:
    header_message = f"Rangliste {CONTEST_DAYS}-Tage " + header_message

async def main():

    async with app:
        async for message in app.get_chat_history(CHAT_ID):
            skip = 0
            # check excludes
            for exclude in EXCLUDE_PATTERN:
                if exclude in str(message.caption):
                    # skip this message
                    skip = 1

            if not SIGN_MESSAGES:
                # force to set author from caption
                message.author_signature = ""
                if "@" in str(message.caption):
                    # extract telegram handle from caption
                    message_caption_array = message.caption.split()
                    for caption_word in message_caption_array:
                        if caption_word.startswith("@"):
                            # make sure nobody can inject commands here
                            message.author_signature = re.sub(r"[^a-zA-Z0-9\_]", "", caption_word)
                if message.author_signature == "":
                    skip = 1

            # check if message is a photo
            if str(message.media) == "MessageMediaType.PHOTO" and not skip:

                # check if message was in desired timeframe
                message_time = datetime.strptime(str(message.date), "%Y-%m-%d %H:%M:%S")
                message_difftime = contest_time - message_time

                if ( (message_difftime.days <= CONTEST_DAYS-1) 
                        and not (message_difftime.days < 0) ):

                    if not POST_PARTICIPANTS_CHAT_ID:
                        # verify reactions for ranking message
                        reaction_counter = 0
                        try:
                            reaction_counter = message.reactions.reactions[0].count
                        except:
                            continue         
                                           
                    # check if participant has more than one post
                    duplicate = 0
                    highest_count = 0
                    for participant in participants:

                        if participant.from_user.id == message.from_user.id:
                            duplicate = 1

                            if POST_PARTICIPANTS_CHAT_ID:
                                if datetime.strptime(str(participant.date), "%Y-%m-%d %H:%M:%S") < message_time:
                                    # remember only the newest meme
                                    participant = message
                                continue

                            if RANK_MEMES:
                                # already exist in participants array, only one post allowed (prefer best)
                                if participant.reactions.reactions[0].count > message.reactions.reactions[0].count:
                                    # best variant already exist, do not append it again
                                    continue
                                else:
                                    # update existent meme data
                                    participant.photo.file_id = message.photo.file_id
                                    participant.photo.file_unique_id = message.photo.file_unique_id
                                    participant.caption = message.caption
                                    participant.id = message.id
                                    participant.views = message.views
                                    participant.from_user = message.from_user
                                    participant.reactions.reactions[0].count = message.reactions.reactions[0].count                  
                            else:
                                post_count = participant.reactions.reactions[0].count

                                # remember the best meme of current participant
                                if post_count > highest_count:
                                    highest_count = post_count

                                if ( highest_count < message.reactions.reactions[0].count ):
                                    # update existent meme data
                                    participant.photo.file_id = message.photo.file_id
                                    participant.photo.file_unique_id = message.photo.file_unique_id
                                    participant.caption = message.caption
                                    participant.id = message.id
                                    participant.views = message.views
                                    participant.from_user = message.from_user

                                # update reaction counter
                                participant.reactions.reactions[0].count += message.reactions.reactions[0].count

                        elif str(message.author_signature) == "None":
                            duplicate = 1

                    if duplicate == 0:
                        # append to participants array
                        participants.append(message)
                        if POST_PARTICIPANTS_CHAT_ID:
                            if not SIGN_MESSAGES:
                                message_author = "@" + message.author_signature
                            else:
                                message_author = "//" + message.from_user.first_name

                            await app.send_photo(POST_PARTICIPANTS_CHAT_ID, message.photo.file_id, 
                                   message_author, parse_mode=enums.ParseMode.MARKDOWN)

                    if CREATE_CSV:
                        csv_rows = []

                        for participant in participants:
                            participant_postlink = build_postlink(participant)
                            csv_rows.append([participant.author_signature, participant_postlink, 
                                participant.date, participant.reactions.reactions[0].count, participant.views])

                        write_csv(csv_rows)

                elif (message_difftime.days < 0 or skip):
                    # message newer than expected or excluded, keep searching messages
                    continue

                else:
                    # message too old from here, stop loop
                    break

    # create final message with ranking
    if not POST_PARTICIPANTS_CHAT_ID:
        final_message = create_ranking()

        if FINAL_MESSAGE_CHAT_ID:
            async with app:
                if winner_photo != "" and POST_WINNER_PHOTO:
                    await app.send_photo(FINAL_MESSAGE_CHAT_ID, winner_photo, final_message, parse_mode=enums.ParseMode.MARKDOWN)
                elif winner_photo != "" and not POST_WINNER_PHOTO:
                    await app.send_message(FINAL_MESSAGE_CHAT_ID, final_message, parse_mode=enums.ParseMode.MARKDOWN)
                else:
                    if CONTEST_DAYS == 1:
                        print("Something went wrong! Can not find winner photo for final ranking message")
                    else:
                        print("Can not find best meme photo, please fix me")

        if CREATE_CSV and CSV_CHAT_ID:
            async with app:
                await app.send_document(CSV_CHAT_ID, "contest.csv", caption=header_message)

def write_csv(csv_rows):
    """Write data to CSV file"""
    csv_filename = "contest.csv"
    csv_fields = ['Username', 'Postlink', 'Timestamp', 'Count', 'Views']
    
    with open(csv_filename, 'w') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(csv_fields)
        csvwriter.writerows(csv_rows)

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
        #print("Remove participant %s %s" % (participants[winner_id].author_signature, str(participants[winner_id].reactions.reactions[0].count)))
        participants.pop(winner_id)

    return winner

def get_winners():
    """Get all winners and return winners array"""
    winners = []

    i = 1
    while i <= CONTEST_MAX_RANKS:
        current_winner = get_winner()
        if current_winner:
            #print("Add Winner %s %s" % (current_winner.author_signature, str(current_winner.reactions.reactions[0].count)))
            winners.append(current_winner)
        i += 1

    return winners

def build_postlink(message):
    """Builds link to given message"""
    message_id = str(message.id)
    message_chat_id = str(message.chat.id).replace("-100","")
    postlink = "https://t.me/c/" + message_chat_id + "/" + message_id
    return postlink

def create_ranking():
    """Build the final ranking message"""
    global winner_photo

    # get winners
    winners = get_winners()

    # init vars
    rank = 0
    last_count = 0
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
        if POST_LINK:
            winner_postlink = build_postlink(winner)
            winner_count = f"[{winner_count}]({winner_postlink})"

        final_message = final_message + "#" + str(rank) \
                + " " + winner_display_name \
                + " " + str(winner_count) \
                + " 🏆 \n"

        i += 1
        if i > CONTEST_MAX_RANKS:
            break
    
    final_message = header_message + ":\n\n" + final_message + "\n" + FINAL_MESSAGE_FOOTER
    print(final_message)   

    return final_message

app.run(main())
