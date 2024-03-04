#!/usr/bin/env python

"""Example config file"""

from datetime import datetime

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

# Create a ranking based on views count and not reactions
# True or False
CONTEST_RANKING_BY_VIEWS = False

# Create a poll with numbered images from winners found
# True or False (Default: False)
CONTEST_POLL = False

# Evaluate the last poll found and
# Overrides CONTEST_POLL
# True or False
CONTEST_POLL_RESULT = False

# Set color for numbered photos
# False for random colors or RGB, set as array [212, 175, 55]
CONTEST_POLL_COLOR = [212, 175, 55]

# Poll result mode: Pattern to find the last open poll to evaluate
# Poll create mode: Pattern used with CONTEST_POLL_FROM_POLLS
# to find recent poll results and create a new poll
CONTEST_POLL_PATTERN = ["Meme of the week"]

# Update the highscore message with winner
# If not exist, create a message manually first
# False or postlink (https://t.me/c/{chat_id}/{message_id})
CONTEST_HIGHSCORE = False

# posts we want to exclude from ranking.
# Add your patterns to this array.
EXCLUDE_PATTERN = ["Meme Contest", "Ranking"]

# Text header to print on top of final messages
# Template variables:
# - ranking mode: {TEMPLATE_WINNER}, {TEMPLATE_VOTES}
# - poll create mode: {TEMPLATE_TIME}, {TEMPLATE_POLL_WINNER},
#   {TEMPLATE_POLL_VOTES}
# - poll evaluate mode: {TEMPLATE_START_DATE}, {TEMPLATE_END_DATE}
FINAL_MESSAGE_HEADER = "Ranking 24-hours "

# simple text footer in ranking view,
# should be used to identify exclude posts
FINAL_MESSAGE_FOOTER = f"🏆 [{EXCLUDE_PATTERN[0]}](https://t.me/mychannelname) 🏆"

# Send the final message to a given chat id
# with ranking and winner photo or set to False
FINAL_MESSAGE_CHAT_ID = False

# Generate a ranking message based on CSV data
# could be useful for monthly rankings
# Set config to True or False (Default: False)
PARTICIPANTS_FROM_CSV = False

# Print eternal list of participants and override everything else
# Needs at least 30 Days of CSV Data to collect
PARTICIPANTS_LIST = False

# Used to allow duplicates to collect historical data
PARTICIPANT_DUPLICATES = False

# link the ranked post
# in final message on the result counter
# True or False (Default: True)
POST_LINK = True

# Path to a CSV File oder False
# Ranking Mode: Define path to file if PARTICIPANTS_FROM_CSV is used
# Collect Mode: Set to check repost against unique ids
CSV_FILE = (
    "contest_memecontest_"
    + f"{datetime.strptime(CONTEST_DATE, '%Y-%m-%d %H:%M:%S').strftime('%Y')}"
    + ".csv"
)
# Ranking Mode: Create or update the CSV_FILE
# with all participants found
CREATE_CSV = True

# Send CSV file to a given chat id
CSV_CHAT_ID = FINAL_MESSAGE_CHAT_ID

# Add winner photo in final message (Default: True)
# False: Disable the winner photo for final message
# True: Find the photo automatically
# "<Path>": A file on disk to post as photo
POST_WINNER_PHOTO = True

# Read author_signature from signed message
# True or False to find author from message caption instead
SIGN_MESSAGES = False

# Ranking based on memes not authors (True)
# or sum up all reactions based by author instead (False)
RANK_MEMES = True

# Send Contest Participant found from CHAT_ID to this chat
# or set to False to disable this feature
POST_PARTICIPANTS_CHAT_ID = False

# Format date
DATE_FORMATTING = "%d.%m.%Y"

# END TWEAK CONFIG
#########################
