import math

# --- BOT CONFIGURATION ---
BOT_TOKEN = "8582091221:AAHct6LVG16Dt_TMgFfm54nZksNTyJLLa2g"  # Apna bot token yahan daalein
BOT_OWNER_ID = 8377619196         # Apni Telegram User ID yahan daalein (Zaroori hai for notifications)
BOT_OWNER_NAME = "@iknow_077"    # Apne bot owner ka naam

# --- DATABASE CONFIGURATION ---
DB_NAME = "mahiru_bot.db"

# --- ECONOMY SETTINGS ---
DAILY_REWARD = 10000
TAX_RATE = 0.10  # 10% tax for /give command
MIN_KILL_REWARD = 1000
MAX_KILL_REWARD = 2000
GROUP_CLAIM_REWARD = 50000 # Group claim karne par milne wala one-time reward

# RPG Durations (in seconds)
DEATH_DURATION_SECONDS = 60 * 60 * 6  # 6 hours
PROTECT_DURATION_SECONDS = 60 * 60 * 24 # 24 hours

# RPG Costs
PROTECT_COST = 200
REVIVE_COST = 250
ROB_PENALTY_COST = 300

# RPG Limits
REVIVE_LIMIT_DAILY = 3