# EA Summit Helsinki Invite Leaderboard

A Telegram bot that tracks invite counts for the EA Summit Helsinki and automatically publishes to a GitHub Pages leaderboard.

## Features

- **Telegram Bot Interface**: Submit and track invites via Telegram commands
- **Auto-Publishing**: Automatically updates GitHub Pages on every submission
- **Real-time Leaderboard**: View rankings with medals for top 3
- **Personal Stats**: Check your own invite count and ranking
- **JSON Storage**: Clean, multiline JSON for readable git diffs
- **No Authentication Required**: Simple and open for all participants

## Quick Start

### 1. Create a Telegram Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow the instructions
3. Choose a name (e.g., "EA Summit Helsinki Leaderboard")
4. Choose a username (e.g., "ea_summit_helsinki_bot")
5. Copy the API token you receive

### 2. Set Up the Bot

```bash
# Clone the repository
git clone https://github.com/xylix/eafi-summit-leaderboard.git
cd eafi-summit-leaderboard

# Install dependencies
pip install -r requirements.txt

# Set your bot token
export TELEGRAM_BOT_TOKEN='your-token-here'

# Run the bot
python3 bot.py
```

### 3. Set Up GitHub Pages

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Pages**
3. Under **Source**, select your branch (e.g., `claude/invite-leaderboard-app-RW0q2`)
4. Click **Save**
5. Your leaderboard will be live at: `https://xylix.github.io/eafi-summit-leaderboard/`

## Bot Commands

- `/start` - Get welcome message and instructions
- `/submit <number>` - Submit your invite count (e.g., `/submit 10`)
- `/invites <number>` - Alias for `/submit`
- `/leaderboard` - View current standings
- `/mystats` - Check your personal stats

## How It Works

1. **User submits invites** via Telegram command
2. **Bot saves to JSON** file with pretty-printing
3. **Bot updates HTML** with latest leaderboard
4. **Bot commits and pushes** to GitHub automatically
5. **GitHub Pages** serves the updated leaderboard

## Data Storage

The bot uses a JSON file (`leaderboard_data.json`) with this structure:

```json
{
  "entries": [
    {
      "created_at": "2026-01-16T10:30:00.000000",
      "invites": 15,
      "updated_at": "2026-01-16T12:45:00.000000",
      "user_id": 123456789,
      "username": "alice"
    }
  ]
}
```

The multiline format ensures clean git diffs when data changes.

## Running in Production

For 24/7 operation, run the bot on a server:

### Using systemd (Linux)

Create `/etc/systemd/system/ea-summit-bot.service`:

```ini
[Unit]
Description=EA Summit Helsinki Leaderboard Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/eafi-summit-leaderboard
Environment="TELEGRAM_BOT_TOKEN=your-token-here"
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ea-summit-bot
sudo systemctl start ea-summit-bot
sudo systemctl status ea-summit-bot
```

### Using screen/tmux

```bash
screen -S ea-summit-bot
export TELEGRAM_BOT_TOKEN='your-token-here'
python3 bot.py
# Press Ctrl+A, then D to detach
```

### Using Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python3", "bot.py"]
```

```bash
docker build -t ea-summit-bot .
docker run -d --name ea-summit-bot \
  -e TELEGRAM_BOT_TOKEN='your-token-here' \
  -v $(pwd):/app \
  ea-summit-bot
```

## Development

The bot auto-commits to the branch `claude/invite-leaderboard-app-RW0q2`. To change the target branch, edit the `publish()` method in `bot.py`.

## Troubleshooting

**Bot doesn't respond:**
- Check that `TELEGRAM_BOT_TOKEN` is set correctly
- Verify the bot is running (`ps aux | grep bot.py`)
- Check logs for errors

**GitHub push fails:**
- Ensure git is configured with credentials
- Check the branch name matches in `bot.py`
- Verify write permissions to the repository

**Leaderboard not updating:**
- Check GitHub Pages is enabled and pointing to the correct branch
- Wait a few minutes for GitHub Pages to rebuild
- Check the commit history to verify updates are being pushed

## License

Open source - feel free to use and modify for your events!