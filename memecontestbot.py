from pyrogram import Client
from datetime import date

app = Client("my_account")

# TWEAK CONFIG HERE
chat_id = "mychannelname" # channel name for public or chat id for private chats like -1123412341234
contest_day = date.today() # can be a string like "2022-12-14"
final_message_footer = "@mychannelname"

# global vars
participants = []
winners = []
winner_photo = ""

async def main():

    async with app:
        # "me" refers to your own chat (Saved Messages)
        async for message in app.get_chat_history(chat_id):

            # check if message is a photo
            if str(message.media) == "MessageMediaType.PHOTO":

                # check if message was in desired timeframe        
                if str(contest_day) in str(message.date):

                    # verify views
                    views_counter = 0
                    if message.views:
                        views_counter = message.views
                    else:
                        continue

                    # verify reactions
                    reaction_counter = 0
                    if message.reactions:
                        reaction_counter = message.reactions.reactions[0].count
                    else:
                        continue

                    # the message should have reactions and views
                    if reaction_counter > 0 and views_counter > 0:

                        # check if participant has more than one post
                        duplicate = 0
                        for participant in participants:
                            if participant.author_signature == message.author_signature \
                                    or str(message.author_signature) == "None":
                                # already exist in participants array, only one post allowed
                                duplicate = 1
                                break

                        if duplicate == 0:
                            # append to participants array
                            # print("Add participant %s" % str(message.author_signature))
                            participants.append(message)

    # create winner array
    i = 1
    while i <= 10:
        winner = get_winner()
        if winner:
            if i == 1:
            # this is our rank 1 winner
                winner_photo = winner.photo.file_id
                #print(winner_photo)
            #print("Add winner %s" % str(winner.author_signature))
            winners.append(winner)
        i += 1

    # create final message of top 10 winners
    rank = 1
    formatted_date = contest_day.strftime("%d.%m.%Y")
    final_message = f"Tages-Ranking Top 10 ({formatted_date}):\n\n"
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
    
    async with app:
        await app.send_photo(chat_id, winner_photo, final_message)

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
