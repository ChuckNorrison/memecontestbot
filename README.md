# memecontestbot
A telegram bot for a telegram channel ranking based on reactions. 

The bot will retrieve the Top 10 channel posts with the most given reactions.

A message will be build and send to the chat.

The Bot can be set as cron to post a ranking automatically.

## Setup Telegram App
The first step requires you to obtain a valid Telegram API key (api_id and api_hash pair):

1. Visit https://my.telegram.org/apps and log in with your Telegram account.
2. Fill out the form with your details and register a new Telegram application.
3. Done. The API key consists of two parts: api_id and api_hash. Keep it secret.

## Setup python and pyrogram
1. `git clone https://github.com/ChuckNorrison/memecontestbot`
2. `pip3 install -U pyrogram`
3. Edit the file memecontestbot.py and insert your desired telegram chat id or public channel name as `chat_id`

## Usage
Start the bot with `python3 memecontestbot.py`. On first start it will ask for your api_id and api_hash and your corresponding phone number to act as userbot. The bot will use your telegram account and so it will be visible with your telegram user.

Channels should be configured to only accept a single reaction emoji (multiple reaction emojis are not supported yet). Edit channel and enable "Sign messages" to display author signatures in channel posts to create a ranking.

More detailed infos can be found in the [pyrogram docs](https://docs.pyrogram.org/start/setup)
