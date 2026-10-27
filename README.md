# SkillUp Academy Telegram Bot

A standard Telegram chat bot for educational lessons, quizzes, daily learning tips, and simple progress tracking. It uses Telegram's Bot API through the bot token and built-in lesson content. It is **not** a Mini App or Web App and does not use external content APIs.

## Features

- Inline-button menu inside Telegram chat
- Built-in lessons on digital skills, business basics, and productivity
- Multiple-choice knowledge quiz with immediate feedback
- Daily learning tips
- Basic progress tracking stored in a local JSON file
- `/start` and `/help` commands

## Requirements

- Python 3.10 or newer
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

## Run locally

1. Clone this repository.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set the bot token as an environment variable. Do not commit your token to GitHub.

   macOS/Linux:
   ```bash
   export BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
   python main.py
   ```

   Windows PowerShell:
   ```powershell
   $env:BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
   python main.py
   ```

4. Open your bot in Telegram and send `/start`.

## Deploy on Render

1. Create a **Background Worker** service connected to this GitHub repository.
2. Use `pip install -r requirements.txt` as the build command.
3. Use `python main.py` as the start command.
4. Add an environment variable named `BOT_TOKEN` with the token from @BotFather.
5. Deploy the service and check its logs.

### Progress storage note

By default, progress is saved in `progress.json` in the current working directory. On many hosted deployments, the local filesystem may be temporary, so progress can be lost when the service restarts or redeploys. For durable progress, attach persistent storage supported by your hosting plan and set `DATA_FILE` to a path on that storage. This does not require an external API.

## Security

- Never place your Telegram bot token in source code or commit it to GitHub.
- If a token is exposed, revoke it through @BotFather and create a new one.
- This bot does not collect additional profile details beyond the Telegram user ID needed to associate progress.

## Educational content

Lessons and quiz questions are bundled in `main.py`. Edit those built-in lists to add or update content.
