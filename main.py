import logging
import json
import os
import random
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

# --- Configuration & Setup ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Replace with your actual bot token
BOT_TOKEN = "8050711631:AAEOmQtI1LDg8F5zBST1tIPh0mDtHbIISEs"

# Your owner's numeric ID for /owner command (if nightking1515 is not your actual ID)
OWNER_ID = 1077750796

# Data file path
USER_DATA_FILE = os.getenv("DATABASE_PATH", "users.json")

# --- Global Data and Constants ---
# User data structure: {tg_id: {"level": int, "rank": str, "xp": int, "won": int, "hp": int, "strength": int, "inventory": [], "wins": int, "losses": int, "pvp_points": int, "loan": int}}
users = {}

# PvP state management
FIGHT_STATE = {} # {chat_id: {"fighter1": {"id": int, "hp": int, "name": str}, "fighter2": {"id": int, "hp": int, "name": str}, "message_id": int, "turn": int, "in_progress": bool}}

# Rank system
RANKS = ["E", "D", "C", "B", "A"] + [f"S{i}" for i in range(1, 101)] + [f"SJP{i}" for i in range(1, 101)]

# PvP Bot details for special battles
BOT_HP = 100
BOT_NAME = "EvilBot"
REWARDS = {
    "pvp": {"xp": 100000, "won": 1000000, "pvp_points": 22},
    "pvp_bot": {"xp": 10000, "won": 100000, "pvp_points": 5}
}
PENALTIES = {
    "pvp": {"xp": 500, "won": 100000, "pvp_points": 26},
    "pvp_bot": {"xp": 100, "won": 10000, "pvp_points": 3}
}

SHOP_ITEMS = {
    "swords": [
        {"id": 1, "name": "Iron Sword", "price": 200, "damage": 10},
        {"id": 2, "name": "Steel Sword", "price": 500, "damage": 20},
        {"id": 3, "name": "Silver Sword", "price": 800, "damage": 30},
        {"id": 4, "name": "Magic Sword", "price": 1500, "damage": 50},
        {"id": 5, "name": "Flame Sword", "price": 2200, "damage": 70},
        {"id": 6, "name": "Ice Sword", "price": 2500, "damage": 80},
        {"id": 7, "name": "Thunder Sword", "price": 3000, "damage": 100},
        {"id": 8, "name": "Dark Sword", "price": 4000, "damage": 120},
        {"id": 9, "name": "Light Sword", "price": 4200, "damage": 125},
        {"id": 10, "name": "Dragon Slayer", "price": 5000, "damage": 150},
        {"id": 11, "name": "Shadow Blade", "price": 6000, "damage": 180},
        {"id": 12, "name": "Heavenly Sword", "price": 7500, "damage": 200},
        {"id": 13, "name": "Chaos Sword", "price": 10000, "damage": 250},
        {"id": 14, "name": "Demonic Sword", "price": 12000, "damage": 300},
        {"id": 15, "name": "Excalibur", "price": 15000, "damage": 400},
    ],
    "revival": [
        {"id": 16, "name": "Revival Potion", "price": 500, "effect": "Revive with 20% HP"},
        {"id": 17, "name": "Strong Revival Potion", "price": 1200, "effect": "Revive with 50% HP"},
        {"id": 18, "name": "Phoenix Feather", "price": 2500, "effect": "Revive with 100% HP"},
        {"id": 19, "name": "Life Scroll", "price": 3000, "effect": "Revive + 20% XP"},
        {"id": 20, "name": "Divine Elixir", "price": 4000, "effect": "Revive with full stats"},
        {"id": 21, "name": "Resurrection Stone", "price": 5000, "effect": "Revive 2 times"},
        {"id": 22, "name": "Angel Tear", "price": 6500, "effect": "Revive + Shield for 1 turn"},
        {"id": 23, "name": "Holy Water", "price": 7000, "effect": "Revive + Full HP"},
        {"id": 24, "name": "God’s Blessing", "price": 9000, "effect": "Auto Revive once"},
        {"id": 25, "name": "Immortal Charm", "price": 12000, "effect": "Revive + Invincible 1 turn"},
    ],
    "poison": [
        {"id": 26, "name": "Poison Dagger", "price": 700, "damage": 15},
        {"id": 27, "name": "Venom Bottle", "price": 1200, "damage": 25},
        {"id": 28, "name": "Toxin Bomb", "price": 2000, "damage": 40},
        {"id": 29, "name": "Paralysis Poison", "price": 2500, "damage": 50},
        {"id": 30, "name": "Deadly Venom", "price": 3500, "damage": 80},
        {"id": 31, "name": "Corruption Gas", "price": 4000, "damage": 100},
        {"id": 32, "name": "Silent Killer", "price": 5000, "damage": 120},
        {"id": 33, "name": "Toxic Arrow", "price": 6000, "damage": 140},
        {"id": 34, "name": "Necro Venom", "price": 7500, "damage": 180},
        {"id": 35, "name": "Plague Bomb", "price": 9000, "damage": 220},
    ],
    "special": [
        {"id": 36, "name": "Hunter Key", "price": 300, "effect": "Unlock dungeons"},
        {"id": 37, "name": "Magic Shield", "price": 2000, "effect": "Reduce damage 20%"},
        {"id": 38, "name": "Golden Armor", "price": 5000, "effect": "Reduce damage 50%"},
        {"id": 39, "name": "XP Booster", "price": 1500, "effect": "Gain double XP"},
        {"id": 40, "name": "Lucky Charm", "price": 1200, "effect": "Increase drop rate"},
        {"id": 41, "name": "Soul Orb", "price": 2500, "effect": "Extra summon power"},
        {"id": 42, "name": "Dark Crystal", "price": 4000, "effect": "Boost poison attack"},
        {"id": 43, "name": "Sacred Ring", "price": 6000, "effect": "Immune to poison 2 turns"},
        {"id": 44, "name": "Teleport Scroll", "price": 1000, "effect": "Escape from battle"},
        {"id": 45, "name": "Binding Chains", "price": 2000, "effect": "Stun enemy 1 turn"},
        {"id": 46, "name": "Power Elixir", "price": 3000, "effect": "Increase damage 30%"},
        {"id": 47, "name": "Stamina Potion", "price": 1500, "effect": "Restore 100 stamina"},
        {"id": 48, "name": "Hunter Medal", "price": 500, "effect": "Collectible"},
        {"id": 49, "name": "Dimensional Stone", "price": 7000, "effect": "Summon ally"},
        {"id": 50, "name": "Time Relic", "price": 10000, "effect": "Take extra turn"},
    ]
}

