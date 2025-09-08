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

# --- Replace with your actual credentials ---
BOT_TOKEN = "8050711631:AAEOmQtI1LDg8F5zBST1tIPh0mDtHbIISEs"
OWNER_ID = 6820913319

# Data file path (will be in /data on Render for persistence)
USER_DATA_FILE = os.getenv("DATABASE_PATH", "users.json")

# --- Global Data and Constants ---
# User data structure
users = {} # {tg_id: {"level": int, "rank": str, "xp": int, "won": int, "hp": int, "strength": int, "inventory": [], "wins": int, "losses": int, "pvp_points": int, "loan": int, "daily_tasks_done": int}}

# PvP state management
FIGHT_STATE = {} # {chat_id: {"fighter1": {"id": int, "hp": int, "name": str}, "fighter2": {"id": int, "hp": int, "name": str}, "message_id": int, "turn": int, "in_progress": bool, "is_bot_fight": bool, "is_special_battle": bool, "special_hunter": str}}

# Rank system
RANKS = ["E", "D", "C", "B", "A"] + [f"S{i}" for i in range(1, 101)] + [f"SJP{i}" for i in range(1, 101)]
RANK_THRESHOLDS = {
    "D": 100, "C": 250, "B": 500, "A": 1000, "S1": 2500, "S2": 3000, "S3": 3500, "S4": 4000, "S5": 4500, "S6": 5000, "S7": 5500, "S8": 6000, "S9": 6500, "S10": 7000, "S11": 7500, "S12": 8000, "S13": 8500, "S14": 9000, "S15": 9500, "S16": 10000, "S17": 10500, "S18": 11000, "S19": 11500, "S20": 12000, "S21": 12500, "S22": 13000, "S23": 13500, "S24": 14000, "S25": 14500, "S26": 15000, "S27": 15500, "S28": 16000, "S29": 16500, "S30": 17000, "S31": 17500, "S32": 18000, "S33": 18500, "S34": 19000, "S35": 19500, "S36": 20000, "S37": 20500, "S38": 21000, "S39": 21500, "S40": 22000, "S41": 22500, "S42": 23000, "S43": 23500, "S44": 24000, "S45": 24500, "S46": 25000, "S47": 25500, "S48": 26000, "S49": 26500, "S50": 27000, "S51": 27500, "S52": 28000, "S53": 28500, "S54": 29000, "S55": 29500, "S56": 30000, "S57": 30500, "S58": 31000, "S59": 31500, "S60": 32000, "S61": 32500, "S62": 33000, "S63": 33500, "S64": 34000, "S65": 34500, "S66": 35000, "S67": 35500, "S68": 36000, "S69": 36500, "S70": 37000, "S71": 37500, "S72": 38000, "S73": 38500, "S74": 39000, "S75": 39500, "S76": 40000, "S77": 40500, "S78": 41000, "S79": 41500, "S80": 42000, "S81": 42500, "S82": 43000, "S83": 43500, "S84": 44000, "S85": 44500, "S86": 45000, "S87": 45500, "S88": 46000, "S89": 46500, "S90": 47000, "S91": 47500, "S92": 48000, "S93": 48500, "S94": 49000, "S95": 49500, "S96": 50000, "S97": 50500, "S98": 51000, "S99": 51500, "S100": 52000, "SJP1": 100000, "SJP2": 110000, "SJP3": 120000, "SJP4": 130000, "SJP5": 140000, "SJP6": 150000, "SJP7": 160000, "SJP8": 170000, "SJP9": 180000, "SJP10": 190000, "SJP11": 200000, "SJP12": 210000, "SJP13": 220000, "SJP14": 230000, "SJP15": 240000, "SJP16": 250000, "SJP17": 260000, "SJP18": 270000, "SJP19": 280000, "SJP20": 290000, "SJP21": 300000, "SJP22": 310000, "SJP23": 320000, "SJP24": 330000, "SJP25": 340000, "SJP26": 350000, "SJP27": 360000, "SJP28": 370000, "SJP29": 380000, "SJP30": 390000, "SJP31": 400000, "SJP32": 410000, "SJP33": 420000, "SJP34": 430000, "SJP35": 440000, "SJP36": 450000, "SJP37": 460000, "SJP38": 470000, "SJP39": 480000, "SJP40": 490000, "SJP41": 500000, "SJP42": 510000, "SJP43": 520000, "SJP44": 530000, "SJP45": 540000, "SJP46": 550000, "SJP47": 560000, "SJP48": 570000, "SJP49": 580000, "SJP50": 590000, "SJP51": 600000, "SJP52": 610000, "SJP53": 620000, "SJP54": 630000, "SJP55": 640000, "SJP56": 650000, "SJP57": 660000, "SJP58": 670000, "SJP59": 680000, "SJP60": 690000, "SJP61": 700000, "SJP62": 710000, "SJP63": 720000, "SJP64": 730000, "SJP65": 740000, "SJP66": 750000, "SJP67": 760000, "SJP68": 770000, "SJP69": 780000, "SJP70": 790000, "SJP71": 800000, "SJP72": 810000, "SJP73": 820000, "SJP74": 830000, "SJP75": 840000, "SJP76": 850000, "SJP77": 860000, "SJP78": 870000, "SJP79": 880000, "SJP80": 890000, "SJP81": 900000, "SJP82": 910000, "SJP83": 920000, "SJP84": 930000, "SJP85": 940000, "SJP86": 950000, "SJP87": 960000, "SJP88": 970000, "SJP89": 980000, "SJP90": 990000, "SJP91": 1000000, "SJP92": 1010000, "SJP93": 1020000, "SJP94": 1030000, "SJP95": 1040000, "SJP96": 1050000, "SJP97": 1060000, "SJP98": 1070000, "SJP99": 1080000, "SJP100": 1090000
}

