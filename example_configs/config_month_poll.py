#!/usr/bin/env python
from datetime import datetime, timedelta
from calendar import monthrange, monthcalendar

#########################
# START TWEAK CONFIG HERE

# channel name for public channels
# or chat id for private chats to analyze
CHAT_ID = "memecontest"

# only posts prior this date and time will get analyzed
# Automatically set the last day of the last month as CONTEST_DATE
date = datetime.now()
# date = datetime.strptime("2024-03-15 11:59:59", "%Y-%m-%d %H:%M:%S")
CONTEST_DATE = date.strftime("%Y-%m-%d %H:%M:%S")

year = date.year
if date.month > 1:
    month = date.month-1
else:
    month = 12
    year = year-1

day = monthrange(year, month)[1]
hour = date.hour
minute = date.minute
second = date.second

CONTEST_DATE = f"{year}-{month}-{day} {hour}:{minute}:{second}"

# Days to analyze
# Automatically set to last day of month with calender
CONTEST_DAYS = day

# amount of winners to honor in ranking message
CONTEST_MAX_RANKS = 12

# Create a poll with numbered images from winners found
# True or False
CONTEST_POLL = True

# Header for poll message
month = datetime.strptime(CONTEST_DATE, "%Y-%m-%d %H:%M:%S")
month = month.strftime("%B")
CONTEST_POLL_HEADER = (
    "Die Wahl zum Meme des Monats\n"
    f"{month} {year} (24h Abstimmung)"
)
# Set color for numbered photos
# False for random colors or RGB, set as array [212, 175, 55]
CONTEST_POLL_COLOR = [212, 175, 55]

# Collect poll winners and not daily winners
# True or False (Default: False)
CONTEST_POLL_FROM_POLLS = True

# Poll result mode: Pattern to find the last open poll to evaluate
# Poll create mode: Pattern used with CONTEST_POLL_FROM_POLLS
# to find recent poll results and create a new poll
CONTEST_POLL_PATTERN = ["Meme der Woche"]

# posts we want to exclude from ranking.
# Add your patterns to this array.
EXCLUDE_PATTERN = ["Meme Contest", "Rangliste"]

# text header to print on top of final messages
FINAL_MESSAGE_HEADER= f"Rangliste {CONTEST_DAYS}-Days "

# Display a special Icon or Symbol for the first rank
RANKING_WINNER_SUFFIX = ""

# simple text footer in ranking view,
# should be used to identify exclude posts
FINAL_MESSAGE_FOOTER = (
    f"🏆 [{EXCLUDE_PATTERN[0]}](https://t.me/memecontest) 🏆"
    "\n\nHier bitte über das "
    "Meme des Monats abstimmen!\n"
    "⬇️ ⬇️ ⬇️ ⬇️ ⬇️ ⬇️"
)

# Send the final message to a given chat id
# with ranking and winner photo or set to False
FINAL_MESSAGE_CHAT_ID = CHAT_ID

# Collect all CSV data and write new overall CSV file
# Set config to True or False (Default: False)
PARTICIPANTS_FROM_CSV = True

# link the ranked post
# in final message on the result counter
# True or False (Default: True)
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
