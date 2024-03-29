# memecontestbot
[![Pylint](https://github.com/ChuckNorrison/memecontestbot/actions/workflows/pylint.yml/badge.svg)](https://github.com/ChuckNorrison/memecontestbot/actions/workflows/pylint.yml)

A telegram bot for channel or group, to create a ranking message based on photo reactions like a meme contest.

The Bot can be set as cron to post a ranking automatically. 
Daily, weekly or monthly ranking messages for your Telegram Channel or Group.

## Features
- On execute, it walks through chat history of a given telegram `CHAT_ID` and period of `CONTEST_DAYS`. It analyze reactions to create a ranking.
- Decide whether to post the final ranking message in a given chat or not (`FINAL_MESSAGE_CHAT_ID`)
- Set a number as `CONTEST_MAX_RANKS` to limit winners count for the final ranking message
- Set `EXCLUDE_PATTERN` to exclude message posts from analyzing.
- Enable `CREATE_CSV`, to log all message posts found with amount of reactions and views count into a CSV file.
- Enable `RANK_MEMES` to collect votes based on Memes. Disable for Author based ranking, so all votes gets added.
- Collect Photos from `CHAT_ID` and post them to another Chat defined as `POST_PARTICIPANTS_CHAT_ID`
- Use `PARTICIPANTS_FROM_CSV` to create ranking from CSV data instead of chat data
- Enable `CONTEST_POLL` to create a ranking with poll and vote from numbered images
- Enable `CONTEST_POLL_RESULT` to evaluate last poll and post the winner
- Set `CONTEST_HIGHSCORE` to update a highscore message with the ranking winner

## Setup Telegram App
The first step requires you to obtain a valid Telegram API key (api_id and api_hash pair):

- Visit https://my.telegram.org/apps and log in with your Telegram account.
- Fill out the form with your details and register a new Telegram application.
- Done. The API key consists of two parts: api_id and api_hash. Keep it secret.

## Setup Telegram Bot
The Bot was developed and tested with Python 3.8+ on Debian based distro.

### Clone this repository
- `git clone https://github.com/ChuckNorrison/memecontestbot`
- `cd memecontestbot`
- Edit the file `config.py` and insert your desired telegram chat id or public channel name in `CHAT_ID`)
- Edit the file `config_api.py` and insert your API ID and API HASH

### Install Python 3.x and module dependencies
- `sudo apt install python3 python3-pip`
- `pip3 install -r requirements.txt`

If you already run some python projects, keep in mind to use a [venv](https://docs.python.org/3/library/venv.html) or alternative ways to install python (i.e. check deadsnakes ppa to install specific python versions).

## Usage
Start the bot with `python3 memecontestbot.py`. 

On first start it will ask for your corresponding phone number to act as userbot. The bot will use your telegram account and so it will be visible with your telegram user. Delete the file `my_account.session`, to reset authentication.

Chats should be configured to only accept a single reaction emoji (multiple reaction emojis are not supported yet).

Call the bot with argument `-c` or `--config` and a path to desired configfile to override default `config.py`.

More detailed infos for Telegram API can be found in the [pyrogram docs](https://docs.pyrogram.org/start/setup)
