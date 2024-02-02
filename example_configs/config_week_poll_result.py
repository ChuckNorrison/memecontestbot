#!/usr/bin/env python
from datetime import datetime

#########################
# START TWEAK CONFIG HERE

# channel name for public channels
# or chat id for private chats to analyze
CHAT_ID = "memecontest"

# only posts prior this date and time will get analyzed
CONTEST_DATE = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#CONTEST_DATE = "2022-12-26 23:59:59" # example with fixed date and time

# only posts newer than x days will be ranked.
# 1 = 24h contest without duplicates,
# 2+ days post with same author gets added
CONTEST_DAYS = 7

# amount of winners to honor in ranking message
CONTEST_MAX_RANKS = 10

# Evaluate the last poll found and
# Overrides CONTEST_POLL
# True or False
CONTEST_POLL_RESULT = True

# Append ranking into poll result message
CONTEST_POLL_RESULT_RANKING = True

# Update the highscore message with winner
# If not exist, create a message first
# False or postlink (https://t.me/c/{chat_id}/{message_id})
CONTEST_HIGHSCORE = "https://t.me/memecontest/11"

# posts we want to exclude from ranking.
# Add your patterns to this array.
EXCLUDE_PATTERN = ["Meme Contest", "Rangliste"]

# text header to print on top of final messages
FINAL_MESSAGE_HEADER= (
    "Ihr habt mit {TEMPLATE_POLL_VOTES} Stimmen gewählt,\n"
    "Das Meme der Woche vom {TEMPLATE_TIME}\n"
    "geht an {TEMPLATE_POLL_WINNER}\n\n"
    "Wochensieger vom "
    f"{datetime.strptime(CONTEST_DATE, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y')}\n"
    "von {TEMPLATE_WINNER} mit {TEMPLATE_VOTES} 🏆\n\n"
    f"Rangliste {CONTEST_DAYS}-Tage "
)

FINAL_MESSAGE_HEADER_DRAW = (
    "Gleichstand mit je {TEMPLATE_POLL_VOTES} Stimmen!\n"
    "Das Meme der Woche vom {TEMPLATE_TIME}\n"
    "geht an {TEMPLATE_POLL_WINNER} und {TEMPLATE_POLL_WINNER_SECOND}\n\n"
    "Wochensieger vom "
    f"{datetime.strptime(CONTEST_DATE, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y')}\n"
    "von {TEMPLATE_WINNER} mit {TEMPLATE_VOTES} 🏆\n\n"
    f"Rangliste {CONTEST_DAYS}-Tage "
)

# Display a special Icon or Symbol for the first rank
RANKING_WINNER_SUFFIX = "🎭"

# simple text footer in ranking view,
# should be used to identify exclude posts
FINAL_MESSAGE_FOOTER = f"🏆 [{EXCLUDE_PATTERN[0]}](https://t.me/memecontest) 🏆"

# Send the final message to a given chat id
# with ranking and winner photo or set to False
FINAL_MESSAGE_CHAT_ID = CHAT_ID

# link the ranked post
# in final message on the result counter
POST_LINK = False

# Add winner photo in final message
# True to add or False to disable the winner photo for final message
POST_WINNER_PHOTO = True

# Ranking based on memes not authors
# True or False to rank the authors instead
RANK_MEMES = False

# END TWEAK CONFIG
#########################
