import logging
import sqlite3
import random
import os 
from datetime import datetime
from threading import Lock
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

load_dotenv()
BOT_TOKEN ="8050711631:AAEOmQtI1LDg8F5zBST1tIPh0mDtHbIISEs"
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "@Nightking1515")
DATA_FILE = os.getenv("DATA_FILE", "users.json")
# If you later want a separate shop file, change here. For now shop is embedded.
# Persistent write lock
_file_lock = Lock()

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set. Put it into environment or .env file (BOT_TOKEN=...)")

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('solo_leveling_bot.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        level INTEGER DEFAULT 0,
        rank TEXT DEFAULT 'E',
        balance INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0,
        losses INTEGER DEFAULT 0,
        strength INTEGER DEFAULT 10,
        health INTEGER DEFAULT 100,
        pvp_points INTEGER DEFAULT 0,
        registered_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Inventory table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item_id INTEGER,
        item_name TEXT,
        item_type TEXT,
        quantity INTEGER DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')
    
    # PvP requests table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pvp_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_user_id INTEGER,
        to_user_id INTEGER,
        chat_id INTEGER,
        status TEXT DEFAULT 'pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (from_user_id) REFERENCES users (user_id),
        FOREIGN KEY (to_user_id) REFERENCES users (user_id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Shop items
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
        {"id": 24, "name": "God's Blessing", "price": 9000, "effect": "Auto Revive once"},
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

# Rank system
RANKS = ["E", "D", "C", "B", "A"] + [f"S{i}" for i in range(1, 101)] + [f"SJ{i}" for i in range(1, 101)]
RANK_THRESHOLDS = {rank: i * 100 for i, rank in enumerate(RANKS)}

# Helper functions
def get_user(user_id):
    conn = sqlite3.connect('solo_leveling_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def register_user(user_id, username, first_name, last_name):
    conn = sqlite3.connect('solo_leveling_bot.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
        (user_id, username, first_name, last_name)
    )
    conn.commit()
    conn.close()

def update_user(user_id, **kwargs):
    conn = sqlite3.connect('solo_leveling_bot.db')
    cursor = conn.cursor()
    set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
    values = list(kwargs.values()) + [user_id]
    cursor.execute(f"UPDATE users SET {set_clause} WHERE user_id = ?", values)
    conn.commit()
    conn.close()

def get_user_inventory(user_id):
    conn = sqlite3.connect('solo_leveling_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory WHERE user_id = ?", (user_id,))
    inventory = cursor.fetchall()
    conn.close()
    return inventory

def add_to_inventory(user_id, item_id, item_name, item_type):
    conn = sqlite3.connect('solo_leveling_bot.db')
    cursor = conn.cursor()
    
    # Check if item already exists
    cursor.execute(
        "SELECT * FROM inventory WHERE user_id = ? AND item_id = ?",
        (user_id, item_id)
    )
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute(
            "UPDATE inventory SET quantity = quantity + 1 WHERE user_id = ? AND item_id = ?",
            (user_id, item_id)
        )
    else:
        cursor.execute(
            "INSERT INTO inventory (user_id, item_id, item_name, item_type) VALUES (?, ?, ?, ?)",
            (user_id, item_id, item_name, item_type)
        )
    
    conn.commit()
    conn.close()

def remove_from_inventory(user_id, item_id):
    conn = sqlite3.connect('solo_leveling_bot.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT quantity FROM inventory WHERE user_id = ? AND item_id = ?",
        (user_id, item_id)
    )
    item = cursor.fetchone()
    
    if item and item[0] > 1:
        cursor.execute(
            "UPDATE inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_id = ?",
            (user_id, item_id)
        )
    else:
        cursor.execute(
            "DELETE FROM inventory WHERE user_id = ? AND item_id = ?",
            (user_id, item_id)
        )
    
    conn.commit()
    conn.close()

def create_pvp_request(from_user_id, to_user_id, chat_id):
    conn = sqlite3.connect('solo_leveling_bot.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO pvp_requests (from_user_id, to_user_id, chat_id) VALUES (?, ?, ?)",
        (from_user_id, to_user_id, chat_id)
    )
    conn.commit()
    conn.close()

def get_pvp_request(from_user_id, to_user_id):
    conn = sqlite3.connect('solo_leveling_bot.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM pvp_requests WHERE from_user_id = ? AND to_user_id = ? AND status = 'pending'",
        (from_user_id, to_user_id)
    )
    request = cursor.fetchone()
    conn.close()
    return request

def update_pvp_request(request_id, status):
    conn = sqlite3.connect('solo_leveling_bot.db')
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE pvp_requests SET status = ? WHERE id = ?",
        (status, request_id)
    )
    conn.commit()
    conn.close()

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id, user.username, user.first_name, user.last_name)
    
    welcome_text = (
        f"Welcome {user.first_name} to the Solo Leveling Hunter Bot! 🎯\n\n"
        "You are now registered as an E-Rank Hunter. "
        "Complete quests, defeat monsters, and rise through the ranks to become the strongest hunter!\n\n"
        "Use /help to see all available commands."
    )
    
    await update.message.reply_text(welcome_text)

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    target_user = user
    
    # Check if replying to another user
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    
    db_user = get_user(target_user.id)
    
    if not db_user:
        await update.message.reply_text("User not found!")
        return
    
    user_id, username, first_name, last_name, level, rank, balance, wins, losses, strength, health, pvp_points, registered_at = db_user
    
    inventory = get_user_inventory(target_user.id)
    item_count = sum(item[5] for item in inventory) if inventory else 0
    
    profile_text = (
        f"🏆 {first_name}'s Hunter Profile 🏆\n\n"
        f"⭐ Level: {level}\n"
        f"🎖️ Rank: {rank}\n"
        f"💰 Balance: {balance} won\n"
        f"⚔️ Strength: {strength}\n"
        f"❤️ Health: {health}\n"
        f"🏅 PvP Points: {pvp_points}\n"
        f"✅ Wins: {wins}\n"
        f"❌ Losses: {losses}\n"
        f"🎒 Items: {item_count}\n"
        f"📅 Registered: {registered_at.split()[0]}"
    )
    
    await update.message.reply_text(profile_text)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = get_user(user.id)
    
    if not db_user:
        await update.message.reply_text("You are not registered! Use /start to register.")
        return
    
    user_id, username, first_name, last_name, level, rank, balance, wins, losses, strength, health, pvp_points, registered_at = db_user
    
    current_rank_index = RANKS.index(rank) if rank in RANKS else 0
    next_rank = RANKS[current_rank_index + 1] if current_rank_index + 1 < len(RANKS) else "MAX"
    
    points_needed = 0
    if next_rank != "MAX":
        points_needed = RANK_THRESHOLDS.get(next_rank, 0) - pvp_points
    
    status_text = (
        f"📊 {first_name}'s Status 📊\n\n"
        f"💪 Strength: {strength}\n"
        f"❤️ Health: {health}\n"
        f"🎖️ Current Rank: {rank}\n"
        f"🎯 Next Rank: {next_rank}\n"
        f"🔺 PvP Points Needed: {points_needed}\n"
        f"🏅 Current PvP Points: {pvp_points}"
    )
    
    await update.message.reply_text(status_text)

async def pvp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if not update.message.reply_to_message:
        await update.message.reply_text("You need to reply to a user's message to challenge them!")
        return
    
    target_user = update.message.reply_to_message.from_user
    
    if user.id == target_user.id:
        await update.message.reply_text("You cannot challenge yourself!")
        return
    
    # Check if both users are registered
    if not get_user(user.id) or not get_user(target_user.id):
        await update.message.reply_text("Both users need to be registered with /start first!")
        return
    
    # Create PvP request
    create_pvp_request(user.id, target_user.id, update.message.chat_id)
    
    keyboard = [
        [InlineKeyboardButton("Accept Challenge", callback_data=f"pvp_accept_{user.id}")],
        [InlineKeyboardButton("Decline Challenge", callback_data=f"pvp_decline_{user.id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"⚔️ {user.first_name} has challenged {target_user.first_name} to a PvP battle!\n"
        f"{target_user.first_name}, do you accept?",
        reply_markup=reply_markup
    )

async def pvpbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = get_user(user.id)
    
    if not db_user:
        await update.message.reply_text("You are not registered! Use /start to register.")
        return
    
    user_id, username, first_name, last_name, level, rank, balance, wins, losses, strength, health, pvp_points, registered_at = db_user
    
    # Simulate battle with bot
    bot_strength = random.randint(5, 20) + level * 2
    user_strength = strength
    
    if user_strength > bot_strength:
        # User wins
        won_amount = random.randint(50, 200)
        xp_gained = random.randint(20, 50)
        pvp_gained = random.randint(5, 15)
        
        update_user(user.id, wins=wins+1, balance=balance+won_amount, level=level+xp_gained, pvp_points=pvp_points+pvp_gained)
        
        await update.message.reply_text(
            f"🎉 {first_name} wins the battle against the Bot! 🏆\n\n"
            f"👑 Victory Rewards:\n"
            f"- 🧠 XP: +{xp_gained}\n"
            f"- 💴 won: +{won_amount}\n"
            f"- 🎖 PvP Points: +{pvp_gained}"
        )
    else:
        # User loses
        lost_amount = random.randint(10, 50)
        xp_gained = random.randint(5, 15)
        pvp_lost = random.randint(1, 5)
        
        update_user(user.id, losses=losses+1, balance=max(0, balance-lost_amount), 
                   level=level+xp_gained, pvp_points=max(0, pvp_points-pvp_lost))
        
        await update.message.reply_text(
            f"💀 {first_name} was defeated by the Bot!\n\n"
            f"💀 Defeat Penalties:\n"
            f"- 🧠 XP: +{xp_gained}\n"
            f"- 💴 won: -{lost_amount}\n"
            f"- 🎖 PvP Points: -{pvp_lost}"
        )

async def won(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = get_user(user.id)
    
    if not db_user:
        await update.message.reply_text("You are not registered! Use /start to register.")
        return
    
    user_id, username, first_name, last_name, level, rank, balance, wins, losses, strength, health, pvp_points, registered_at = db_user
    
    await update.message.reply_text(f"💰 Your current balance: {balance} won")

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("All Items", callback_data="shop_all")],
        [InlineKeyboardButton("Swords", callback_data="shop_swords")],
        [InlineKeyboardButton("Revival Items", callback_data="shop_revival")],
        [InlineKeyboardButton("Special Items", callback_data="shop_special")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🛒 Welcome to the Hunter Shop! 🛒\n\n"
        "Choose a category to browse:",
        reply_markup=reply_markup
    )

async def inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    inventory = get_user_inventory(user.id)
    
    if not inventory:
        await update.message.reply_text("Your inventory is empty!")
        return
    
    inventory_text = "🎒 Your Inventory:\n\n"
    for item in inventory:
        item_id, user_id, item_id_db, item_name, item_type, quantity = item
        inventory_text += f"• {item_name} x{quantity} ({item_type})\n"
    
    await update.message.reply_text(inventory_text)

async def swards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    inventory = get_user_inventory(user.id)
    
    if not inventory:
        await update.message.reply_text("You don't have any swords!")
        return
    
    swords = [item for item in inventory if item[4] == "sword"]
    
    if not swords:
        await update.message.reply_text("You don't have any swords!")
        return
    
    swords_text = "⚔️ Your Swords:\n\n"
    for sword in swords:
        item_id, user_id, item_id_db, item_name, item_type, quantity = sword
        sword_item = next((item for category in SHOP_ITEMS.values() for item in category if item["id"] == item_id_db), None)
        damage = sword_item.get("damage", 0) if sword_item else 0
        swords_text += f"• {item_name} x{quantity} (Damage: +{damage})\n"
    
    await update.message.reply_text(swords_text)

async def revivalitem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    inventory = get_user_inventory(user.id)
    
    if not inventory:
        await update.message.reply_text("You don't have any revival items!")
        return
    
    revival_items = [item for item in inventory if item[4] == "revival"]
    
    if not revival_items:
        await update.message.reply_text("You don't have any revival items!")
        return
    
    revival_text = "💊 Your Revival Items:\n\n"
    for item in revival_items:
        item_id, user_id, item_id_db, item_name, item_type, quantity = item
        revival_item = next((item for category in SHOP_ITEMS.values() for item in category if item["id"] == item_id_db), None)
        effect = revival_item.get("effect", "No effect") if revival_item else "No effect"
        revival_text += f"• {item_name} x{quantity} ({effect})\n"
    
    await update.message.reply_text(revival_text)

async def dailytask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    tasks = [
        "Defeat 5 monsters in dungeons",
        "Complete 3 PvP battles",
        "Collect 10 rare items",
        "Reach 1000 steps in the hunter gym",
        "Help 3 fellow hunters"
    ]
    
    daily_tasks = random.sample(tasks, 3)
    
    tasks_text = "📋 Your Daily Tasks:\n\n"
    for i, task in enumerate(daily_tasks, 1):
        tasks_text += f"{i}. {task}\n"
    
    tasks_text += "\nComplete these tasks and use /taskreward to claim your rewards!"
    
    await update.message.reply_text(tasks_text)

async def taskreward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = get_user(user.id)
    
    if not db_user:
        await update.message.reply_text("You are not registered! Use /start to register.")
        return
    
    user_id, username, first_name, last_name, level, rank, balance, wins, losses, strength, health, pvp_points, registered_at = db_user
    
    # Random rewards
    reward_type = random.choice(["revival", "won", "key"])
    
    if reward_type == "revival":
        revival_items = SHOP_ITEMS["revival"]
        reward_item = random.choice(revival_items)
        add_to_inventory(user.id, reward_item["id"], reward_item["name"], "revival")
        reward_text = f"🎁 You received: {reward_item['name']}!"
    elif reward_type == "won":
        won_amount = random.randint(100, 500)
        update_user(user.id, balance=balance+won_amount)
        reward_text = f"🎁 You received: {won_amount} won!"
    else:  # key
        key_items = [item for item in SHOP_ITEMS["special"] if "key" in item["name"].lower()]
        reward_item = random.choice(key_items) if key_items else {"name": "Hunter Key", "id": 36}
        add_to_inventory(user.id, reward_item["id"], reward_item["name"], "special")
        reward_text = f"🎁 You received: {reward_item['name']}!"
    
    await update.message.reply_text(
        f"✅ Daily Task Completed!\n\n"
        f"{reward_text}\n\n"
        f"Check your inventory with /inventory"
    )

async def tophunters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('solo_leveling_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT first_name, rank, pvp_points FROM users ORDER BY pvp_points DESC LIMIT 10")
    top_hunters = cursor.fetchall()
    conn.close()
    
    if not top_hunters:
        await update.message.reply_text("No hunters ranked yet!")
        return
    
    hunters_text = "🏆 Top Hunters by Rank 🏆\n\n"
    for i, (name, rank, points) in enumerate(top_hunters, 1):
        hunters_text += f"{i}. {name} - {rank} ({points} points)\n"
    
    await update.message.reply_text(hunters_text)

async def globleleader(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('solo_leveling_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT first_name, level, balance FROM users ORDER BY level DESC, balance DESC LIMIT 10")
    leaders = cursor.fetchall()
    conn.close()
    
    if not leaders:
        await update.message.reply_text("No leaders yet!")
        return
    
    leaders_text = "🌍 Global Leaders 🌍\n\n"
    for i, (name, level, balance) in enumerate(leaders, 1):
        leaders_text += f"{i}. {name} - Level {level} ({balance} won)\n"
    
    await update.message.reply_text(leaders_text)

async def localleader(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # For simplicity, we'll just show top users by level
    # In a real implementation, you might filter by chat group
    conn = sqlite3.connect('solo_leveling_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT first_name, level, balance FROM users ORDER BY level DESC, balance DESC LIMIT 10")
    leaders = cursor.fetchall()
    conn.close()
    
    if not leaders:
        await update.message.reply_text("No local leaders yet!")
        return
    
    leaders_text = "📍 Local Leaders 📍\n\n"
    for i, (name, level, balance) in enumerate(leaders, 1):
        leaders_text += f"{i}. {name} - Level {level} ({balance} won)\n"
    
    await update.message.reply_text(leaders_text)

async def wongive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if not update.message.reply_to_message:
        await update.message.reply_text("You need to reply to a user's message to give them won!")
        return
    
    target_user = update.message.reply_to_message.from_user
    
    if user.id == target_user.id:
        await update.message.reply_text("You cannot give won to yourself!")
        return
    
    # Check if both users are registered
    user_db = get_user(user.id)
    target_db = get_user(target_user.id)
    
    if not user_db or not target_db:
        await update.message.reply_text("Both users need to be registered with /start first!")
        return
    
    user_id, username, first_name, last_name, level, rank, balance, wins, losses, strength, health, pvp_points, registered_at = user_db
    target_id, target_username, target_first_name, target_last_name, target_level, target_rank, target_balance, target_wins, target_losses, target_strength, target_health, target_pvp_points, target_registered_at = target_db
    
    # Check amount to give
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /wongive <amount> (as a reply to the user you want to give to)")
        return
    
    amount = int(context.args[0])
    
    if amount <= 0:
        await update.message.reply_text("Amount must be positive!")
        return
    
    if balance < amount:
        await update.message.reply_text("You don't have enough won!")
        return
    
    # Transfer won
    update_user(user.id, balance=balance-amount)
    update_user(target_user.id, balance=target_balance+amount)
    
    await update.message.reply_text(
        f"✅ {first_name} gave {amount} won to {target_first_name}!\n\n"
        f"Your new balance: {balance-amount} won"
    )

async def title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = get_user(user.id)
    
    if not db_user:
        await update.message.reply_text("You are not registered! Use /start to register.")
        return
    
    user_id, username, first_name, last_name, level, rank, balance, wins, losses, strength, health, pvp_points, registered_at = db_user
    
    # Determine title based on rank
    if rank.startswith("SJ"):
        title_text = "Shadow Monarch"
    elif rank.startswith("S"):
        title_text = "S-Rank Hunter"
    elif rank in ["A", "B"]:
        title_text = "Elite Hunter"
    elif rank == "C":
        title_text = "Experienced Hunter"
    elif rank == "D":
        title_text = "Junior Hunter"
    else:  # E
        title_text = "Beginner Hunter"
    
    await update.message.reply_text(
        f"🏅 {first_name}'s Title: {title_text}\n\n"
        f"Your current rank: {rank}\n"
        f"Keep leveling up to earn more prestigious titles!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🆘 Solo Leveling Bot Help 🆘\n\n"
        "Available Commands:\n"
        "/start - Register as a hunter\n"
        "/profile - View your or another user's profile (reply to user)\n"
        "/status - Check your strength and rank progress\n"
        "/pvp - Challenge another user to a battle (reply to user)\n"
        "/pvpbot - Battle against the bot\n"
        "/won - Check your won balance\n"
        "/shop - Browse the hunter shop\n"
        "/inventory - Check your items\n"
        "/swards - View your swords\n"
        "/revivalitem - View your revival items\n"
        "/dailytask - Get your daily tasks\n"
        "/taskreward - Claim task rewards\n"
        "/tophunters - View top hunters by rank\n"
        "/globleleader - View global leaders\n"
        "/localleader - View local leaders\n"
        "/wongive - Give won to another user (reply to user)\n"
        "/title - Check your hunter title\n"
        "/help - Show this help message\n"
        "/guide - Learn how to use the bot\n"
        "/owner - Contact the bot owner\n"
    )
    
    await update.message.reply_text(help_text)

async def guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    guide_text = (
        "📖 Solo Leveling Bot Guide 📖\n\n"
        "1. Start with /start to register as a hunter\n"
        "2. Use /pvpbot to battle against the bot and earn rewards\n"
        "3. Challenge other hunters with /pvp (reply to their message)\n"
        "4. Earn won (currency) from battles\n"
        "5. Buy items from the /shop to strengthen your hunter\n"
        "6. Complete /dailytask and claim rewards with /taskreward\n"
        "7. Rise through the ranks from E to SJ100!\n\n"
        "Rank System:\n"
        "E → D → C → B → A → S1 → S2 → ... → S100 → SJ1 → SJ2 → ... → SJ100\n\n"
        "The higher your rank, the more powerful you become!"
    )
    
    await update.message.reply_text(guide_text)

async def owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👑 Bot Owner: @Nightking1515\n\n"
        "For questions, suggestions, or issues with the bot, please contact the owner."
    )

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = get_user(user.id)
    
    if not db_user:
        await update.message.reply_text("You are not registered! Use /start to register.")
        return
    
    user_id, username, first_name, last_name, level, rank, balance, wins, losses, strength, health, pvp_points, registered_at = db_user
    
    if not context.args:
        await update.message.reply_text("Usage: /buy <item_id>")
        return
    
    item_id = context.args[0]
    
    # Find the item
    item = None
    for category in SHOP_ITEMS.values():
        for shop_item in category:
            if str(shop_item["id"]) == item_id:
                item = shop_item
                break
        if item:
            break
    
    if not item:
        await update.message.reply_text("Item not found!")
        return
    
    if balance < item["price"]:
        await update.message.reply_text("You don't have enough won to buy this item!")
        return
    
    # Create confirmation keyboard
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data=f"buy_confirm_{item_id}")],
        [InlineKeyboardButton("No", callback_data="buy_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    item_type = "sword" if "damage" in item else "revival" if "effect" in item else "special"
    
    item_details = (
        f"🛒 Item Details:\n\n"
        f"📦 Name: {item['name']}\n"
        f"💰 Price: {item['price']} won\n"
    )
    
    if "damage" in item:
        item_details += f"⚔️ Damage: +{item['damage']}\n"
    elif "effect" in item:
        item_details += f"✨ Effect: {item['effect']}\n"
    
    item_details += f"\nDo you want to buy this item?"
    
    await update.message.reply_text(item_details, reply_markup=reply_markup)

async def rank_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    target_user = user
    
    # Check if replying to another user
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    
    db_user = get_user(target_user.id)
    
    if not db_user:
        await update.message.reply_text("User not found!")
        return
    
    user_id, username, first_name, last_name, level, rank, balance, wins, losses, strength, health, pvp_points, registered_at = db_user
    
    await update.message.reply_text(f"🎖️ {first_name}'s Rank: {rank}")

async def level_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    target_user = user
    
    # Check if replying to another user
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    
    db_user = get_user(target_user.id)
    
    if not db_user:
        await update.message.reply_text("User not found!")
        return
    
    user_id, username, first_name, last_name, level, rank, balance, wins, losses, strength, health, pvp_points, registered_at = db_user
    
    await update.message.reply_text(f"⭐ {first_name}'s Level: {level}")

# Callback query handler
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    data = query.data
    
    if data.startswith("shop_"):
        category = data.split("_")[1]
        
        if category == "all":
            items_text = "🛒 All Items 🛒\n\n"
            for category_name, items in SHOP_ITEMS.items():
                items_text += f"📦 {category_name.capitalize()}:\n"
                for item in items:
                    items_text += f"ID: {item['id']} - {item['name']} - {item['price']} won\n"
                items_text += "\n"
            
            await query.edit_message_text(items_text)
        else:
            if category not in SHOP_ITEMS:
                await query.edit_message_text("Category not found!")
                return
            
            items_text = f"🛒 {category.capitalize()} 🛒\n\n"
            for item in SHOP_ITEMS[category]:
                items_text += f"ID: {item['id']} - {item['name']} - {item['price']} won"
                if "damage" in item:
                    items_text += f" (Damage: +{item['damage']})"
                elif "effect" in item:
                    items_text += f" (Effect: {item['effect']})"
                items_text += "\n"
            
            await query.edit_message_text(items_text)
    
    elif data.startswith("pvp_accept_"):
        from_user_id = int(data.split("_")[2])
        pvp_request = get_pvp_request(from_user_id, user.id)
        
        if not pvp_request:
            await query.edit_message_text("PvP request not found or expired!")
            return
        
        # Get both users' data
        from_user_db = get_user(from_user_id)
        to_user_db = get_user(user.id)
        
        if not from_user_db or not to_user_db:
            await query.edit_message_text("One or both users not found!")
            return
        
        from_user_id, from_username, from_first_name, from_last_name, from_level, from_rank, from_balance, from_wins, from_losses, from_strength, from_health, from_pvp_points, from_registered_at = from_user_db
        to_user_id, to_username, to_first_name, to_last_name, to_level, to_rank, to_balance, to_wins, to_losses, to_strength, to_health, to_pvp_points, to_registered_at = to_user_db
        
        # Simulate battle
        from_total_strength = from_strength
        to_total_strength = to_strength
        
        # Add sword bonuses
        from_swords = [item for item in get_user_inventory(from_user_id) if item[4] == "sword"]
        to_swords = [item for item in get_user_inventory(to_user_id) if item[4] == "sword"]
        
        for sword in from_swords:
            sword_item = next((item for category in SHOP_ITEMS.values() for item in category if item["id"] == sword[2]), None)
            if sword_item and "damage" in sword_item:
                from_total_strength += sword_item["damage"] * sword[5]  # damage * quantity
        
        for sword in to_swords:
            sword_item = next((item for category in SHOP_ITEMS.values() for item in category if item["id"] == sword[2]), None)
            if sword_item and "damage" in sword_item:
                to_total_strength += sword_item["damage"] * sword[5]  # damage * quantity
        
        # Determine winner
        from_roll = random.randint(1, from_total_strength)
        to_roll = random.randint(1, to_total_strength)
        
        if from_roll > to_roll:
            # Challenger wins
            won_amount = random.randint(50, 200)
            xp_gained = random.randint(20, 50)
            pvp_gained = random.randint(5, 15)
            
            update_user(from_user_id, wins=from_wins+1, balance=from_balance+won_amount, 
                       level=from_level+xp_gained, pvp_points=from_pvp_points+pvp_gained)
            update_user(to_user_id, losses=to_losses+1, level=to_level+xp_gained//2, 
                       pvp_points=max(0, to_pvp_points-pvp_gained//2))
            
            battle_text = (
                f"🎉 {from_first_name} wins the battle against {to_first_name}! 🏆\n\n"
                f"👑 Victory Rewards for {from_first_name}:\n"
                f"- 🧠 XP: +{xp_gained}\n"
                f"- 💴 won: +{won_amount}\n"
                f"- 🎖 PvP Points: +{pvp_gained}\n\n"
                f"💀 Defeat Penalties for {to_first_name}:\n"
                f"- 🧠 XP: +{xp_gained//2}\n"
                f"- 🎖 PvP Points: -{pvp_gained//2}"
            )
        else:
            # Defender wins
            won_amount = random.randint(50, 200)
            xp_gained = random.randint(20, 50)
            pvp_gained = random.randint(5, 15)
            
            update_user(to_user_id, wins=to_wins+1, balance=to_balance+won_amount, 
                       level=to_level+xp_gained, pvp_points=to_pvp_points+pvp_gained)
            update_user(from_user_id, losses=from_losses+1, level=from_level+xp_gained//2, 
                       pvp_points=max(0, from_pvp_points-pvp_gained//2))
            
            battle_text = (
                f"🎉 {to_first_name} wins the battle against {from_first_name}! 🏆\n\n"
                f"👑 Victory Rewards for {to_first_name}:\n"
                f"- 🧠 XP: +{xp_gained}\n"
                f"- 💴 won: +{won_amount}\n"
                f"- 🎖 PvP Points: +{pvp_gained}\n\n"
                f"💀 Defeat Penalties for {from_first_name}:\n"
                f"- 🧠 XP: +{xp_gained//2}\n"
                f"- 🎖 PvP Points: -{pvp_gained//2}"
            )
        
        await query.edit_message_text(battle_text)
    
    elif data.startswith("pvp_decline_"):
        from_user_id = int(data.split("_")[2])
        await query.edit_message_text("PvP challenge declined!")
    
    elif data.startswith("buy_confirm_"):
        item_id = int(data.split("_")[2])
        db_user = get_user(user.id)
        
        if not db_user:
            await query.edit_message_text("You are not registered!")
            return
        
        user_id, username, first_name, last_name, level, rank, balance, wins, losses, strength, health, pvp_points, registered_at = db_user
        
        # Find the item
        item = None
        for category in SHOP_ITEMS.values():
            for shop_item in category:
                if shop_item["id"] == item_id:
                    item = shop_item
                    break
            if item:
                break
        
        if not item:
            await query.edit_message_text("Item not found!")
            return
        
        if balance < item["price"]:
            await query.edit_message_text("You don't have enough won to buy this item!")
            return
        
        # Buy the item
        item_type = "sword" if "damage" in item else "revival" if "effect" in item else "special"
        add_to_inventory(user.id, item["id"], item["name"], item_type)
        update_user(user.id, balance=balance-item["price"])
        
        await query.edit_message_text(
            f"✅ Purchase Successful!\n\n"
            f"You bought: {item['name']} for {item['price']} won\n"
            f"Remaining balance: {balance-item['price']} won\n\n"
            f"Check your inventory with /inventory"
        )
    
    elif data == "buy_cancel":
        await query.edit_message_text("Purchase cancelled!")

def main():
    # Initialize database
    init_db()
    
    # Create Application
    application = Application.builder().token("YOUR_BOT_TOKEN_HERE").build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("pvp", pvp))
    application.add_handler(CommandHandler("pvpbot", pvpbot))
    application.add_handler(CommandHandler("won", won))
    application.add_handler(CommandHandler("shop", shop))
    application.add_handler(CommandHandler("inventory", inventory))
    application.add_handler(CommandHandler("swards", swards))
    application.add_handler(CommandHandler("revivalitem", revivalitem))
    application.add_handler(CommandHandler("dailytask", dailytask))
    application.add_handler(CommandHandler("taskreward", taskreward))
    application.add_handler(CommandHandler("tophunters", tophunters))
    application.add_handler(CommandHandler("globleleader", globleleader))
    application.add_handler(CommandHandler("localleader", localleader))
    application.add_handler(CommandHandler("wongive", wongive))
    application.add_handler(CommandHandler("title", title))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("guide", guide))
    application.add_handler(CommandHandler("owner", owner))
    application.add_handler(CommandHandler("buy", buy))
    application.add_handler(CommandHandler("rank", rank_cmd))
    application.add_handler(CommandHandler("level", level_cmd))
    
    # Add callback query handler
    application.add_handler(CallbackQueryHandler(button))
    
    # Start the Bot
    application.run_polling()

if __name__ == "__main__":
    main()
