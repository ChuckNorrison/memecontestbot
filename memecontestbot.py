#!/usr/bin/env python

"""
Simple Bot to analyze telegram post reactions and create a ranking.
Can be configured for daily or weekly rankings (get_chat_history has a limit of posts to return from chat).

Usage:
Start bot to create a nice ranking.
"""

from pyrogram import Client, enums
from datetime import datetime
import csv

app = Client("my_account")

#########################
# START TWEAK CONFIG HERE

# channel name for public channels 
# or chat id for private chats to analyze
chat_id = "mychannelname" 

# only posts prior this date and time will get analyzed
contest_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
#contest_date = "2022-12-19 23:59:59" # example with fixed date and time

# only posts newer than x days will be ranked. 
# 1 = 24h contest without duplicates, 
# 2+ days post with same author gets added
contest_days = 1  

# amount of winners to honor in ranking message
contest_max_ranks = 10 

# posts we want to exclude from ranking. 
# Add your patterns to this array.
exclude_pattern = ["Meme Contest"] 

# simple text footer in ranking view, 
# should be used to identify exclude posts
final_message_footer = f"🏆 [{exclude_pattern[0]}](https://t.me/mychannelname) 🏆"

# Send the final message to a given chat id 
# with ranking and winner photo or set to False
send_final_message = chat_id

# link the ranked post 
# in final message on the result counter
post_link = True 

# Create a CSV file with all participants found
create_csv = True

# Send CSV file to a given chat id
send_csv = False

# END TWEAK CONFIG
#########################

# global vars
participants = []
winner_photo = ""
contest_time = datetime.strptime(contest_date, "%Y-%m-%d %H:%M:%S")

# Set header message
formatted_date = contest_time.strftime("%d.%m.%Y %H:%M")
if contest_days == 1:
    header_message = f"Rangliste 24-Stunden Top {contest_max_ranks} (Stand: {formatted_date})"
else:
    header_message = f"Rangliste {contest_days}-Tage Top {contest_max_ranks} (Stand: {formatted_date})"

async def main():

    async with app:
        async for message in app.get_chat_history(chat_id):

            # check excludes
            for exclude in exclude_pattern:
                if exclude in str(message.caption):
                    # skip this post message
                    continue

            # check if message is a photo
            if str(message.media) == "MessageMediaType.PHOTO":

                # check if message was in desired timeframe
                message_time = datetime.strptime(str(message.date), "%Y-%m-%d %H:%M:%S")
                message_difftime = contest_time - message_time
                #print(message_difftime.days)
                if ( message_difftime.days <= contest_days-1 ):

                    # verify views
                    views_counter = 0
                    if message.views:
                        views_counter = message.views
                    else:
                        continue

                    # verify reactions
                    reaction_counter = 0
                    try:
                        reaction_counter = message.reactions.reactions[0].count
                    except:
                        continue

                    # the message should have reactions and views
                    if reaction_counter > 0 and views_counter > 0:

                        # check if participant has more than one post
                        duplicate = 0
                        highest_count = 0
                        for participant in participants:
                            if participant.author_signature == message.author_signature:
                                duplicate = 1
                                if contest_days == 1:
                                    # already exist in participants array, only one post allowed (prefer best)
                                    if participant.reactions.reactions[0].count > message.reactions.reactions[0].count:
                                        # best variant already exist, do not append it again
                                        continue
                                    else:
                                        # update the better post in existent array
                                        participant = message
                                else:
                                    post_count = participant.reactions.reactions[0].count

                                    # remember the best meme of current participant
                                    if post_count > highest_count:
                                        highest_count = post_count

                                    if ( highest_count < message.reactions.reactions[0].count ):
                                        # update caption and image
                                        participant.photo.file_id = message.photo.file_id
                                        participant.photo.file_unique_id = message.photo.file_unique_id
                                        participant.caption = message.caption
                                        participant.id = message.id
                                        participant.views = message.views
                                    
                                    # update reaction counter
                                    participant.reactions.reactions[0].count += message.reactions.reactions[0].count

                            elif str(message.author_signature) == "None":
                                duplicate = 1

                        if duplicate == 0 and message_difftime.days != -1:
                            # append to participants array
                            # print("Add participant %s (%s) %s" 
                            #         % (message.author_signature, str(message_difftime), message.reactions.reactions[0].count))
                            participants.append(message)

                        if create_csv:
                            csv_rows = []

                            for participant in participants:
                                participant_postlink = build_postlink(participant)
                                csv_rows.append([participant.author_signature, participant_postlink, 
                                    participant.date, participant.reactions.reactions[0].count, participant.views])

                            write_csv(csv_rows)

                else:
                    break

    # create final message with ranking
    final_message = create_ranking()

    if send_final_message:
        async with app:
            if winner_photo != "":
                await app.send_photo(send_final_message, winner_photo, final_message, parse_mode=enums.ParseMode.MARKDOWN)
            else:
                if contest_days == 1:
                    print("Something went wrong! Can not find winner photo for final ranking message")
                else:
                    print("Can not find best meme photo, please fix me")

    if create_csv and send_csv:
        async with app:
            await app.send_document(send_csv, "contest.csv", caption=header_message)

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
    while i <= contest_max_ranks:
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
            # extract handle from caption
            winner_caption_array = winner.caption.split()
            for caption_word in winner_caption_array:
                if "@" in caption_word:
                    # make sure nobody can inject commands here
                    winner_display_name = re.sub(r"@[^a-zA-Z0-9 ]", "", caption_word)

        # add post link
        if post_link:
            winner_postlink = build_postlink(winner)
            winner_count = f"[{winner_count}]({winner_postlink})"

        final_message = final_message + "#" + str(rank) \
                + " " + winner_display_name \
                + " " + winner_count \
                + " 🏆 \n"

        i += 1
        if i > contest_max_ranks:
            break
    
    final_message = header_message + ":\n\n" + final_message + "\n" + final_message_footer
    print(final_message)   

    return final_message

app.run(main())
