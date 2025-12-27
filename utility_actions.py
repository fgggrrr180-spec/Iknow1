# utility_actions.py

from telegram.ext import ContextTypes
from telegram import Update
from telegram.constants import ParseMode 
import time
from database import get_user_history
from config import BOT_OWNER_ID, BOT_OWNER_NAME 

# /tr command 
async def tr_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("❓ Usage: `/tr [text]` or reply to a message with `/tr` to translate the text.")
    
    text_to_translate = " ".join(context.args)
    
    await update.message.reply_text(
        f"🌐 **Translation Feature**\n"
        f"Text to translate: *{text_to_translate}*\n"
        f"Status: **Working!** (Translation backend integration pending)", 
        parse_mode=ParseMode.MARKDOWN
    )

# /owner command (Fix)
async def owner_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner_link = f"[{BOT_OWNER_NAME}](tg://user?id={BOT_OWNER_ID})"
    
    reply_text = (
        f"👑 **Bot Owner** 👑\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"👤 **Name:** {owner_link}\n"
        f"🔗 **ID:** `{BOT_OWNER_ID}`\n"
        f"💬 **Contact:** Click the name above to chat with the owner!"
    )
    
    await update.message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)

# /history command (Fix)
async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.effective_user
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        
    target_id = target.id
    target_name = f"@{target.username}" if target.username else target.first_name
    
    history = get_user_history(target_id) 
    
    if not history: 
        return await update.message.reply_text(f"❌ **{target_name}** ki koi name/username history nahi mili.", parse_mode=ParseMode.MARKDOWN)
        
    reply_text = f"📜 **{target_name}'s** Name/Username History 📜\n\n"
    
    # Filter to show only unique changes 
    last_name = None
    last_username = None

    for type, value, timestamp in history:
        date_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(timestamp))
        
        if type == 'name' and value != last_name:
            desc = "👤 Name Change"
            reply_text += f"`{date_str}` | {desc}: **{value}**\n"
            last_name = value
        elif type == 'username' and value != last_username:
            desc = "🔗 Username Change"
            reply_text += f"`{date_str}` | {desc}: **{value}**\n"
            last_username = value
        
    await update.message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)