# XP needed for each level
LEVEL_XP_THRESHOLDS = {i: i * 500 for i in range(1, 101)}

# PvP Bot details for special battles
BOT_HP = 100
BOT_NAME = "EvilBot"
SPECIAL_HUNTERS = {
    20: "Thomas Andre", 40: "Liu Zhigang", 60: "Christopher Reed", 80: "Go Gun-Hee", 100: "Antares"
}
SPECIAL_SHADOWS = {
    25: "Igris", 50: "Tusk", 75: "Bellion", 100: "Beru"
}
REWARDS = {
    "pvp": {"xp": 100000, "won": 1000000, "pvp_points": 22},
    "pvp_bot": {"xp": 10000, "won": 100000, "pvp_points": 5}
}
PENALTIES = {
    "pvp": {"xp": 500, "won": 100000, "pvp_points": 26},
    "pvp_bot": {"xp": 100, "won": 10000, "pvp_points": 3}
}

# The shop list you provided
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

# Loan System
LOAN_OFFERS = [
    {"amount": 5000, "interest": 10, "repayment_turns": 10},
    {"amount": 10000, "interest": 8, "repayment_turns": 15},
    {"amount": 25000, "interest": 5, "repayment_turns": 20},
]
# Daily Tasks
DAILY_TASKS = [
    {"task": "Win a PvP match", "reward_type": "won", "reward_value": 5000},
    {"task": "Defeat the EvilBot", "reward_type": "keys", "reward_value": 1},
    {"task": "Buy an item from the shop", "reward_type": "revival_item", "reward_value": "Revival Potion"},
]

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
    # Make sure all users have a loan key
    for user_id in users:
        if "loan" not in users[user_id]:
            users[user_id]["loan"] = 0
        if "loan_amount" not in users[user_id]:
            users[user_id]["loan_amount"] = 0
        if "loan_interest" not in users[user_id]:
            users[user_id]["loan_interest"] = 0
        if "daily_tasks_done" not in users[user_id]:
            users[user_id]["daily_tasks_done"] = 0
        if "daily_task_date" not in users[user_id]:
            users[user_id]["daily_task_date"] = None

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
    for rank, threshold in RANK_THRESHOLDS.items():
        if pvp_points >= threshold:
            continue
        else:
            return rank
    return RANKS[-1]

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
            "pvp_points": 0, "loan": 0, "loan_amount": 0, "loan_interest": 0,
            "daily_tasks_done": 0, "daily_task_date": None,
            "full_name": update.effective_user.full_name
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
        f"**Hunter Profile: {user_data.get('full_name', target_user.full_name)}**\n\n"
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
    
    # Calculate next rank and points needed
    current_rank_index = RANKS.index(user_data['rank'])
    if current_rank_index < len(RANKS) - 1:
        next_rank = RANKS[current_rank_index + 1]
        next_rank_threshold = RANK_THRESHOLDS.get(next_rank, 0)
        points_needed = next_rank_threshold - user_data['pvp_points']
    else:
        next_rank = "Max Rank"
        points_needed = 0

    status_msg = (
        f"**Hunter Status: {user_data['full_name']}**\n\n"
        f"Strength: {user_data['strength']}\n"
        f"{strength_bar}\n\n"
        f"Current Rank: {user_data['rank']}\n"
        f"PvP Points: {user_data['pvp_points']}\n"
        f"Next Rank: {next_rank} (Needs {max(0, points_needed)} points)"
    )
    await update.message.reply_markdown(status_msg)

