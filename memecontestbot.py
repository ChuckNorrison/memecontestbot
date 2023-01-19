#!/usr/bin/env python

"""
Simple Bot to analyze telegram post reactions and create a ranking.
Can be configured for daily or weekly rankings (get_chat_history has a limit of posts to return from chat).

Usage:
Start bot to create a nice ranking.
"""

from pyrogram import Client, enums
from datetime import datetime
from os import path, listdir, remove
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
        FINAL_MESSAGE_OVERALL
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
    global winner_photo

    if FINAL_MESSAGE_OVERALL:
        csv_filename = ("contest_" + str(CHAT_ID) + "_overall_" + 
            contest_time.strftime("%Y-%m-%d_%H-%M-%S") + ".csv")

        # create overall csv and ranking message
        write_overall_csv(csv_filename, "contest_" + str(CHAT_ID))
        overall_winners = get_csv_winners(csv_filename)
        final_message = create_overall_ranking(overall_winners)

        # send ranking message to given chat
        if FINAL_MESSAGE_CHAT_ID and overall_winners:

            async with app:
                if winner_photo != "" and POST_WINNER_PHOTO:

                    # get photo id from winner photo url
                    if "https://t.me/c/" in winner_photo:
                        msg_id = postlink_to_msg_id(winner_photo)
                        message = await app.get_messages(CHAT_ID, msg_id)
                        if message:                     
                            winner_photo = get_photo_id_from_msg(message)

                    await app.send_photo(FINAL_MESSAGE_CHAT_ID, winner_photo, 
                            final_message, parse_mode=enums.ParseMode.MARKDOWN)

                elif winner_photo != "" and not POST_WINNER_PHOTO:
                    await app.send_message(FINAL_MESSAGE_CHAT_ID, final_message, 
                            parse_mode=enums.ParseMode.MARKDOWN)

                else:
                    if CONTEST_DAYS == 1:
                        print("Something went wrong! Can not find winner photo for final overall ranking message")
                    else:
                        print("Can not find best meme photo overall, please fix me")

            if CSV_CHAT_ID:
                async with app:
                    await app.send_document(CSV_CHAT_ID, csv_filename, 
                            caption=header_message)

        # skip everything else
        exit()

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
                if ( message.author_signature == "" 
                        or "httpstme" in message.author_signature ):
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

                            if POST_PARTICIPANTS_CHAT_ID:
                                participant_time = datetime.strptime(str(participant.date), "%Y-%m-%d %H:%M:%S")
                                if participant_time < message_time:
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
                                try:
                                    message_author = "//" + message.from_user.first_name
                                except:
                                    message_author = "//" + message.author_signature

                            await app.send_photo(POST_PARTICIPANTS_CHAT_ID, message.photo.file_id, 
                                    message_author, parse_mode=enums.ParseMode.MARKDOWN)

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
                    await app.send_photo(FINAL_MESSAGE_CHAT_ID, winner_photo, 
                            final_message, parse_mode=enums.ParseMode.MARKDOWN)
                elif winner_photo != "" and not POST_WINNER_PHOTO:
                    await app.send_message(FINAL_MESSAGE_CHAT_ID, final_message, 
                            parse_mode=enums.ParseMode.MARKDOWN)
                else:
                    if CONTEST_DAYS == 1:
                        print("Something went wrong! Can not find winner photo for final ranking message")
                    else:
                        print("Can not find best meme photo, please fix me")

        if CREATE_CSV:
            csv_rows = []

            for participant in participants:
                participant_postlink = build_postlink(participant)
                csv_rows.append([participant.author_signature, participant_postlink, 
                    participant.date, participant.reactions.reactions[0].count, participant.views])

            csv_filename = write_rows_to_csv(csv_rows, 
                    "contest_" + str(CHAT_ID) + "_" + str(CONTEST_DAYS))

            if CSV_CHAT_ID and csv_filename:
                async with app:
                    await app.send_document(CSV_CHAT_ID, csv_filename, 
                            caption=header_message)

def write_rows_to_csv(csv_rows, pattern):
    """Write contest data to CSV file"""

    # clean up, only keep 4 csv files
    filecount = 0
    files = listdir()
    files = sorted(files, key = path.getmtime, reverse=True)
    for filename in files:
        if ( filename.endswith('.csv') 
                and pattern in filename ):            
            filecount += 1
            if filecount >= 4:
                remove(filename)

    # write a new csv file
    csv_fields = ['Username', 'Postlink', 'Timestamp', 'Count', 'Views']
    csv_filename = ("contest_" + str(CHAT_ID) + "_" + 
            str(CONTEST_DAYS) + "d_" + contest_time.strftime("%Y-%m-%d_%H-%M-%S") + ".csv")

    with open(csv_filename, 'w') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(csv_fields)
        csvwriter.writerows(csv_rows)

    return csv_filename

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

def write_overall_csv(csvname, pattern):
    """Read single CSV files and write data to new overall CSV file"""
    csv_overall_rows = []
    csv_header = 0
    for filename in listdir():
        if ( filename.endswith('.csv') 
                and not csvname in filename 
                and not "_overall_" in filename
                and pattern in filename ):

            with open(filename, newline='') as csvfile:
                csvreader = csv.reader(csvfile, delimiter=',')
                for row in csvreader:
                    # skip header if already written
                    if "Username" in row and csv_header:
                        continue
                    else:
                        csv_header = 1

                    # remember all csv data found
                    csv_overall_rows.append(row)

    # clean up
    if path.exists(csvname):
        remove(csvname)

    with open(csvname, 'w') as csvfile_overall:
        csvwriter = csv.writer(csvfile_overall)                    
        csvwriter.writerows(csv_overall_rows)

def get_csv_winners(csvfile):
    csvwinners = []
    with open(csvfile, mode ='r') as csvfile:

         csvDict = csv.DictReader(csvfile)

         for row in csvDict:
              found = 0
              for csvwinner in csvwinners:
                   if row['Username'] == csvwinner[0]:
                        csvwinner[3] += int(row['Count'])
                        found = 1

              if not found:
                   csvwinners.append([str(row['Username']),str(row['Postlink']), 
                        str(row['Timestamp']), int(row['Count']),int(row['Views'])])

    return csvwinners

def create_overall_ranking(winners):
    global winner_photo

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

        # set rank 1 winner photo
        if rank == 1 and winner_photo == "":
            winner_photo = winner[1]    

        if not SIGN_MESSAGES:
            winner_display_name = "@" + winner[0]
        else:
            winner_display_name = winner[0]

        final_message = final_message + "#" + str(rank) \
                + " " + winner_display_name \
                + " " + str(winner[3]) \
                + " 🏆 \n"

        i += 1
        if i > CONTEST_MAX_RANKS:
            break
    
    final_message = header_message + ":\n\n" + final_message + "\n" + FINAL_MESSAGE_FOOTER
    print(final_message)   

    return final_message

def postlink_to_msg_id(postlink):
    arrpostlink = str(postlink).split("/")
    return int(arrpostlink[-1])

def get_photo_id_from_msg(message):
    if str(message.media) == "MessageMediaType.PHOTO":
        return message.photo.file_id
    else:
        return False


app.run(main())
