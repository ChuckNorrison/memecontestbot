#!/usr/bin/env python

"""
Simple Bot to analyze telegram post reactions and create a ranking.
Can be configured for daily or weekly rankings (get_chat_history has a limit of posts to return from chat).

Usage:
Start bot to create a nice ranking.
"""

from pyrogram import Client, enums
from datetime import datetime

app = Client("my_account")

# TWEAK CONFIG HERE
chat_id = "mychannelname" # channel name for public channels or chat id for private chats.
contest_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # you can enter any time manually as decribed
#contest_date = "2022-12-10 23:59:59"
contest_days = 1 # 1 = 24h contest without duplicates, 2+ days post with same author gets added 
contest_days_ranking = 10 # amount of winners to honor in ranking
final_message_footer = "🏆 [Meme Contest](https://t.me/mychannelname) 🏆" # simple text footer in ranking view
send_final_message = False # Send the final message to a given chat id with ranking and winner photo or set to False
post_link = True # link the ranked post in final message behind result count

# global vars
participants = []
winner_photo = ""
contest_time = datetime.strptime(contest_date, "%Y-%m-%d %H:%M:%S")

async def main():

    async with app:
        async for message in app.get_chat_history(chat_id):

            # check if message is a photo
            if ( str(message.media) == "MessageMediaType.PHOTO" 
                    # filter admin posts
                    and "Meme Contest" not in str(message.caption) ):

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
                                    
                                    # update reaction counter
                                    participant.reactions.reactions[0].count += message.reactions.reactions[0].count

                            elif str(message.author_signature) == "None":
                                duplicate = 1

                        if duplicate == 0 and message_difftime.days != -1:
                            # append to participants array
                            # print("Add participant %s (%s) %s" 
                            #         % (message.author_signature, str(message_difftime), message.reactions.reactions[0].count))
                            participants.append(message)
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

def get_winner():
    """Extracts the best post from participants and returns the winner"""
    highest_count = 0
    winner = []
    winner_id = -1

    i = 0
    for participant in participants:
        if participant.reactions.reactions[0].count > highest_count:
            highest_count = participant.reactions.reactions[0].count
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
    while i <= contest_days_ranking:
        current_winner = get_winner()
        if current_winner:
            #print("Add Winner %s %s" % (current_winner.author_signature, str(current_winner.reactions.reactions[0].count)))
            winners.append(current_winner)
        i += 1

    return winners

def create_ranking():
    """Build the final ranking message"""
    global winner_photo

    # get winners
    winners = get_winners()

    rank = 1
    formatted_date = contest_time.strftime("%d.%m.%Y %H:%M")
    
    if contest_days == 1:
        final_message = f"Rangliste 24-Stunden Top {contest_days_ranking} (Stand: {formatted_date}):\n\n"
    else:
        final_message = f"Rangliste {contest_days}-Tage Top {contest_days_ranking} (Stand: {formatted_date}):\n\n"

    last_winner = ""
    for winner in winners:

        # set rank 1 winner photo
        if rank == 1:
            winner_photo = winner.photo.file_id

        # check for telegram handles in caption
        winner_display_name = winner.author_signature
        if not winner_display_name:
            winner_display_name = "None"

        if "@" in str(winner.caption):
            # extract handle from caption
            winner_caption_array = winner.caption.split()
            for caption_word in winner_caption_array:
                if "@" in caption_word:
                    winner_display_name = caption_word

        # add post link
        winner_count = winner.reactions.reactions[0].count
        if post_link:
            winner_message_id = str(winner.id)
            winner_chat_id = str(winner.chat.id).replace("-100","")
            winner_post_url = "https://t.me/c/" + winner_chat_id + "/" + winner_message_id
            winner_count = f"[{winner_count}]({winner_post_url})"

        final_message = final_message + "#" + str(rank) \
                + " " + winner_display_name \
                + " " + winner_count \
                + " 🏆 \n"

        rank += 1
        if rank > contest_days_ranking:
            break
    
    final_message = final_message + "\n" + final_message_footer
    print(final_message)   

    return final_message

app.run(main())
