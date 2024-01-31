#!/usr/bin/env python
from datetime import datetime

#########################
# START TWEAK CONFIG HERE

# channel name for public channels
# or chat id for private chats to analyze
CHAT_ID = "memecollector"

# only posts prior this date and time will get analyzed
CONTEST_DATE = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#CONTEST_DATE = "2022-12-27 23:59:59" # example with fixed date and time

# Set a message footer for each message send
FINAL_MESSAGE_FOOTER = ""

# Path to a CSV File oder False
# Ranking Mode: Create/Update a CSV file with all participants found
# Collect Mode: Set to check repost against unique ids
CSV_FILE = False

# Enable collect mode with a valid chat id or False
# Send Contest Participant found from CHAT_ID to this chat
# if enabled, ranking message is disabled
POST_PARTICIPANTS_CHAT_ID = "memecontest"

# END TWEAK CONFIG
#########################
