# main.py
"""
Solo Leveling Telegram Bot - single-file implementation
- Persistent JSON storage in 'users.json' (auto-created)
- Embedded SHOP_ITEMS (50 items you provided)
- Commands: /start, /profile, /status, /shop, /buy, /inventory, /pvp, /pvpbot, /wongive, /tophunters, /globleleader, /localleader, /help, /guide, /owner
- Additional stubs: /bank, /myloan, /rank, /level, /swards, /revivalitem, /dailytask, /taskreward, /title
Notes:
- Ensure BOT_TOKEN is set in environment or .env file.
- To run: pip install python-telegram-bot python-dotenv, then `python main.py`
"""

import os
import json
import uuid
import logging
from datetime import datetime, timedelta
from functools import wraps
from threading import Lock

from dotenv import load_dotenv

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

# ---------------------------
# Configuration & Constants
# ---------------------------
load_dotenv()
BOT_TOKEN ="8050711631:AAEOmQtI1LDg8F5zBST1tIPh0mDtHbIISEs"
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "@Nightking1515")
DATA_FILE = os.getenv("DATA_FILE", "users.json")
# If you later want a separate shop file, change here. For now shop is embedded.
# Persistent write lock
_file_lock = Lock()

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set. Put it into environment or .env file (BOT_TOKEN=...)")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("solo-bot")

# ---------------------------
# Embedded Shop Items (50)
# ---------------------------
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
    {"id": 15, "name": "Excalibur", "price": 15000, "damage": 400}
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
    {"id": 25, "name": "Immortal Charm", "price": 12000, "effect": "Revive + Invincible 1 turn"}
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
    {"id": 35, "name": "Plague Bomb", "price": 9000, "damage": 220}
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
    {"id": 50, "name": "Time Relic", "price": 10000, "effect": "Take extra turn"}
  ]
}

# Build ITEM_INDEX for lookups
ITEM_INDEX = {}
for cat, arr in SHOP_ITEMS.items():
    for it in arr:
        it_copy = dict(it)
        it_copy["category"] = cat
        ITEM_INDEX[it["id"]] = it_copy

# ---------------------------
# Persistence helpers (users.json)
# ---------------------------
def _ensure_datafile():
    with _file_lock:
        if not os.path.exists(DATA_FILE):
            base = {
                "users": {},
                "user_items": {},
                "battles": {},
                "loans": {},
                "daily_tasks": {},
                "config": {
                    "pvp_rewards": {
                        "xp_win": 100000,
                        "won_win": 1000000,
                        "pvp_points_win": 22,
                        "xp_lose": 500,
                        "won_lose": -100000,
                        "pvp_points_lose": -26
                    }
                }
            }
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(base, f, indent=2)

def read_data():
    _ensure_datafile()
    with _file_lock:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

def write_data(data):
    with _file_lock:
        tmp = DATA_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, DATA_FILE)

# ---------------------------
# Utility functions
# ---------------------------
def format_money(n):
    return f"{n:,}"

def ensure_user(data, tg_user):
    users = data.setdefault("users", {})
    uid = str(tg_user.id)
    if uid not in users:
        users[uid] = {
            "id": tg_user.id,
            "username": tg_user.username or "",
            "first_name": tg_user.first_name or "",
            "level": 0,
            "xp": 0,
            "rank": "E",
            "won": 0,
            "pvp_points": 0,
            "wins": 0,
            "losses": 0,
            "registered_at": datetime.utcnow().isoformat(),
            "local_gc": None,
            "title": ""
        }
        write_data(data)
    return users[uid]

def get_user(data, user_id):
    return data.get("users", {}).get(str(user_id))

def save_user(data, user_obj):
    data.setdefault("users", {})[str(user_obj["id"])] = user_obj
    write_data(data)

