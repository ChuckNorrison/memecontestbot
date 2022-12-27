#!/usr/bin/env python

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
exclude_pattern = ["Meme Contest", "Tagessieger", "Rangliste"] 

# simple text footer in ranking view, 
# should be used to identify exclude posts
final_message_footer = f"🏆 [{exclude_pattern[0]}](https://t.me/mychannelname) 🏆"

# Send the final message to a given chat id 
# with ranking and winner photo or set to False
final_message_chat_id = False 

# link the ranked post 
# in final message on the result counter
post_link = True 

# Create a CSV file with all participants found
create_csv = True

# Send CSV file to a given chat id
csv_chat_id = final_message_chat_id

# Add winner photo in final message
# True to add or False to disable the winner photo for final message
post_winner_photo = False

# END TWEAK CONFIG
#########################
