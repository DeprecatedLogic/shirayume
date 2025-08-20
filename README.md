# Shirayume.exe
Your Discord’s secret sauce of economy chaos, mod magic, mini-game madness, and utility wizardry, all wrapped in a bot that actually gets you.

## Features
- Moderation
- Economy
- Utility (polls & other similar stuff)
- Minigames
- Game-like system (Ranks, levels, leaderboard, etc.)
- ...

## Getting Started

### Prerequisites
Make sure `Python 3.11` or newer is installed.

### How to run
1. Clone this repository & cd
```
git clone https://github.com/ItzKarizma/Shirayume.exe.git
cd Shirayume.exe
```
2. Create and configure a virtual environment for Python
```
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
```
3. Install required packages
```
pip install -r requirements.txt
```
4. Launch the Discord bot
```
python launch.py
```

## Project structure

### **1. `cogs/`**

This folder holds the **modular command/event scripts** of the Discord bot. Discord.py uses “cogs” to organize commands, listeners, and features into logical units.

* **`minigames/`**
  * Contains scripts for small games the bot can run.
  * `basic.py`: Implementation of basic mini-games (like dice, coinflip, etc.)
  * `__init__.py`: Allows Python to treat `minigames` as a package and usually loads the cogs.

* **`__init__.py` in `cogs/`**
  * Makes `cogs` a Python package.
  * Often contains code that registers all cogs in this folder when the bot launches.

* Other `.py` files:
  * **`economy.py`** → Handles currency commands and interactions.
  * **`moderation.py`** → Auto-moderation, banning/kicking, anti-spam, welcome messages.
  * **`polls.py`** → Commands for creating and managing polls.
  * **`ranks.py`** → Leveling, achievements, titles.
  * **`utilities_commands.py`** → Misc commands like `/dice`, `/quote`.
  * **`web_scraping_commands.py`** → Commands that fetch and process data from the web.

> **Link to rest of project:** Each cog interacts with `database` for persistent storage, `services` for calculations/logic, and `utils` for helper functions.

### **2. `database/`**

Handles **data storage and management**.

* **`database_manager.py`** → Main database interface: connects to MariaDB, runs queries, and manages sessions.
* **`models.py`** → Definitions of Python classes that represent database tables (like users, economy, ranks, messages).
* **`diagram.drawio`** → Visual ERD of the database schema (for planning or documentation).
* **`schema.sql`** → SQL code to create the database tables.
* **`dump.sql`** → Backup/export of the database content.

> **Link to rest of project:** The cogs use `database_manager.py` and models to persist and fetch data.

### **3. `services/`**

Contains **logic and computations** separate from commands. Keeps your cogs clean.

* **`currency_service.py`** → Handles currency logic: adding/removing coins, checking balances.
* **`xp_service.py`** → Handles leveling, XP gain, and rank calculations.

> **Link:** Cogs call `services` functions to apply logic, while `services` may query `database` for persistent data.

### **4. `utils/`**

Helper functions and shared utilities.

* **`errors.py`** → Custom exception classes and error handling.
* **`helpers.py`** → General helper functions used across cogs and services.
* **`web_scraper.py`** → Functions to fetch and parse websites for cogs that require scraping.

> **Link:** Both `cogs` and `services` import `utils` for reusable functions.

### **5. Root files**

* **`venv/`** → Python virtual environment with installed dependencies.
* **`.env`** → Secret keys: Discord token, DB credentials.
* **`.gitignore`** → Ignore files like `venv/`, `.env`, etc.
* **`config.json`** → Bot configuration:
  * Prefix, official guild, features enabled, creators’ roles, etc.
* **`launch.py`** → Main bot entry point. Loads cogs, connects to Discord, and starts the bot.
* **`LICENSE.md`** → Project license.
* **`README.md`** → Documentation for the project.
* **`requirements.txt`** → Python dependencies needed for the bot.

### **6. How everything ties together**

1. **`launch.py`** reads `config.json` and `.env`.
2. Loads **cogs**, which define commands and events.
3. Cogs call **services** for logic like XP or currency.
4. Services interact with **database** to read/write persistent data.
5. **Utils** provide helpers and error handling for all layers.
6. Bot responds to Discord messages, executes commands, and stores results in the database.

## Author Notes

## License
This project is licensed under the terms of a custom MIT license.
The difference between the original license and the modified one is that you cannot use this project for commercial purposes.

To make it simple, it's for personal and educational use only.
