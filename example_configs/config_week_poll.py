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
CONTEST_DAYS = 7

# amount of winners to honor in ranking message
CONTEST_MAX_RANKS = 7

# Create a poll with numbered images from winners found
# True or False
CONTEST_POLL = True

# Set color for numbered photos
# False for random colors or RGB, set as array [212, 175, 55]
CONTEST_POLL_COLOR = [212, 175, 55]

# Header for poll message
CONTEST_POLL_HEADER = (
    "Die Wahl zum Meme der Woche\n"
    "vom {TEMPLATE_START_DATE} - {TEMPLATE_END_DATE} (24h Abstimmung)"
)

# posts we want to exclude from ranking.
# Add your patterns to this array.
EXCLUDE_PATTERN = ["Meme Contest", "Rangliste"]

# text header to print on top of final messages
FINAL_MESSAGE_HEADER= "Rangliste 7-Tage "

# Display a special Icon or Symbol for the first rank
RANKING_WINNER_SUFFIX = ""

# simple text footer in ranking view,
# should be used to identify exclude posts
FINAL_MESSAGE_FOOTER = (
    f"🏆 [{EXCLUDE_PATTERN[0]}](https://t.me/memecontest) 🏆"
    "\n\nHier bitte über das "
    "Meme der Woche abstimmen!\n"
    "⬇️ ⬇️ ⬇️ ⬇️ ⬇️ ⬇️"
)

# Send the final message to a given chat id
# with ranking and winner photo or set to False
FINAL_MESSAGE_CHAT_ID = CHAT_ID

# Collect all CSV data and write new overall CSV file
# Set config to True or False
PARTICIPANTS_FROM_CSV = True

# link the ranked post
# in final message on the result counter
POST_LINK = True

# Path to a CSV File or False
# Ranking or Poll Mode: Define path to file if PARTICIPANTS_FROM_CSV is used
# Collect Mode: Set to check repost against unique ids
CSV_FILE = (
    "contest_contestmeme_"
    + f"{datetime.strptime(CONTEST_DATE, '%Y-%m-%d %H:%M:%S').strftime('%Y')}"
    + ".csv"
)

# Add winner photo in final message (Default: True)
# False: Disable the winner photo for final message
# True: Find the photo automatically
# "<Path>": A file on disk to post as photo
POST_WINNER_PHOTO = False

# Ranking based on memes not authors
# True or False to rank the authors instead
RANK_MEMES = True

# END TWEAK CONFIG
#########################