def add_item_to_user(data, user_id, item_id, qty=1, unlocked=False):
    ui = data.setdefault("user_items", {})
    key = str(user_id)
    arr = ui.setdefault(key, [])
    # merge with same item (if not unlocked)
    for entry in arr:
        if entry["item_id"] == item_id and not entry.get("unlocked", False):
            entry["quantity"] = entry.get("quantity", 0) + qty
            write_data(data)
            return entry
    entry = {"item_id": item_id, "quantity": qty, "unlocked": unlocked, "acquired_at": datetime.utcnow().isoformat()}
    arr.append(entry)
    write_data(data)
    return entry

def user_items(data, user_id):
    return data.get("user_items", {}).get(str(user_id), [])

def hp_bar(hp, max_hp):
    seg = 10
    filled = int(max(0, hp) / max_hp * seg) if max_hp>0 else 0
    return "🟢" * filled + "⚪" * (seg - filled)

def strength_bar(value, max_value=200):
    seg = 10
    filled = int(min(value, max_value) / max_value * seg)
    return "🔵" * filled + "⚪" * (seg - filled)

# Battle formulas (tweakable)
def max_hp_for_level(level):
    return 100 + level * 10

def base_strength(level):
    return 5 + level // 2

# ---------------------------
# Decorator to load data into context
# ---------------------------
def with_data(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE):
        data = read_data()
        context.chat_data["data"] = data
        try:
            return await func(update, context, data)
        finally:
            # changes should call write_data explicitly in helper functions
            pass
    return wrapped

# ---------------------------
# Command Handlers
# ---------------------------

@with_data
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    user = update.effective_user
    ensure_user(data, user)
    await update.message.reply_text(f"Welcome, {user.first_name}! You are registered as Level 0, Rank E. Use /help to view commands.")

@with_data
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    # If reply to someone, show that user's profile else self
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
    else:
        target = update.effective_user
    u = get_user(data, target.id)
    if not u:
        await update.message.reply_text("User not registered.")
        return
    items = user_items(data, target.id)
    text = (f"Profile — {target.first_name}\n"
            f"Level: {u['level']}  Rank: {u['rank']}\n"
            f"XP: {u['xp']}  Won: {format_money(u['won'])}\n"
            f"Wins: {u['wins']}  Losses: {u['losses']}\n"
            f"Items: {len(items)}\n"
            f"Title: {u.get('title','')}")
    await update.message.reply_text(text)

@with_data
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    user = update.effective_user
    u = get_user(data, user.id)
    if not u:
        u = ensure_user(data, user)
    strength = base_strength(u["level"])
    need = 0
    # simplified next rank logic (can be extended)
    next_pts = {"E": 100, "D": 300, "C": 700, "B": 1500, "A": 3000}.get(u["rank"], 999999)
    need = max(0, next_pts - u["pvp_points"])
    await update.message.reply_text(f"Status — {user.first_name}\nStrength: {strength}\nPVP Points: {u['pvp_points']}\nPoints needed for next rank: {need}")

# ---------------------------
# SHOP / BUY / INVENTORY
# ---------------------------

@with_data
async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    kb = [
        [InlineKeyboardButton("All Items", callback_data="shop:all")],
        [InlineKeyboardButton("Swords", callback_data="shop:swords"),
         InlineKeyboardButton("Revival Items", callback_data="shop:revival")],
        [InlineKeyboardButton("Poison", callback_data="shop:poison"),
         InlineKeyboardButton("Special", callback_data="shop:special")]
    ]
    await update.message.reply_text("Shop — choose a category (or use /buy <item_id>):", reply_markup=InlineKeyboardMarkup(kb))

async def shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = read_data()
    _, cat = query.data.split(":", 1)
    lines = []
    if cat == "all":
        for c, items in SHOP_ITEMS.items():
            for it in items:
                lines.append(f"{it['id']}. {it['name']} — {format_money(it.get('price',0))} won")
    else:
        items = SHOP_ITEMS.get(cat, [])
        for it in items:
            lines.append(f"{it['id']}. {it['name']} — {format_money(it.get('price',0))} won")
    text = f"Category: {cat}\n\n" + "\n".join(lines[:60])
    await query.edit_message_text(text)