# --- Data Persistence Functions ---
def load_user_data():
    global users
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            try:
                users = {int(k): v for k, v in json.load(f).items()}
            except json.JSONDecodeError:
                users = {}
    else:
        users = {}

def save_user_data():
    with open(USER_DATA_FILE, "w") as f:
        json.dump(users, f, indent=4)

load_user_data()

def get_item_by_id(item_id: int):
    for category_items in SHOP_ITEMS.values():
        for item in category_items:
            if item["id"] == item_id:
                return item
    return None

def get_rank_from_points(pvp_points):
    # This is a simplified logic. You'll need to define rank thresholds later.
    if pvp_points < 100: return "E"
    if pvp_points < 200: return "D"
    if pvp_points < 300: return "C"
    # ... and so on for all ranks.
    return "A"

def get_health_bar(current_hp, max_hp=100, bar_length=10):
    filled_squares = int((max(0, current_hp) / max_hp) * bar_length)
    empty_squares = bar_length - filled_squares
    return "🟢" * filled_squares + "⚪" * empty_squares

def get_strength_bar(strength, max_strength=100, bar_length=10):
    filled_squares = int((strength / max_strength) * bar_length)
    empty_squares = bar_length - filled_squares
    return "🔵" * filled_squares + "⚪" * empty_squares

# --- Conversation States ---
# Pvp states
START_PVP, PVP_ACTION = range(2)

