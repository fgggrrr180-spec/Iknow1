# main.py

import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update, BotCommand, BotCommandScopeAllPrivateChats, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ChatMemberStatus, ParseMode 
import telegram
import time
from telegram.ext import ContextTypes 

from config import BOT_TOKEN, BOT_OWNER_ID, BOT_OWNER_NAME
from database import init_db, add_group_to_db, log_name_change, get_user_history

# --- NAYA IMPORT (24/7 Keep-Alive ke liye) ---
from keep_alive import keep_alive 

# 1. Economy Imports (balhistory removed, detail, claim, own added)
from economy import (
    bal_command, daily_command, give_command, protect_command, 
    rob_command, kill_command, revive_command, toprich_command, topkill_command,
    check_command, detail_command, claim_command, own_command 
)
# 2. Utility Imports (tr, owner, history added)
from utility_actions import (
    tr_command, owner_command, history_command 
)
# 3. Fun Actions Imports (dare, truth added)
from fun_actions import (
    slap_command, punch_command, kiss_command, hug_command, 
    bite_command, crush_command, love_command, look_command, brain_command, stupid_meter_command, 
    truth_command, dare_command, game_placeholder_command
)
from mod_actions import (
    ban_user_command, unban_user_command, mute_user_command, unmute_user_command, pin_message_command,
    promote_user_command, demote_user_command, warn_user_command
)

# --- CORE COMMANDS ---

# Placeholder command for unimplemented features
async def placeholder_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛠️ This feature is under construction! Come back later.", parse_mode=ParseMode.MARKDOWN)

# /id command (FIXED logic)
async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    reply_text = ""
    
    reply_text += f"👤 **Your User ID:** `{user.id}`\n"
    
    if update.message.reply_to_message:
        replied_user = update.message.reply_to_message.from_user
        reply_text += f"➡️ **Replied User ID:** `{replied_user.id}`\n"
        
    if update.effective_chat.type != 'private':
        reply_text += f"🏠 **Chat ID:** `{chat_id}`"

    await update.message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)