@with_data
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    # usage: /buy <item_id>
    if not context.args:
        await update.message.reply_text("Usage: /buy <item_id>")
        return
    try:
        item_id = int(context.args[0])
    except:
        await update.message.reply_text("Invalid item id.")
        return
    item = ITEM_INDEX.get(item_id)
    if not item:
        await update.message.reply_text("Item not found.")
        return
    text = f"Item: {item['name']}\nPrice: {format_money(item.get('price',0))} won\n"
    if "damage" in item:
        text += f"Damage: {item['damage']}\n"
    if "effect" in item:
        text += f"Effect: {item['effect']}\n"
    kb = [[InlineKeyboardButton("✅ Yes, buy", callback_data=f"buy_confirm:{item_id}"),
           InlineKeyboardButton("❌ No, cancel", callback_data="buy_cancel")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def buy_confirm_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, raw = query.data.split(":",1)
    item_id = int(raw)
    item = ITEM_INDEX.get(item_id)
    data = read_data()
    user = query.from_user
    u = get_user(data, user.id)
    if not u:
        u = ensure_user(data, user)
    price = item.get("price", 0)
    if u["won"] < price:
        await query.edit_message_text(f"Insufficient won. You have {format_money(u['won'])} won.")
        return
    u["won"] -= price
    add_item_to_user(data, user.id, item_id, qty=1, unlocked=(item.get("category")=="special" and "shadow" in item.get("name","").lower()))
    save_user(data, u)
    await query.edit_message_text(f"Bought {item['name']} for {format_money(price)} won.\nRemaining: {format_money(u['won'])} won")

async def buy_cancel_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Purchase cancelled.")

@with_data
async def inventory(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    user = update.effective_user
    items = user_items(data, user.id)
    if not items:
        await update.message.reply_text("Your inventory is empty.")
        return
    lines = []
    for e in items:
        it = ITEM_INDEX.get(e["item_id"], {"name":"Unknown"})
        lines.append(f"{it['name']} x{e.get('quantity',1)} {'(permanent)' if e.get('unlocked') else ''}")
    await update.message.reply_text("Your Items:\n" + "\n".join(lines))

# ---------------------------
# PvP system (group-only)
# ---------------------------

@with_data
async def pvp(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    # Must be a reply to challenge someone
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a user's message with /pvp to challenge them in this group.")
        return
    challenger = update.effective_user
    target = update.message.reply_to_message.from_user
    if challenger.id == target.id:
        await update.message.reply_text("You cannot challenge yourself.")
        return
    # send challenge with accept/decline inline buttons
    kb = [[InlineKeyboardButton("Accept ✅", callback_data=f"pvp_accept:{challenger.id}:{target.id}"),
           InlineKeyboardButton("Decline ❌", callback_data=f"pvp_decline:{challenger.id}:{target.id}")]]
    await update.message.reply_text(f"🔥 Battle Request!\n{challenger.first_name} challenged {target.first_name} to a duel!\n{target.first_name}, accept?", reply_markup=InlineKeyboardMarkup(kb))

async def pvp_accept_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = read_data()
    _, ch_id, tar_id = query.data.split(":")
    ch_id = int(ch_id); tar_id = int(tar_id)
    # only targeted user can accept
    if query.from_user.id != tar_id:
        await query.answer("Only the challenged user can accept.", show_alert=True)
        return
    # create battle
    battle_id = str(uuid.uuid4())
    p1 = get_user(data, ch_id) or ensure_user(data, context.bot.get_chat(ch_id))
    p2 = get_user(data, tar_id) or ensure_user(data, context.bot.get_chat(tar_id))
    p1_hp = max_hp_for_level(p1["level"])
    p2_hp = max_hp_for_level(p2["level"])
    p1_str = base_strength(p1["level"])
    p2_str = base_strength(p2["level"])
    battle = {
        "id": battle_id,
        "chat_id": query.message.chat_id,
        "message_id": None,
        "player1": ch_id,
        "player2": tar_id,
        "p1_hp": p1_hp,
        "p2_hp": p2_hp,
        "p1_max": p1_hp,
        "p2_max": p2_hp,
        "p1_str": p1_str,
        "p2_str": p2_str,
        "turn": ch_id,
        "status": "ongoing",
        "logs": []
    }
    data.setdefault("battles", {})[battle_id] = battle
    write_data(data)
    text = battle_text(battle, data)
    kb = action_kb(battle_id, battle["turn"])
    msg = await query.message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    data = read_data()
    data["battles"][battle_id]["message_id"] = msg.message_id
    write_data(data)

async def pvp_decline_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Challenge declined.")

def battle_text(battle, data):
    p1 = get_user(data, battle["player1"])
    p2 = get_user(data, battle["player2"])
    p1_name = p1["first_name"] if p1 else f"Player {battle['player1']}"
    p2_name = p2["first_name"] if p2 else f"Player {battle['player2']}"
    txt = "🔥 Battle Time! 🔥\n\n"
    txt += f"{p1_name}\n🌿 Health: {hp_bar(battle['p1_hp'], battle['p1_max'])} {battle['p1_hp']}/{battle['p1_max']}\n"
    txt += f"✨ strength: {strength_bar(battle['p1_str'])} {battle['p1_str']} 💨\n\n"
    txt += f"{p2_name}\n🌿 Health: {hp_bar(battle['p2_hp'], battle['p2_max'])} {battle['p2_hp']}/{battle['p2_max']}\n"
    txt += f"✨ strength: {strength_bar(battle['p2_str'])} {battle['p2_str']} 💨\n\n"
    current = p1_name if battle["turn"] == battle["player1"] else p2_name
    txt += f"👉 {current}'s Turn — Choose your action:"
    return txt

def action_kb(battle_id, user_id):
    kb = [
        [InlineKeyboardButton("Attack ⚔️", callback_data=f"act:{battle_id}:attack:{user_id}")],
        [InlineKeyboardButton("Defend 🛡️", callback_data=f"act:{battle_id}:defend:{user_id}")],
        [InlineKeyboardButton("Use Item 💊", callback_data=f"act:{battle_id}:useitem:{user_id}")],
        [InlineKeyboardButton("Use Revival 🌟", callback_data=f"act:{battle_id}:revive:{user_id}")]
    ]
    return InlineKeyboardMarkup(kb)

async def battle_action_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = read_data()
    try:
        _, battle_id, action, uid_str = query.data.split(":")
    except:
        await query.answer("Invalid action.", show_alert=True)
        return
    uid = int(uid_str)
    user = query.from_user
    if user.id != uid:
        await query.answer("Not your turn / not allowed.", show_alert=True)
        return
    battle = data.get("battles", {}).get(battle_id)
    if not battle:
        await query.answer("Battle not found.", show_alert=True)
        return
    if battle["status"] != "ongoing":
        await query.answer("Battle already finished.", show_alert=True)
        return
    if battle["turn"] != user.id:
        await query.answer("It's not your turn.", show_alert=True)
        return
    # perform action
    await perform_action(battle_id, action, user.id, query, context)

async def perform_action(battle_id, action, user_id, query, context):
    data = read_data()
    battle = data["battles"].get(battle_id)
    if not battle:
        await query.answer("Battle missing.", show_alert=True)
        return
    attacker_is_p1 = (user_id == battle["player1"])
    if attacker_is_p1:
        atk_str = battle["p1_str"]
        tgt_hp_key = "p2_hp"
    else:
        atk_str = battle["p2_str"]
        tgt_hp_key = "p1_hp"
    # simplistic implementations of actions
    if action == "attack":
        dmg = max(1, int(atk_str * 1.2))
        battle[tgt_hp_key] = max(0, battle[tgt_hp_key] - dmg)
        battle["logs"].append(f"{user_id} attacked for {dmg}")
    elif action == "defend":
        # defend heals a small fraction for simplicity
        if attacker_is_p1:
            battle["p1_hp"] = min(battle["p1_max"], battle["p1_hp"] + int(battle["p1_max"] * 0.10))
        else:
            battle["p2_hp"] = min(battle["p2_max"], battle["p2_hp"] + int(battle["p2_max"] * 0.10))
        battle["logs"].append(f"{user_id} defended and regained HP")
    elif action == "useitem":
        items = user_items(data, user_id)
        if not items:
            await query.answer("You have no items to use.", show_alert=True)
            return
        # pick first applicable item
        first = items[0]
        it = ITEM_INDEX.get(first["item_id"])
        if it and "damage" in it:
            dmg = it["damage"]
            battle[tgt_hp_key] = max(0, battle[tgt_hp_key] - dmg)
            battle["logs"].append(f"{user_id} used {it['name']} for {dmg} damage")
        else:
            battle["logs"].append(f"{user_id} used {it['name']}")
    elif action == "revive":
        items = user_items(data, user_id)
        rev = None
        for e in items:
            i = ITEM_INDEX.get(e["item_id"])
            if i and (i.get("category")=="revival"):
                rev = (e,i)
                break
        if not rev:
            await query.answer("No revival items found.", show_alert=True)
            return
        e,i = rev
        e["quantity"] = e.get("quantity",1) - 1
        if e["quantity"] <= 0:
            data["user_items"][str(user_id)].remove(e)
        # heal to 50%
        if attacker_is_p1:
            battle["p1_hp"] = min(battle["p1_max"], int(battle["p1_max"] * 0.5))
        else:
            battle["p2_hp"] = min(battle["p2_max"], int(battle["p2_max"] * 0.5))
        battle["logs"].append(f"{user_id} used revival {i['name']}")
    else:
        await query.answer("Unknown action.", show_alert=True)
        return
    # switch turn
    battle["turn"] = battle["player2"] if attacker_is_p1 else battle["player1"]
    write_data(data)
    # update message
    try:
        text = battle_text(battle, data)
        kb = action_kb(battle_id, battle["turn"])
        await context.bot.edit_message_text(chat_id=battle["chat_id"], message_id=battle["message_id"], text=text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.exception("Failed to edit battle message: %s", e)
    # check victory
    if battle["p1_hp"] <= 0 or battle["p2_hp"] <= 0:
        await conclude_battle(battle_id, context)

async def conclude_battle(battle_id, context):
    data = read_data()
    battle = data.get("battles", {}).get(battle_id)
    if not battle:
        return
    if battle["p1_hp"] <= 0:
        winner_id = battle["player2"]; loser_id = battle["player1"]
    else:
        winner_id = battle["player1"]; loser_id = battle["player2"]
    winner = get_user(data, winner_id); loser = get_user(data, loser_id)
    cfg = data.get("config", {}).get("pvp_rewards", {})
    # apply rewards/penalties (as provided)
    winner["xp"] = winner.get("xp",0) + cfg.get("xp_win",100000)
    winner["won"] = winner.get("won",0) + cfg.get("won_win",1000000)
    winner["pvp_points"] = winner.get("pvp_points",0) + cfg.get("pvp_points_win",22)
    winner["wins"] = winner.get("wins",0) + 1
    loser["xp"] = loser.get("xp",0) + cfg.get("xp_lose",500)
    loser["won"] = max(0, loser.get("won",0) + cfg.get("won_lose",-100000))
    loser["pvp_points"] = max(0, loser.get("pvp_points",0) + cfg.get("pvp_points_lose",-26))
    loser["losses"] = loser.get("losses",0) + 1
    battle["status"] = "finished"
    write_data(data)
    save_user(data, winner); save_user(data, loser)
    # final message format as required
    winner_name = winner["first_name"]
    loser_name = loser["first_name"]
    text = (f"🎉 {winner_name} wins the battle! 🏆\n\n"
            f"👑 Victory Rewards:\n- 🧠 XP: +{cfg.get('xp_win')}\n- 💴 won: +{format_money(cfg.get('won_win'))}\n- 🎖 pvp points: +{cfg.get('pvp_points_win')}\n\n"
            f"💀 Defeat Penalties for {loser_name}:\n- 🧠 XP: +{cfg.get('xp_lose')}\n- 💴 won: {format_money(cfg.get('won_lose'))}\n- 🎖 pvp points: {cfg.get('pvp_points_lose')}")
    try:
        await context.bot.send_message(chat_id=battle["chat_id"], text=text)
    except Exception as e:
        logger.exception("Failed to send final battle message: %s", e)

# ---------------------------
# PvP vs Bot
# ---------------------------

@with_data
async def pvpbot(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    user = update.effective_user
    u = get_user(data, user.id)
    if not u:
        u = ensure_user(data, user)
    # bot difficulty scales with player's level/rank: simple +2 level
    bot_level = max(1, u["level"] + 2)
    bot_hp = max_hp_for_level(bot_level)
    bot_str = base_strength(bot_level)
    battle_id = str(uuid.uuid4())
    battle = {
        "id": battle_id,
        "chat_id": update.effective_chat.id,
        "message_id": None,
        "player1": user.id,
        "player2": 0,  # 0 denotes bot
        "p1_hp": max_hp_for_level(u["level"]),
        "p2_hp": bot_hp,
        "p1_max": max_hp_for_level(u["level"]),
        "p2_max": bot_hp,
        "p1_str": base_strength(u["level"]),
        "p2_str": bot_str,
        "turn": user.id,
        "status": "ongoing",
        "is_bot": True,
        "logs": []
    }
    data.setdefault("battles", {})[battle_id] = battle
    write_data(data)
    text = battle_text(battle, data)
    kb = action_kb(battle_id, battle["turn"])
    msg = await update.message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    data = read_data()
    data["battles"][battle_id]["message_id"] = msg.message_id
    write_data(data)

# ---------------------------
# Currency transfer & leaderboards
# ---------------------------
@with_data
async def wongive(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    if not update.message.reply_to_message or not context.args:
        await update.message.reply_text("Reply to a user and use: /wongive <amount>")
        return
    try:
        amount = int(context.args[0])
    except:
        await update.message.reply_text("Invalid amount.")
        return
    giver = update.effective_user
    receiver = update.message.reply_to_message.from_user
    g = get_user(data, giver.id)
    r = get_user(data, receiver.id)
    if not g:
        g = ensure_user(data, giver)
    if not r:
        r = ensure_user(data, receiver)
    if g["won"] < amount:
        await update.message.reply_text("Insufficient won.")
        return
    g["won"] -= amount
    r["won"] += amount
    save_user(data, g); save_user(data, r)
    await update.message.reply_text(f"Transferred {format_money(amount)} won to {receiver.first_name}.")

@with_data
async def tophunters(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    users = list(data.get("users", {}).values())
    users.sort(key=lambda u: (u.get("pvp_points",0), u.get("level",0)), reverse=True)
    lines = []
    for u in users[:10]:
        lines.append(f"{u.get('first_name')} — Rank: {u.get('rank')} PVP: {u.get('pvp_points')}")
    await update.message.reply_text("Top Hunters:\n" + ("\n".join(lines) if lines else "No data yet"))

@with_data
async def globleleader(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    users = list(data.get("users", {}).values())
    users.sort(key=lambda u: (u.get("level",0), u.get("won",0)), reverse=True)
    lines = [f"{u.get('first_name')} — Level {u.get('level')} Won: {format_money(u.get('won',0))}" for u in users[:10]]
    await update.message.reply_text("Global Leaderboard:\n" + ("\n".join(lines) if lines else "No data yet"))

@with_data
async def localleader(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    # requires local_gc in user profile, show top in this GC
    chat = update.effective_chat
    users = [u for u in data.get("users", {}).values() if u.get("local_gc")==chat.id]
    users.sort(key=lambda u: (u.get("level",0), u.get("won",0)), reverse=True)
    lines = [f"{u.get('first_name')} — Level {u.get('level')} Won: {format_money(u.get('won',0))}" for u in users[:10]]
    await update.message.reply_text("Local Leaderboard:\n" + ("\n".join(lines) if lines else "No local data yet"))

# ---------------------------
# Info & stubs for remaining commands
# ---------------------------
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "/start — register\n"
        "/profile — show profile (reply to other's message to view theirs)\n"
        "/status — strength & progress\n"
        "/shop — open shop\n"
        "/buy <item_id> — buy item\n"
        "/inventory — show your items\n"
        "/pvp — reply to a user to challenge them (group-only)\n"
        "/pvpbot — fight the bot\n"
        "/wongive <amount> — reply to someone and transfer won\n"
        "/tophunters — top ranks\n"
        "/globleleader — global leaderboard\n"
        "/localleader — local leaderboard\n"
        "/bank /myloan /dailytask /taskreward /title /owner /guide /help\n    "
    )
    await update.message.reply_text(text)

async def guide_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Guide: This bot is Solo Leveling themed. Use /shop to buy items, /pvp to fight others in group chats. Boss fights unlock at S-rank milestones (hook-ready).")

async def owner_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Owner: {OWNER_USERNAME}")

# Stubs: implement later or extend
@with_data
async def bank_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    await update.message.reply_text("Bank: loan offers will be displayed here (coming soon).")

@with_data
async def myloan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    await update.message.reply_text("MyLoan: your loans summary will show here (coming soon).")

@with_data
async def rank_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    await update.message.reply_text("Rank lookup: reply to a user with /rank to see their rank.")

@with_data
async def level_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    await update.message.reply_text("Level lookup: reply to a user with /level to see their level.")

@with_data
async def swards_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    await update.message.reply_text("Swards: check your swords (use /inventory).")

@with_data
async def revivalitem_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    await update.message.reply_text("Revival items: check your revival items (use /inventory).")

@with_data
async def dailytask_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    await update.message.reply_text("Daily tasks: 3 tasks will be listed here (coming soon).")

@with_data
async def taskreward_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    await update.message.reply_text("Task reward: claim your task rewards here (coming soon).")

@with_data
async def title_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    await update.message.reply_text("Titles: Titles for high rankers will be shown here (coming soon).")

# ---------------------------
# Startup / Register handlers
# ---------------------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    # basic commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("shop", shop))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("inventory", inventory))
    app.add_handler(CommandHandler("pvp", pvp, filters=filters.ChatType.GROUPS | filters.ChatType.SUPERGROUPS))
    app.add_handler(CommandHandler("pvpbot", pvpbot))
    app.add_handler(CommandHandler("wongive", wongive))
    app.add_handler(CommandHandler("tophunters", tophunters))
    app.add_handler(CommandHandler("globleleader", globleleader))
    app.add_handler(CommandHandler("localleader", localleader))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("guide", guide_cmd))
    app.add_handler(CommandHandler("owner", owner_cmd))
    # stubs
    app.add_handler(CommandHandler("bank", bank_cmd))
    app.add_handler(CommandHandler("myloan", myloan_cmd))
    app.add_handler(CommandHandler("rank", rank_cmd))
    app.add_handler(CommandHandler("level", level_cmd))
    app.add_handler(CommandHandler("swards", swards_cmd))
    app.add_handler(CommandHandler("revivalitem", revivalitem_cmd))
    app.add_handler(CommandHandler("dailytask", dailytask_cmd))
    app.add_handler(CommandHandler("taskreward", taskreward_cmd))
    app.add_handler(CommandHandler("title", title_cmd))

    # callback handlers
    app.add_handler(CallbackQueryHandler(shop_callback, pattern=r"^shop:"))
    app.add_handler(CallbackQueryHandler(buy_confirm_cb, pattern=r"^buy_confirm:"))
    app.add_handler(CallbackQueryHandler(buy_cancel_cb, pattern=r"^buy_cancel"))
    app.add_handler(CallbackQueryHandler(pvp_accept_cb, pattern=r"^pvp_accept:"))
    app.add_handler(CallbackQueryHandler(pvp_decline_cb, pattern=r"^pvp_decline:"))
    app.add_handler(CallbackQueryHandler(battle_action_cb, pattern=r"^act:"))

    logger.info("Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
