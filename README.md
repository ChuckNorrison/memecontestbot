# memecontestbot
A telegram bot for a telegram channel ranking based on reactions. 

The Bot can be set as cron to post a ranking automatically.

## Features
- On execute, it retrieves message posts of a given telegram chat (`CHAT_ID`) and period (`CONTEST_DAYS`) and analyze reactions to create a ranking.
- Decide whether to post the final ranking message in a given chat or not (`FINAL_MESSAGE_CHAT_ID`)
- Configure how much winners will get into the ranking (`CONTEST_MAX_RANKS`)
- Exclude message posts from analyzing (`EXCLUDE_PATTERN`)
- Enable CSV file creation, to log all message posts found with amount of reactions and views count (`CREATE_CSV`)
- Meme or Author based ranking (`RANK_MEMES`)

## Setup Telegram App
The first step requires you to obtain a valid Telegram API key (api_id and api_hash pair):

1. Visit https://my.telegram.org/apps and log in with your Telegram account.
2. Fill out the form with your details and register a new Telegram application.
3. Done. The API key consists of two parts: api_id and api_hash. Keep it secret.

## Install requirements
The Bot was developed and tested with Python 3.10 on Debian based distro.

### Clone this repository
1. `git clone https://github.com/ChuckNorrison/memecontestbot`
2. `cd memecontestbot`
3. Edit the file memecontestbot.py and insert your desired telegram chat id or public channel name as `CHAT_ID`

### Install Python 3.x
1. `sudo apt install python3 python3-pip`
2. `pip3 install -r requirements.txt`

If you already run some python projects, keep in mind to use a [venv](https://docs.python.org/3/library/venv.html) or alternative ways to install python (check deadsnakes ppa).

## Usage
Start the bot with `python3 memecontestbot.py`. 

On first start it will ask for your api_id and api_hash and your corresponding phone number to act as userbot. The bot will use your telegram account and so it will be visible with your telegram user. Delete the file `my_account.session`, to reenter api_id and api_hash.

Channels should be configured to only accept a single reaction emoji (multiple reaction emojis are not supported yet).

Call the bot with argument `-c` or `--config` and a path to desired configfile to override default `config.py`.

More detailed infos can be found in the [pyrogram docs](https://docs.pyrogram.org/start/setup)
