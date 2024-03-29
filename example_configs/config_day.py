#!/usr/bin/env python
from datetime import datetime

#########################
# START TWEAK CONFIG HERE

# channel name for public channels
# or chat id for private chats to analyze
CHAT_ID = "memecontest"

# only posts prior this date and time will get analyzed
CONTEST_DATE = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#CONTEST_DATE = "2023-02-17 23:59:59" # example with fixed date and time

# only posts newer than x days will be ranked.
# 1 = 24h contest without duplicates,
# 2+ days post with same author gets added
CONTEST_DAYS = 1

# amount of winners to honor in ranking message
CONTEST_MAX_RANKS = 10

# Update the highscore message with winner
# If not exist, create a message first
# False or postlink (https://t.me/c/{chat_id}/{message_id})
CONTEST_HIGHSCORE = "https://t.me/memecontest/11"

# Format the date
# https://strftime.org/
DATE_FORMATTING = "%b. %d, %Y"

# posts we want to exclude from ranking.
# Add your patterns to this array.
EXCLUDE_PATTERN = ["Meme Contest", "Rangliste"]

# text header to print on top of final messages
# Template variables: {TEMPLATE_WINNER}, {TEMPLATE_VOTES}
FINAL_MESSAGE_HEADER = (
    f"Tagessieger vom "
    f"{datetime.strptime(CONTEST_DATE, '%Y-%m-%d %H:%M:%S').strftime(DATE_FORMATTING)} "
    "von {TEMPLATE_WINNER} mit {TEMPLATE_VOTES} 🏆\n\n"
    f"Rangliste 24-Stunden "
)

# text footer to print on bottom of final messages,
# Use exclude pattern in combination to filter bot messages
FINAL_MESSAGE_FOOTER = f"🏆 [{EXCLUDE_PATTERN[0]}](https://t.me/memecontest) 🏆"

# Send the final message to a given chat id
# with ranking and winner photo or set to False
FINAL_MESSAGE_CHAT_ID = CHAT_ID

# Collect all CSV data and write new overall CSV file
# Set config to True or False
PARTICIPANTS_FROM_CSV = False

# link the ranked post
# in final message on the result counter
POST_LINK = True

# Path to a CSV File oder False
# Ranking Mode: Define path to file if PARTICIPANTS_FROM_CSV is used
# Collect Mode: Set to check repost against unique ids
CSV_FILE = (
    "contest_contestmeme_"
    + f"{datetime.strptime(CONTEST_DATE, '%Y-%m-%d %H:%M:%S').strftime('%Y')}"
    + ".csv"
)
# Ranking Mode: Create or update the CSV_FILE
# with all participants found
CREATE_CSV = True

# Send CSV file to a given chat id
#CSV_CHAT_ID = FINAL_MESSAGE_CHAT_ID
CSV_CHAT_ID = False

# Ranking based on memes not authors
# True or False to rank the authors instead
RANK_MEMES = True

# END TWEAK CONFIG
#########################