# --- Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in users:
        users[user_id] = {
            "level": 0, "rank": "E", "xp": 0, "won": 1000, "hp": 100,
            "strength": 10, "inventory": [], "wins": 0, "losses": 0,
            "pvp_points": 0, "loan": 0, "full_name": update.effective_user.full_name
        }
        save_user_data()
        await update.message.reply_text(
            f"Welcome, {update.effective_user.full_name}! You are now registered as a Hunter."
            f"\nYour starting rank is E and your balance is 1000 won."
        )
    else:
        await update.message.reply_text("You are already a registered Hunter.")

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_user = update.effective_user
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user

    user_data = users.get(target_user.id)
    if not user_data:
        await update.message.reply_text("User is not registered.")
        return

    profile_msg = (
        f"**Hunter Profile: {target_user.full_name}**\n\n"
        f"Level: {user_data.get('level', 0)}\n"
        f"Rank: {user_data.get('rank', 'E')}\n"
        f"Balance: {user_data.get('won', 0)} won\n"
        f"Items: {len(user_data.get('inventory', []))}\n"
        f"PvP Record: {user_data.get('wins', 0)} Wins / {user_data.get('losses', 0)} Losses\n"
        f"PvP Points: {user_data.get('pvp_points', 0)}"
    )
    await update.message.reply_markdown(profile_msg)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = users.get(user_id)
    if not user_data:
        await update.message.reply_text("You are not a registered Hunter. Use /start.")
        return
    
    strength_bar = get_strength_bar(user_data['strength'])
    status_msg = (
        f"**Hunter Status: {update.effective_user.full_name}**\n\n"
        f"Strength: {user_data['strength']}\n"
        f"{strength_bar}\n\n"
        f"To level up your rank, you need more PvP points.\n"
        f"Current Rank: {user_data['rank']}\n"
        f"PvP Points: {user_data['pvp_points']}"
    )
    await update.message.reply_markdown(status_msg)

async def won_give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_id = update.effective_user.id
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to the user you want to give won to.")
        return
    
    recipient_id = update.message.reply_to_message.from_user.id
    if sender_id == recipient_id:
        await update.message.reply_text("You cannot give won to yourself.")
        return
        
    try:
        amount = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please specify a valid amount. Example: /wongive 100")
        return
        
    sender_data = users.get(sender_id)
    recipient_data = users.get(recipient_id)
    
    if not sender_data or not recipient_data:
        await update.message.reply_text("Both users must be registered Hunters.")
        return
    
    if sender_data["won"] < amount:
        await update.message.reply_text("You don't have enough won.")
        return
        
    sender_data["won"] -= amount
    recipient_data["won"] += amount
    save_user_data()
    
    await update.message.reply_text(f"You gave {amount} won to {recipient_data['full_name']}.")

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("All Items", callback_data="shop_all")],
        [InlineKeyboardButton("Swords", callback_data="shop_swords"),
         InlineKeyboardButton("Revival Items", callback_data="shop_revival")]
    ])
    await update.message.reply_text("🛒 **Welcome to the Shop!**\n\nChoose a category:", reply_markup=kb, parse_mode="Markdown")

async def handle_shop_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data.split("_")[1]
    
    items_to_show = []
    if category == "all":
        for cat in SHOP_ITEMS.values():
            items_to_show.extend(cat)
    else:
        items_to_show = SHOP_ITEMS.get(category, [])

    message_text = f"**{category.capitalize()} Items:**\n\n"
    for item in items_to_show:
        details = f"ID: {item['id']} - {item['name']} - Price: {item['price']} won"
        if "damage" in item:
            details += f", Damage: {item['damage']}"
        if "effect" in item:
            details += f", Effect: {item['effect']}"
        message_text += f"• {details}\n"

    await query.edit_message_text(message_text, parse_mode="Markdown")

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        item_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please specify a valid item number. Example: /buy 1")
        return

    item = get_item_by_id(item_id)
    if not item:
        await update.message.reply_text("Item not found in the shop.")
        return

    user_id = update.effective_user.id
    user_data = users.get(user_id)
    if not user_data:
        await update.message.reply_text("You are not a registered Hunter. Use /start.")
        return
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Yes", callback_data=f"buy_confirm_{item_id}"),
         InlineKeyboardButton("❌ No", callback_data="buy_cancel")]
    ])

    details = f"🛒 **{item['name']}** - Price: {item['price']} won"
    if "damage" in item:
        details += f"\nDamage: {item['damage']}"
    if "effect" in item:
        details += f"\nEffect: {item['effect']}"
    
    await update.message.reply_markdown(
        f"{details}\n\nDo you want to buy this item?",
        reply_markup=kb
    )

