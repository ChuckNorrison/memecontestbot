# memecontestbot
A telegram bot for a telegram channel ranking based on reactions. 

The Bot can be set as cron to post a ranking automatically.

## Features
- On execute, it retrieves message posts of a given telegram chat (`chat_id`) and period (`contest_days`) and analyze reactions to create a ranking.
- Decide whether to post the final ranking message in a given chat or not (config: `send_final_message`)
- Configure how much winners will get into the ranking (config: `contest_max_ranks`)
- Exclude message posts from analyzing (config: `exclude_pattern`)
- Enable CSV file creation, to log all message posts found with amount of reactions and views count (`create_csv`)

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
3. Edit the file memecontestbot.py and insert your desired telegram chat id or public channel name as `chat_id`

### Install Python 3.x
1. `sudo apt install python3 python3-pip`
2. `pip3 install -r requirements.txt`

If you already run some python projects, keep in mind to use a [venv](https://docs.python.org/3/library/venv.html) or alternative ways to install python (check deadsnakes ppa).

## Usage
Start the bot with `python3 memecontestbot.py`. On first start it will ask for your api_id and api_hash and your corresponding phone number to act as userbot. The bot will use your telegram account and so it will be visible with your telegram user.

Channels should be configured to only accept a single reaction emoji (multiple reaction emojis are not supported yet). Edit channel and enable "Sign messages" to display author signatures in channel posts to create a ranking.

More detailed infos can be found in the [pyrogram docs](https://docs.pyrogram.org/start/setup)
