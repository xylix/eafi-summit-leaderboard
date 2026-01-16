#!/usr/bin/env python3
"""
EA Summit Helsinki Invite Leaderboard Bot

A Telegram bot that tracks invite counts and automatically publishes
to GitHub Pages.
"""

import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
DATA_FILE = Path('leaderboard_data.json')
HTML_FILE = Path('index.html')
REPO_PATH = Path('/home/user/eafi-summit-leaderboard')


class LeaderboardManager:
    """Manages leaderboard data storage and retrieval."""

    def __init__(self, data_file: Path):
        self.data_file = data_file
        self.data = self._load_data()

    def _load_data(self) -> dict:
        """Load leaderboard data from JSON file."""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Error reading {self.data_file}, creating new data")
                return {'entries': []}
        return {'entries': []}

    def _save_data(self):
        """Save leaderboard data to JSON file with pretty printing."""
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2, sort_keys=True)
            f.write('\n')  # Add trailing newline for clean diffs

    def submit_invites(self, user_id: int, username: str, invites: int) -> tuple[bool, int]:
        """
        Submit or update invite count for a user.

        Returns:
            tuple: (is_new_entry, previous_count)
        """
        entries = self.data.get('entries', [])

        # Find existing entry
        for entry in entries:
            if entry['user_id'] == user_id:
                previous_count = entry['invites']
                entry['invites'] = invites
                entry['username'] = username  # Update username in case it changed
                entry['updated_at'] = datetime.now().isoformat()
                self._save_data()
                return False, previous_count

        # Create new entry
        entries.append({
            'user_id': user_id,
            'username': username,
            'invites': invites,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        })
        self.data['entries'] = entries
        self._save_data()
        return True, 0

    def get_leaderboard(self) -> list[dict]:
        """Get sorted leaderboard entries."""
        entries = self.data.get('entries', [])
        return sorted(entries, key=lambda x: x['invites'], reverse=True)

    def get_user_stats(self, user_id: int) -> Optional[dict]:
        """Get stats for a specific user."""
        for entry in self.data.get('entries', []):
            if entry['user_id'] == user_id:
                return entry
        return None

    def get_total_stats(self) -> dict:
        """Get total statistics."""
        entries = self.data.get('entries', [])
        return {
            'total_participants': len(entries),
            'total_invites': sum(e['invites'] for e in entries)
        }


