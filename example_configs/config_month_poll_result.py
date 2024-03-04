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

last_date = f"{year}-{month}-{day} {hour}:{minute}:{second}"

# Days to analyze
# Automatically set to last day of month with calender
CONTEST_DAYS = day

# amount of winners to honor in ranking message
CONTEST_MAX_RANKS = 12

# Create a poll to vote from numbered images
# True or False
CONTEST_POLL = False

# Evaluate the last poll found
# Overrides CONTEST_POLL
# True or False
CONTEST_POLL_RESULT = True

# Append ranking into poll result message
CONTEST_POLL_RESULT_RANKING = False

# Poll result mode: Pattern to find the last open poll to evaluate
# Poll create mode: Pattern used with CONTEST_POLL_FROM_POLLS
# to find recent poll results and create a new poll
CONTEST_POLL_PATTERN = ["Meme des Monats"]

# Update the highscore message with winner
# If not exist, create a message first
# False or postlink (https://t.me/c/{chat_id}/{message_id})
CONTEST_HIGHSCORE = "https://t.me/memecontest/11"

# posts we want to exclude from ranking.
# Add your patterns to this array.
EXCLUDE_PATTERN = ["Meme Contest", "Rangliste"]

# text header to print on top of final messages
month = datetime.strptime(last_date, "%Y-%m-%d %H:%M:%S")
month = date.strftime("%B")
FINAL_MESSAGE_HEADER= (
    "Ihr habt mit {TEMPLATE_POLL_VOTES} Stimmen gewählt,\n"
    f"Das Meme des Monats vom {month} {year}\n"
    "geht an {TEMPLATE_POLL_WINNER}\n\n"
)

FINAL_MESSAGE_HEADER_DRAW = (
    "Gleichstand mit je {TEMPLATE_POLL_VOTES} Stimmen!\n"
    f"Das Meme des Monats vom {month} {year}\n"
    "geht an {TEMPLATE_POLL_WINNER} und {TEMPLATE_POLL_WINNER_SECOND}\n\n"
)

# Display a special Icon or Symbol for the first rank
RANKING_WINNER_SUFFIX = "🎗"

# text footer to print on bottom of final messages,
# Use exclude pattern in combination to filter bot messages
FINAL_MESSAGE_FOOTER = f"🏆 [{EXCLUDE_PATTERN[0]}](https://t.me/memecontest) 🏆"

# Send the final message to a given chat id
# with ranking and winner photo or set to False
FINAL_MESSAGE_CHAT_ID = CHAT_ID

# link the ranked post
# in final message on the result counter (True or False)
POST_LINK = True

# Ranking based on memes not authors
# True or False to rank the authors instead
RANK_MEMES = False

# END TWEAK CONFIG
#########################
