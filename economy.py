# economy.py (Final Version with all bug fixes)

from telegram.ext import ContextTypes
from telegram import Update
import time
import math
import random
from telegram.constants import ParseMode 

from database import (
    get_user_data, set_user_data, update_balance, is_protected, is_dead, 
    get_top_users, get_group_claim_data, set_group_claim_data, 
    log_balance_change, get_balance_history
)
from config import (
    TAX_RATE, ROB_PENALTY_COST, PROTECT_COST, REVIVE_COST, DAILY_REWARD, 
    DEATH_DURATION_SECONDS, PROTECT_DURATION_SECONDS, MIN_KILL_REWARD, MAX_KILL_REWARD, 
    REVIVE_LIMIT_DAILY, BOT_OWNER_ID, GROUP_CLAIM_REWARD
)

# --- HELPER FUNCTION (NEW for consistent name display) ---
def get_user_mention(user):
    """Returns a clickable user mention (Name) or @username for Markdown."""
    if user.username:
        # Use @username if available
        return f"@{user.username}"
    # Otherwise, use a mention link with first_name as the text
    return f"[{user.first_name}](tg://user?id={user.id})"

# --- ECONOMY COMMANDS ---

async def bal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.effective_user
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        
    balance, _, _, _, _, _, _ = get_user_data(target.id) 
    target_name = get_user_mention(target)
    
    await update.message.reply_text(f"💰 **{target_name}** ka current balance: **${balance}**", parse_mode=ParseMode.MARKDOWN)

async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance, _, _, _, _, _, daily_ts = get_user_data(user_id) 
    
    current_day = time.strftime('%Y-%m-%d')
    last_claim_day = time.strftime('%Y-%m-%d', time.localtime(daily_ts))

    if last_claim_day == current_day:
        await update.message.reply_text("❌ Aapne aaj ka daily reward pehle hi claim kar liya hai. Kal aana!", parse_mode=ParseMode.MARKDOWN)
        return

    update_balance(user_id, DAILY_REWARD)
    log_balance_change(user_id, 'daily', DAILY_REWARD) 
    set_user_data(user_id, daily_ts=time.time())
    
    await update.message.reply_text(f"✅ Daily reward claimed! You got **${DAILY_REWARD}**", parse_mode=ParseMode.MARKDOWN)