async def won_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = users.get(update.effective_user.id)
    if not user_data:
        await update.message.reply_text("You are not a registered Hunter. Use /start.")
        return
    await update.message.reply_text(f"Your current balance is {user_data['won']} won.")

async def bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = users.get(user_id)
    if not user_data:
        await update.message.reply_text("You are not a registered Hunter. Use /start.")
        return

    if user_data['loan_amount'] > 0:
        await update.message.reply_text("You already have an outstanding loan. Use /myloan to check it.")
        return

    kb = [
        [InlineKeyboardButton(f"Take Loan: {offer['amount']} won ({offer['interest']}% interest)", callback_data=f"take_loan_{offer['amount']}_{offer['interest']}")]
        for offer in LOAN_OFFERS
    ]
    await update.message.reply_text("💰 **Bank Loan Offers**\n\nChoose an offer to take a loan:", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def myloan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = users.get(user_id)
    if not user_data:
        await update.message.reply_text("You are not a registered Hunter. Use /start.")
        return
    
    if user_data['loan_amount'] > 0:
        await update.message.reply_text(
            f"You have an outstanding loan of **{user_data['loan_amount']} won** at **{user_data['loan_interest']}%** interest."
            f"\n\nTo repay, use /repay <amount>.", parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("You have no outstanding loans.")

async def take_loan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split('_')
    amount = int(data[2])
    interest = int(data[3])
    
    user_id = query.from_user.id
    user_data = users.get(user_id)
    
    user_data['loan_amount'] = amount + (amount * interest / 100)
    user_data['loan_interest'] = interest
    user_data['won'] += amount
    save_user_data()
    
    await query.edit_message_text(f"✅ Loan of {amount} won taken! Your new balance is {user_data['won']} won.")

async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_user = update.effective_user
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user

    user_data = users.get(target_user.id)
    if not user_data:
        await update.message.reply_text("User is not registered.")
        return
    await update.message.reply_text(f"{user_data.get('full_name', target_user.full_name)}'s current rank is {user_data.get('rank', 'E')}.")

async def level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_user = update.effective_user
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user

    user_data = users.get(target_user.id)
    if not user_data:
        await update.message.reply_text("User is not registered.")
        return
    await update.message.reply_text(f"{user_data.get('full_name', target_user.full_name)}'s current level is {user_data.get('level', 0)}.")

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

async def inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = users.get(update.effective_user.id)
    if not user_data:
        await update.message.reply_text("You are not a registered Hunter. Use /start.")
        return

    if not user_data["inventory"]:
        await update.message.reply_text("Your inventory is empty.")
        return

    item_counts = {}
    for item in user_data["inventory"]:
        item_counts[item] = item_counts.get(item, 0) + 1

    inventory_msg = "**Your Inventory:**\n\n"
    for item, count in item_counts.items():
        inventory_msg += f"• {item} (x{count})\n"

    await update.message.reply_markdown(inventory_msg)

async def swords(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = users.get(update.effective_user.id)
    if not user_data:
        await update.message.reply_text("You are not a registered Hunter. Use /start.")
        return
    
    sword_list = [item for item in user_data['inventory'] if any(sword['name'] == item for sword in SHOP_ITEMS['swords'])]
    
    if not sword_list:
        await update.message.reply_text("You have no swords in your inventory.")
        return
        
    swords_msg = "**Your Swords:**\n\n"
    for sword in sword_list:
        swords_msg += f"• {sword}\n"
    
    await update.message.reply_markdown(swords_msg)

async def revivalitem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = users.get(update.effective_user.id)
    if not user_data:
        await update.message.reply_text("You are not a registered Hunter. Use /start.")
        return
    
    revival_list = [item for item in user_data['inventory'] if any(revival['name'] == item for revival in SHOP_ITEMS['revival'])]
    
    if not revival_list:
        await update.message.reply_text("You have no revival items in your inventory.")
        return
        
    revival_msg = "**Your Revival Items:**\n\n"
    for item in revival_list:
        revival_msg += f"• {item}\n"
    
    await update.message.reply_markdown(revival_msg)

async def dailytask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = users.get(update.effective_user.id)
    if not user_data:
        await update.message.reply_text("You are not a registered Hunter. Use /start.")
        return
    
    import datetime
    today = datetime.date.today().isoformat()
    
    if user_data.get('daily_task_date') == today:
        await update.message.reply_text("You have already received your daily tasks for today.")
        return

    tasks = random.sample(DAILY_TASKS, 3)
    user_data['daily_tasks'] = tasks
    user_data['daily_task_date'] = today
    save_user_data()

    task_msg = "**Daily Tasks:**\n\n"
    for i, task in enumerate(tasks):
        task_msg += f"{i+1}. {task['task']}\n"
    task_msg += "\nComplete these tasks to claim your reward with /taskreward."
    
    await update.message.reply_markdown(task_msg)

async def taskreward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = users.get(update.effective_user.id)
    if not user_data:
        await update.message.reply_text("You are not a registered Hunter. Use /start.")
        return

    import datetime
    today = datetime.date.today().isoformat()
    if user_data.get('daily_task_date') != today:
        await update.message.reply_text("You have not received your daily tasks yet. Use /dailytask.")
        return

    if user_data.get('daily_tasks_done') >= len(user_data.get('daily_tasks', [])):
        await update.message.reply_text("You have already completed your tasks for today.")
        return
    
    # Simple logic: assume tasks are completed. You'll need to add a check for task completion later
    
    reward_type = random.choice(["won", "keys", "revival_item"])
    reward_value = 0
    reward_msg = ""
    
    if reward_type == "won":
        reward_value = 5000
        user_data['won'] += reward_value
        reward_msg = f"🎉 You completed your task and received {reward_value} won!"
    elif reward_type == "keys":
        reward_value = 1
        user_data['inventory'].append("Hunter Key")
        reward_msg = f"🎉 You completed your task and received a Hunter Key!"
    elif reward_type == "revival_item":
        reward_value = "Revival Potion"
        user_data['inventory'].append("Revival Potion")
        reward_msg = f"🎉 You completed your task and received a Revival Potion!"
    
    user_data['daily_tasks_done'] += 1
    save_user_data()
    await update.message.reply_text(reward_msg)

async def tophunters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sorted_hunters = sorted(users.values(), key=lambda x: x.get('pvp_points', 0), reverse=True)
    top_10 = sorted_hunters[:10]
    
    msg = "**🏆 Top 10 High Rank Hunters (Global)**\n\n"
    for i, hunter in enumerate(top_10):
        msg += f"{i+1}. {hunter['full_name']} (Rank: {hunter['rank']}, PvP Points: {hunter['pvp_points']})\n"
        
    await update.message.reply_markdown(msg)

async def globleleader(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sorted_hunters = sorted(users.values(), key=lambda x: (x.get('level', 0), x.get('won', 0)), reverse=True)
    top_10 = sorted_hunters[:10]
    
    msg = "**🌐 Global Leaders (Level & Won)**\n\n"
    for i, hunter in enumerate(top_10):
        msg += f"{i+1}. {hunter['full_name']} (Level: {hunter['level']}, Won: {hunter['won']})\n"
        
    await update.message.reply_markdown(msg)

async def localleader(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_members_ids = [member.user.id for member in await context.bot.get_chat_members_count(chat_id)]
    
    local_users = [users.get(uid) for uid in chat_members_ids if uid in users]
    
    sorted_local_users = sorted(local_users, key=lambda x: (x.get('level', 0), x.get('won', 0)), reverse=True)
    top_10 = sorted_local_users[:10]
    
    msg = f"**👥 Local Leaders for this Group**\n\n"
    for i, user in enumerate(top_10):
        msg += f"{i+1}. {user['full_name']} (Level: {user['level']}, Won: {user['won']})\n"
    
    await update.message.reply_markdown(msg)
    
async def wongive(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = users.get(user_id)
    if not user_data:
        await update.message.reply_text("You are not a registered Hunter. Use /start.")
        return

    # A simple example of title based on rank
    user_rank = user_data['rank']
    if user_rank == "A":
        title_name = "Elite Hunter"
    elif user_rank.startswith("S"):
        title_name = "S-Rank Hunter"
    elif user_rank.startswith("SJP"):
        title_name = "Shadow Monarch"
    else:
        title_name = "Apprentice"
    
    await update.message.reply_text(f"Your current title is: **{title_name}**", parse_mode="Markdown")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "**Available Commands:**\n\n"
        "/start - Register as a Hunter.\n"
        "/profile - View your profile or another user's profile.\n"
        "/status - Check your strength and rank progression.\n"
        "/pvp - Challenge another user to a PvP battle (reply to them).\n"
        "/pvpbot - Challenge a bot to a PvP battle.\n"
        "/won - Check your current won balance.\n"
        "/bank - View loan offers.\n"
        "/myloan - Check your outstanding loan.\n"
        "/rank - View your rank or another user's rank.\n"
        "/level - View your level or another user's level.\n"
        "/shop - Open the shop.\n"
        "/buy <item_id> - Buy an item from the shop.\n"
        "/inventory - View your inventory.\n"
        "/swords - Check your sword inventory.\n"
        "/revivalitem - Check your revival item inventory.\n"
        "/dailytask - Get your daily tasks.\n"
        "/taskreward - Claim your task rewards.\n"
        "/tophunters - See the top-ranked Hunters globally.\n"
        "/globleleader - See the global leaders in level and won.\n"
        "/localleader - See the local leaders in this group.\n"
        "/wongive - Give won to another user (reply to them).\n"
        "/title - View your current title.\n"
        "/help - View this help message.\n"
        "/guide - Get a guide on how the bot works.\n"
        "/owner - Contact the bot owner."
    )
    await update.message.reply_markdown(help_text)

async def guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    guide_text = (
        "**Solo Leveling Bot Guide**\n\n"
        "Welcome to the world of Hunters! Here's how to play:\n\n"
        "1.  **Start Your Journey:** Use `/start` to become a hunter. You will begin at Level 0, Rank E.\n\n"
        "2.  **Gain Power:** Engage in PvP battles with other users or the bot using `/pvp` and `/pvpbot`. Winning battles earns you XP to level up and PvP points to increase your rank.\n\n"
        "3.  **Rank Up:** Your rank progresses from E to SJP100. At certain ranks (S20, S40, S60, S80, S100), you will face special boss battles against powerful hunters from the Solo Leveling anime. Winning these battles gives you their unique abilities as permanent items!\n\n"
        "4.  **Manage Resources:** Use `/won` to check your currency. You can buy items from the `/shop` and view your belongings with `/inventory`.\n\n"
        "5.  **PvP Combat:** Battles are turn-based and happen in a single message. You can choose to Attack, Defend, or use items. The outcome depends on your strength, luck, and the items you use."
    )
    await update.message.reply_markdown(guide_text)

async def owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"You can contact the owner, Nightking, on Telegram @Nightking1515. His user ID is {OWNER_ID}.")

# --- PvP Conversation Handler ---
async def pvp_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to a user to start PvP.")
        return ConversationHandler.END
    
    challenger = update.effective_user
    opponent = update.message.reply_to_message.from_user
    
    if challenger.id == opponent.id:
        await update.message.reply_text("You cannot challenge yourself!")
        return ConversationHandler.END

    if update.effective_chat.id in FIGHT_STATE and FIGHT_STATE[update.effective_chat.id]["in_progress"]:
        await update.message.reply_text("A fight is already in progress in this chat!")
        return ConversationHandler.END

    FIGHT_STATE[update.effective_chat.id] = {
        "fighter1": {"id": challenger.id, "name": challenger.full_name, "hp": 100},
        "fighter2": {"id": opponent.id, "name": opponent.full_name, "hp": 100},
        "turn": challenger.id,
        "is_bot_fight": False,
        "in_progress": True,
        "message_id": None,
        "is_special_battle": False,
        "special_hunter": None
    }
    
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("Yes", callback_data="pvp_accept"), InlineKeyboardButton("No", callback_data="pvp_decline")]])
    await update.message.reply_text(
        f"⚔️ {challenger.full_name} has challenged {opponent.full_name} to a PvP battle!\n"
        f"Hey {opponent.full_name}, do you accept?", reply_markup=kb
    )
    return START_PVP

async def pvp_bot_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    challenger = update.effective_user
    user_data = users.get(challenger.id)
    if not user_data:
        await update.message.reply_text("You are not a registered Hunter. Use /start.")
        return ConversationHandler.END

    if update.effective_chat.id in FIGHT_STATE and FIGHT_STATE[update.effective_chat.id]["in_progress"]:
        await update.message.reply_text("A fight is already in progress in this chat!")
        return ConversationHandler.END
    
    is_special = False
    special_name = "EvilBot"
    
    user_rank = user_data["rank"]
    if user_rank in SPECIAL_HUNTERS.values():
        await update.message.reply_text("You have a special Hunter battle coming up soon! You can only challenge the Hunter corresponding to your rank.")
        return ConversationHandler.END

    if user_rank.startswith("S"):
        rank_num = int(user_rank[1:])
        if rank_num in SPECIAL_HUNTERS:
            is_special = True
            special_name = SPECIAL_HUNTERS[rank_num]
    elif user_rank.startswith("SJP"):
        rank_num = int(user_rank[3:])
        if rank_num in SPECIAL_SHADOWS:
            is_special = True
            special_name = SPECIAL_SHADOWS[rank_num]
    
    FIGHT_STATE[update.effective_chat.id] = {
        "fighter1": {"id": challenger.id, "name": challenger.full_name, "hp": 100, "strength": user_data['strength']},
        "fighter2": {"id": -1, "name": special_name, "hp": BOT_HP, "strength": random.randint(10, 30)},
        "turn": challenger.id,
        "is_bot_fight": True,
        "in_progress": True,
        "message_id": None,
        "is_special_battle": is_special,
        "special_hunter": special_name
    }
    await pvp_turn(update, context)
    return PVP_ACTION

async def pvp_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    if chat_id not in FIGHT_STATE or not FIGHT_STATE[chat_id]["in_progress"]:
        return ConversationHandler.END
    
    state = FIGHT_STATE[chat_id]
    if query.from_user.id != state["fighter2"]["id"]:
        return
        
    if query.data == "pvp_accept":
        await query.edit_message_text("Battle accepted! Let's fight!")
        await pvp_turn(update, context)
        return PVP_ACTION
    else:
        await query.edit_message_text("PvP request declined.")
        FIGHT_STATE[chat_id]["in_progress"] = False
        return ConversationHandler.END

async def pvp_turn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id not in FIGHT_STATE or not FIGHT_STATE[chat_id]["in_progress"]:
        return
    
    state = FIGHT_STATE[chat_id]
    
    current_player_id = state["fighter1"]["id"] if state["turn"] == state["fighter1"]["id"] else state["fighter2"]["id"]
    
    if not state["is_bot_fight"]:
        if update.effective_user.id != current_player_id:
            return
    else:
        # If it's a bot fight, always process the user's action
        pass

    action = update.message.text.lower()
    
    if action == "attack":
        damage = random.randint(10, 25)
        
        target_hp = state["fighter2"]["hp"] if current_player_id == state["fighter1"]["id"] else state["fighter1"]["hp"]
        target_hp -= damage
        
        if current_player_id == state["fighter1"]["id"]:
            state["fighter2"]["hp"] = target_hp
            state["turn"] = state["fighter2"]["id"]
        else:
            state["fighter1"]["hp"] = target_hp
            state["turn"] = state["fighter1"]["id"]
            
        # Check for winner
        if state["fighter1"]["hp"] <= 0 or state["fighter2"]["hp"] <= 0:
            await pvp_end(update, context)
            return ConversationHandler.END

        # Update message
        status_msg = get_battle_status_msg(state)
        
        if state["message_id"]:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=state["message_id"],
                text=status_msg,
                parse_mode="Markdown"
            )
        else:
            msg = await update.message.reply_markdown(status_msg)
            state["message_id"] = msg.message_id
            
    return PVP_ACTION

