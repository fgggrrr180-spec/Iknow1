# fun_actions.py

from telegram.ext import ContextTypes
from telegram import Update
from telegram.constants import ParseMode 
import random
import time

# --- DARE LIST ---
DARE_LIST = [
    "Send a voice note singing the national anthem.",
    "Post an embarrassing baby picture of yourself.",
    "Send the most recent photo in your gallery.",
    "Change your username to 'Bot Lover' for 1 hour.",
    "Confess one crush you've had in the past 5 years.",
    "Do 10 push-ups and send a video proof.",
    "Write a 4-line poem about the person above you in the chat list.",
    "Call a random person in your contacts and sing 'Happy Birthday'.",
    "Let someone else write your next status message for the next 30 minutes.",
    "Explain what you think the person who dared you dreams about.",
]
# --- TRUTH LIST ---
TRUTH_LIST = [
    "What is the most embarrassing thing you've ever worn?",
    "What's the biggest lie you've told recently?",
    "What is one thing you regret doing online?",
    "What's your biggest fear?",
    "What's one thing you hate about yourself?",
]

# --- PLACEHOLDER FUN COMMANDS (To match main.py imports) ---
async def slap_command(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("🖐️ Slap action placeholder.")
async def punch_command(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("👊 Punch action placeholder.")
async def kiss_command(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("😘 Kiss action placeholder.")
async def hug_command(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("🤗 Hug action placeholder.")
async def bite_command(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("🦷 Bite action placeholder.")
async def crush_command(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("❤️ Crush action placeholder.")
async def love_command(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("💞 Love action placeholder.")
async def look_command(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("👀 Look action placeholder.")
async def brain_command(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("🧠 Brain action placeholder.")
async def stupid_meter_command(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("🤪 Stupid Meter placeholder.")

# Placeholder command for pending features (for /puzzle)
async def game_placeholder_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛠️ This game feature is under construction! Come back later.", parse_mode=ParseMode.MARKDOWN)

# /dare command (Fix)
async def dare_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.effective_user
    target_name = f"@{target.username}" if target.username else target.first_name
    
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        target_name = f"[{target.first_name}](tg://user?id={target.id})"
    
    random_dare = random.choice(DARE_LIST)
    
    reply_text = (
        f"🔥 **Dare Time!** 🔥\n"
        f"**Target:** {target_name}\n\n"
        f"😈 Your Dare is: **{random_dare}**\n\n"
        f"Do you accept the challenge?"
    )
    
    await update.message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)

# /truth command (New working function)
async def truth_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.effective_user
    target_name = f"@{target.username}" if target.username else target.first_name
    
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        target_name = f"[{target.first_name}](tg://user?id={target.id})"
    
    random_truth = random.choice(TRUTH_LIST)
    
    reply_text = (
        f"✨ **Truth Time!** ✨\n"
        f"**Target:** {target_name}\n\n"
        f"😇 Your Question is: **{random_truth}**\n\n"
        f"Answer truthfully!"
    )
    
    await update.message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)