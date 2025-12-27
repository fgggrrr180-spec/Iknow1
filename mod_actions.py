# mod_actions.py

import telegram
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus, ParseMode 
import time

# --- Helper Functions ---

# Check if the user executing the command is an admin
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    if update.effective_chat.type == 'private':
        await update.message.reply_text("❌ This command must be used in a group.", parse_mode=ParseMode.MARKDOWN)
        return False
        
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
            return True
        else:
            await update.message.reply_text("❌ You must be an admin to use this command.")
            return False
    except Exception as e:
        print(f"Error checking admin status: {e}")
        return False

# Check if the bot has admin rights (for ban/mute)
async def bot_has_restrict_rights(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat_id = update.effective_chat.id
    bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
    if not bot_member.can_restrict_members:
        await update.message.reply_text("❌ I need **'Ban Users'** permission to perform this action.", parse_mode=ParseMode.MARKDOWN)
        return False
    return True

# --- Moderation Command Handlers ---

# /ban command
async def ban_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if not update.message.reply_to_message: return await update.message.reply_text("❓ Reply to the user you want to ban.")
    if not await bot_has_restrict_rights(update, context): return

    target = update.message.reply_to_message.from_user
    target_id = target.id
    target_name = target.first_name
    
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target_id)
        await update.message.reply_text(f"✅ User **{target_name}** has been banned.", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text(f"❌ Could not ban user. Error: {e}", parse_mode=ParseMode.MARKDOWN)

# /unban command
async def unban_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if not update.message.reply_to_message: return await update.message.reply_text("❓ Reply to the user you want to unban.")
    if not await bot_has_restrict_rights(update, context): return

    target = update.message.reply_to_message.from_user
    target_id = target.id
    target_name = target.first_name
    
    try:
        await context.bot.unban_chat_member(update.effective_chat.id, target_id)
        await update.message.reply_text(f"✅ User **{target_name}** has been unbanned.", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text(f"❌ Could not unban user. Error: {e}", parse_mode=ParseMode.MARKDOWN)

# /mute command
async def mute_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if not update.message.reply_to_message: return await update.message.reply_text("❓ Reply to the user you want to mute.")
    if not await bot_has_restrict_rights(update, context): return

    target = update.message.reply_to_message.from_user
    target_id = target.id
    target_name = target.first_name
    
    # Calculate mute duration (1 hour default if no argument)
    mute_duration_minutes = 60
    if context.args and context.args[0].isdigit():
        mute_duration_minutes = int(context.args[0])
    
    until_date = int(time.time() + mute_duration_minutes * 60)
    
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            target_id,
            permissions=telegram.ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        await update.message.reply_text(
            f"🤫 User **{target_name}** muted for **{mute_duration_minutes} minutes**.", 
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Could not mute user. Error: {e}", parse_mode=ParseMode.MARKDOWN)

# /unmute command
async def unmute_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if not update.message.reply_to_message: return await update.message.reply_text("❓ Reply to the user you want to unmute.")
    if not await bot_has_restrict_rights(update, context): return

    target = update.message.reply_to_message.from_user
    target_id = target.id
    target_name = target.first_name

    try:
        # Re-enabling all permissions (unmute)
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            target_id,
            permissions=telegram.ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_add_web_page_previews=True
            )
        )
        await update.message.reply_text(f"🗣️ User **{target_name}** has been unmuted.", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text(f"❌ Could not unmute user. Error: {e}", parse_mode=ParseMode.MARKDOWN)

# /pin command
async def pin_message_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if not update.message.reply_to_message: return await update.message.reply_text("❓ Reply to the message you want to pin.")

    bot_member = await context.bot.get_chat_member(update.effective_chat.id, context.bot.id)
    if not bot_member.can_pin_messages:
        return await update.message.reply_text("❌ I need **'Pin Messages'** permission to pin messages.", parse_mode=ParseMode.MARKDOWN)
    
    message_to_pin = update.message.reply_to_message
    
    try:
        await context.bot.pin_chat_message(
            chat_id=update.effective_chat.id, 
            message_id=message_to_pin.message_id, 
            disable_notification=False 
        )
        await update.message.reply_text("📌 Message pinned successfully.")
    except Exception as e:
        await update.message.reply_text(f"❌ Could not pin message. Error: {e}")

# /promote command
async def promote_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if not update.message.reply_to_message: return await update.message.reply_text("❓ Reply to the user you want to promote.")

    bot_member = await context.bot.get_chat_member(update.effective_chat.id, context.bot.id)
    if not bot_member.can_promote_members:
        return await update.message.reply_text("❌ I need **'Add New Admins'** permission to promote users.", parse_mode=ParseMode.MARKDOWN)

    target = update.message.reply_to_message.from_user
    target_id = target.id
    target_name = target.first_name
    
    try:
        await context.bot.promote_chat_member(
            update.effective_chat.id,
            target_id,
            can_manage_chat=True,
            can_delete_messages=True,
            can_restrict_members=True,
            can_invite_users=True,
            can_pin_messages=True,
            can_change_info=False,
            can_promote_members=False # Safety feature
        )
        await update.message.reply_text(f"👑 User **{target_name}** has been promoted to Admin!", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text(f"❌ Could not promote user. Error: {e}", parse_mode=ParseMode.MARKDOWN)

# /demote command
async def demote_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if not update.message.reply_to_message: return await update.message.reply_text("❓ Reply to the user you want to demote.")

    bot_member = await context.bot.get_chat_member(update.effective_chat.id, context.bot.id)
    if not bot_member.can_promote_members:
        return await update.message.reply_text("❌ I need **'Add New Admins'** permission to demote users.", parse_mode=ParseMode.MARKDOWN)

    target = update.message.reply_to_message.from_user
    target_id = target.id
    target_name = target.first_name
    
    try:
        # Demote by setting all permissions to False
        await context.bot.promote_chat_member(
            update.effective_chat.id,
            target_id,
            can_manage_chat=False,
            can_delete_messages=False,
            can_restrict_members=False,
            can_invite_users=False,
            can_pin_messages=False,
            can_change_info=False,
            can_promote_members=False
        )
        await update.message.reply_text(f"📉 User **{target_name}** has been demoted.", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text(f"❌ Could not demote user. Error: {e}", parse_mode=ParseMode.MARKDOWN)

# /warn command (Basic message for now)
async def warn_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if not update.message.reply_to_message: return await update.message.reply_text("❓ Reply to the user you want to warn.")

    target = update.message.reply_to_message.from_user
    target_name = target.first_name
    
    reason = "No reason specified."
    if context.args:
        reason = " ".join(context.args)
    
    await update.message.reply_text(
        f"⚠️ **Warning!** ⚠️\n"
        f"User **{target_name}** has been warned by **{update.effective_user.first_name}**.\n"
        f"Reason: *{reason}*", 
        parse_mode=ParseMode.MARKDOWN
    )