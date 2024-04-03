# memecontestbot
[![Pylint](https://github.com/ChuckNorrison/memecontestbot/actions/workflows/pylint.yml/badge.svg)](https://github.com/ChuckNorrison/memecontestbot/actions/workflows/pylint.yml)

A telegram userbot for channels or groups, to create a ranking from photo reactions like a meme contest.

The Bot can be set as cron to post a ranking automatically. 
Daily, weekly or monthly ranking messages and polls.

## Features
- Walk through telegram chat or CSV data and count
media reactions or views and create a ranking message.
- Configs for daily, weekly and monthly rankings
or polls to vote from.
- Collect and repost media in another chat.
- Update a highscore message with winner medals.

## Setup Telegram App
The first step requires you to obtain a valid Telegram API key (api_id and api_hash pair):

- Visit https://my.telegram.org/apps and log in with your Telegram account.
- Fill out the form with your details and register a new Telegram application.
- Done. The API key consists of two parts: api_id and api_hash. Keep it secret.

## Setup Telegram Bot
The Bot was developed and tested with Python 3.8+ on debian based distro.

### Clone this repository
- `git clone https://github.com/ChuckNorrison/memecontestbot`
- `cd memecontestbot`
- Edit the file `config.py` and insert your desired telegram chat id or public channel name in `CHAT_ID`)
- Edit the file `config_api.py` and insert your API ID and API HASH

### Install Python 3.x and module dependencies
- `sudo apt install python3 python3-pip`
- `pip3 install -r requirements.txt`

### Switch to maintained pyrogram fork
Better performance and error handling in this fork. This was tested and reviewed.
- `pip install -U https://github.com/KurimuzonAkuma/pyrogram/archive/refs/tags/v2.1.16.zip`

If you already run some python projects, keep in mind to use a [venv](https://docs.python.org/3/library/venv.html) or alternative ways to install python (i.e. check deadsnakes ppa to install specific python versions).

## Usage
Start the bot with `python3 memecontestbot.py`. 

On first start it will ask for your corresponding phone number to act as userbot. The bot will use your telegram account and so it will be visible with your telegram user. Delete the file `my_account.session`, to reset authentication.

Chats should be configured to only accept a single reaction emoji (multiple reaction emojis are not supported yet).

Call the bot with argument `-c` or `--config` and a path to desired configfile to override default `config.py`.

More detailed infos for Telegram API can be found in the [pyrogram docs](https://docs.pyrogram.org/start/setup)
