#!/usr/bin/env python
from datetime import datetime, timedelta
from calendar import monthrange

#########################
# START TWEAK CONFIG HERE

# channel name for public channels
# or chat id for private chats to analyze
CHAT_ID = "memecontest"

# only posts prior this date and time will get analyzed
# monthly ranking via crontab on first day of next month
CONTEST_DATE = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
#CONTEST_DATE = "2023-06-30 23:59:00" # example with fixed date and time

# only posts newer than x days will be ranked.
# 1 = 24h contest without duplicates,
# 2+ days post with same author gets added
year = datetime.strptime(CONTEST_DATE, '%Y-%m-%d %H:%M:%S').strftime('%Y')
month = datetime.strptime(CONTEST_DATE, '%Y-%m-%d %H:%M:%S').strftime('%m')
CONTEST_DAYS = monthrange(int(year), int(month))[1]

# amount of winners to honor in ranking message
CONTEST_MAX_RANKS = 10

# Update the highscore message with winner
# If not exist, create a message first
# False or postlink (https://t.me/c/{chat_id}/{message_id})
CONTEST_HIGHSCORE = "https://t.me/memecontest/11"

# posts we want to exclude from ranking.
# Add your patterns to this array.
EXCLUDE_PATTERN = ["Meme Contest", "Tagessieger", "Rangliste"]

# text header to print on top of final messages
# TEMPLATE_WINNER = "tester"
# TEMPLATE_VOTES = 50
FINAL_MESSAGE_HEADER = (
    f"Monatssieger vom "
    f"{datetime.strptime(CONTEST_DATE, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y')} "
    "von {TEMPLATE_WINNER} mit {TEMPLATE_VOTES} 🏆\n\n"
    f"Rangliste {datetime.strptime(CONTEST_DATE, '%Y-%m-%d %H:%M:%S').strftime('%B')} "
)

# simple text footer in ranking view,
# should be used to identify exclude posts
FINAL_MESSAGE_FOOTER = f"🏆 [{EXCLUDE_PATTERN[0]}](https://t.me/memecontest) 🏆"

# Display a special Icon or Symbol for the first rank
RANKING_WINNER_SUFFIX = "🏵"

# Send the final message to a given chat id
# with ranking and winner photo or set to False
FINAL_MESSAGE_CHAT_ID = CHAT_ID

# Collect all CSV data and write new overall CSV file
# Set config to True or False
PARTICIPANTS_FROM_CSV = True

# Eternal list of lords mode, override everything else
# Needs at least 30 Days of CSV Data
#PARTICIPANTS_LIST = False

# Path to a CSV File oder False
# Ranking Mode: Define path to file if PARTICIPANTS_FROM_CSV is used
# Collect Mode: Set to check repost against unique ids
CSV_FILE = (
    "contest_contestmeme_"
    + f"{datetime.strptime(CONTEST_DATE, '%Y-%m-%d %H:%M:%S').strftime('%Y')}"
    + ".csv"
)
CREATE_CSV = False

# Send CSV file to a given chat id
CSV_CHAT_ID = False

# link the ranked post
# in final message on the result counter (True or False)
POST_LINK = False

# Add winner photo in final message
# True to add or False to disable the winner photo for final message
POST_WINNER_PHOTO = False

# Ranking based on memes not authors
# True or False to rank the authors instead
RANK_MEMES = False

# Send Contest Participant found from CHAT_ID to this chat
# if enabled, ranking message is disabled
# set to False to disable
POST_PARTICIPANTS_CHAT_ID = False

# END TWEAK CONFIG
#########################
