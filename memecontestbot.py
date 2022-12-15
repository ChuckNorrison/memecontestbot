from pyrogram import Client, enums
from datetime import datetime

app = Client("my_account")

# TWEAK CONFIG HERE
chat_id = "mychannelname" # channel name for public or chat id for private chats like -1123412341234
contest_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # you can enter any time manually as decribed
contest_days = 1 # 1 = 24h contest without duplicates, 2+ days post with same author gets added 
final_message_footer = "🏆 @mychannelname 🏆" # simple text footer in ranking view
send_final_message = False # Send the final message to the chat id with ranking and winner photo


# global vars
participants = []
winners = []
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
                            if participant.author_signature == message.author_signature \
                                    or str(message.author_signature) == "None":
                                if contest_days == 1:
                                    # already exist in participants array, only one post allowed (prefer best)
                                    if participant.reactions.reactions[0].count > message.reactions.reactions[0].count:
                                        # best variant does exist, do not append this again
                                        duplicate = 1
                                        break
                                    else:
                                        # update the better count in existent array if possible
                                        participant.reactions.reactions[0].count = message.reactions.reactions[0].count
                                else:
                                    participant.reactions.reactions[0].count += message.reactions.reactions[0].count
                                    break

                        if duplicate == 0:
                            # append to participants array
                            participants.append(message)

    # create winner array
    i = 1
    while i <= 10:
        winner = get_winner()
        if winner:
            if i == 1:
                # this is our rank 1 winner
                winner_photo = winner.photo.file_id
            winners.append(winner)
        i += 1

    # create final message with ranking
    rank = 1
    formatted_date = contest_time.strftime("%d.%m.%Y %H:%M")
    
    if contest_days == 1:
        final_message = f"Rangliste 24-Stunden Top 10 ({formatted_date}):\n\n"
    else:
        final_message = f"Rangliste {contest_days}-Tage Top 10 ({formatted_date}):\n\n"

    last_winner = ""
    for winner in winners:
        if last_winner == winner.author_signature:
            continue

        final_message = final_message + "#" + str(rank) \
                + " " + winner.author_signature \
                + " " + str(winner.reactions.reactions[0].count) \
                + " 🏆 \n"
        last_winner = winner.author_signature

        rank += 1
        if rank > 10:
            break
    
    final_message = final_message + "\n" + final_message_footer
    print(final_message)
    
    if send_final_message:
        async with app:
            await app.send_photo(chat_id, winner_photo, final_message, parse_mode=enums.ParseMode.MARKDOWN)

def get_winner():
    highest_count = 0
    winner = []

    i = 0
    for participant in participants:
        i += 1
        if participant.reactions.reactions[0].count > highest_count:
            highest_count = participant.reactions.reactions[0].count
            winner = participant
            winner_id = i-1

    # remove winner from participants array
    if len(participants) > 1:
        participants.pop(winner_id)

    return winner

app.run(main())
