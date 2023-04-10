#!/usr/bin/env python
from datetime import datetime

#########################
# START TWEAK CONFIG HERE

# channel name for public channels
# or chat id for private chats to analyze
CHAT_ID = "contestmeme"

# only posts prior this date and time will get analyzed
#CONTEST_DATE = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
CONTEST_DATE = "2023-04-08 23:59:59" # example with fixed date and time

# only posts newer than x days will be ranked.
# 1 = 24h contest without duplicates,
# 2+ days post with same author gets added
CONTEST_DAYS = 7

# amount of winners to honor in ranking message
CONTEST_MAX_RANKS = 10

# Create a poll with numbered images from winners found
# True or False
CONTEST_POLL = False

# Evaluate the last poll found and
# Overrides CONTEST_POLL
# True or False
CONTEST_POLL_RESULT = False

# posts we want to exclude from ranking.
# Add your patterns to this array.
EXCLUDE_PATTERN = ["Meme Contest", "Tagessieger", "Rangliste"]

# text header to print on top of final messages
FINAL_MESSAGE_HEADER = (
    f"[Wochensieger](https://t.me/+GI5KPz-LRLEyMDA0) vom "
    f"{datetime.strptime(CONTEST_DATE, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y')} "
    "von {TEMPLATE_WINNER} mit {TEMPLATE_VOTES} 🏆\n\n"
    f"Rangliste {CONTEST_DAYS}-Tage "
)

# Display a special Icon or Symbol for the first rank
RANKING_WINNER_SUFFIX = "🎖"

# simple text footer in ranking view,
# should be used to identify exclude posts
FINAL_MESSAGE_FOOTER = f"🏆 [{EXCLUDE_PATTERN[0]}](https://t.me/contestmeme) 🏆"

# Send the final message to a given chat id
# with ranking and winner photo or set to False
#FINAL_MESSAGE_CHAT_ID = -1001804783605 # Dev Kanal
FINAL_MESSAGE_CHAT_ID = False

# Collect all CSV data and write new overall CSV file
# Set config to True or False
PARTICIPANTS_FROM_CSV = False

# link the ranked post
# in final message on the result counter
POST_LINK = True

# Create a CSV file with all participants found
CREATE_CSV = False

# Send CSV file to a given chat id
CSV_CHAT_ID = FINAL_MESSAGE_CHAT_ID

# Add winner photo in final message
# True to add or False to disable the winner photo for final message
POST_WINNER_PHOTO = False

# Read author_signature from signed message
# True or False to find author from message caption instead
SIGN_MESSAGES = False

# Ranking based on memes not authors
# True or False to rank the authors instead
RANK_MEMES = False

# Send Contest Participant found from CHAT_ID to this chat
# or set to False to disable this feature
POST_PARTICIPANTS_CHAT_ID = False

# END TWEAK CONFIG
#########################