async def handle_buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    user_data = users.get(user_id)
    
    if data.startswith("buy_confirm_"):
        item_id = int(data.split("_")[2])
        item = get_item_by_id(item_id)
        
        if user_data["won"] < item["price"]:
            await query.edit_message_text(
                f"💸 Not enough won! You have {user_data['won']} but need {item['price']}."
            )
            return

        user_data["won"] -= item["price"]
        user_data["inventory"].append(item["name"])
        save_user_data()

        await query.edit_message_text(
            f"✅ You bought {item['name']} for {item['price']} won!\n"
            f"Remaining balance: {user_data['won']} won."
        )
    elif data == "buy_cancel":
        await query.edit_message_text("❌ Purchase cancelled.")

# PvP conversation handler
async def pvp_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to a user to start PvP.")
        return ConversationHandler.END
    
    challenger = update.effective_user
    opponent = update.message.reply_to_message.from_user
    
    if challenger.id == opponent.id:
        await update.message.reply_text("You cannot challenge yourself!")
        return ConversationHandler.END

    FIGHT_STATE[update.effective_chat.id] = {
        "fighter1": {"id": challenger.id, "name": challenger.full_name, "hp": 100},
        "fighter2": {"id": opponent.id, "name": opponent.full_name, "hp": 100},
        "turn": 1,
        "is_bot_fight": False,
        "in_progress": True,
        "message_id": None
    }
    
    await update.message.reply_text(
        f"⚔️ {challenger.full_name} has challenged {opponent.full_name} to a PvP battle!\n"
        f"Hey {opponent.full_name}, do you accept? Say 'yes' to start."
    )
    return START_PVP

async def pvp_bot_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    challenger = update.effective_user
    FIGHT_STATE[update.effective_chat.id] = {
        "fighter1": {"id": challenger.id, "name": challenger.full_name, "hp": 100},
        "fighter2": {"id": -1, "name": BOT_NAME, "hp": BOT_HP},
        "turn": 1,
        "is_bot_fight": True,
        "in_progress": True,
        "message_id": None
    }
    await pvp_turn(update, context)
    return PVP_ACTION

async def pvp_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in FIGHT_STATE or not FIGHT_STATE[chat_id]["in_progress"]:
        return ConversationHandler.END
    
    state = FIGHT_STATE[chat_id]
    if update.effective_user.id != state["fighter2"]["id"]:
        return
        
    if update.message.text.lower() == "yes":
        await update.message.reply_text("Battle accepted! Let's fight!")
        await pvp_turn(update, context)
        return PVP_ACTION
    else:
        await update.message.reply_text("PvP request declined.")
        FIGHT_STATE[chat_id]["in_progress"] = False
        return ConversationHandler.END

async def pvp_turn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in FIGHT_STATE or not FIGHT_STATE[chat_id]["in_progress"]:
        return
    
    state = FIGHT_STATE[chat_id]
    
    # Check if it's user's turn
    current_player_id = state["fighter1"]["id"] if state["turn"] == 1 else state["fighter2"]["id"]
    if update.effective_user.id != current_player_id and not state["is_bot_fight"]:
        await update.message.reply_text("It's not your turn.")
        return

    # Simulate attack
    if update.message.text.lower() == "attack":
        damage = random.randint(10, 25)
        
        target_hp = state["fighter2"]["hp"] if state["turn"] == 1 else state["fighter1"]["hp"]
        target_hp -= damage
        
        if state["turn"] == 1:
            state["fighter2"]["hp"] = target_hp
        else:
            state["fighter1"]["hp"] = target_hp
        
        state["turn"] = 2 if state["turn"] == 1 else 1

        # Check for winner
        if state["fighter1"]["hp"] <= 0 or state["fighter2"]["hp"] <= 0:
            await pvp_end(update, context)
            return ConversationHandler.END

        # Update message
        status_msg = get_battle_status_msg(state)
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Attack", callback_data="pvp_attack")]
        ])
        if state["message_id"]:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=state["message_id"],
                text=status_msg,
                reply_markup=kb,
                parse_mode="Markdown"
            )
        else:
            msg = await update.message.reply_markdown(status_msg, reply_markup=kb)
            state["message_id"] = msg.message_id
            
    return PVP_ACTION