# /start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    
    if user:
        # Log name and username history
        log_name_change(user.id, 'name', user.first_name)
        if user.username:
            log_name_change(user.id, 'username', user.username)
            
    if chat.type == 'private':
        bot_info = await context.bot.get_me()
        bot_username = bot_info.username
        
        keyboard = [
            [
                InlineKeyboardButton("➕ Add Me To Your Group ➕", url=f"https://t.me/{bot_username}?startgroup=true")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"Hello **{user.first_name}**! I am Mahiru Shiina All-Rounder Bot. Use /help to see commands, or add me to your group to manage it!",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
    elif update.message.new_chat_members:
        new_members = ", ".join([m.first_name for m in update.message.new_chat_members])
        adder_id = update.effective_user.id
        add_group_to_db(chat.id, adder_id)
        await context.bot.send_message(
            chat_id=chat.id, 
            text=f"Welcome {new_members} to the group! Use /help to see what I can do."
        )

async def help_command(update: Update, context):
    help_text = (
        "🌸 **Mahiru Shiina All-Rounder Bot Commands** 🌸\n\n"
        "**💰 Economy & RPG Commands:**\n"
        "*/bal*, */daily*, */give* (Reply + amount), */protect*, */rob* (Reply + amount), */kill* (Reply), */revive* (Reply)\n"
        "*/toprich*, */topkill*, */check*, */detail*, */claim*, */own*, */history*\n"
        
        "\n**🛠️ Utility & Misc Commands:**\n"
        "*/id* (Reply to someone), */owner*, */tr*, */adminlist* (*Placeholder*), */broadcast* [msg] (Owner only)\n"
        
        "\n**🎉 Fun Actions (Reply to someone):**\n"
        "*/crush*, */love*, */look*, */brain*, */stupid_meter*, */slap*, */punch*, */bite*, */kiss*, */hug*\n"
        
        "\n**🎲 Games:**\n"
        "*/truth*, */dare*, */puzzle* (*Placeholder*)\n"
        "*/start*, */help* - Bot Info."
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def adminlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Admin list feature is pending.")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != BOT_OWNER_ID:
        return await update.message.reply_text("❌ You are not the bot owner.", parse_mode=ParseMode.MARKDOWN)
    await update.message.reply_text("Broadcast feature is pending.")

# --- COMMAND SETTER FOR MENU BUTTON ---
async def set_commands(application: Application):
    """Sets the Telegram bot commands/menu."""
    commands = [
        BotCommand("start", "Start the bot & get group invite link"),
        BotCommand("help", "Show all commands and features"),
        BotCommand("bal", "Check your or someone else's balance"),
        BotCommand("daily", "Claim your daily reward"),
        BotCommand("kill", "Kill a user (Reply)"),
        BotCommand("protect", "Buy protection for 24 hours"),
        BotCommand("pin", "Pin a message (Admin, Reply)"),
        BotCommand("ban", "Ban a user (Admin, Reply)"),
    ]
    await application.bot.set_my_commands(commands, scope=BotCommandScopeAllPrivateChats())
    print("Bot commands set successfully.")


# --- MAIN EXECUTION ---
def main():
    """Start the bot."""
    
    # 1. Initialize DB and Keep Alive
    init_db()
    
    # --- 24/7 KEEP-ALIVE START KAREIN (ZAROORI) ---
    print("Starting keep-alive webserver...")
    keep_alive()
    # -----------------------------------------------
    
    application = Application.builder().token(BOT_TOKEN).post_init(set_commands).build()
    
    # 1. Add Handlers (Core/Utility)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("id", id_command))
    application.add_handler(CommandHandler("owner", owner_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(CommandHandler("tr", tr_command))
    application.add_handler(CommandHandler("adminlist", adminlist_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    
    # 2. Add Handlers (Economy & RPG)
    application.add_handler(CommandHandler("bal", bal_command))
    application.add_handler(CommandHandler("daily", daily_command))
    application.add_handler(CommandHandler("give", give_command))
    application.add_handler(CommandHandler("protect", protect_command))
    application.add_handler(CommandHandler("rob", rob_command))
    application.add_handler(CommandHandler("kill", kill_command))
    application.add_handler(CommandHandler("revive", revive_command))
    application.add_handler(CommandHandler("toprich", toprich_command))
    application.add_handler(CommandHandler("topkill", topkill_command))
    application.add_handler(CommandHandler("check", check_command))
    application.add_handler(CommandHandler("claim", claim_command))
    application.add_handler(CommandHandler("own", own_command))
    application.add_handler(CommandHandler("detail", detail_command))
    
    # 3. Add Handlers (MODERATION FEATURES)
    application.add_handler(CommandHandler("ban", ban_user_command))
    application.add_handler(CommandHandler("unban", unban_user_command))
    application.add_handler(CommandHandler("mute", mute_user_command))
    application.add_handler(CommandHandler("unmute", unmute_user_command))
    application.add_handler(CommandHandler("pin", pin_message_command))
    application.add_handler(CommandHandler("promote", promote_user_command))
    application.add_handler(CommandHandler("demote", demote_user_command))
    application.add_handler(CommandHandler("warn", warn_user_command))

    # 4. Add Handlers (Fun Actions/Games)
    application.add_handler(CommandHandler("slap", slap_command))
    application.add_handler(CommandHandler("punch", punch_command))
    application.add_handler(CommandHandler("kiss", kiss_command))
    application.add_handler(CommandHandler("hug", hug_command))
    application.add_handler(CommandHandler("bite", bite_command))
    application.add_handler(CommandHandler("crush", crush_command))
    application.add_handler(CommandHandler("love", love_command))
    application.add_handler(CommandHandler("look", look_command))
    application.add_handler(CommandHandler("brain", brain_command))
    application.add_handler(CommandHandler("stupid_meter", stupid_meter_command))
    application.add_handler(CommandHandler("dare", dare_command))
    application.add_handler(CommandHandler("truth", truth_command))

    # 5. Placeholder Handlers (Only /puzzle remains)
    placeholder_commands_misc = ["puzzle"] 
    for cmd in placeholder_commands_misc:
        application.add_handler(CommandHandler(cmd, game_placeholder_command))
    
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, start_command))
    
    # Run the bot
    print("Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()