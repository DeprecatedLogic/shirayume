# Shirayume.exe
Your Discord’s secret sauce of economy chaos, mod magic, mini-game madness, and utility wizardry, all wrapped in a bot that actually gets you.

## Features
- **Moderation**: Kick, ban, timeout, and log actions with a sleek MariaDB database to keep your server in check.
- **Economy**: Currency system for users to earn, spend, and flex their virtual wealth.
- **Utility**: Polls, quotes, and other handy commands to spice up your server.
- **Minigames**: Minigames to play with users in your server or against other servers!
- **Leveling System**: Ranks, XP, and leaderboards.
- **Web Scraping**: Fetch and process web data for dynamic commands.
- *More to come as our caffeine effects kick in!*

## Getting Started

### Prerequisites
- Make sure `Python 3.13` or newer is installed.
- MariaDB server (for persistent storage)
- A Discord bot token (get one from the [Discord Developer Portal](https://discord.com/developers/applications))

### How to run
1. Clone this repository & navigate to the directory
```
git clone https://github.com/DeprecatedLogic/Shirayume.exe.git
cd Shirayume.exe
```
2. Create and configure a virtual environment for Python
```
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install --upgrade pip
```
3. Install dependencies
```
pip install -r requirements.txt
```
4. Configure environment variables in `.env`
```
DISCORD_TOKEN=your_discord_bot_token
DB_HOST=your_mariadb_host
DB_USER=your_mariadb_user
DB_PASSWORD=your_mariadb_password
DATABASE=your_database_name
```
5. Set up the MariaDB database using `database/schema.sql`.
6. Launch the Discord bot
```
python launch.py
```

## Project structure
Shirayume.exe is organized for clarity and modularity: 
* **`cogs/`**: Modular Discord.py cogs for commands and events (e.g., moderation, economy, minigames).
* **`database/`**: MariaDB integration with in-memory caching, models, and schema for persistent storage.
* **`services/`**: Logic for currency, XP, and other calculations, keeping cogs clean.
* **`utils/`**: Helper functions, error handling, and other utilities.
* **Root Files**:
  * `launch.py`: Entry point to start the bot.
  * `config.json`: Bot configuration (prefix, enabled features, etc.)
  * `.env`: Secure storage for secrets (ignored by `.gitignore`).
  * `requirements.txt`: Python dependencies.
  * `LICENSE.md`: Custom MIT license (non-commercial use).
The bot ties together via `launch.py`, which loads cogs, connects to Discord, and uses services and the database for seamless operation.

## Author Notes
Fueled by late-night catpuccino. - [DeprecatedLogic](https://github.com/DeprecatedLogic)

## License
Licensed under a custom MIT license for personal and educational use only. No commercial shenanigans allowed, keep it chill and code for fun!