async def pvp_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    state = FIGHT_STATE[chat_id]
    
    winner = state["fighter1"] if state["fighter1"]["hp"] > 0 else state["fighter2"]
    loser = state["fighter1"] if state["fighter1"]["hp"] <= 0 else state["fighter2"]
    
    is_pvp_bot = state["is_bot_fight"]
    
    reward_type = "pvp_bot" if is_pvp_bot else "pvp"
    
    # Update user data
    winner_data = users.get(winner["id"])
    if winner_data:
        winner_data["wins"] += 1
        winner_data["xp"] += REWARDS[reward_type]["xp"]
        winner_data["won"] += REWARDS[reward_type]["won"]
        winner_data["pvp_points"] += REWARDS[reward_type]["pvp_points"]
        
    loser_data = users.get(loser["id"])
    if loser_data:
        loser_data["losses"] += 1
        loser_data["xp"] += PENALTIES[reward_type]["xp"]
        loser_data["won"] -= PENALTIES[reward_type]["won"]
        loser_data["pvp_points"] -= PENALTIES[reward_type]["pvp_points"]
        
    save_user_data()
    
    result_msg = (
        f"🎉 **{winner['name']}** wins the battle! 🏆\n\n"
        f"👑 **Victory Rewards**:\n"
        f"- 🧠 XP: +{REWARDS[reward_type]['xp']}\n"
        f"- 💴 won: +{REWARDS[reward_type]['won']}\n"
        f"- 🎖 pvp points: +{REWARDS[reward_type]['pvp_points']}\n\n"
        f"💀 **Defeat Penalties** for **{loser['name']}**:\n"
        f"- 🧠 XP: +{PENALTIES[reward_type]['xp']}\n"
        f"- 💴 won: -{PENALTIES[reward_type]['won']}\n"
        f"- 🎖 pvp points: -{PENALTIES[reward_type]['pvp_points']}"
    )

    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=state["message_id"],
        text=result_msg,
        parse_mode="Markdown"
    )
    
    FIGHT_STATE[chat_id]["in_progress"] = False
    return ConversationHandler.END

def get_battle_status_msg(state):
    fighter1 = state["fighter1"]
    fighter2 = state["fighter2"]

    return (
        f"🔥 **Battle Time!** 🔥\n\n"
        f"**{fighter1['name']}**\n"
        f"🌿 **Health**: {get_health_bar(fighter1['hp'])} {fighter1['hp']}/100 🟢\n"
        f"✨ **Strength**: {get_strength_bar(users.get(fighter1['id'], {}).get('strength', 0))} {users.get(fighter1['id'], {}).get('strength', 0)} 💨\n\n"
        f"**{fighter2['name']}**\n"
        f"🌿 **Health**: {get_health_bar(fighter2['hp'])} {fighter2['hp']}/100 🟢\n"
        f"✨ **Strength**: {get_strength_bar(users.get(fighter2['id'], {}).get('strength', 0))} {users.get(fighter2['id'], {}).get('strength', 0)} 💨\n\n"
        f"👉 **Turn**: {state['fighter1']['name'] if state['turn'] == 1 else state['fighter2']['name']}! Choose your action:"
    )

# --- Main function ---
def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers for basic commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("wongive", wongive))
    application.add_handler(CommandHandler("shop", shop))
    application.add_handler(CommandHandler("buy", buy))

    # Handler for callbacks (buttons)
    application.add_handler(CallbackQueryHandler(handle_buy_callback, pattern=r"buy_confirm_|\bbuy_cancel\b"))
    application.add_handler(CallbackQueryHandler(handle_shop_category, pattern=r"shop_"))

    # PvP Conversation Handler
    pvp_handler = ConversationHandler(
        entry_points=[CommandHandler("pvp", pvp_start), CommandHandler("pvpbot", pvp_bot_start)],
        states={
            START_PVP: [MessageHandler(filters.TEXT & ~filters.COMMAND, pvp_accept)],
            PVP_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, pvp_turn)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
    )
    application.add_handler(pvp_handler)

    # All other handlers (add them as you implement them)
    # application.add_handler(CommandHandler("won", won_cmd))
    # ... and so on

    application.run_polling()

if __name__ == "__main__":
    main()