async def pvp_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    state = FIGHT_STATE[chat_id]
    
    winner = state["fighter1"] if state["fighter1"]["hp"] > 0 else state["fighter2"]
    loser = state["fighter1"] if state["fighter1"]["hp"] <= 0 else state["fighter2"]
    
    is_pvp_bot = state["is_bot_fight"]
    
    if winner["id"] > 0:
        winner_data = users.get(winner["id"])
        if winner_data:
            winner_data["wins"] += 1
            winner_data["won"] += REWARDS["pvp"]["won"] if not is_pvp_bot else REWARDS["pvp_bot"]["won"]
            winner_data["xp"] += REWARDS["pvp"]["xp"] if not is_pvp_bot else REWARDS["pvp_bot"]["xp"]
            winner_data["pvp_points"] += REWARDS["pvp"]["pvp_points"] if not is_pvp_bot else REWARDS["pvp_bot"]["pvp_points"]
            # Check for rank up
            winner_data["rank"] = get_rank_from_points(winner_data["pvp_points"])

    if loser["id"] > 0:
        loser_data = users.get(loser["id"])
        if loser_data:
            loser_data["losses"] += 1
            loser_data["won"] -= PENALTIES["pvp"]["won"] if not is_pvp_bot else PENALTIES["pvp_bot"]["won"]
            loser_data["xp"] += PENALTIES["pvp"]["xp"] if not is_pvp_bot else PENALTIES["pvp_bot"]["xp"]
            loser_data["pvp_points"] -= PENALTIES["pvp"]["pvp_points"] if not is_pvp_bot else PENALTIES["pvp_bot"]["pvp_points"]
            # Check for rank up
            loser_data["rank"] = get_rank_from_points(loser_data["pvp_points"])
            
    save_user_data()
    
    result_msg = (
        f"🎉 **{winner['name']}** wins the battle! 🏆\n\n"
        f"👑 **Victory Rewards**:\n"
        f"- 🧠 XP: +{REWARDS['pvp']['xp'] if not is_pvp_bot else REWARDS['pvp_bot']['xp']}\n"
        f"- 💴 won: +{REWARDS['pvp']['won'] if not is_pvp_bot else REWARDS['pvp_bot']['won']}\n"
        f"- 🎖 pvp points: +{REWARDS['pvp']['pvp_points'] if not is_pvp_bot else REWARDS['pvp_bot']['pvp_points']}\n\n"
        f"💀 **Defeat Penalties** for **{loser['name']}**:\n"
        f"- 🧠 XP: +{PENALTIES['pvp']['xp'] if not is_pvp_bot else PENALTIES['pvp_bot']['xp']}\n"
        f"- 💴 won: -{PENALTIES['pvp']['won'] if not is_pvp_bot else PENALTIES['pvp_bot']['won']}\n"
        f"- 🎖 pvp points: -{PENALTIES['pvp']['pvp_points'] if not is_pvp_bot else PENALTIES['pvp_bot']['pvp_points']}"
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
        f"👉 **Turn**: {state['fighter1']['name'] if state['turn'] == state['fighter1']['id'] else state['fighter2']['name']}! Choose your action: Attack"
    )