class GitHubPublisher:
    """Handles publishing leaderboard to GitHub Pages."""

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path

    def _run_git_command(self, command: list[str]) -> tuple[bool, str]:
        """Run a git command and return success status and output."""
        try:
            result = subprocess.run(
                command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)

    def update_html(self, leaderboard_data: list[dict], stats: dict):
        """Update the HTML file with current leaderboard data."""
        html_content = self._generate_html(leaderboard_data, stats)
        with open(self.repo_path / HTML_FILE, 'w') as f:
            f.write(html_content)

    def _generate_html(self, leaderboard_data: list[dict], stats: dict) -> str:
        """Generate HTML content with leaderboard data."""
        # Generate leaderboard items HTML
        if not leaderboard_data:
            items_html = '<li class="empty-state">No entries yet. Be the first to submit!</li>'
        else:
            medals = ['🥇', '🥈', '🥉']
            items = []
            for index, entry in enumerate(leaderboard_data):
                rank = index + 1
                rank_class = f'rank-{rank}' if rank <= 3 else ''
                medal = f'<span class="medal">{medals[index]}</span>' if rank <= 3 else ''
                username = self._escape_html(entry['username'])
                invites = entry['invites']

                items.append(f'''
                        <li class="leaderboard-item {rank_class}">
                            <div class="rank">
                                {medal}
                                <span>#{rank}</span>
                            </div>
                            <div class="player-info">
                                <div class="player-name">@{username}</div>
                            </div>
                            <div class="invite-count">
                                {invites} <span class="label">invites</span>
                            </div>
                        </li>''')
            items_html = '\n'.join(items)

        # Read the template and replace the dynamic parts
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EA Summit Helsinki - Invite Leaderboard 🏆</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }}

        .container {{
            max-width: 800px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            color: white;
            margin-bottom: 30px;
            animation: fadeInDown 0.6s ease-out;
        }}

        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}

        .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}

        .bot-info {{
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            margin-bottom: 30px;
            animation: fadeInUp 0.6s ease-out;
            text-align: center;
        }}

        .bot-info h2 {{
            color: #667eea;
            margin-bottom: 15px;
        }}

        .bot-info p {{
            margin: 10px 0;
            font-size: 1.1em;
        }}

        .bot-info code {{
            background: #f5f5f5;
            padding: 3px 8px;
            border-radius: 4px;
            font-family: monospace;
            color: #667eea;
        }}

        .leaderboard {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            animation: fadeInUp 0.6s ease-out 0.2s backwards;
        }}

        .leaderboard-title {{
            text-align: center;
            color: #667eea;
            margin-bottom: 25px;
            font-size: 2em;
        }}

        .leaderboard-list {{
            list-style: none;
        }}

        .leaderboard-item {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 10px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            transition: transform 0.2s, box-shadow 0.2s;
            animation: slideIn 0.4s ease-out;
        }}

        .leaderboard-item:hover {{
            transform: translateX(5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}

        .leaderboard-item.rank-1 {{
            background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
            font-size: 1.1em;
            font-weight: 600;
        }}

        .leaderboard-item.rank-2 {{
            background: linear-gradient(135deg, #e0e0e0 0%, #c9d6df 100%);
            font-weight: 600;
        }}

        .leaderboard-item.rank-3 {{
            background: linear-gradient(135deg, #f4a582 0%, #e8b59a 100%);
            font-weight: 600;
        }}

        .rank {{
            font-size: 1.5em;
            font-weight: bold;
            min-width: 60px;
            display: flex;
            align-items: center;
        }}

        .medal {{
            font-size: 1.8em;
            margin-right: 10px;
        }}

        .player-info {{
            flex: 1;
            padding: 0 20px;
        }}

        .player-name {{
            font-weight: 600;
            font-size: 1.1em;
        }}

        .invite-count {{
            font-size: 1.3em;
            font-weight: bold;
            color: #667eea;
            min-width: 80px;
            text-align: right;
        }}

        .invite-count .label {{
            font-size: 0.7em;
            color: #666;
            font-weight: normal;
        }}

        .empty-state {{
            text-align: center;
            padding: 40px;
            color: #999;
            font-size: 1.2em;
        }}

        .stats {{
            display: flex;
            justify-content: space-around;
            margin-top: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            border-radius: 10px;
        }}

        .stat {{
            text-align: center;
        }}

        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}

        .stat-label {{
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }}

        .last-updated {{
            text-align: center;
            margin-top: 20px;
            color: #666;
            font-size: 0.9em;
        }}

        @keyframes fadeInDown {{
            from {{
                opacity: 0;
                transform: translateY(-20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        @keyframes slideIn {{
            from {{
                opacity: 0;
                transform: translateX(-20px);
            }}
            to {{
                opacity: 1;
                transform: translateX(0);
            }}
        }}

        @media (max-width: 600px) {{
            h1 {{
                font-size: 2em;
            }}

            .leaderboard-item {{
                flex-direction: column;
                text-align: center;
            }}

            .player-info {{
                padding: 10px 0;
            }}

            .invite-count {{
                text-align: center;
            }}

            .stats {{
                flex-direction: column;
                gap: 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎉 EA Summit Helsinki 🎉</h1>
            <p class="subtitle">Invite Leaderboard Challenge</p>
        </header>

        <div class="bot-info">
            <h2>📱 Submit via Telegram Bot</h2>
            <p>To submit your invites, message the bot with:</p>
            <p><code>/submit &lt;number&gt;</code> - Submit your invite count</p>
            <p><code>/leaderboard</code> - View current standings</p>
            <p><code>/mystats</code> - Check your stats</p>
        </div>

        <div class="leaderboard">
            <h2 class="leaderboard-title">🏆 Leaderboard 🏆</h2>
            <ul id="leaderboardList" class="leaderboard-list">
{items_html}
            </ul>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">{stats['total_participants']}</div>
                    <div class="stat-label">Participants</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{stats['total_invites']}</div>
                    <div class="stat-label">Total Invites</div>
                </div>
            </div>
            <div class="last-updated">
                Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
            </div>
        </div>
    </div>
</body>
</html>'''

    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))

    def publish(self, commit_message: str = "Update leaderboard") -> tuple[bool, str]:
        """Commit and push changes to GitHub."""
        # Add files
        success, output = self._run_git_command(['git', 'add', str(DATA_FILE), str(HTML_FILE)])
        if not success:
            return False, f"Failed to add files: {output}"

        # Check if there are changes to commit
        success, output = self._run_git_command(['git', 'diff', '--cached', '--quiet'])
        if success:  # No changes
            return True, "No changes to publish"

        # Commit
        success, output = self._run_git_command(['git', 'commit', '-m', commit_message])
        if not success:
            return False, f"Failed to commit: {output}"

        # Push with retry logic
        for attempt in range(4):
            success, output = self._run_git_command([
                'git', 'push', '-u', 'origin', 'claude/invite-leaderboard-app-RW0q2'
            ])
            if success:
                return True, "Published successfully!"

            if attempt < 3:  # Don't sleep on last attempt
                import time
                wait_time = 2 ** (attempt + 1)  # 2s, 4s, 8s
                logger.warning(f"Push failed, retrying in {wait_time}s...")
                time.sleep(wait_time)

        return False, f"Failed to push after retries: {output}"


# Initialize managers
leaderboard = LeaderboardManager(DATA_FILE)
publisher = GitHubPublisher(REPO_PATH)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when /start is issued."""
    welcome_message = """
🎉 *Welcome to EA Summit Helsinki Invite Leaderboard!* 🎉

Track your invites and compete with other organizers!

*Commands:*
/submit <number> - Submit your invite count
/leaderboard - View current standings
/mystats - Check your personal stats

Example: `/submit 10`

Let's make this summit amazing! 🚀
"""
    await update.message.reply_text(welcome_message, parse_mode='Markdown')


async def submit_invites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle invite submission."""
    user = update.effective_user
    username = user.username or f"user{user.id}"

    # Parse invite count from command
    if not context.args or len(context.args) != 1:
        await update.message.reply_text(
            "Please provide the number of invites.\n"
            "Example: `/submit 10`",
            parse_mode='Markdown'
        )
        return

    try:
        invites = int(context.args[0])
        if invites < 0:
            await update.message.reply_text("Invite count must be a positive number!")
            return
    except ValueError:
        await update.message.reply_text("Please provide a valid number!")
        return

    # Submit to leaderboard
    is_new, previous = leaderboard.submit_invites(user.id, username, invites)

    if is_new:
        message = f"🎉 Great! Added you to the leaderboard with *{invites}* invites!"
    else:
        message = f"✅ Updated your invites from *{previous}* to *{invites}*!"

    await update.message.reply_text(message, parse_mode='Markdown')

    # Auto-publish to GitHub
    logger.info(f"Auto-publishing after submission by @{username}")
    leaderboard_data = leaderboard.get_leaderboard()
    stats = leaderboard.get_total_stats()
    publisher.update_html(leaderboard_data, stats)

    success, pub_message = publisher.publish(
        f"Update leaderboard: @{username} submitted {invites} invites"
    )
    if success:
        logger.info(f"Published to GitHub: {pub_message}")
    else:
        logger.error(f"Failed to publish: {pub_message}")
        await update.message.reply_text(
            "⚠️ Submission saved but failed to publish to website. Check logs."
        )


async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the current leaderboard."""
    entries = leaderboard.get_leaderboard()
    stats = leaderboard.get_total_stats()

    if not entries:
        await update.message.reply_text(
            "📊 The leaderboard is empty!\n"
            "Be the first to submit with `/submit <number>`",
            parse_mode='Markdown'
        )
        return

    # Build leaderboard message
    medals = ['🥇', '🥈', '🥉']
    lines = ["*🏆 EA Summit Helsinki Leaderboard 🏆*\n"]

    for index, entry in enumerate(entries):
        rank = index + 1
        medal = medals[index] if rank <= 3 else f"{rank}."
        username = entry['username']
        invites = entry['invites']
        lines.append(f"{medal} @{username}: *{invites}* invites")

    lines.append(f"\n📊 *Stats:*")
    lines.append(f"👥 Total participants: {stats['total_participants']}")
    lines.append(f"✉️ Total invites: {stats['total_invites']}")

    await update.message.reply_text('\n'.join(lines), parse_mode='Markdown')


async def show_mystats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show personal stats for the user."""
    user = update.effective_user
    stats = leaderboard.get_user_stats(user.id)

    if not stats:
        await update.message.reply_text(
            "You haven't submitted any invites yet!\n"
            "Use `/submit <number>` to get started.",
            parse_mode='Markdown'
        )
        return

    # Find rank
    entries = leaderboard.get_leaderboard()
    rank = next(i + 1 for i, e in enumerate(entries) if e['user_id'] == user.id)

    medals = {1: '🥇', 2: '🥈', 3: '🥉'}
    rank_display = medals.get(rank, f"#{rank}")

    message = f"""
*Your Stats* 📊

Rank: {rank_display}
Invites: *{stats['invites']}*
Last updated: {stats['updated_at'][:10]}

Keep up the great work! 🚀
"""
    await update.message.reply_text(message, parse_mode='Markdown')


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error {context.error}")


def main():
    """Start the bot."""
    # Get token from environment variable
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN environment variable not set!\n"
            "Get a token from @BotFather on Telegram and set it with:\n"
            "export TELEGRAM_BOT_TOKEN='your-token-here'"
        )

    # Create application
    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("submit", submit_invites))
    application.add_handler(CommandHandler("invites", submit_invites))  # Alias
    application.add_handler(CommandHandler("leaderboard", show_leaderboard))
    application.add_handler(CommandHandler("mystats", show_mystats))

    # Add error handler
    application.add_error_handler(error_handler)

    # Start the bot
    logger.info("Starting EA Summit Helsinki Leaderboard Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
