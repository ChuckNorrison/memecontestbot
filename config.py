#!/usr/bin/env python

#########################
# START TWEAK CONFIG HERE

# channel name for public channels 
# or chat id for private chats to analyze
CHAT_ID = "mychannelname"

# only posts prior this date and time will get analyzed
CONTEST_DATE = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
#CONTEST_DATE = "2022-12-26 23:59:59" # example with fixed date and time

# only posts newer than x days will be ranked. 
# 1 = 24h contest without duplicates, 
# 2+ days post with same author gets added
CONTEST_DAYS = 1

# amount of winners to honor in ranking message
CONTEST_MAX_RANKS = 10

# posts we want to exclude from ranking. 
# Add your patterns to this array.
EXCLUDE_PATTERN = ["Meme Contest", "Tagessieger", "Rangliste"] 

# simple text footer in ranking view, 
# should be used to identify exclude posts
FINAL_MESSAGE_FOOTER = f"🏆 [{EXCLUDE_PATTERN[0]}](https://t.me/mychannelname) 🏆"

# Send the final message to a given chat id 
# with ranking and winner photo or set to False
FINAL_MESSAGE_CHAT_ID = False 

# link the ranked post 
# in final message on the result counter
POST_LINK = True 

# Create a CSV file with all participants found
CREATE_CSV = True

# Send CSV file to a given chat id
CSV_CHAT_ID = FINAL_MESSAGE_CHAT_ID

# Add winner photo in final message
# True to add or False to disable the winner photo for final message
POST_WINNER_PHOTO = True

# Read author_signature from signed message
# True or False to find author from message caption instead
SIGN_MESSAGES = True

# END TWEAK CONFIG
#########################