async def give_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not context.args or not context.args[0].isdigit():
        return await update.message.reply_text("❓ Usage: `/give [amount]` and reply to the user.")

    sender_id = update.effective_user.id
    receiver = update.message.reply_to_message.from_user
    receiver_id = receiver.id
    amount = int(context.args[0])

    if sender_id == receiver_id: return await update.message.reply_text("❌ You cannot send money to yourself.")
    if amount <= 0: return await update.message.reply_text("❌ Amount must be greater than zero.")

    sender_balance, _, _, _, _, _, _ = get_user_data(sender_id) 
    if sender_balance < amount: return await update.message.reply_text("❌ You do not have sufficient funds.")

    tax = math.ceil(amount * TAX_RATE)
    transfer_amount = amount - tax
    tax_percentage = int(TAX_RATE * 100)
    
    receiver_display_name = get_user_mention(receiver)
    sender_name = get_user_mention(update.effective_user)

    update_balance(sender_id, -amount)
    log_balance_change(sender_id, 'give_out', -amount, details=receiver.first_name)
    update_balance(receiver_id, transfer_amount)
    log_balance_change(receiver_id, 'give_in', transfer_amount, details=update.effective_user.first_name)
    update_balance(BOT_OWNER_ID, tax)
    log_balance_change(BOT_OWNER_ID, 'tax', tax, details=update.effective_user.first_name)

    notification_message = (
        f"💸 **Commission Received!** 💸\n"
        f"👤 User: **{sender_name}** (`{sender_id}`)\n"
        f"💰 Amount: **${tax}** (from ${amount} transaction)\n"
        f"🔄 Type: `/give` Tax"
    )
    try:
        await context.bot.send_message(chat_id=BOT_OWNER_ID, text=notification_message, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        print(f"Error sending commission notification to owner: {e}")
        
    await update.message.reply_text(
        f"✅ You gave **${amount}** to **{receiver_display_name}**\n"
        f"with **${tax}** fee deducted! ({tax_percentage}% tax applied) 💸", 
        parse_mode=ParseMode.MARKDOWN
    )

# --- RPG COMMANDS ---

async def protect_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance, _, protect_ts, _, _, _, _ = get_user_data(user_id) 
    
    if is_protected(protect_ts):
        remaining = int(protect_ts - time.time())
        d = remaining // 86400
        h = (remaining % 86400) // 3600
        m = (remaining % 3600) // 60
        return await update.message.reply_text(
            f"🛡️ You are already protected!\n"
            f"⏳ Remaining: **{d}d {h}h {m}m**", parse_mode=ParseMode.MARKDOWN
        )
    
    if balance < PROTECT_COST:
        return await update.message.reply_text(f"❌ Protection needs **${PROTECT_COST}**.", parse_mode=ParseMode.MARKDOWN)

    new_protect_ts = time.time() + PROTECT_DURATION_SECONDS
    update_balance(user_id, -PROTECT_COST)
    log_balance_change(user_id, 'protect_cost', -PROTECT_COST) 
    set_user_data(user_id, protect_ts=new_protect_ts) 
    
    await update.message.reply_text(
        f"✅ Protection bought! **${PROTECT_COST}** deducted.\n"
        "🛡️ You are safe from `/kill` and `/rob` for the next **24 hours**.", parse_mode=ParseMode.MARKDOWN
    )

async def rob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not context.args or not context.args[0].isdigit():
        return await update.message.reply_text("❓ Usage: `/rob [amount]` and reply to the user.")

    killer = update.effective_user
    target = update.message.reply_to_message.from_user
    killer_id = killer.id
    target_id = target.id
    amount = int(context.args[0])
    
    killer_data = get_user_data(killer_id)
    target_data = get_user_data(target_id)
    killer_balance, killer_death_ts, _, _, _, _, _ = killer_data 
    target_balance, target_death_ts, target_protect_ts, _, _, _, _ = target_data 
    
    killer_name = get_user_mention(killer)
    target_name = get_user_mention(target)

    if killer_id == target_id: return await update.message.reply_text("❌ Robbing yourself is pointless.")
    if is_dead(killer_death_ts): return await update.message.reply_text("💀 Dead users cannot rob!", parse_mode=ParseMode.MARKDOWN)
    
    if is_protected(target_protect_ts): return await update.message.reply_text(f"🛡️ **{target_name}** is protected right now!", parse_mode=ParseMode.MARKDOWN)
    
    if is_dead(target_death_ts): return await update.message.reply_text(f"⚰️ **{target_name}** is already dead.")
    if target_balance < amount: return await update.message.reply_text(f"❌ **{target_name}** doesn't have **${amount}** to rob.")

    if random.random() < 0.5:
        # SUCCESS!
        earned_amount = amount
        update_balance(killer_id, earned_amount)
        update_balance(target_id, -earned_amount)
        log_balance_change(killer_id, 'rob_gain', earned_amount, details=target.first_name)
        log_balance_change(target_id, 'rob_loss', -earned_amount, details=killer.first_name)

        notification_message = (
            f"🚨 **You were ROBBED!** 🚨\n"
            f"👤 Robber: **{killer_name}**\n"
            f"💸 Loss: **${earned_amount}**" 
        )
        try:
            await context.bot.send_message(chat_id=target_id, text=notification_message, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            print(f"Error sending rob notification to target {target_id}: {e}")
        
        await update.message.reply_text(
            f"💸 **{killer_name}** successfully robbed **${earned_amount}** from **{target_name}**!", parse_mode=ParseMode.MARKDOWN
        )
    else:
        # FAILURE! Penalty for killer
        if killer_balance >= ROB_PENALTY_COST:
            update_balance(killer_id, -ROB_PENALTY_COST)
            log_balance_change(killer_id, 'rob_loss', -ROB_PENALTY_COST, details="Failed Robbery")
            await update.message.reply_text(
                f"🚨 **{killer_name}**, your robbery failed! A **${ROB_PENALTY_COST}** penalty has been deducted!", parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(f"🚨 **{killer_name}**, your robbery failed! You were lucky to escape the penalty.")

async def kill_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message: return await update.message.reply_text("❓ Usage: `/kill` and reply to the target user.")
    killer = update.effective_user
    target = update.message.reply_to_message.from_user
    killer_id = killer.id
    target_id = target.id
    
    killer_data = get_user_data(killer_id)
    target_data = get_user_data(target_id)
    
    _, killer_death_ts, _, _, _, _, _ = killer_data 
    _, target_death_ts, target_protect_ts, _, _, target_total_kills, _ = target_data 
    
    killer_name = get_user_mention(killer)
    target_name = get_user_mention(target)

    if killer_id == target_id: return await update.message.reply_text("❌ Suicide is not allowed.")
    if is_dead(killer_death_ts): return await update.message.reply_text("💀 Dead users cannot kill anyone!", parse_mode=ParseMode.MARKDOWN) 
    
    if is_protected(target_protect_ts): return await update.message.reply_text(f"🛡️ **{target_name}** is protected right now!", parse_mode=ParseMode.MARKDOWN)
    
    if is_dead(target_death_ts): return await update.message.reply_text(f"⚰️ **{target_name}** is already dead.")

    # Kill Successful
    reward = random.randint(MIN_KILL_REWARD, MAX_KILL_REWARD)
    new_target_death_ts = time.time() + DEATH_DURATION_SECONDS
    
    update_balance(killer_id, reward)
    log_balance_change(killer_id, 'kill_gain', reward) 
    
    killer_balance, killer_death_ts, killer_protect_ts, killer_revive_count, killer_revive_date, killer_total_kills, killer_daily_ts = get_user_data(killer_id)
    set_user_data(killer_id, total_kills=killer_total_kills + 1)
    set_user_data(target_id, death_ts=new_target_death_ts)
    
    notification_message = (
        f"💀 **You were KILLED!** 💀\n"
        f"🔥 Killer: **{killer_name}**\n"
        f"⚰️ You are now dead and can be revived in **{DEATH_DURATION_SECONDS // 3600} hours**."
    )
    try:
        await context.bot.send_message(chat_id=target_id, text=notification_message, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        print(f"Error sending kill notification to target {target_id}: {e}")
        
    await update.message.reply_text(
        f"👤 —🍒→ **{killer_name}** 🔥\" killed xx **{target_name}** xx!\n"
        f"💰 Earned: **${reward}**", parse_mode=ParseMode.MARKDOWN
    )

async def revive_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    target = user
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        
    user_id = user.id
    target_id = target.id
    
    user_data = get_user_data(user_id) 
    target_data = get_user_data(target_id)
    
    balance, _, _, user_revive_count, user_revive_date, _, _ = user_data 
    _, target_death_ts, _, _, _, _, _ = target_data 
    
    current_date = time.strftime('%Y-%m-%d')
    if user_revive_date != current_date:
        set_user_data(user_id, revive_count=0, revive_date=current_date)
        user_revive_count = 0
    
    target_name = get_user_mention(target)
    user_name = get_user_mention(user)
    
    if target_id == user_id and not is_dead(target_death_ts):
        return await update.message.reply_text("❌ You are not dead.")
    if target_id != user_id and not is_dead(target_death_ts):
        return await update.message.reply_text(f"❌ {target_name} is not dead.")
        
    if user_revive_count >= REVIVE_LIMIT_DAILY:
        return await update.message.reply_text("❌ You have reached your daily revive limit!")

    if balance < REVIVE_COST:
        return await update.message.reply_text(f"❌ You need **${REVIVE_COST}** to revive {target_name}.", parse_mode=ParseMode.MARKDOWN)

    # Revive Successful
    update_balance(user_id, -REVIVE_COST)
    log_balance_change(user_id, 'revive_cost', -REVIVE_COST) 
    set_user_data(user_id, revive_count=user_revive_count + 1)
    set_user_data(target_id, death_ts=0.0) 

    await update.message.reply_text(
        f"💉 **{target_name}** has been revived by **{user_name}**!\n"
        f"**${REVIVE_COST}** deducted from your balance.", parse_mode=ParseMode.MARKDOWN
    )

async def toprich_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_users = get_top_users('balance', limit=10)
    if not top_users: return await update.message.reply_text("No data found in the database.")
    
    top_list = "🏆 **Top 10 Richest Users (Global)** 🏆\n\n"
    for i, (user_id, balance) in enumerate(top_users):
        try:
            user_info = await context.bot.get_chat(user_id)
            
            display_name = f"[{user_info.first_name}](tg://user?id={user_id})"
            
            if user_info.username:
                display_name += f" (@{user_info.username})"
            
        except Exception:
            display_name = f"Unknown User (`{user_id}`)"
            
        top_list += f"{i+1}. **{display_name}**: **${balance}**\n" 
        
    await update.message.reply_text(top_list, parse_mode=ParseMode.MARKDOWN)

async def topkill_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_killers = get_top_users('total_kills', limit=10)
    if not top_killers: return await update.message.reply_text("No kills data found in the database.")
    
    top_list = "🔪 **Top 10 Killers (Global)** 🔪\n\n"
    for i, (user_id, kills) in enumerate(top_killers):
        try:
            user_info = await context.bot.get_chat(user_id)
            
            display_name = f"[{user_info.first_name}](tg://user?id={user_id})"
            
            if user_info.username:
                display_name += f" (@{user_info.username})"
                
        except Exception:
            display_name = f"Unknown User (`{user_id}`)"
            
        top_list += f"{i+1}. **{display_name}**: **{kills} Kills**\n" 
        
    await update.message.reply_text(top_list, parse_mode=ParseMode.MARKDOWN)

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return await update.message.reply_text("❓ Usage: Reply to a user with `/check` to see their protection status.")
        
    target_user = update.message.reply_to_message.from_user
    target_id = target_user.id
    target_name = get_user_mention(target_user)
    
    user_data = get_user_data(target_id)
    _, _, protect_ts, _, _, _, _ = user_data 
    
    if is_protected(protect_ts):
        remaining = int(protect_ts - time.time())
        h, m = remaining // 3600, (remaining % 3600) // 60
        await update.message.reply_text(
            f"🛡️ **{target_name}** is currently protected.\n"
            f"Protection expires in **{h}h {m}m**.", parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(f"❌ **{target_name}** is currently **Not Protected**.", parse_mode=ParseMode.MARKDOWN)

# /detail command (New working function)
async def detail_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.effective_user
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user

    target_id = target.id
    target_name = get_user_mention(target)

    balance, death_ts, protect_ts, revive_count, revive_date, total_kills, daily_ts = get_user_data(target_id)
    
    if is_dead(death_ts):
        remaining_death = int(death_ts - time.time())
        h = remaining_death // 3600
        m = (remaining_death % 3600) // 60
        death_status = f"💀 **DEAD!** (Revive in **{h}h {m}m**)"
    else:
        death_status = "✨ **ALIVE**"

    if is_protected(protect_ts):
        remaining_protect = int(protect_ts - time.time())
        h = remaining_protect // 3600
        m = (remaining_protect % 3600) // 60
        protect_status = f"🛡️ **Protected** (Ends in **{h}h {m}m**)"
    else:
        protect_status = "🚫 **Not Protected**"
        
    current_date = time.strftime('%Y-%m-%d')
    if revive_date != current_date:
        revive_count = 0 
        
    remaining_revives = REVIVE_LIMIT_DAILY - revive_count
    remaining_revives = max(0, remaining_revives) 

    last_claim_day = time.strftime('%Y-%m-%d', time.localtime(daily_ts))
    daily_status = "✅ **Claimed Today**" if last_claim_day == current_date else "❌ **Not Claimed Today**"

    reply_text = (
        f"👤 **{target_name}'s RPG Profile** 👤\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"💰 **Balance:** **${balance}**\n"
        f"🔪 **Total Kills:** **{total_kills}**\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"🩸 **Health Status:** {death_status}\n"
        f"🛡️ **Protection:** {protect_status}\n"
        f"💉 **Revives Left (Today):** **{remaining_revives}/{REVIVE_LIMIT_DAILY}**\n"
        f"🎁 **Daily Claim:** {daily_status}\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"🔗 User ID: `{target_id}`"
    )
    
    await update.message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)

# /claim command (New working function)
async def claim_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == 'private':
        return await update.message.reply_text("❌ This command must be used in a group.", parse_mode=ParseMode.MARKDOWN)

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    claimed_by_id, claimed_ts = get_group_claim_data(chat_id)

    if claimed_by_id:
        try:
            claimant_user = await context.bot.get_chat(claimed_by_id)
            claimant_name = f"[{claimant_user.first_name}](tg://user?id={claimed_by_id})"
        except Exception:
            claimant_name = f"User ID: `{claimed_by_id}`"

        claim_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(claimed_ts))
        return await update.message.reply_text(
            f"❌ This group has already been claimed by **{claimant_name}** on `{claim_date}`.",
            parse_mode=ParseMode.MARKDOWN
        )

    set_group_claim_data(chat_id, user_id, time.time())
    update_balance(user_id, GROUP_CLAIM_REWARD)
    log_balance_change(user_id, 'group_claim', GROUP_CLAIM_REWARD, details=str(chat_id))

    user_name = get_user_mention(update.effective_user)

    await update.message.reply_text(
        f"👑 Group Claim Successful! 👑\n"
        f"**{user_name}** has claimed ownership of this group and received a **${GROUP_CLAIM_REWARD}** reward!",
        parse_mode=ParseMode.MARKDOWN
    )

# /own command (New working function)
async def own_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == 'private':
        return await update.message.reply_text("❌ This command must be used in a group.", parse_mode=ParseMode.MARKDOWN)

    chat_id = update.effective_chat.id
    claimed_by_id, claimed_ts = get_group_claim_data(chat_id)

    if not claimed_by_id:
        return await update.message.reply_text("❌ This group has not been claimed yet. Use `/claim` to claim it!", parse_mode=ParseMode.MARKDOWN)

    try:
        claimant_user = await context.bot.get_chat(claimed_by_id)
        claimant_name = f"[{claimant_user.first_name}](tg://user?id={claimed_by_id})"
    except Exception:
        claimant_name = f"User ID: `{claimed_by_id}`"

    claim_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(claimed_ts))

    await update.message.reply_text(
        f"🏰 **Group Ownership Status** 🏰\n"
        f"👑 **Owner:** {claimant_name}\n"
        f"⏰ **Claimed On:** `{claim_date}`",
        parse_mode=ParseMode.MARKDOWN
    )