# --- Main function ---
def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers for basic commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("won", won_cmd))
    application.add_handler(CommandHandler("bank", bank))
    application.add_handler(CommandHandler("myloan", myloan))
    application.add_handler(CommandHandler("rank", rank))
    application.add_handler(CommandHandler("level", level))
    application.add_handler(CommandHandler("shop", shop))
    application.add_handler(CommandHandler("buy", buy))
    application.add_handler(CommandHandler("inventory", inventory))
    application.add_handler(CommandHandler("swords", swords))
    application.add_handler(CommandHandler("revivalitem", revivalitem))
    application.add_handler(CommandHandler("dailytask", dailytask))
    application.add_handler(CommandHandler("taskreward", taskreward))
    application.add_handler(CommandHandler("tophunters", tophunters))
    application.add_handler(CommandHandler("globleleader", globleleader))
    application.add_handler(CommandHandler("localleader", localleader))
    application.add_handler(CommandHandler("wongive", wongive))
    application.add_handler(CommandHandler("title", title))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("guide", guide))
    application.add_handler(CommandHandler("owner", owner))

    # Handler for callbacks (buttons)
    application.add_handler(CallbackQueryHandler(handle_buy_callback, pattern=r"buy_confirm_|\bbuy_cancel\b"))
    application.add_handler(CallbackQueryHandler(handle_shop_category, pattern=r"shop_"))
    application.add_handler(CallbackQueryHandler(take_loan, pattern=r"take_loan_"))

    # PvP Conversation Handler
    pvp_handler = ConversationHandler(
        entry_points=[CommandHandler("pvp", pvp_start), CommandHandler("pvpbot", pvp_bot_start)],
        states={
            START_PVP: [CallbackQueryHandler(pvp_accept, pattern=r"pvp_accept|pvp_decline")],
            PVP_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, pvp_turn)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
    )
    application.add_handler(pvp_handler)

    application.run_polling()

if __name__ == "__main__":
    main()
