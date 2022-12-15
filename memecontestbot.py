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
chat_id = "mychannelname"
contest_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # you can enter any time manually as decribed
#contest_date = "2022-12-10 23:59:59"
contest_days = 1 # 1 = 24h contest without duplicates, 2+ days post with same author gets added 
contest_days_ranking = 10 # amount of winners to honor in ranking
final_message_footer = "🏆 @mychannelname 🏆" # simple text footer in ranking view
send_final_message = False # Send the final message to the chat id with ranking and winner photo


# global vars
participants = []
winner_photo = ""
contest_time = datetime.strptime(contest_date, "%Y-%m-%d %H:%M:%S")

async def main():

    async with app:
        # "me" refers to your own chat (Saved Messages)
        async for message in app.get_chat_history(chat_id):

            # check if message is a photo
            if str(message.media) == "MessageMediaType.PHOTO":

                # check if message was in desired timeframe
                message_time = datetime.strptime(str(message.date), "%Y-%m-%d %H:%M:%S")
                message_difftime = contest_time - message_time
                #print(message_difftime)
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
                        for participant in participants:
                            if participant.author_signature == message.author_signature:
                                duplicate = 1
                                if contest_days == 1:
                                    # already exist in participants array, only one post allowed (prefer best)
                                    if participant.reactions.reactions[0].count > message.reactions.reactions[0].count:
                                        # best variant does exist, do not append this again
                                        continue
                                    else:
                                        # update the better count in existent array if possible
                                        participant.reactions.reactions[0].count = message.reactions.reactions[0].count
                                else:
                                    participant.reactions.reactions[0].count += message.reactions.reactions[0].count

                            elif str(message.author_signature) == "None":
                                duplicate = 1

                        if duplicate == 0:
                            # append to participants array
                            #print("Add participant %s" % message.author_signature)
                            participants.append(message)
                else:
                    break

    # create final message with ranking
    final_message = create_ranking()

    if send_final_message:
        async with app:
            if winner_photo != "":
                await app.send_photo(chat_id, winner_photo, final_message, parse_mode=enums.ParseMode.MARKDOWN)
            else:
                print("Can not find winner photo for send final ranking message")

def get_winner():
    """Extracts the best post from participants and returns the winner"""
    highest_count = 0
    winner = []

    i = 0
    for participant in participants:
        if participant.reactions.reactions[0].count > highest_count:
            highest_count = participant.reactions.reactions[0].count
            winner = participant
            winner_id = i
        i += 1

    # remove winner from participants array
    if winner_id and len(participants) >= 0:
        #print("Remove participant %s" % participants[winner_id].author_signature)
        participants.pop(winner_id)

    return winner

def get_winners():
    """Get all winners and return winners array"""
    winners = []

    i = 1
    while i <= contest_days_ranking:
        winner = get_winner()
        if winner:
            #print("Add Winner %s" % winner.author_signature)
            winners.append(winner)
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
        if last_winner == winner.author_signature:
            continue

        if rank == 1:
            # this is our rank 1 winner
            winner_photo = winner.photo.file_id

        final_message = final_message + "#" + str(rank) \
                + " " + winner.author_signature \
                + " " + str(winner.reactions.reactions[0].count) \
                + " 🏆 \n"
        last_winner = winner.author_signature

        rank += 1
        if rank > contest_days_ranking:
            break
    
    final_message = final_message + "\n" + final_message_footer
    print(final_message)   

    return final_message

app.run(main())
