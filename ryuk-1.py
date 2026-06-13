"""
╔════════════════════════════════════════════════════════════════════╗
║        Ryuk S1 Manager - ALL-IN-ONE SYSTEM                        ║
║                     Credits: RYUK                                 ║
║              Optimized for Maximum Speed & Performance            ║
╚════════════════════════════════════════════════════════════════════╝

Python 3.11+
python-telegram-bot 21.6

Features:
- Multi-bot management & control (hosts all bots)
- Ultra-fast NC (name change) - minimal delays
- Speed-optimized spam loops with dynamic delays
- All raid features integrated
- Global operations across groups
- Zero artificial rate limiting
- Direct delay control via commands
- Memory-efficient caching
- Advanced admin system
- Group & user tracking
- Bot renaming & PFP management
- Per-chat delay configurations
- Auto-token validation & removal
- Smart bot detection per group
- Kicked bot notifications

WARNING: Use responsibly & keep compliant with Telegram ToS
Credits: RYUK Network
"""

import asyncio
import gc
import logging
import os
import sqlite3
import time
import json
import random
import tempfile
import requests
import threading
import urllib.request

from http.server import BaseHTTPRequestHandler, HTTPServer
from collections import OrderedDict
from typing import Optional, Set, Dict, List
from dotenv import load_dotenv

import psutil

from telegram import Update, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    TypeHandler,
    filters,
)
from telegram.error import RetryAfter

# ╔════════════════════════════════════════════════════════════════╗
# ║                      CONFIGURATION                             ║
# ╚════════════════════════════════════════════════════════════════╝


load_dotenv()

def safe_int(value, default):
    try:
        return int(value)
    except:
        return default

TOKENS = [t.strip() for t in os.getenv("TOKENS", "").split(",") if t.strip()]

OWNER_ID = safe_int(os.getenv("OWNER_ID"), 8073185253)

MANAGER_TOKEN = os.getenv("MANAGER_TOKEN", "").strip()

SELF_URL = os.getenv("SELF_URL", "").strip()

PING_INTERVAL = safe_int(os.getenv("PING_INTERVAL"), 300)

DATABASE = "ryuk_manager.db"
ADMIN_FILE = "ryuk_admins.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

os.makedirs("downloads/global", exist_ok=True)

class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.strip().rstrip('/').lower()
        
        # Dashboard + Health
        if path in ["", "/", "/dashboard", "/health"]:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            
            active_bots = len(bots) if 'bots' in globals() else 0
            ping_interval = PING_INTERVAL if 'PING_INTERVAL' in globals() else 300
            
            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Ryuk S1 Dashboard</title>
    <meta http-equiv="refresh" content="10">
    <style>
        body {{ background:#0a0a0a; color:#0f0; font-family:Arial; text-align:center; padding:30px; }}
        .box {{ background:#111; max-width:800px; margin:auto; padding:25px; border-radius:10px; border:1px solid #0f0; }}
        h1 {{ color:#0f0; }}
        table {{ margin:20px auto; border-collapse:collapse; }}
        th, td {{ padding:10px; border:1px solid #333; }}
    </style>
</head>
<body>
    <div class="box">
        <h1>🔥 Ryuk S1 Manager</h1>
        <p><strong>Status:</strong> <span style="color:#0f0;">🟢 ONLINE</span></p>
        <p><strong>URL:</strong> {os.environ.get('SELF_URL', 'Not Set')}</p>
        <p><strong>Time:</strong> {time.strftime("%Y-%m-%d %H:%M:%S")}</p>
        
        <div class="box">
            <h2>📊 System</h2>
            <p><strong>Active Bots:</strong> {active_bots}</p>
            <p><strong>Memory:</strong> {psutil.Process().memory_info().rss / (1024*1024):.1f} MB</p>
        </div>
        
        <div class="box">
            <h2>🔄 Self-Ping</h2>
            <p>Running every {ping_interval} seconds</p>
        </div>
        
        <h2>🤖 Connected Bots</h2>
        <table>
            <tr><th>Bot</th><th>Status</th></tr>
"""
            
            if active_bots > 0:
                for bot in bots:
                    try:
                        uname = getattr(bot, 'username', None)
                        html += f"<tr><td>@{uname or 'Unknown'}</td><td style='color:#0f0'>✅ Connected</td></tr>"
                    except:
                        html += "<tr><td>Unknown</td><td>Checking...</td></tr>"
            else:
                html += "<tr><td colspan='2'>No bots yet...</td></tr>"
            
            html += """
        </table>
        <p style="color:#666; margin-top:20px;">Auto refreshes every 10 seconds</p>
    </div>
</body>
</html>"""
            self.wfile.write(html.encode('utf-8'))
            return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not Found")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass

def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), _HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"🌐 Health server running on port {port}")
    logger.info(f"🌐 Health server + Dashboard started on port {port}")


async def self_ping_loop():
    SELF_URL = os.environ.get("SELF_URL", "").strip()

    if not SELF_URL:
        logger.warning("⚠️ SELF_URL environment variable is not set")
        return

    logger.info(f"🔄 Self-ping loop started: {SELF_URL}")
    interval = int(os.environ.get("SELF_PING_INTERVAL", 300))

    while True:
        try:
            urllib.request.urlopen(SELF_URL, timeout=15).read()
            logger.info(f"✅ Self-ping successful: {SELF_URL}")
        except Exception as e:
            logger.error(f"❌ Self-ping failed: {e}")
        
        await asyncio.sleep(interval)

# ╔════════════════════════════════════════════════════════════════╗
# ║                    SPAM TEXTS & EMOJIS                         ║
# ╚════════════════════════════════════════════════════════════════╝

RAID_TEXTS = ["𝘊𝘏𝘜D", "𝘓𝘜𝘕𝘋 𝘒𝘈𝘏𝘈", "𝘗𝘐𝘓LE", "𝘊𝘏𝘐KNE", "𝘎andu", "PENKELODE", "𝘜𝘛𝘏 MC", "𝘓𝘜𝘕𝘋 𝘓E",]
NCEMO_EMOJIS = ["👻", "🩷", "😂", "🤣", "♥️", "💦", "😹", "🥶", "🥀", "🎀", "😈", "👑", "😤", "🤷", "👅", "🤙", "🤦", "😏", "👏", "🔥", "💥", "✌️", "🩸", "❤️‍🔥", "💀", "🤪", "😱"]
SWIPE_TEXTS = ["NAME RNDI", "NAME tmkc", "pille NAME", "NAME 𝘒𝙖 bhosda"]
TARGET_SLIDE_TEXTS = ["{} 𝘜𝙏𝙃🤣", "{} TMKC", "{} 𝘊𝙖𝙢 garl🤣", "{} teri ma ke lund baja ke uska gala daba dunga"]
REPLY_RYUK_TEXTS = ["BHEN CHUDA NA RNDI","chal teri mkc"]

# ╔════════════════════════════════════════════════════════════════╗
# ║          MINIMAL GLOBAL STATE - NC + SPM ONLY                  ║
# ╚════════════════════════════════════════════════════════════════╝

class LRUCache:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity
 
    def add(self, key):
        self.cache[key] = None
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
 
    def __contains__(self, key):
        return key in self.cache

# ── Essential Only ───────────────────────────────────────────────
global_replied_messages = LRUCache(1200)

if os.path.exists(ADMIN_FILE):
    try:
        with open(ADMIN_FILE, "r") as f:
            SUDO_USERS = set(int(x) for x in json.load(f))
    except:
        SUDO_USERS = {OWNER_ID}
else:
    SUDO_USERS = {OWNER_ID}

def save_sudo():
    with open(ADMIN_FILE, "w") as f:
        json.dump(list(SUDO_USERS), f)

# ── Core Required Globals ────────────────────────────────────────
bots = []                    # Required
bot_usernames = []           # For dashboard

# ── Lightweight Task Management ──────────────────────────────────
class TaskManager:
    def __init__(self):
        self.tasks = {}                    # (category, key) → task
        self.bot_group_cache = {}          # bot_id → set(chat_ids)

    def add(self, category: str, key, task):
        if task:
            self.tasks[(category, key)] = task

    def stop(self, category: str, key=None):
        """Stop tasks by category (and optional key)"""
        to_remove = []
        for (cat, k), task in list(self.tasks.items()):
            if cat == category and (key is None or k == key):
                try:
                    task.cancel()
                except:
                    pass
                to_remove.append((cat, k))
        for item in to_remove:
            self.tasks.pop(item, None)

    def cleanup(self):
        """Remove finished tasks"""
        for key in list(self.tasks.keys()):
            if self.tasks[key].done():
                self.tasks.pop(key, None)
        gc.collect()

task_manager = TaskManager()

# ── Small & Essential Only ───────────────────────────────────────
active_menus = {}
pending_addbots = set()
known_users = set()
known_chats = set()

# ── Delays (NC + SPM) ────────────────────────────────────────────
nc_delays = {}
spm_delays = {}
global_nc_delay = 0.1
global_spm_delay = 0.05
gc_delays = {}

# Removed: bot_tokens, saved_pfps, pfp_delays, global_pfp_delay

# ── Database Functions (Unchanged) ───────────────────────────────
def init_db():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bots (
            id INTEGER PRIMARY KEY, token TEXT UNIQUE, username TEXT, added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS groups (token TEXT, chat_id INTEGER, UNIQUE(token, chat_id))
    """)
    conn.commit()
    conn.close()

def add_bot_db(token, username=""):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO bots(token, username) VALUES(?, ?)", (token, username))
    conn.commit()
    conn.close()

def remove_bot_db(token):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("DELETE FROM bots WHERE token=?", (token,))
    conn.commit()
    conn.close()

def get_bots_db():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT token, username FROM bots")
    rows = cur.fetchall()
    conn.close()
    return rows

def add_group_db(token, chat_id):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO groups(token, chat_id) VALUES(?, ?)", (token, chat_id))
    conn.commit()
    conn.close()

def get_groups_db(token):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT chat_id FROM groups WHERE token=?", (token,))
    rows = cur.fetchall()
    conn.close()
    return [x[0] for x in rows]

# ╔════════════════════════════════════════════════════════════════╗
# ║                    HELPERS & DECORATORS                        ║
# ╚════════════════════════════════════════════════════════════════╝

async def safe_reply(update: Update, text: str, **kwargs):
    if not update.message:
        return
    unique_msg_id = f"{update.message.chat_id}_{update.message.message_id}"
    if unique_msg_id in global_replied_messages:
        return
    global_replied_messages.add(unique_msg_id)
    try:
        await update.message.reply_text(text, **kwargs)
    except:
        pass

def only_sudo(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or update.effective_user.id not in SUDO_USERS:
            return await safe_reply(update, "❌ 𝙉𝙤𝙩 𝘼𝙪𝙩𝙝𝙤𝙧𝙞𝙯𝙚𝙙.")
        return await func(update, context)
    return wrapper

def only_owner(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or update.effective_user.id != OWNER_ID:
            return await safe_reply(update, "❌ 𝙊𝙬𝙣𝙚𝙧 𝙊𝙣𝙡𝙮.")
        return await func(update, context)
    return wrapper

def extract_command_text(raw_text: Optional[str]) -> str:
    if not raw_text:
        return ""
    parts = raw_text.split(" ", 1)
    return parts[1].strip() if len(parts) > 1 else ""

async def get_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        return update.message.reply_to_message.from_user.id
    if update.message.entities:
        for entity in update.message.entities:
            if entity.type == 'text_mention':
                return entity.user.id
    if context.args:
        arg = context.args[0]
        try:
            return int(arg)
        except:
            if arg.startswith("@"):
                try:
                    return (await context.bot.get_chat(arg)).id
                except:
                    pass
    return None

async def get_mention_from_id(context, uid):
    try:
        return f"[{(await context.bot.get_chat(uid)).first_name}](tg://user?id={uid})"
    except:
        return f"`{uid}`"

def get_delay(chat_id, delay_type="nc"):
    if chat_id in gc_delays:
        if delay_type == "nc":
            return gc_delays[chat_id].get("nc", nc_delays.get(chat_id, global_nc_delay))
        elif delay_type == "spm":
            return gc_delays[chat_id].get("spm", spm_delays.get(chat_id, global_spm_delay))
    if delay_type == "nc":
        return nc_delays.get(chat_id, global_nc_delay)
    elif delay_type == "spm":
        return spm_delays.get(chat_id, global_spm_delay)
    return global_pfp_delay

async def validate_bot_token(token: str) -> bool:
    try:
        app = Application.builder().token(token).build()
        me = await app.bot.get_me()
        return True
    except:
        return False

async def update_bot_group_cache(bot_id: int, chat_id: int):
    if bot_id not in bot_group_cache:
        bot_group_cache[bot_id] = set()
    bot_group_cache[bot_id].add(chat_id)

def is_bot_in_chat(bot_id: int, chat_id: int) -> bool:
    if bot_id not in bot_group_cache:
        return False
    return chat_id in bot_group_cache[bot_id]

# Owner action tracking helpers
def mark_owner_action(chat_id: int, action_type: str):
    """Mark an action as owner-initiated"""
    owner_initiated_actions[(chat_id, action_type)] = OWNER_ID

def can_stop_action(user_id: int, chat_id: int, action_type: str) -> bool:
    """Check if user can stop an action. Owner can always stop, sudo can only stop non-owner actions"""
    if user_id == OWNER_ID:
        return True
    action_key = (chat_id, action_type)
    if action_key in owner_initiated_actions:
        return owner_initiated_actions[action_key] != OWNER_ID
    return True  # Allow stopping if no owner initiated it

# ╔════════════════════════════════════════════════════════════════╗
# ║         WORKER TASKS - ZERO RATE LIMIT, SPEED OPTIMIZED        ║
# ╚════════════════════════════════════════════════════════════════╝

async def bot_loop(bot, chat_id, base, mode, task_ref):
    i = 0
    while True:
        try:
            delay = get_delay(chat_id, "nc")
            text = f"{base} {RAID_TEXTS[i % len(RAID_TEXTS)]}" if mode == "raid" else f"{base} {NCEMO_EMOJIS[i % len(NCEMO_EMOJIS)]}"
            i += 1
            await bot.set_chat_title(chat_id, text)
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            break
        except:
            await asyncio.sleep(0.05)

async def pyramid_loop_worker(bot, chat_id, name, task_ref):
    base_text = f"{name} 𝘗𝙔𝙍𝘈𝙈𝙄𝘋🎖️"
    chars_left = 128 - len(base_text)
    max_stars = max(1, min(15, chars_left // 2))
    
    while True:
        try:
            delay = get_delay(chat_id, "nc")
            star_count = random.randint(1, max_stars)
            await bot.set_chat_title(chat_id, base_text + "⭐" * star_count)
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            break
        except:
            await asyncio.sleep(0.05)

async def spm_loop_sender(bot, chat_id: int, text: str):
    while True:
        try:
            delay = get_delay(chat_id, "spm")
            await bot.send_message(chat_id=chat_id, text=text, disable_web_page_preview=True)
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            break
        except:
            await asyncio.sleep(0.01)

async def slidespam_worker(bot, chat_id: int, message_id: int, text: str):
    while True:
        try:
            delay = get_delay(chat_id, "spm")
            await bot.send_message(chat_id=chat_id, text=text, reply_to_message_id=message_id, disable_web_page_preview=True)
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            break
        except:
            await asyncio.sleep(0.01)

async def targetslide_worker(bot, chat_id: int, message_id: int, name: str):
    while True:
        try:
            delay = get_delay(chat_id, "spm")
            msg = random.choice(TARGET_SLIDE_TEXTS).format(name)
            await bot.send_message(chat_id=chat_id, text=msg, reply_to_message_id=message_id, disable_web_page_preview=True)
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            break
        except:
            await asyncio.sleep(0.01)

async def media_spm_sender(bot, chat_id: int, media_type: str, file_id: str):
    while True:
        try:
            delay = get_delay(chat_id, "spm")
            if media_type == "sticker":
                await bot.send_sticker(chat_id=chat_id, sticker=file_id)
            elif media_type == "gif":
                await bot.send_animation(chat_id=chat_id, animation=file_id)
            elif media_type == "photo":
                await bot.send_photo(chat_id=chat_id, photo=file_id)
            elif media_type == "video":
                await bot.send_video(chat_id=chat_id, video=file_id)
            elif media_type == "voice":
                await bot.send_voice(chat_id=chat_id, voice=file_id)
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            break
        except:
            await asyncio.sleep(0.01)

async def pfp_loop_worker(bot, chat_id: int):
    while True:
        try:
            delay = get_delay(chat_id, "pfp")
            folder = f"downloads/{chat_id}"
            if not os.path.exists(folder):
                await asyncio.sleep(5)
                continue
            files = [f for f in os.listdir(folder) if f.endswith('.jpg')]
            if not files:
                await asyncio.sleep(5)
                continue
            pic = random.choice(files)
            with open(f"{folder}/{pic}", 'rb') as f:
                await bot.set_chat_photo(chat_id, photo=f)
            await asyncio.sleep(delay)
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
        except asyncio.CancelledError:
            break
        except:
            await asyncio.sleep(0.5)

async def setpfp_loop_worker(bot_idx: int, chat_id: int, pfp_file_path: str):
    bot = bots[bot_idx]
    while True:
        try:
            delay = get_delay(chat_id, "pfp")
            if os.path.exists(pfp_file_path):
                with open(pfp_file_path, 'rb') as f:
                    await bot.set_chat_photo(chat_id, photo=f)
            await asyncio.sleep(delay)
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
        except asyncio.CancelledError:
            break
        except:
            await asyncio.sleep(0.5)

# ╔════════════════════════════════════════════════════════════════╗
# ║                    MENU SYSTEM                                 ║
# ╚════════════════════════════════════════════════════════════════╝

def get_selector_keyboard(task_id: str):
    menu = active_menus[task_id]
    sel = menu["selected"]
    keyboard = []
    row = []
    for i, uname in enumerate(bot_usernames):
        check = "✅" if i in sel else "❌"
        row.append(InlineKeyboardButton(f"{check} {uname}", callback_data=f"tk_{task_id}_tgl_{i}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([
        InlineKeyboardButton("🔘 All", callback_data=f"tk_{task_id}_all"),
        InlineKeyboardButton("⚪ None", callback_data=f"tk_{task_id}_none")
    ])
    keyboard.append([InlineKeyboardButton("🚀 LAUNCH", callback_data=f"tk_{task_id}_start")])
    return InlineKeyboardMarkup(keyboard)

# ╔════════════════════════════════════════════════════════════════╗
# ║          COMMANDS - NAME CHANGE (ZERO RATE LIMIT)              ║
# ╚════════════════════════════════════════════════════════════════╝

@only_sudo
async def gcnc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("⚠️ `/gcnc <text>`")
    
    base = " ".join(context.args)
    chat_id = update.message.chat_id
    active_count = 0

    for bot in bots:
        if bot.id in task_manager.bot_group_cache and chat_id in task_manager.bot_group_cache[bot.id]:
            key = ("nc", chat_id, bot.id)
            task = asyncio.create_task(bot_loop(bot, chat_id, base, "raid"))
            task_manager.add("nc", key, task)
            active_count += 1

    await update.message.reply_text(f"🔄 Raid NC started on **{active_count} bots**")


@only_sudo
async def ncemo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    
    # Default text if user doesn't provide any
    if context.args:
        base = " ".join(context.args)
    else:
        base = "ebbu chudai"
    
    active_count = 0
    for bot in bots:
        if bot.id in task_manager.bot_group_cache and chat_id in task_manager.bot_group_cache[bot.id]:
            key = ("nc", chat_id, bot.id)
            task = asyncio.create_task(bot_loop(bot, chat_id, base, "emo"))
            task_manager.add("nc", key, task)
            active_count += 1

    if active_count > 0:
        await update.message.reply_text(
            f"🔄 **Emoji NC Started Successfully**\n"
            f"**Text:** `{base}`\n"
            f"**Active Bots:** {active_count}"
        )
    else:
        await update.message.reply_text("⚠️ No bots found in this group.")


@only_sudo
async def stopgcnc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    task_manager.stop("nc", chat_id)
    await update.message.reply_text("🛑 All NC stopped in this group")


@only_sudo
async def delaync_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("⚠️ `/delaync <seconds>` (0.08-5s)")
    try:
        val = float(context.args[0])
        val = max(0.08, min(5, val))
        nc_delays[update.message.chat_id] = val
        await update.message.reply_text(f"⚡ NC speed set to `{val}s`")
    except:
        await update.message.reply_text("❌ Invalid number")

# ╔════════════════════════════════════════════════════════════════╗
# ║          COMMANDS - MESSAGE SPAM (ZERO RATE LIMIT)             ║
# ╚════════════════════════════════════════════════════════════════╝

@only_sudo
async def spm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = extract_command_text(update.message.text)
    if not text:
        return await safe_reply(update, "⚠️ `/spm <text>`", parse_mode="Markdown")
    
    chat_id = update.message.chat_id
    
    # Create spam task
    task = asyncio.create_task(spm_loop_sender(context.application.bot, chat_id, text))
    
    # Store using lightweight TaskManager
    task_manager.add("spam", chat_id, task)
    
    await safe_reply(update, f"✅ Spam started (delay: {get_delay(chat_id, 'spm')}s)")


@only_sudo
async def stopspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    task_manager.stop("spam", chat_id)   # Stop spam only in this chat
    await safe_reply(update, "🛑 Spam stopped in this chat")


@only_sudo
async def stopallspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = len([k for k in task_manager.tasks.keys() if k[0] == "spam"])
    task_manager.stop("spam")            # Stop ALL spam tasks globally
    await safe_reply(update, f"🛑 Stopped {count} spam tasks globally")


@only_sudo
async def delaygcspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await safe_reply(update, "⚠️ `/delaygcspm <seconds>` (0.05-5s)", parse_mode="Markdown")
    try:
        val = float(context.args[0])
        val = max(0.05, min(5, val))
        spm_delays[update.message.chat_id] = val
        await safe_reply(update, f"⚡ Spam speed = `{val}s` (applies to running & new spam)", parse_mode="Markdown")
    except:
        await safe_reply(update, "❌ Invalid")

# ╔════════════════════════════════════════════════════════════════╗
# ║                COMMANDS - SLIDE & TARGET                       ║
# ╚════════════════════════════════════════════════════════════════╝

@only_sudo
async def slidespam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return await safe_reply(update, "⚠️ Reply to a message", parse_mode="Markdown")
    uid = update.message.reply_to_message.from_user.id
    text = extract_command_text(update.message.text)
    if not text:
        return await safe_reply(update, "⚠️ `/slidespam <text>`", parse_mode="Markdown")
    if uid in slidespam_tasks:
        for t in slidespam_tasks[uid]:
            try:
                t.cancel()
            except:
                pass
    slidespam_tasks[uid] = []
    chat_id = update.message.chat_id
    msg_id = update.message.reply_to_message.message_id
    for bot in bots:
        task = asyncio.create_task(slidespam_worker(bot, chat_id, msg_id, text))
        slidespam_tasks[uid].append(task)
    await safe_reply(update, "💬 Slide spam activated")

@only_sudo
async def stopslidespam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return
    uid = update.message.reply_to_message.from_user.id
    if uid in slidespam_tasks:
        for t in slidespam_tasks[uid]:
            try:
                t.cancel()
            except:
                pass
        del slidespam_tasks[uid]
        await safe_reply(update, "🛑 Slide spam stopped")

@only_sudo
async def targetslide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return await safe_reply(update, "⚠️ Reply please", parse_mode="Markdown")
    uid = update.message.reply_to_message.from_user.id
    name = " ".join(context.args) if context.args else update.message.reply_to_message.from_user.first_name
    if uid in targetslide_tasks:
        for t in targetslide_tasks[uid]:
            try:
                t.cancel()
            except:
                pass
    targetslide_tasks[uid] = []
    chat_id = update.message.chat_id
    msg_id = update.message.reply_to_message.message_id
    for bot in bots:
        task = asyncio.create_task(targetslide_worker(bot, chat_id, msg_id, name))
        targetslide_tasks[uid].append(task)
    await safe_reply(update, "🎯 Target slide activated")

@only_sudo
async def stoptargetslide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return
    uid = update.message.reply_to_message.from_user.id
    if uid in targetslide_tasks:
        for t in targetslide_tasks[uid]:
            try:
                t.cancel()
            except:
                pass
        del targetslide_tasks[uid]
        await safe_reply(update, "🛑 Target slide stopped")

# ╔════════════════════════════════════════════════════════════════╗
# ║                   COMMANDS - MEDIA SPAM                        ║
# ╚════════════════════════════════════════════════════════════════╝

@only_sudo
async def stickerspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.sticker:
        return await safe_reply(update, "⚠️ Reply to sticker", parse_mode="Markdown")
    file_id = update.message.reply_to_message.sticker.file_id
    chat_id = update.message.chat_id
    unique_msg_id = f"{chat_id}_{update.message.message_id}"
    if unique_msg_id in global_replied_messages:
        return
    global_replied_messages.add(unique_msg_id)
    task_id = str(random.randint(10000, 99999))
    active_menus[task_id] = {"cmd": "stickerspm", "chat_id": chat_id, "payload": file_id, "selected": set()}
    await update.message.reply_text("🎭 STICKER SPAM - Select Bots", reply_markup=get_selector_keyboard(task_id), parse_mode="Markdown")

@only_sudo
async def stopstickerspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in sticker_spm_tasks:
        for t in sticker_spm_tasks[chat_id]:
            try:
                t.cancel()
            except:
                pass
        sticker_spm_tasks[chat_id] = []
        await safe_reply(update, "🛑 Sticker spam stopped")

@only_sudo
async def gifspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.animation:
        return await safe_reply(update, "⚠️ Reply to GIF", parse_mode="Markdown")
    file_id = update.message.reply_to_message.animation.file_id
    chat_id = update.message.chat_id
    unique_msg_id = f"{chat_id}_{update.message.message_id}"
    if unique_msg_id in global_replied_messages:
        return
    global_replied_messages.add(unique_msg_id)
    task_id = str(random.randint(10000, 99999))
    active_menus[task_id] = {"cmd": "gifspm", "chat_id": chat_id, "payload": file_id, "selected": set()}
    await update.message.reply_text("🎥 GIF SPAM - Select Bots", reply_markup=get_selector_keyboard(task_id), parse_mode="Markdown")

@only_sudo
async def stopgifspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in gif_spm_tasks:
        for t in gif_spm_tasks[chat_id]:
            try:
                t.cancel()
            except:
                pass
        gif_spm_tasks[chat_id] = []
        await safe_reply(update, "🛑 GIF spam stopped")

@only_sudo
async def mediaspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not (update.message.reply_to_message.photo or update.message.reply_to_message.video):
        return await safe_reply(update, "⚠️ Reply to photo/video", parse_mode="Markdown")
    if update.message.reply_to_message.photo:
        file_id = update.message.reply_to_message.photo[-1].file_id
        media_type = "photo"
    else:
        file_id = update.message.reply_to_message.video.file_id
        media_type = "video"
    chat_id = update.message.chat_id
    unique_msg_id = f"{chat_id}_{update.message.message_id}"
    if unique_msg_id in global_replied_messages:
        return
    global_replied_messages.add(unique_msg_id)
    task_id = str(random.randint(10000, 99999))
    active_menus[task_id] = {"cmd": "mediaspm", "type": media_type, "chat_id": chat_id, "payload": file_id, "selected": set()}
    await update.message.reply_text("🖼️ MEDIA SPAM - Select Bots", reply_markup=get_selector_keyboard(task_id), parse_mode="Markdown")

@only_sudo
async def stopmediaspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in media_spm_tasks:
        for t in media_spm_tasks[chat_id]:
            try:
                t.cancel()
            except:
                pass
        media_spm_tasks[chat_id] = []
        await safe_reply(update, "🛑 Media spam stopped")

@only_sudo
async def voicespm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.voice:
        return await safe_reply(update, "⚠️ Reply to voice", parse_mode="Markdown")
    file_id = update.message.reply_to_message.voice.file_id
    chat_id = update.message.chat_id
    unique_msg_id = f"{chat_id}_{update.message.message_id}"
    if unique_msg_id in global_replied_messages:
        return
    global_replied_messages.add(unique_msg_id)
    task_id = str(random.randint(10000, 99999))
    active_menus[task_id] = {"cmd": "voicespm", "chat_id": chat_id, "payload": file_id, "selected": set()}
    await update.message.reply_text("🎤 VOICE SPAM - Select Bots", reply_markup=get_selector_keyboard(task_id), parse_mode="Markdown")

@only_sudo
async def stopvoicespm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in voice_spm_tasks:
        for t in voice_spm_tasks[chat_id]:
            try:
                t.cancel()
            except:
                pass
        voice_spm_tasks[chat_id] = []
        await safe_reply(update, "🛑 Voice spam stopped")

# ╔════════════════════════════════════════════════════════════════╗
# ║                      COMMANDS - PFP                            ║
# ╚════════════════════════════════════════════════════════════════╝

@only_sudo
async def save_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        return await safe_reply(update, "⚠️ Reply to photo", parse_mode="Markdown")
    chat_id = update.message.chat_id
    photo = update.message.reply_to_message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    os.makedirs(f"downloads/{chat_id}", exist_ok=True)
    path = f"downloads/{chat_id}/{photo.file_unique_id}.jpg"
    await file.download_to_drive(path)
    saved_pfps[chat_id] = path
    await safe_reply(update, "📸 PFP saved (use /setpfp or /pfp)")

@only_sudo
async def del_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        return await safe_reply(update, "⚠️ Reply to photo", parse_mode="Markdown")
    chat_id = update.message.chat_id
    uid = update.message.reply_to_message.photo[-1].file_unique_id
    path = f"downloads/{chat_id}/{uid}.jpg"
    if os.path.exists(path):
        os.remove(path)
        await safe_reply(update, "🗑 PFP deleted")
    else:
        await safe_reply(update, "⚠️ Not found")

@only_sudo
async def setpfp_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.reply_to_message or not update.message.reply_to_message.photo:
        return await safe_reply(update, "⚠️ Reply to a photo with /setpfp")

    msg = await update.message.reply_text("🖼 Updating bot pfps...")

    photo = update.message.reply_to_message.photo[-1]
    tg_file = await context.bot.get_file(photo.file_id)

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
            temp_path = f.name

        await tg_file.download_to_drive(temp_path)

        if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
            return await msg.edit_text("❌ Download failed")

        ok = 0
        fail = 0

        for token in bot_tokens:
            if not token:
                continue

            try:
                url = f"https://api.telegram.org/bot{token}/setMyProfilePhoto"

                with open(temp_path, "rb") as img:
                    files = {"photo": img}
                    r = requests.post(url, files=files, timeout=30)

                res = r.json()

                if res.get("ok"):
                    ok += 1
                else:
                    fail += 1

            except Exception as e:
                fail += 1

        await msg.edit_text(f"🖼 DONE✅ Success: {ok} ❌ Failed: {fail}")

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

@only_sudo
async def pfp_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    folder = f"downloads/{chat_id}"
    if not os.path.exists(folder) or not os.listdir(folder):
        return await safe_reply(update, "⚠️ No PFPs. Use `/save` first", parse_mode="Markdown")
    unique_msg_id = f"{chat_id}_{update.message.message_id}"
    if unique_msg_id in global_replied_messages:
        return
    global_replied_messages.add(unique_msg_id)
    task_id = str(random.randint(10000, 99999))
    active_menus[task_id] = {"cmd": "pfp", "chat_id": chat_id, "payload": "", "selected": set()}
    await update.message.reply_text("📸 PFP ROTATION - Select Bots", reply_markup=get_selector_keyboard(task_id), parse_mode="Markdown")

@only_sudo
async def stoppfp_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    stopped = False
    if chat_id in pfp_tasks:
        for t in pfp_tasks[chat_id]:
            try:
                t.cancel()
                stopped = True
            except:
                pass
        pfp_tasks[chat_id] = []
    if chat_id in setpfp_tasks:
        for t in setpfp_tasks[chat_id]:
            try:
                t.cancel()
                stopped = True
            except:
                pass
        setpfp_tasks[chat_id] = []
    if stopped:
        await safe_reply(update, "🛑 PFP stopped")

# ╔════════════════════════════════════════════════════════════════╗
# ║                COMMANDS - SWIPE & AUTO-REPLY                   ║
# ╚════════════════════════════════════════════════════════════════╝

@only_sudo
async def swipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await safe_reply(update, "⚠️ `/swipe <name>`", parse_mode="Markdown")
    swipe_mode[update.message.chat_id] = " ".join(context.args)
    await safe_reply(update, "⚡ Swipe mode activated")

@only_sudo
async def stopswipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    swipe_mode.pop(update.message.chat_id, None)
    await safe_reply(update, "🛑 Swipe mode disabled")

@only_sudo
async def replyryuk_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = await get_target_user(update, context)
    if not uid:
        return await safe_reply(update, "⚠️ Reply/mention user")
    replyryuk_targets.add(uid)
    await safe_reply(update, "💬 Auto-reply activated")

@only_sudo
async def stopreplyryuk_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = await get_target_user(update, context)
    if not uid:
        return await safe_reply(update, "⚠️ Reply/mention")
    replyryuk_targets.discard(uid)
    last_ryuk_reply.pop(uid, None)
    await safe_reply(update, "🛑 Auto-reply disabled")

# ╔════════════════════════════════════════════════════════════════╗
# ║                  COMMANDS - ADMIN FUNCTIONS                    ║
# ╚════════════════════════════════════════════════════════════════╝

@only_owner
async def addsudo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = await get_target_user(update, context)
    if uid:
        SUDO_USERS.add(uid)
        save_sudo()
        mention = await get_mention_from_id(context, uid)
        await safe_reply(update, f"👑 {mention} is now SUDO", parse_mode="Markdown")

@only_owner
async def delsudo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = await get_target_user(update, context)
    if uid and uid in SUDO_USERS:
        SUDO_USERS.remove(uid)
        save_sudo()
        mention = await get_mention_from_id(context, uid)
        await safe_reply(update, f"🗑 {mention} removed from SUDO", parse_mode="Markdown")

@only_sudo
async def listsudo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "👑 SUDO Users:\n\n"
    for uid in SUDO_USERS:
        mention = await get_mention_from_id(context, uid)
        text += f"• {mention}\n"
    await safe_reply(update, text, parse_mode="Markdown")

@only_sudo
async def mute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = await get_target_user(update, context)
    if not uid:
        return await safe_reply(update, "⚠️ Reply/mention user")
    muted_users.add(uid)
    mention = await get_mention_from_id(context, uid)
    await safe_reply(update, f"🔇 {mention} muted", parse_mode="Markdown")

@only_sudo
async def unmute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = await get_target_user(update, context)
    if not uid:
        return
    muted_users.discard(uid)
    mention = await get_mention_from_id(context, uid)
    await safe_reply(update, f"🔊 {mention} unmuted", parse_mode="Markdown")

@only_sudo
async def mutelist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not muted_users:
        return await safe_reply(update, "📭 No muted users")
    text = "🔇 Muted Users:\n\n"
    for uid in muted_users:
        mention = await get_mention_from_id(context, uid)
        text += f"• {mention}\n"
    await safe_reply(update, text, parse_mode="Markdown")

@only_sudo
async def promote_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = await get_target_user(update, context)
    if not uid:
        return await safe_reply(update, "⚠️ Reply/mention user")
    try:
        await context.bot.promote_chat_member(
            chat_id=update.message.chat_id, user_id=uid,
            can_change_info=True, can_delete_messages=True, can_invite_users=True,
            can_restrict_members=True, can_pin_messages=True, can_promote_members=True,
            can_manage_chat=True, can_manage_video_chats=True, is_anonymous=False
        )
        mention = await get_mention_from_id(context, uid)
        await safe_reply(update, f"✅ {mention} promoted", parse_mode="Markdown")
    except Exception as e:
        await safe_reply(update, f"❌ Error: {e}")

@only_sudo
async def demote_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = await get_target_user(update, context)
    if not uid:
        return
    try:
        await context.bot.promote_chat_member(
            chat_id=update.message.chat_id, user_id=uid,
            can_change_info=False, can_delete_messages=False, can_invite_users=False,
            can_restrict_members=False, can_pin_messages=False, can_promote_members=False,
            can_manage_chat=False, can_manage_video_chats=False, is_anonymous=False
        )
        mention = await get_mention_from_id(context, uid)
        await safe_reply(update, f"🛑 {mention} demoted", parse_mode="Markdown")
    except Exception as e:
        await safe_reply(update, f"❌ {e}")

@only_sudo
async def promoteallbots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    success = 0
    for bot in bots:
        try:
            await context.bot.promote_chat_member(
                chat_id=update.message.chat_id, user_id=bot.id,
                can_change_info=True, can_delete_messages=True, can_invite_users=True,
                can_restrict_members=True, can_pin_messages=True, can_promote_members=True,
                can_manage_chat=True, can_manage_video_chats=True, is_anonymous=False
            )
            success += 1
        except:
            pass
    await safe_reply(update, f"🤖 Promoted {success} bots")

@only_sudo
async def promoteall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if not known_users:
        return await safe_reply(update, "⚠️ No users found yet")
    unique_msg_id = f"{chat_id}_{update.message.message_id}"
    if unique_msg_id in global_replied_messages:
        return
    global_replied_messages.add(unique_msg_id)
    msg = await update.message.reply_text("⏳ Promoting all users...", parse_mode="Markdown")
    success = 0
    for uid in list(known_users):
        try:
            await context.bot.promote_chat_member(
                chat_id=chat_id, user_id=uid,
                can_change_info=True, can_delete_messages=False, can_invite_users=True,
                can_restrict_members=False, can_pin_messages=True, can_promote_members=True,
                can_manage_chat=True, can_manage_video_chats=True, is_anonymous=False
            )
            success += 1
        except:
            pass
    await msg.edit_text(f"✅ Promoted {success} users", parse_mode="Markdown")

# ╔════════════════════════════════════════════════════════════════╗
# ║            COMMANDS - MULTI-BOT CONTROL                        ║
# ╚════════════════════════════════════════════════════════════════╝

@only_sudo
async def activebots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not bots:
        return await safe_reply(update, "❌ No active bots")

    lines = []
    for bot in bots:
        try:
            me = await bot.get_me()
            uname = "@" + me.username if me.username else "NO_USERNAME"
            lines.append(f"• {uname} | {me.first_name}")
        except Exception as e:
            lines.append(f"• ERROR: {e}")

    text = "🤖 ACTIVE BOTS\n\n" + "\n".join(lines) + f"\n\n✅ Total: {len(bots)}"
    await safe_reply(update, text)

@only_sudo
async def leave_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    await safe_reply(update, "👋 All bots leaving...")
    for bot in bots:
        try:
            await bot.leave_chat(chat_id)
        except:
            pass

@only_sudo
async def addbots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pending_addbots.add(update.effective_user.id)
    await update.message.reply_text("📝 Send bot tokens.\nOne token per line.")

async def token_receiver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    if text.startswith("+") or text.startswith("/"):
        return

    uid = update.effective_user.id
    if uid not in pending_addbots:
        return

    pending_addbots.remove(uid)

    tokens = [x.strip() for x in text.splitlines() if x.strip()]

    success = 0
    failed = 0
    added_names = []
    removed_invalid = []

    for token in tokens:
        try:
            if token in ACTIVE_BOTS:
                continue

            is_valid = await validate_bot_token(token)
            if not is_valid:
                removed_invalid.append(token[:20] + "...")
                continue

            await run_worker(token)
            bot = Application.builder().token(token).build().bot
            me = await bot.get_me()

            add_bot_db(token, me.username or me.first_name)
            added_names.append(f"@{me.username}" if me.username else me.first_name)
            success += 1

        except Exception as e:
            failed += 1

    text = f"🤖 ADD BOTS RESULT\n\n✅ Added: {success}\n❌ Failed: {failed}\n"
    
    if removed_invalid:
        text += f"🚫 Invalid Tokens: {len(removed_invalid)}\n"

    if added_names:
        text += "\n" + "\n".join(f"• {x}" for x in added_names)

    await update.message.reply_text(text)

@only_sudo
async def listbots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bots_list = get_bots_db()
    if not bots_list:
        return await safe_reply(update, "❌ No bots registered")
    msg = "🤖 **Saved Bots**\n\n" + "\n".join([f"• `{name or 'Unknown'}`" for _, name in bots_list])
    await safe_reply(update, msg, parse_mode="Markdown")

@only_sudo
async def listallbots_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all active bots with their usernames"""
    if not bots:
        return await safe_reply(update, "❌ No active bots")
    
    text = "🤖 **Active Bots**\n\n"
    for bot in bots:
        try:
            me = await bot.get_me()
            username = f"@{me.username}" if me.username else "<unknown>"
            text += f"• `{username}`\n"
        except:
            text += "• `ERROR`\n"
    
    text += f"\n✅ **Total: {len(bots)} bots**"
    await safe_reply(update, text, parse_mode="Markdown")

@only_sudo
async def getallgclinks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get all group chat links where bots are present (group chats only, not channels or personal chats)"""
    if not bot_group_cache:
        return await safe_reply(update, "⚠️ No groups tracked yet")
    
    all_chats = set()
    for bot_id, chats in bot_group_cache.items():
        all_chats.update(chats)
    
    if not all_chats:
        return await safe_reply(update, "⚠️ No groups found")
    
    group_links = []
    for chat_id in sorted(all_chats):
        try:
            chat = await context.bot.get_chat(chat_id)
            if chat.type not in ["supergroup", "group"]:
                continue
            link = chat.invite_link if hasattr(chat, 'invite_link') and chat.invite_link else f"ID: `{chat_id}`"
            title = chat.title or "Unknown"
            group_links.append((title, link))
        except:
            pass
    
    if not group_links:
        return await safe_reply(update, "⚠️ No group chats found (channels and personal chats were excluded)")
    
    text = f"📋 **Group Chats ({len(group_links)} total):**\n\n"
    for idx, (title, link) in enumerate(group_links, 1):
        text += f"{idx}. {title}\n"
        text += f"   └─ {link}\n\n"
    
    text += "✅ To leave all groups, use `/leaveallgroups`"
    await safe_reply(update, text, parse_mode="Markdown")

@only_sudo
async def leaveallgroups_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Leave all group chats"""
    if not bot_group_cache:
        return await safe_reply(update, "⚠️ No groups to leave")
    
    all_chats = set()
    for bot_id, chats in bot_group_cache.items():
        all_chats.update(chats)
    
    if not all_chats:
        return await safe_reply(update, "⚠️ No groups found")
    
    msg = await update.message.reply_text(f"👋 Leaving {len(all_chats)} groups...")
    
    success = 0
    for bot in bots:
        for chat_id in list(all_chats):
            try:
                await bot.leave_chat(chat_id)
                success += 1
            except:
                pass
    
    await msg.edit_text(f"✅ Left groups! ({success} operations completed)")

@only_owner
async def rnbots_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rename all bots with new name - Owner Only"""
    if not context.args:
        return await safe_reply(update, "⚠️ `/rnbots <new_name>`", parse_mode="Markdown")
    new_name = " ".join(context.args)
    success = 0
    for bot in bots:
        try:
            await bot.set_my_name(new_name)
            success += 1
        except:
            pass
    
    for token, username in get_bots_db():
        add_bot_db(token, new_name)
    
    await safe_reply(update, f"✅ Renamed {success} bots to `{new_name}`", parse_mode="Markdown")

# ╔════════════════════════════════════════════════════════════════╗
# ║           NEW COMMANDS - Plus Prefix (+) Version               ║
# ╚════════════════════════════════════════════════════════════════╝

@only_sudo
async def plus_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop all operations - Plus prefix version"""
    await stopall_cmd(update, context)

@only_sudo  
async def plus_optimize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Optimize memory - Plus prefix version"""
    await optimize_cmd(update, context)

@only_sudo
async def plus_flood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Flood with messages - aliases to spm"""
    await spm_cmd(update, context)

@only_sudo
async def plus_wave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Wave emoji spam"""
    if not context.args:
        return await safe_reply(update, "⚠️ `+wave` - uses emoji NC", parse_mode="Markdown")
    await ncemo_cmd(update, context)

@only_sudo
async def plus_halt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Halt all activities"""
    await stopall_cmd(update, context)

@only_sudo
async def plus_haltlock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Halt and lock - stops all operations"""
    await stopall_cmd(update, context)

@only_sudo
async def plus_killall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kill all operations"""
    await stopall_cmd(update, context)

@only_sudo
async def plus_phase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rotating name changes with emojis"""
    if not context.args:
        return await safe_reply(update, "⚠️ `+phase <name>`", parse_mode="Markdown")
    await pyramidnc_cmd(update, context)

@only_sudo
async def plus_stnc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start pyramid/rotating NC"""
    if not context.args:
        return await safe_reply(update, "⚠️ `+stnc <name>`", parse_mode="Markdown")
    await pyramidnc_cmd(update, context)

@only_sudo
async def plus_haltnc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop all NC operations"""
    await stopgcnc(update, context)

@only_sudo
async def plus_silnt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Silent stop equivalent"""
    await plus_stop(update, context)

@only_sudo
async def plus_gcnc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start group text NC"""
    if not context.args:
        return await safe_reply(update, "⚠️ `+gcnc <text>`", parse_mode="Markdown")
    await gcnc(update, context)

@only_sudo
async def plus_ncemo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start emoji NC"""
    if not context.args:
        return await safe_reply(update, "⚠️ `+ncemo <text>`", parse_mode="Markdown")
    await ncemo_cmd(update, context)

@only_sudo
async def plus_stopgcnc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop NC operations"""
    await stopgcnc(update, context)

@only_sudo
async def plus_delaync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set NC delay"""
    if not context.args:
        return await safe_reply(update, "⚠️ `+delaync <seconds>`", parse_mode="Markdown")
    await delaync_cmd(update, context)

@only_sudo
async def plus_stopspm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop local spam"""
    await stopspm_cmd(update, context)

@only_sudo
async def plus_stopallspm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop all spam"""
    await stopallspm_cmd(update, context)

@only_sudo
async def plus_delaygcspm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set spam delay"""
    if not context.args:
        return await safe_reply(update, "⚠️ `+delaygcspm <seconds>`", parse_mode="Markdown")
    await delaygcspm_cmd(update, context)

@only_sudo
async def plus_botcount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show active bot count"""
    await activebots(update, context)

@only_sudo
async def plus_stickstorm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sticker spam alias"""
    await stickerspm_cmd(update, context)

@only_sudo
async def plus_gifblast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """GIF spam alias"""
    await gifspm_cmd(update, context)

@only_sudo
async def plus_mediaraid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Media spam alias"""
    await mediaspm_cmd(update, context)

@only_sudo
async def plus_voicestorm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Voice spam alias"""
    await voicespm_cmd(update, context)

@only_sudo
async def plus_stopstick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop sticker spam"""
    await stopstickerspm_cmd(update, context)

@only_sudo
async def plus_stopgif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop GIF spam"""
    await stopgifspm_cmd(update, context)

@only_sudo
async def plus_stopmedia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop media spam"""
    await stopmediaspm_cmd(update, context)

@only_sudo
async def plus_stopvoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop voice spam"""
    await stopvoicespm_cmd(update, context)

@only_sudo
async def plus_slideraid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Slide spam alias"""
    await slidespam(update, context)

@only_sudo
async def plus_lockslide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start target slide"""
    if not context.args:
        return await safe_reply(update, "⚠️ `+lockslide <name>`", parse_mode="Markdown")
    await targetslide(update, context)

@only_sudo
async def plus_stopslide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop slide spam"""
    await stopslidespam(update, context)

@only_sudo
async def plus_unlockslide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop target slide"""
    await stoptargetslide(update, context)

@only_sudo
async def plus_savepfp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save PFP alias"""
    await save_cmd(update, context)

@only_sudo
async def plus_delpfp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete PFP alias"""
    await del_cmd(update, context)

@only_sudo
async def plus_applypfp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set PFP rotation alias"""
    await setpfp_cmd(update, context)

@only_sudo
async def plus_viewpfp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start PFP rotation alias"""
    await pfp_cmd(update, context)

@only_sudo
async def plus_freezepfp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop PFP alias"""
    await stoppfp_cmd(update, context)

@only_sudo
async def plus_autoswipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start swipe mode alias"""
    await swipe(update, context)

@only_sudo
async def plus_stopswipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop swipe alias"""
    await stopswipe(update, context)

@only_sudo
async def plus_autoreply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Auto reply alias"""
    await replyryuk_cmd(update, context)

@only_sudo
async def plus_stopreply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop auto reply alias"""
    await stopreplyryuk_cmd(update, context)

@only_sudo
async def plus_silence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mute alias"""
    await mute_cmd(update, context)

@only_sudo
async def plus_unsilence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unmute alias"""
    await unmute_cmd(update, context)

@only_sudo
async def plus_mutelog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List muted members alias"""
    await mutelist_cmd(update, context)

@only_sudo
async def plus_elevate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Promote alias"""
    await promote_cmd(update, context)

@only_sudo
async def plus_downgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Demote alias"""
    await demote_cmd(update, context)

@only_sudo
async def plus_elevateall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Promote all bots alias"""
    await promoteallbots(update, context)

@only_sudo
async def plus_elevatebots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Promote all bots alias"""
    await promoteallbots(update, context)

@only_sudo
async def plus_addauthority(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add sudo alias"""
    await addsudo_cmd(update, context)

@only_sudo
async def plus_delauthority(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove sudo alias"""
    await delsudo_cmd(update, context)

@only_sudo
async def plus_authoritylist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List sudo alias"""
    await listsudo_cmd(update, context)

@only_sudo
async def plus_loadbots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Load bots alias"""
    await addbots(update, context)

@only_sudo
async def plus_bots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List saved bots alias"""
    await listbots(update, context)

@only_sudo
async def plus_allbots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List active bots alias"""
    await listallbots_cmd(update, context)

@only_sudo
async def plus_renamebots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rename all bots alias"""
    await rnbots_cmd(update, context)

@only_owner
async def plus_botowners(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot owners in DM"""
    await botowners_cmd(update, context)

@only_sudo
async def plus_elevateallusers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Promote all users alias"""
    await promoteall(update, context)

@only_sudo
async def plus_latency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check latency"""
    await ping_cmd(update, context)

@only_sudo
async def plus_userid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show your user ID"""
    await myid(update, context)

@only_sudo
async def plus_fetchlinks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch all group links"""
    await getallgclinks_cmd(update, context)

@only_sudo
async def plus_exitall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Make all bots leave all groups"""
    await leaveallgroups_cmd(update, context)

@only_sudo
async def plus_exitgc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Make all bots leave all groups"""
    await leaveallgroups_cmd(update, context)

@only_sudo
async def plus_latency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check latency"""
    await ping_cmd(update, context)

@only_sudo
async def plus_userid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show your user ID"""
    await myid(update, context)

@only_sudo
async def plus_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the bot menu"""
    await help_cmd(update, context)

@only_owner
async def plus_rnbots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rename all bots"""
    await rnbots_cmd(update, context)

async def plus_command_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    if not text.startswith("+"):
        return

    parts = text[1:].split(" ", 1)
    cmd = parts[0].lower()
    args = parts[1].split() if len(parts) > 1 else []
    context.args = args

    plus_map = {
        "stop": plus_stop,
        "halt": plus_halt,
        "haltlock": plus_haltlock,
        "killall": plus_killall,
        "optimize": plus_optimize,
        "flood": plus_flood,
        "wave": plus_wave,
        "phase": plus_phase,
        "stnc": plus_stnc,
        "haltnc": plus_haltnc,
        "silnt": plus_silnt,
        "ryuknc": plus_gcnc,
        "emojify": plus_ncemo,
        "orbit": plus_phase,
        "gcnc": plus_gcnc,
        "nc": plus_gcnc,
        "ncemo": plus_ncemo,
        "stopgcnc": plus_stopgcnc,
        "ncspeed": plus_delaync,
        "delaync": plus_delaync,
        "blast": plus_flood,
        "haltspm": plus_stopspm,
        "stopspm": plus_stopallspm,
        "spmspeed": plus_delaygcspm,
        "stickstorm": plus_stickstorm,
        "gifblast": plus_gifblast,
        "mediaraid": plus_mediaraid,
        "voicestorm": plus_voicestorm,
        "stopstick": plus_stopstick,
        "stopgif": plus_stopgif,
        "stopmedia": plus_stopmedia,
        "stopvoice": plus_stopvoice,
        "slideraid": plus_slideraid,
        "lockslide": plus_lockslide,
        "stopslide": plus_stopslide,
        "unlockslide": plus_unlockslide,
        "savepfp": plus_savepfp,
        "delpfp": plus_delpfp,
        "applypfp": plus_applypfp,
        "viewpfp": plus_viewpfp,
        "freezepfp": plus_freezepfp,
        "autoswipe": plus_autoswipe,
        "stopswipe": plus_stopswipe,
        "autoreply": plus_autoreply,
        "stopreply": plus_stopreply,
        "silence": plus_silence,
        "unsilence": plus_unsilence,
        "mutelog": plus_mutelog,
        "elevate": plus_elevate,
        "downgrade": plus_downgrade,
        "elevateall": plus_elevateall,
        "elevatebots": plus_elevatebots,
        "addauthority": plus_addauthority,
        "delauthority": plus_delauthority,
        "authoritylist": plus_authoritylist,
        "loadbots": plus_loadbots,
        "bots": plus_bots,
        "allbots": plus_allbots,
        "renamebots": plus_renamebots,
        "botcount": plus_botcount,
        "fetchlinks": plus_fetchlinks,
        "exitall": plus_exitall,
        "exitgc": plus_exitgc,
        "botowners": plus_botowners,
        "latency": plus_latency,
        "userid": plus_userid,
        "menu": plus_menu,
        "elevateallusers": plus_elevateallusers,
        "rnbots": plus_rnbots,
    }

    if cmd in plus_map:
        await plus_map[cmd](update, context)

# ╔════════════════════════════════════════════════════════════════╗
# ║              AUTO-REPLIES & MESSAGE HANDLING                   ║
# ╚════════════════════════════════════════════════════════════════╝

async def auto_replies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.from_user:
        return
    
    chat_id = update.message.chat_id
    uid = update.message.from_user.id
    known_chats.add(chat_id)
    known_users.add(uid)
    
    await update_bot_group_cache(context.bot.id, chat_id)

    if uid in muted_users:
        try:
            await update.message.delete()
        except:
            pass
        return

    if uid in replyryuk_targets and REPLY_RYUK_TEXTS:
        now_ts = time.time()
        bot_id = context.bot.id
        user_bot_cooldowns = last_ryuk_reply.setdefault(uid, {})
        if now_ts - user_bot_cooldowns.get(bot_id, 0) >= 0.2:
            user_bot_cooldowns[bot_id] = now_ts
            try:
                await update.message.reply_text(random.choice(REPLY_RYUK_TEXTS), reply_to_message_id=update.message.message_id)
            except:
                pass

    if update.message.from_user.is_bot:
        return

    if chat_id in swipe_mode:
        name_arg = swipe_mode[chat_id]
        template = random.choice(SWIPE_TEXTS)
        try:
            await update.message.reply_text(template.replace("NAME", name_arg))
        except:
            pass

async def kicked_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bot kicked/left notifications"""
    if not update.my_chat_member:
        return
    
    try:
        chat_id = update.my_chat_member.chat.id
        new_status = update.my_chat_member.new_chat_member.status
        
        if new_status in ["kicked", "left"]:
            try:
                bot_me = await context.bot.get_me()
                bot_name = f"@{bot_me.username}" if bot_me.username else f"Bot {bot_me.id}"
            except:
                bot_name = "Unknown Bot"
            
            try:
                chat_info = await context.bot.get_chat(chat_id)
                chat_name = chat_info.title or f"Chat {chat_id}"
            except:
                chat_name = f"Chat {chat_id}"
            
            for bot_id in list(bot_group_cache.keys()):
                if chat_id in bot_group_cache.get(bot_id, set()):
                    bot_group_cache[bot_id].discard(chat_id)
            
            status_text = "🚫 KICKED" if new_status == "kicked" else "👋 LEFT"
            try:
                await context.bot.send_message(
                    chat_id=OWNER_ID,
                    text=f"{status_text}\n\n`{bot_name}` has been {new_status} from `{chat_name}`",
                    parse_mode="Markdown"
                )
            except:
                pass
    except:
        pass

async def tracker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.effective_chat:
            return
        chat_id = update.effective_chat.id
        if chat_id < 0:
            # Only update for the bot that received the message
            add_group_db(context.bot.token, chat_id)
            await update_bot_group_cache(context.bot.id, chat_id)
    except Exception as e:
        logger.error(f"[TRACKER] Error updating group cache: {e}")


# ╔════════════════════════════════════════════════════════════════╗
# ║                    SPAM TEXTS & EMOJIS                         ║
# ╚════════════════════════════════════════════════════════════════╝

RAID_TEXTS = ["𝘊𝘏𝘜D", "𝘓𝘜𝘕𝘋 𝘒𝘈𝘏𝘈", "𝘗𝘐𝘓LE", "𝘊𝘏𝘐KNE", "𝘎andu", "PENKELODE", "𝘜𝘛𝘏 MC", "𝘓𝘜𝘕𝘋 𝘓E",]
NCEMO_EMOJIS = ["👻", "🩷", "😂", "🤣", "♥️", "💦", "😹", "🥶", "🥀", "🎀", "😈", "👑", "😤", "🤷", "👅", "🤙", "🤦", "😏", "👏", "🔥", "💥", "✌️", "🩸", "❤️‍🔥", "💀", "🤪", "😱"]
SWIPE_TEXTS = ["NAME RNDI", "NAME tmkc", "pille NAME", "NAME 𝘒𝙖 bhosda"]
TARGET_SLIDE_TEXTS = ["{} 𝘜𝙏𝙃🤣", "{} TMKC", "{} 𝘊𝙖𝙢 garl🤣", "{} teri ma ke lund baja ke uska gala daba dunga"]
REPLY_RYUK_TEXTS = ["BHEN CHUDA NA RNDI","chal teri mkc"]

# ╔════════════════════════════════════════════════════════════════╗
# ║                    GLOBAL STATE                                ║
# ╚════════════════════════════════════════════════════════════════╝

class LRUCache:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity
    
    def add(self, key):
        self.cache[key] = None
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
    
    def __contains__(self, key):
        return key in self.cache

global_replied_messages = LRUCache(5000)

if os.path.exists(ADMIN_FILE):
    try:
        with open(ADMIN_FILE, "r") as f:
            SUDO_USERS = set(int(x) for x in json.load(f))
    except:
        SUDO_USERS = {OWNER_ID}
else:
    SUDO_USERS = {OWNER_ID}

def save_sudo():
    with open(ADMIN_FILE, "w") as f:
        json.dump(list(SUDO_USERS), f)

# Global state
apps, bots, bot_usernames, bot_tokens = [], [], [], []
ACTIVE_BOTS = {}
RUNNING_APPLICATIONS = {}
bot_group_cache = {}  # {bot_id: set(chat_ids_where_bot_is_present)}

# ╔════════════════════════════════════════════════════════════════╗
# ║                    TASK TRACKING (MINIMAL)                     ║
# ╚════════════════════════════════════════════════════════════════╝

# Only keeping what we need: NC + SPM
group_tasks = {}           # For Raid NC & Emoji NC
spm_loop_tasks = {}        # For message spam

# ── User-controlled delays ───────────────────────────────────────
nc_delays = {}             # Per-chat NC delay
spm_delays = {}            # Per-chat Spam delay

global_nc_delay = 0.1      # Global default for NC
global_spm_delay = 0.05    # Global default for Spam

gc_delays = {}             # Advanced per-chat delay config (if used)

# Tracking
known_chats, known_users = set(), set()
replyryuk_targets = set()
last_ryuk_reply = {}
muted_users = set()
active_menus = {}
swipe_mode = {}
saved_pfps = {}  # {chat_id: file_path}
pending_addbots = set()
kicked_notifications = {}  # {bot_id: {chat_id: timestamp}} - track kicked notifications

# Action tracking for owner-initiated operations
owner_initiated_actions = {}  # {(chat_id, action_type): initiator_id}

# ╔════════════════════════════════════════════════════════════════╗
# ║                    DATABASE                                    ║
# ╚════════════════════════════════════════════════════════════════╝

def init_db():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bots (
            id INTEGER PRIMARY KEY, token TEXT UNIQUE, username TEXT, added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, added_by INTEGER
        )
    """)
    existing_columns = [row[1] for row in cur.execute("PRAGMA table_info(bots)").fetchall()]
    if "added_by" not in existing_columns:
        cur.execute("ALTER TABLE bots ADD COLUMN added_by INTEGER")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS groups (token TEXT, chat_id INTEGER, UNIQUE(token, chat_id))
    """)
    conn.commit()
    conn.close()

def add_bot_db(token, username="", added_by=None):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT added_by FROM bots WHERE token=?", (token,))
    row = cur.fetchone()
    if row is not None and added_by is None:
        added_by = row[0]
    cur.execute(
        "INSERT OR REPLACE INTO bots(token, username, added_by) VALUES(?, ?, ?)",
        (token, username, added_by),
    )
    conn.commit()
    conn.close()

def remove_bot_db(token):
    """Remove bot from database"""
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("DELETE FROM bots WHERE token=?", (token,))
    conn.commit()
    conn.close()

def get_bots_db():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT token, username FROM bots")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_bot_owners():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT token, username, added_by, added_at FROM bots")
    rows = cur.fetchall()
    conn.close()
    return rows

async def botowners_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return await safe_reply(update, "🔒 This command is owner-only and works in a private chat only.", parse_mode="Markdown")

    owners = get_bot_owners()
    if not owners:
        return await safe_reply(update, "⚠️ No bots found in the registry.", parse_mode="Markdown")

    lines = ["**Bot Registry (owner-only)**\n"]
    for token, username, added_by, added_at in owners:
        display_name = username or "<unknown>"
        added_by_text = f"`{added_by}`" if added_by else "`unknown`"
        added_at_text = added_at or "unknown"
        lines.append(f"• `{display_name}` — added by {added_by_text} on `{added_at_text}`")

    await safe_reply(update, "\n".join(lines), parse_mode="Markdown")

def add_group_db(token, chat_id):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO groups(token, chat_id) VALUES(?, ?)", (token, chat_id))
    conn.commit()
    conn.close()

def get_groups_db(token):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT chat_id FROM groups WHERE token=?", (token,))
    rows = cur.fetchall()
    conn.close()
    return [x[0] for x in rows]

# ╔════════════════════════════════════════════════════════════════╗
# ║                    HELPERS & DECORATORS                        ║
# ╚════════════════════════════════════════════════════════════════╝

async def safe_reply(update: Update, text: str, **kwargs):
    if not update.message:
        return
    unique_msg_id = f"{update.message.chat_id}_{update.message.message_id}"
    if unique_msg_id in global_replied_messages:
        return
    global_replied_messages.add(unique_msg_id)
    try:
        await update.message.reply_text(text, **kwargs)
    except:
        pass

def only_sudo(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or update.effective_user.id not in SUDO_USERS:
            return await safe_reply(update, "❌ 𝙉𝙤𝙩 𝘼𝙪𝙩𝙝𝙤𝙧𝙞𝙯𝙚𝙙.")
        return await func(update, context)
    return wrapper

def only_owner(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or update.effective_user.id != OWNER_ID:
            return await safe_reply(update, "❌ 𝙊𝙬𝙣𝙚𝙧 𝙊𝙣𝙡𝙮.")
        return await func(update, context)
    return wrapper

def extract_command_text(raw_text: Optional[str]) -> str:
    if not raw_text:
        return ""
    parts = raw_text.split(" ", 1)
    return parts[1].strip() if len(parts) > 1 else ""

async def get_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        return update.message.reply_to_message.from_user.id
    if update.message.entities:
        for entity in update.message.entities:
            if entity.type == 'text_mention':
                return entity.user.id
    if context.args:
        arg = context.args[0]
        try:
            return int(arg)
        except:
            if arg.startswith("@"):
                try:
                    return (await context.bot.get_chat(arg)).id
                except:
                    pass
    return None

async def get_mention_from_id(context, uid):
    try:
        return f"[{(await context.bot.get_chat(uid)).first_name}](tg://user?id={uid})"
    except:
        return f"`{uid}`"

def get_delay(chat_id, delay_type="nc"):
    """Get delay for chat - respects per-chat config"""
    if chat_id in gc_delays:
        if delay_type == "nc":
            return gc_delays[chat_id].get("nc", nc_delays.get(chat_id, global_nc_delay))
        elif delay_type == "spm":
            return gc_delays[chat_id].get("spm", spm_delays.get(chat_id, global_spm_delay))
    if delay_type == "nc":
        return nc_delays.get(chat_id, global_nc_delay)
    elif delay_type == "spm":
        return spm_delays.get(chat_id, global_spm_delay)
    return global_pfp_delay

async def validate_bot_token(token: str) -> bool:
    """Validate bot token by trying to get bot info"""
    try:
        app = Application.builder().token(token).build()
        me = await app.bot.get_me()
        return True
    except:
        return False

async def update_bot_group_cache(bot_id: int, chat_id: int):
    """Track which groups a bot is in"""
    if bot_id not in bot_group_cache:
        bot_group_cache[bot_id] = set()
    bot_group_cache[bot_id].add(chat_id)

def is_bot_in_chat(bot_id: int, chat_id: int) -> bool:
    """Check if bot is in a specific chat (based on message detection)"""
    if bot_id not in bot_group_cache:
        return False
    return chat_id in bot_group_cache[bot_id]

# Owner action tracking helpers
def mark_owner_action_v2(chat_id: int, action_type: str, initiator_id: int):
    """Mark an action as owner-initiated"""
    owner_initiated_actions[(chat_id, action_type)] = initiator_id

def can_stop_action_v2(user_id: int, chat_id: int, action_type: str) -> bool:
    """Check if user can stop an action. Owner can always stop, sudo can only stop actions they initiated"""
    # Owner can always stop anything
    if user_id == OWNER_ID:
        return True
    # Sudo can only stop actions they initiated themselves
    action_key = (chat_id, action_type)
    initiator = owner_initiated_actions.get(action_key)
    # If owner initiated it, sudo cannot stop
    if initiator == OWNER_ID:
        return False
    # If no one initiated it or someone else did, sudo cannot stop others' actions
    # Only stop if they initiated it
    return initiator == user_id if initiator else True  # Allow stopping non-tracked actions

# ╔════════════════════════════════════════════════════════════════╗
# ║         WORKER TASKS - ZERO RATE LIMIT, SPEED OPTIMIZED        ║
# ╚════════════════════════════════════════════════════════════════╝

async def bot_loop(bot, chat_id, base, mode, task_ref):
    """Ultra-fast name change loop - Uses only user-defined delays"""
    i = 0
    while True:
        try:
            # Always get fresh delay - allows dynamic updates
            delay = get_delay(chat_id, "nc")
            text = f"{base} {RAID_TEXTS[i % len(RAID_TEXTS)]}" if mode == "raid" else f"{base} {NCEMO_EMOJIS[i % len(NCEMO_EMOJIS)]}"
            i += 1
            await bot.set_chat_title(chat_id, text)
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            break
        except:
            await asyncio.sleep(0.05)

async def pyramid_loop_worker(bot, chat_id, name, task_ref):
    """Pyramid name change - Uses only user-defined delays"""
    base_text = f"{name} 𝘗𝙔𝙍𝘈𝙈𝙄𝘋🎖️"
    chars_left = 128 - len(base_text)
    max_stars = max(1, min(15, chars_left // 2))
    
    while True:
        try:
            delay = get_delay(chat_id, "nc")
            star_count = random.randint(1, max_stars)
            await bot.set_chat_title(chat_id, base_text + "⭐" * star_count)
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            break
        except:
            await asyncio.sleep(0.05)

async def spm_loop_sender(bot, chat_id: int, text: str):
    """Ultra-fast message spam - Uses only user-defined delays"""
    while True:
        try:
            delay = get_delay(chat_id, "spm")
            await bot.send_message(chat_id=chat_id, text=text, disable_web_page_preview=True)
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            break
        except:
            await asyncio.sleep(0.01)

async def slidespam_worker(bot, chat_id: int, message_id: int, text: str):
    """Fast slide spam - Uses only user-defined delays"""
    while True:
        try:
            delay = get_delay(chat_id, "spm")
            await bot.send_message(chat_id=chat_id, text=text, reply_to_message_id=message_id, disable_web_page_preview=True)
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            break
        except:
            await asyncio.sleep(0.01)

async def targetslide_worker(bot, chat_id: int, message_id: int, name: str):
    """Target slide spam - Uses only user-defined delays"""
    while True:
        try:
            delay = get_delay(chat_id, "spm")
            msg = random.choice(TARGET_SLIDE_TEXTS).format(name)
            await bot.send_message(chat_id=chat_id, text=msg, reply_to_message_id=message_id, disable_web_page_preview=True)
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            break
        except:
            await asyncio.sleep(0.01)

async def media_spm_sender(bot, chat_id: int, media_type: str, file_id: str):
    """Fast media spam - Uses only user-defined delays"""
    while True:
        try:
            delay = get_delay(chat_id, "spm")
            if media_type == "sticker":
                await bot.send_sticker(chat_id=chat_id, sticker=file_id)
            elif media_type == "gif":
                await bot.send_animation(chat_id=chat_id, animation=file_id)
            elif media_type == "photo":
                await bot.send_photo(chat_id=chat_id, photo=file_id)
            elif media_type == "video":
                await bot.send_video(chat_id=chat_id, video=file_id)
            elif media_type == "voice":
                await bot.send_voice(chat_id=chat_id, voice=file_id)
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            break
        except:
            await asyncio.sleep(0.01)

async def pfp_loop_worker(bot, chat_id: int):
    """PFP rotation - Uses only user-defined delays"""
    while True:
        try:
            delay = get_delay(chat_id, "pfp")
            folder = f"downloads/{chat_id}"
            if not os.path.exists(folder):
                await asyncio.sleep(5)
                continue
            files = [f for f in os.listdir(folder) if f.endswith('.jpg')]
            if not files:
                await asyncio.sleep(5)
                continue
            pic = random.choice(files)
            with open(f"{folder}/{pic}", 'rb') as f:
                await bot.set_chat_photo(chat_id, photo=f)
            await asyncio.sleep(delay)
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
        except asyncio.CancelledError:
            break
        except:
            await asyncio.sleep(0.5)

async def setpfp_loop_worker(bot_idx: int, chat_id: int, pfp_file_path: str):
    """Set PFP for bot and rotate - Uses only user-defined delays"""
    bot = bots[bot_idx]
    while True:
        try:
            delay = get_delay(chat_id, "pfp")
            if os.path.exists(pfp_file_path):
                with open(pfp_file_path, 'rb') as f:
                    await bot.set_chat_photo(chat_id, photo=f)
            await asyncio.sleep(delay)
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
        except asyncio.CancelledError:
            break
        except:
            await asyncio.sleep(0.5)

# ╔════════════════════════════════════════════════════════════════╗
# ║                    MENU SYSTEM                                 ║
# ╚════════════════════════════════════════════════════════════════╝

def get_selector_keyboard(task_id: str):
    menu = active_menus[task_id]
    sel = menu["selected"]
    keyboard = []
    row = []
    for i, uname in enumerate(bot_usernames):
        check = "✅" if i in sel else "❌"
        row.append(InlineKeyboardButton(f"{check} {uname}", callback_data=f"tk_{task_id}_tgl_{i}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([
        InlineKeyboardButton("🔘 All", callback_data=f"tk_{task_id}_all"),
        InlineKeyboardButton("⚪ None", callback_data=f"tk_{task_id}_none")
    ])
    keyboard.append([InlineKeyboardButton("🚀 LAUNCH", callback_data=f"tk_{task_id}_start")])
    return InlineKeyboardMarkup(keyboard)

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id not in SUDO_USERS:
        return await query.answer("❌ Access Denied.", show_alert=True)
    
    data = query.data.split("_")
    task_id = data[1]
    action = data[2]
    
    if task_id not in active_menus:
        return await query.answer("❌ Menu expired.", show_alert=True)
    
    menu = active_menus[task_id]
    
    if action == "tgl":
        await query.answer()
        idx = int(data[3])
        if idx in menu["selected"]:
            menu["selected"].remove(idx)
        else:
            menu["selected"].add(idx)
        await query.edit_message_reply_markup(reply_markup=get_selector_keyboard(task_id))
    
    elif action == "all":
        await query.answer()
        menu["selected"] = set(range(len(bots)))
        await query.edit_message_reply_markup(reply_markup=get_selector_keyboard(task_id))
    
    elif action == "none":
        await query.answer()
        menu["selected"] = set()
        await query.edit_message_reply_markup(reply_markup=get_selector_keyboard(task_id))
    
    elif action == "start":
        if not menu["selected"]:
            return await query.answer("⚠️ Select bots!", show_alert=True)
        await query.answer("🚀 Launched!", show_alert=False)
        await query.edit_message_text(f"✅ **{menu['cmd'].upper()}** Activated!", parse_mode="Markdown")
        
        chat_id = menu["chat_id"]
        for idx in menu["selected"]:
            b = bots[idx]
            if menu["cmd"] == "pfp":
                t = asyncio.create_task(pfp_loop_worker(b, chat_id))
                pfp_tasks.setdefault(chat_id, []).append(t)
            elif menu["cmd"] == "setpfp":
                t = asyncio.create_task(setpfp_loop_worker(idx, chat_id, menu["payload"]))
                setpfp_tasks.setdefault(chat_id, []).append(t)
            elif menu["cmd"] == "stickerspm":
                t = asyncio.create_task(media_spm_sender(b, chat_id, "sticker", menu["payload"]))
                sticker_spm_tasks.setdefault(chat_id, []).append(t)
            elif menu["cmd"] == "gifspm":
                t = asyncio.create_task(media_spm_sender(b, chat_id, "gif", menu["payload"]))
                gif_spm_tasks.setdefault(chat_id, []).append(t)
            elif menu["cmd"] == "mediaspm":
                t = asyncio.create_task(media_spm_sender(b, chat_id, menu["type"], menu["payload"]))
                media_spm_tasks.setdefault(chat_id, []).append(t)
            elif menu["cmd"] == "voicespm":
                t = asyncio.create_task(media_spm_sender(b, chat_id, "voice", menu["payload"]))
                voice_spm_tasks.setdefault(chat_id, []).append(t)
        del active_menus[task_id]

# ╔════════════════════════════════════════════════════════════════╗
# ║              COMMANDS - CORE                                   ║
# ╚════════════════════════════════════════════════════════════════╝

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_reply(update, "💗 **Ryuk s1 manager Online!**\n\n**Credits: RYUK**", parse_mode="Markdown")

@only_sudo
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "**𝗥𝗬𝗨𝗞 S1 MANAGER** ❤️‍🔥\n"
        "**Credits: RYUK**\n\n"
        "🌀 **NC & ROTATION**\n"
        "• `+ryuknc <text>` : Raid text NC\n"
        "• `+emojify <text>` : Emoji NC\n"
        "• `+orbit <name>` : Pyramid/rotating NC\n"
        "• `+haltnc` : Stop all NC\n"
        "• `+ncspeed <seconds>` : Set NC speed\n\n"
        "🚀 **SPAM**\n"
        "• `+blast <text>` : Message spam\n"
        "• `+haltspm` : Stop local spam\n"
        "• `+stopspm` : Stop all spam\n"
        "• `+spmspeed <seconds>` : Set spam speed\n\n"
        "🎞️ **MEDIA SPAM**\n"
        "• `+stickstorm` : Sticker spam\n"
        "• `+gifblast` : GIF spam\n"
        "• `+mediaraid` : Photo/Video spam\n"
        "• `+voicestorm` : Voice spam\n"
        "• `+stopstick` : Stop sticker spam\n"
        "• `+stopgif` : Stop GIF spam\n"
        "• `+stopmedia` : Stop media spam\n"
        "• `+stopvoice` : Stop voice spam\n\n"
        "🎯 **SLIDE & TARGET**\n"
        "• `+slideraid <text>` : Slide spam\n"
        "• `+lockslide <name>` : Target slide\n"
        "• `+stopslide` : Stop slide\n"
        "• `+unlockslide` : Stop target\n\n"
        "🖼️ **PFP**\n"
        "• `+savepfp` : Save PFP\n"
        "• `+delpfp` : Delete PFP\n"
        "• `+applypfp` : Set saved PFP rotation for bots\n"
        "• `+viewpfp` : Start PFP rotation\n"
        "• `+freezepfp` : Stop PFP\n\n"
        "💫 **AUTO-REPLY**\n"
        "• `+autoswipe <name>` : Auto swipe mode\n"
        "• `+stopswipe` : Stop swipe\n"
        "• `+autoreply` : Auto reply\n"
        "• `+stopreply` : Stop reply\n\n"
        "🛡️ **ADMIN**\n"
        "• `+silence` : Mute user\n"
        "• `+unsilence` : Unmute user\n"
        "• `+mutelog` : Muted users\n"
        "• `+elevate` : Promote user\n"
        "• `+downgrade` : Demote user\n"
        "• `+elevateall` : Promote all bots\n"
        "• `+elevatebots` : Promote all bots\n"
        "• `+addauthority` : Add sudo\n"
        "• `+delauthority` : Remove sudo\n"
        "• `+authoritylist` : Sudo list\n\n"
        "🤖 **BOT CONTROL**\n"
        "• `+loadbots` : Add bot tokens\n"
        "• `+bots` : List saved bots\n"
        "• `+allbots` : List active bots with IDs\n"
        "• `+renamebots <new_name>` : Rename ALL bots globally\n"
        "• `+botcount` : Active bot count\n"
        "• `+fetchlinks` : Get all group links\n"
        "• `+exitall` / `+exitgc` : All bots leave all groups\n"
        "• `+botowners` : Owner-only bot registry DM\n\n"
        "⚙️ **UTILITIES**\n"
        "• `+killall` : Stop all\n"
        "• `+optimize` : Optimize\n"
        "• `+latency` : Latency\n"
        "• `+userid` : Your user idimize\n"
        "• `+latency` : Latency\n"
        "• `+userid` : Your user id\n"
    )
    await safe_reply(update, help_text, parse_mode="Markdown")

@only_sudo
async def optimize_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global_replied_messages.cache.clear()
    gc.collect()
    await safe_reply(update, "✨ Optimized & Cleaned up.")

@only_owner
async def stopall_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for d in [group_tasks, pyramid_tasks, slidespam_tasks, targetslide_tasks, spm_loop_tasks, sticker_spm_tasks, gif_spm_tasks, pfp_tasks, setpfp_tasks, media_spm_tasks, voice_spm_tasks]:
        for task_list in d.values():
            if isinstance(task_list, list):
                for t in task_list:
                    t.cancel()
            elif isinstance(task_list, dict):
                for t in task_list.values():
                    t.cancel()
        d.clear()
    swipe_mode.clear()
    replyryuk_targets.clear()
    await safe_reply(update, "🛑 All operations stopped.")

async def ping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_reply(update, f"🏓 {random.randint(30,90)}ms ✅")

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_reply(update, f"🆔 `{update.effective_user.id}`", parse_mode="Markdown")

# ╔════════════════════════════════════════════════════════════════╗
# ║          COMMANDS - NAME CHANGE (ZERO RATE LIMIT)             ║
# ╚════════════════════════════════════════════════════════════════╝

@only_sudo
async def gcnc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await safe_reply(update, "⚠️ `+ryuknc <text>`", parse_mode="Markdown")
    base = " ".join(context.args)
    chat_id = update.message.chat_id
    group_tasks.setdefault(chat_id, {})
    if update.effective_user:
        mark_owner_action_v2(chat_id, "nc", update.effective_user.id)
    
    # Only bots that are in this group will execute
    active_count = 0
    for bot_idx, bot in enumerate(bots):
        # Check if bot is in this chat: bot.id should be a key in bot_group_cache, and chat_id should be in the set
        if bot.id in bot_group_cache and chat_id in bot_group_cache[bot.id]:
            if bot.id not in group_tasks[chat_id]:
                task_ref = {"id": random.randint(100000, 999999)}
                group_tasks[chat_id][bot.id] = asyncio.create_task(bot_loop(bot, chat_id, base, "raid", task_ref))
                active_count += 1
    
    await safe_reply(update, f"🔄 Raid NC started ({active_count} bots in this group)")

@only_sudo
async def ncemo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await safe_reply(update, "⚠️ `+emojify <text>`", parse_mode="Markdown")
    base = " ".join(context.args)
    chat_id = update.message.chat_id
    group_tasks.setdefault(chat_id, {})
    if update.effective_user:
        mark_owner_action_v2(chat_id, "nc", update.effective_user.id)
    
    # Only bots that are in this group will execute
    active_count = 0
    for bot_idx, bot in enumerate(bots):
        # Check if bot is in this chat: bot.id should be a key in bot_group_cache, and chat_id should be in the set
        if bot.id in bot_group_cache and chat_id in bot_group_cache[bot.id]:
            if bot.id not in group_tasks[chat_id]:
                task_ref = {"id": random.randint(100000, 999999)}
                group_tasks[chat_id][bot.id] = asyncio.create_task(bot_loop(bot, chat_id, base, "emo", task_ref))
                active_count += 1
    await safe_reply(update, f"🔄 Emoji NC started ({active_count} bots in this group)")

@only_sudo
async def pyramidnc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await safe_reply(update, "⚠️ `/pyramidnc <name>`", parse_mode="Markdown")
    name = " ".join(context.args)
    chat_id = update.message.chat_id
    pyramid_tasks.setdefault(chat_id, {})
    if update.effective_user:
        mark_owner_action_v2(chat_id, "nc", update.effective_user.id)
    
    # Only bots that are in this group will execute
    active_count = 0
    for bot_idx, bot in enumerate(bots):
        if bot.id in bot_group_cache and chat_id in bot_group_cache[bot.id]:
            if bot.id not in pyramid_tasks[chat_id]:
                task_ref = {"id": random.randint(100000, 999999)}
                pyramid_tasks[chat_id][bot.id] = asyncio.create_task(pyramid_loop_worker(bot, chat_id, name, task_ref))
                active_count += 1
    await safe_reply(update, f"🔺 Pyramid NC `{name}` started ({active_count} bots)", parse_mode="Markdown")

@only_sudo
async def stopgcnc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if not can_stop_action_v2(update.effective_user.id, chat_id, "nc"):
        return await safe_reply(update, "❌ Only owner can stop NC started by owner.")
    stopped = False
    
    if chat_id in group_tasks:
        for task in group_tasks[chat_id].values():
            try:
                task.cancel()
                stopped = True
            except:
                pass
        group_tasks[chat_id] = {}
        owner_initiated_actions.pop((chat_id, "nc"), None)
    
    if chat_id in pyramid_tasks:
        for task in pyramid_tasks[chat_id].values():
            try:
                task.cancel()
                stopped = True
            except:
                pass
        pyramid_tasks[chat_id] = {}
        owner_initiated_actions.pop((chat_id, "nc"), None)
    
    if stopped:
        await safe_reply(update, "🛑 All NC stopped")
    else:
        await safe_reply(update, "⚠️ No NC running")

@only_sudo
async def delaync_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await safe_reply(update, "⚠️ `/delaync <seconds>` (0.05-5s)", parse_mode="Markdown")
    if not can_stop_action_v2(update.effective_user.id, update.message.chat_id, "nc"):
        return await safe_reply(update, "❌ Only owner can change NC speed for owner-started NC.")
    try:
        val = float(context.args[0])
        val = max(0.05, min(5, val))
        nc_delays[update.message.chat_id] = val
        await safe_reply(update, f"⚡ NC speed = `{val}s` (applies to running & new NC)", parse_mode="Markdown")
    except:
        await safe_reply(update, "❌ Invalid")

# ╔════════════════════════════════════════════════════════════════╗
# ║            COMMANDS - MESSAGE SPAM (ZERO RATE LIMIT)          ║
# ╚════════════════════════════════════════════════════════════════╝

@only_sudo
async def spm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = extract_command_text(update.message.text)
    if not text:
        return await safe_reply(update, "⚠️ `/spm <text>`", parse_mode="Markdown")
    chat_id = update.message.chat_id
    if update.effective_user:
        mark_owner_action_v2(chat_id, "spm", update.effective_user.id)
    task = asyncio.create_task(spm_loop_sender(context.application.bot, chat_id, text))
    spm_loop_tasks.setdefault(chat_id, []).append(task)
    await safe_reply(update, "✅ Spam started (NO limit, 0.05s default)")

@only_sudo
async def stopspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if not can_stop_action_v2(update.effective_user.id, chat_id, "spm"):
        return await safe_reply(update, "❌ Only owner can stop spam started by owner.")
    if chat_id in spm_loop_tasks:
        for t in spm_loop_tasks[chat_id]:
            try:
                t.cancel()
            except:
                pass
        spm_loop_tasks[chat_id] = []
        owner_initiated_actions.pop((chat_id, "spm"), None)
        await safe_reply(update, "🛑 Spam stopped")
    else:
        await safe_reply(update, "⚠️ No spam running")

@only_sudo
async def stopallspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        any_owner_spm = any(
            action == "spm" and initiator == OWNER_ID
            for (_, action), initiator in owner_initiated_actions.items()
        )
        if any_owner_spm:
            return await safe_reply(update, "❌ Only owner can stop owner-started spam.")
    count = 0
    for tasks in spm_loop_tasks.values():
        for t in tasks:
            try:
                t.cancel()
                count += 1
            except:
                pass
    spm_loop_tasks.clear()
    for key in list(owner_initiated_actions):
        if key[1] == "spm":
            owner_initiated_actions.pop(key, None)
    await safe_reply(update, f"🛑 Stopped {count} spam tasks")

@only_sudo
async def delaygcspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await safe_reply(update, "⚠️ `/delaygcspm <seconds>` (0.05-5s)", parse_mode="Markdown")
    if not can_stop_action_v2(update.effective_user.id, update.message.chat_id, "spm"):
        return await safe_reply(update, "❌ Only owner can change spam speed for owner-started spam.")
    try:
        val = float(context.args[0])
        val = max(0.05, min(5, val))
        spm_delays[update.message.chat_id] = val
        await safe_reply(update, f"⚡ Spam speed = `{val}s` (applies to running & new spam)", parse_mode="Markdown")
    except:
        await safe_reply(update, "❌ Invalid")

# ╔════════════════════════════════════════════════════════════════╗
# ║                COMMANDS - SLIDE & TARGET                       ║
# ╚════════════════════════════════════════════════════════════════╝

@only_sudo
async def slidespam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return await safe_reply(update, "⚠️ Reply to a message", parse_mode="Markdown")
    uid = update.message.reply_to_message.from_user.id
    text = extract_command_text(update.message.text)
    if not text:
        return await safe_reply(update, "⚠️ `/slidespam <text>`", parse_mode="Markdown")
    if uid in slidespam_tasks:
        for t in slidespam_tasks[uid]:
            try:
                t.cancel()
            except:
                pass
    slidespam_tasks[uid] = []
    chat_id = update.message.chat_id
    msg_id = update.message.reply_to_message.message_id
    for bot in bots:
        task = asyncio.create_task(slidespam_worker(bot, chat_id, msg_id, text))
        slidespam_tasks[uid].append(task)
    await safe_reply(update, "💬 Slide spam activated")

@only_sudo
async def stopslidespam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return
    uid = update.message.reply_to_message.from_user.id
    if uid in slidespam_tasks:
        for t in slidespam_tasks[uid]:
            try:
                t.cancel()
            except:
                pass
        del slidespam_tasks[uid]
        await safe_reply(update, "🛑 Slide spam stopped")

@only_sudo
async def targetslide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return await safe_reply(update, "⚠️ Reply please", parse_mode="Markdown")
    uid = update.message.reply_to_message.from_user.id
    name = " ".join(context.args) if context.args else update.message.reply_to_message.from_user.first_name
    if uid in targetslide_tasks:
        for t in targetslide_tasks[uid]:
            try:
                t.cancel()
            except:
                pass
    targetslide_tasks[uid] = []
    chat_id = update.message.chat_id
    msg_id = update.message.reply_to_message.message_id
    for bot in bots:
        task = asyncio.create_task(targetslide_worker(bot, chat_id, msg_id, name))
        targetslide_tasks[uid].append(task)
    await safe_reply(update, "🎯 Target slide activated")

@only_sudo
async def stoptargetslide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return
    uid = update.message.reply_to_message.from_user.id
    if uid in targetslide_tasks:
        for t in targetslide_tasks[uid]:
            try:
                t.cancel()
            except:
                pass
        del targetslide_tasks[uid]
        await safe_reply(update, "🛑 Target slide stopped")

# ╔════════════════════════════════════════════════════════════════╗
# ║                   COMMANDS - MEDIA SPAM                        ║
# ╚════════════════════════════════════════════════════════════════╝

@only_sudo
async def stickerspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.sticker:
        return await safe_reply(update, "⚠️ Reply to sticker", parse_mode="Markdown")
    file_id = update.message.reply_to_message.sticker.file_id
    chat_id = update.message.chat_id
    unique_msg_id = f"{chat_id}_{update.message.message_id}"
    if unique_msg_id in global_replied_messages:
        return
    global_replied_messages.add(unique_msg_id)
    task_id = str(random.randint(10000, 99999))
    active_menus[task_id] = {"cmd": "stickerspm", "chat_id": chat_id, "payload": file_id, "selected": set()}
    await update.message.reply_text("🎭 STICKER SPAM - Select Bots", reply_markup=get_selector_keyboard(task_id), parse_mode="Markdown")

@only_sudo
async def stopstickerspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in sticker_spm_tasks:
        for t in sticker_spm_tasks[chat_id]:
            try:
                t.cancel()
            except:
                pass
        sticker_spm_tasks[chat_id] = []
        await safe_reply(update, "🛑 Sticker spam stopped")

@only_sudo
async def gifspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.animation:
        return await safe_reply(update, "⚠️ Reply to GIF", parse_mode="Markdown")
    file_id = update.message.reply_to_message.animation.file_id
    chat_id = update.message.chat_id
    unique_msg_id = f"{chat_id}_{update.message.message_id}"
    if unique_msg_id in global_replied_messages:
        return
    global_replied_messages.add(unique_msg_id)
    task_id = str(random.randint(10000, 99999))
    active_menus[task_id] = {"cmd": "gifspm", "chat_id": chat_id, "payload": file_id, "selected": set()}
    await update.message.reply_text("🎥 GIF SPAM - Select Bots", reply_markup=get_selector_keyboard(task_id), parse_mode="Markdown")

@only_sudo
async def stopgifspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in gif_spm_tasks:
        for t in gif_spm_tasks[chat_id]:
            try:
                t.cancel()
            except:
                pass
        gif_spm_tasks[chat_id] = []
        await safe_reply(update, "🛑 GIF spam stopped")

@only_sudo
async def mediaspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not (update.message.reply_to_message.photo or update.message.reply_to_message.video):
        return await safe_reply(update, "⚠️ Reply to photo/video", parse_mode="Markdown")
    if update.message.reply_to_message.photo:
        file_id = update.message.reply_to_message.photo[-1].file_id
        media_type = "photo"
    else:
        file_id = update.message.reply_to_message.video.file_id
        media_type = "video"
    chat_id = update.message.chat_id
    unique_msg_id = f"{chat_id}_{update.message.message_id}"
    if unique_msg_id in global_replied_messages:
        return
    global_replied_messages.add(unique_msg_id)
    task_id = str(random.randint(10000, 99999))
    active_menus[task_id] = {"cmd": "mediaspm", "type": media_type, "chat_id": chat_id, "payload": file_id, "selected": set()}
    await update.message.reply_text("🖼️ MEDIA SPAM - Select Bots", reply_markup=get_selector_keyboard(task_id), parse_mode="Markdown")

@only_sudo
async def stopmediaspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in media_spm_tasks:
        for t in media_spm_tasks[chat_id]:
            try:
                t.cancel()
            except:
                pass
        media_spm_tasks[chat_id] = []
        await safe_reply(update, "🛑 Media spam stopped")

@only_sudo
async def voicespm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.voice:
        return await safe_reply(update, "⚠️ Reply to voice", parse_mode="Markdown")
    file_id = update.message.reply_to_message.voice.file_id
    chat_id = update.message.chat_id
    unique_msg_id = f"{chat_id}_{update.message.message_id}"
    if unique_msg_id in global_replied_messages:
        return
    global_replied_messages.add(unique_msg_id)
    task_id = str(random.randint(10000, 99999))
    active_menus[task_id] = {"cmd": "voicespm", "chat_id": chat_id, "payload": file_id, "selected": set()}
    await update.message.reply_text("🎤 VOICE SPAM - Select Bots", reply_markup=get_selector_keyboard(task_id), parse_mode="Markdown")

@only_sudo
async def stopvoicespm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in voice_spm_tasks:
        for t in voice_spm_tasks[chat_id]:
            try:
                t.cancel()
            except:
                pass
        voice_spm_tasks[chat_id] = []
        await safe_reply(update, "🛑 Voice spam stopped")

# ╔════════════════════════════════════════════════════════════════╗
# ║                      COMMANDS - PFP                            ║
# ╚════════════════════════════════════════════════════════════════╝

@only_sudo
async def save_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        return await safe_reply(update, "⚠️ Reply to photo", parse_mode="Markdown")
    chat_id = update.message.chat_id
    photo = update.message.reply_to_message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    os.makedirs(f"downloads/{chat_id}", exist_ok=True)
    path = f"downloads/{chat_id}/{photo.file_unique_id}.jpg"
    await file.download_to_drive(path)
    saved_pfps[chat_id] = path
    await safe_reply(update, "📸 PFP saved (use /setpfp or /pfp)")

@only_sudo
async def del_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        return await safe_reply(update, "⚠️ Reply to photo", parse_mode="Markdown")
    chat_id = update.message.chat_id
    uid = update.message.reply_to_message.photo[-1].file_unique_id
    path = f"downloads/{chat_id}/{uid}.jpg"
    if os.path.exists(path):
        os.remove(path)
        await safe_reply(update, "🗑 PFP deleted")
    else:
        await safe_reply(update, "⚠️ Not found")

import tempfile
import requests

@only_sudo
async def setpfp_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (
        not update.message
        or not update.message.reply_to_message
        or not update.message.reply_to_message.photo
    ):
        return await safe_reply(update, "⚠️ Reply to a photo with /setpfp")

    msg = await update.message.reply_text("🖼 Updating bot pfps...")

    photo = update.message.reply_to_message.photo[-1]
    tg_file = await context.bot.get_file(photo.file_id)

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
            temp_path = f.name

        await tg_file.download_to_drive(temp_path)

        if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
            return await msg.edit_text("❌ Download failed")

        ok = 0
        fail = 0

        for token in bot_tokens:
            if not token:
                continue

            try:
                url = f"https://api.telegram.org/bot{token}/setMyProfilePhoto"

                with open(temp_path, "rb") as img:
                    files = {"photo": img}
                    r = requests.post(url, files=files, timeout=30)

                res = r.json()

                if res.get("ok"):
                    ok += 1
                else:
                    fail += 1

            except Exception as e:
                fail += 1

        await msg.edit_text(f"🖼 DONE✅ Success: {ok} ❌ Failed: {fail}")

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

@only_sudo
async def pfp_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    folder = f"downloads/{chat_id}"
    if not os.path.exists(folder) or not os.listdir(folder):
        return await safe_reply(update, "⚠️ No PFPs. Use `/save` first", parse_mode="Markdown")
    unique_msg_id = f"{chat_id}_{update.message.message_id}"
    if unique_msg_id in global_replied_messages:
        return
    global_replied_messages.add(unique_msg_id)
    task_id = str(random.randint(10000, 99999))
    active_menus[task_id] = {"cmd": "pfp", "chat_id": chat_id, "payload": "", "selected": set()}
    await update.message.reply_text("📸 PFP ROTATION - Select Bots", reply_markup=get_selector_keyboard(task_id), parse_mode="Markdown")

@only_sudo
async def stoppfp_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    stopped = False
    if chat_id in pfp_tasks:
        for t in pfp_tasks[chat_id]:
            try:
                t.cancel()
                stopped = True
            except:
                pass
        pfp_tasks[chat_id] = []
    if chat_id in setpfp_tasks:
        for t in setpfp_tasks[chat_id]:
            try:
                t.cancel()
                stopped = True
            except:
                pass
        setpfp_tasks[chat_id] = []
    if stopped:
        await safe_reply(update, "🛑 PFP stopped")

# ╔════════════════════════════════════════════════════════════════╗
# ║                COMMANDS - SWIPE & AUTO-REPLY                   ║
# ╚════════════════════════════════════════════════════════════════╝

@only_sudo
async def swipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await safe_reply(update, "⚠️ `/swipe <name>`", parse_mode="Markdown")
    swipe_mode[update.message.chat_id] = " ".join(context.args)
    await safe_reply(update, "⚡ Swipe mode activated")

@only_sudo
async def stopswipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    swipe_mode.pop(update.message.chat_id, None)
    await safe_reply(update, "🛑 Swipe mode disabled")

@only_sudo
async def replyryuk_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = await get_target_user(update, context)
    if not uid:
        return await safe_reply(update, "⚠️ Reply/mention user")
    replyryuk_targets.add(uid)
    await safe_reply(update, "💬 Auto-reply activated")

@only_sudo
async def stopreplyryuk_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = await get_target_user(update, context)
    if not uid:
        return await safe_reply(update, "⚠️ Reply/mention")
    replyryuk_targets.discard(uid)
    last_ryuk_reply.pop(uid, None)
    await safe_reply(update, "🛑 Auto-reply disabled")

# ╔════════════════════════════════════════════════════════════════╗
# ║                  COMMANDS - ADMIN FUNCTIONS                    ║
# ╚════════════════════════════════════════════════════════════════╝

@only_owner
async def addsudo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = await get_target_user(update, context)
    if uid:
        SUDO_USERS.add(uid)
        save_sudo()
        mention = await get_mention_from_id(context, uid)
        await safe_reply(update, f"👑 {mention} is now SUDO", parse_mode="Markdown")

@only_owner
async def delsudo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = await get_target_user(update, context)
    if uid and uid in SUDO_USERS:
        SUDO_USERS.remove(uid)
        save_sudo()
        mention = await get_mention_from_id(context, uid)
        await safe_reply(update, f"🗑 {mention} removed from SUDO", parse_mode="Markdown")

@only_sudo
async def listsudo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "👑 SUDO Users:\n\n"
    for uid in SUDO_USERS:
        mention = await get_mention_from_id(context, uid)
        text += f"• {mention}\n"
    await safe_reply(update, text, parse_mode="Markdown")

@only_sudo
async def mute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = await get_target_user(update, context)
    if not uid:
        return await safe_reply(update, "⚠️ Reply/mention user")
    muted_users.add(uid)
    mention = await get_mention_from_id(context, uid)
    await safe_reply(update, f"🔇 {mention} muted", parse_mode="Markdown")

@only_sudo
async def unmute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = await get_target_user(update, context)
    if not uid:
        return
    muted_users.discard(uid)
    mention = await get_mention_from_id(context, uid)
    await safe_reply(update, f"🔊 {mention} unmuted", parse_mode="Markdown")

@only_sudo
async def mutelist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not muted_users:
        return await safe_reply(update, "📭 No muted users")
    text = "🔇 Muted Users:\n\n"
    for uid in muted_users:
        mention = await get_mention_from_id(context, uid)
        text += f"• {mention}\n"
    await safe_reply(update, text, parse_mode="Markdown")

@only_sudo
async def promote_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = await get_target_user(update, context)
    if not uid:
        return await safe_reply(update, "⚠️ Reply/mention user")
    try:
        await context.bot.promote_chat_member(
            chat_id=update.message.chat_id, user_id=uid,
            can_change_info=True, can_delete_messages=True, can_invite_users=True,
            can_restrict_members=True, can_pin_messages=True, can_promote_members=True,
            can_manage_chat=True, can_manage_video_chats=True, is_anonymous=False
        )
        mention = await get_mention_from_id(context, uid)
        await safe_reply(update, f"✅ {mention} promoted", parse_mode="Markdown")
    except Exception as e:
        await safe_reply(update, f"❌ Error: {e}")

@only_sudo
async def demote_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = await get_target_user(update, context)
    if not uid:
        return
    try:
        await context.bot.promote_chat_member(
            chat_id=update.message.chat_id, user_id=uid,
            can_change_info=False, can_delete_messages=False, can_invite_users=False,
            can_restrict_members=False, can_pin_messages=False, can_promote_members=False,
            can_manage_chat=False, can_manage_video_chats=False, is_anonymous=False
        )
        mention = await get_mention_from_id(context, uid)
        await safe_reply(update, f"🛑 {mention} demoted", parse_mode="Markdown")
    except Exception as e:
        await safe_reply(update, f"❌ {e}")

@only_sudo
async def promoteallbots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    success = 0
    for bot in bots:
        try:
            await context.bot.promote_chat_member(
                chat_id=update.message.chat_id, user_id=bot.id,
                can_change_info=True, can_delete_messages=True, can_invite_users=True,
                can_restrict_members=True, can_pin_messages=True, can_promote_members=True,
                can_manage_chat=True, can_manage_video_chats=True, is_anonymous=False
            )
            success += 1
        except:
            pass
    await safe_reply(update, f"🤖 Promoted {success} bots")

@only_sudo
async def promoteall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if not known_users:
        return await safe_reply(update, "⚠️ No users found yet")
    unique_msg_id = f"{chat_id}_{update.message.message_id}"
    if unique_msg_id in global_replied_messages:
        return
    global_replied_messages.add(unique_msg_id)
    msg = await update.message.reply_text("⏳ Promoting all users...", parse_mode="Markdown")
    success = 0
    for uid in list(known_users):
        try:
            await context.bot.promote_chat_member(
                chat_id=chat_id, user_id=uid,
                can_change_info=True, can_delete_messages=False, can_invite_users=True,
                can_restrict_members=False, can_pin_messages=True, can_promote_members=True,
                can_manage_chat=True, can_manage_video_chats=True, is_anonymous=False
            )
            success += 1
        except:
            pass
    await msg.edit_text(f"✅ Promoted {success} users", parse_mode="Markdown")

# ╔════════════════════════════════════════════════════════════════╗
# ║            COMMANDS - MULTI-BOT CONTROL                        ║
# ╚════════════════════════════════════════════════════════════════╝

@only_sudo
async def activebots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not bots:
        return await safe_reply(update, "❌ No active bots")

    lines = []
    for bot in bots:
        try:
            me = await bot.get_me()
            uname = "@" + me.username if me.username else "NO_USERNAME"
            lines.append(f"• {uname} | {me.first_name}")
        except Exception as e:
            lines.append(f"• ERROR: {e}")

    text = "🤖 ACTIVE BOTS\n\n" + "\n".join(lines) + f"\n\n✅ Total: {len(bots)}"
    await safe_reply(update, text)

@only_sudo
async def leave_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    await safe_reply(update, "👋 All bots leaving...")
    for bot in bots:
        try:
            await bot.leave_chat(chat_id)
        except:
            pass

@only_sudo


async def addbots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pending_addbots.add(update.effective_user.id)
    await update.message.reply_text("📝 Send bot tokens.\nOne token per line.")


async def token_receiver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    if text.startswith("+") or text.startswith("/"):
        return

    uid = update.effective_user.id

    if uid not in pending_addbots:
        return

    pending_addbots.remove(uid)

    tokens = [x.strip() for x in text.splitlines() if x.strip()]

    success = 0
    failed = 0
    added_names = []
    removed_invalid = []

    # 🔥 LOOP MUST BE INSIDE FUNCTION
    for token in tokens:

        if token in ACTIVE_BOTS:
            continue

        # Validate token
        is_valid = await validate_bot_token(token)
        if not is_valid:
            removed_invalid.append(token[:20] + "...")
            continue

        try:
            from telegram import Bot

            bot = Bot(token=token)
            me = await bot.get_me()

        except Exception:
            failed += 1
            continue

        # Save DB
        add_bot_db(token, me.username or me.first_name, uid)
        added_names.append(f"@{me.username}" if me.username else me.first_name)

        # START WORKER
        asyncio.create_task(safe_worker(token))

        success += 1

    # RESPONSE
    msg = f"🤖 ADD BOTS RESULT\n\n✅ Added: {success}\n❌ Failed: {failed}\n"

    if removed_invalid:
        msg += f"\n🚫 Invalid Tokens: {len(removed_invalid)}"

    if added_names:
        msg += "\n\n" + "\n".join(f"• {x}" for x in added_names)

    await update.message.reply_text(msg)

@only_sudo
async def listbots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bots_list = get_bots_db()
    if not bots_list:
        return await safe_reply(update, "❌ No bots registered")
    msg = "🤖 **Saved Bots**\n\n" + "\n".join([f"• `{name or 'Unknown'}`" for _, name in bots_list])
    await safe_reply(update, msg, parse_mode="Markdown")

@only_owner
async def rnbots_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rename all bots with new name - Owner Only"""
    if not context.args:
        return await safe_reply(update, "⚠️ `/rnbots <new_name>`", parse_mode="Markdown")
    new_name = " ".join(context.args)
    success = 0
    for bot in bots:
        try:
            await bot.set_my_name(new_name)
            success += 1
        except:
            pass
    
    for token, username in get_bots_db():
        add_bot_db(token, new_name)
    
    await safe_reply(update, f"✅ Renamed {success} bots to `{new_name}`", parse_mode="Markdown")

# ╔════════════════════════════════════════════════════════════════╗
# ║           NEW COMMANDS - Plus Prefix (+) Version (Section 2)   ║
# ╚════════════════════════════════════════════════════════════════╝

@only_sudo
async def plus_stop_v2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop all operations - Plus prefix version"""
    await stopall_cmd(update, context)

@only_sudo  
async def plus_optimize_v2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Optimize memory - Plus prefix version"""
    await optimize_cmd(update, context)

@only_sudo
async def plus_flood_v2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Flood with messages - aliases to spm"""
    await spm_cmd(update, context)

@only_sudo
async def plus_wave_v2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Wave emoji spam"""
    if not context.args:
        return await safe_reply(update, "⚠️ `+wave` - uses emoji NC", parse_mode="Markdown")
    await ncemo_cmd(update, context)

@only_sudo
async def plus_halt_v2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Halt all activities"""
    await stopall_cmd(update, context)

@only_sudo
async def plus_haltlock_v2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Halt and lock - stops all operations"""
    await stopall_cmd(update, context)

@only_sudo
async def plus_killall_v2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kill all operations"""
    await stopall_cmd(update, context)

@only_sudo
async def plus_phase_v2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rotating name changes with emojis"""
    if not context.args:
        return await safe_reply(update, "⚠️ `+phase <name>`", parse_mode="Markdown")
    await pyramidnc_cmd(update, context)

@only_sudo
async def listallbots_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all active bots with their usernames"""
    if not bots:
        return await safe_reply(update, "❌ No active bots")
    
    text = "🤖 **Active Bots**\n\n"
    for bot in bots:
        try:
            me = await bot.get_me()
            username = f"@{me.username}" if me.username else "<unknown>"
            text += f"• `{username}`\n"
        except:
            text += "• `ERROR`\n"
    
    text += f"\n✅ **Total: {len(bots)} bots**"
    await safe_reply(update, text, parse_mode="Markdown")

@only_sudo
async def getallgclinks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get all group chat links where bots are present (group chats only, not channels or personal chats)"""
    if not bot_group_cache:
        return await safe_reply(update, "⚠️ No groups tracked yet")
    
    all_chats = set()
    for bot_id, chats in bot_group_cache.items():
        all_chats.update(chats)
    
    if not all_chats:
        return await safe_reply(update, "⚠️ No groups found")
    
    group_links = []
    for chat_id in sorted(all_chats):
        try:
            chat = await context.bot.get_chat(chat_id)
            # Only show group chats, not channels (broadcast) or personal chats (private)
            if chat.type not in ["supergroup", "group"]:
                continue
            
            link = chat.invite_link if hasattr(chat, 'invite_link') and chat.invite_link else f"ID: `{chat_id}`"
            title = chat.title or "Unknown"
            group_links.append((title, link))
        except:
            pass
    
    if not group_links:
        return await safe_reply(update, "⚠️ No group chats found (channels and personal chats were excluded)")
    
    text = f"📋 **Group Chats ({len(group_links)} total):**\n\n"
    for idx, (title, link) in enumerate(group_links, 1):
        text += f"{idx}. {title}\n"
        text += f"   └─ {link}\n\n"
    
    text += "✅ To leave all groups, use `/leaveallgroups`"
    await safe_reply(update, text, parse_mode="Markdown")

@only_sudo
async def leaveallgroups_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Leave all group chats"""
    if not bot_group_cache:
        return await safe_reply(update, "⚠️ No groups to leave")
    
    all_chats = set()
    for bot_id, chats in bot_group_cache.items():
        all_chats.update(chats)
    
    if not all_chats:
        return await safe_reply(update, "⚠️ No groups found")
    
    msg = await update.message.reply_text(f"👋 Leaving {len(all_chats)} groups...")
    
    success = 0
    for bot in bots:
        for chat_id in list(all_chats):
            try:
                await bot.leave_chat(chat_id)
                success += 1
            except:
                pass
    
    await msg.edit_text(f"✅ Left groups! ({success} operations completed)")


# ╔════════════════════════════════════════════════════════════════╗
# ║              AUTO-REPLIES & MESSAGE HANDLING                   ║
# ╚════════════════════════════════════════════════════════════════╝

async def auto_replies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.from_user:
        return
    
    chat_id = update.message.chat_id
    uid = update.message.from_user.id
    known_chats.add(chat_id)
    known_users.add(uid)
    
    # Track which bot is in which group
    await update_bot_group_cache(context.bot.id, chat_id)

    if uid in muted_users:
        try:
            await update.message.delete()
        except:
            pass
        return

    if uid in replyryuk_targets and REPLY_RYUK_TEXTS:
        now_ts = time.time()
        bot_id = context.bot.id
        user_bot_cooldowns = last_ryuk_reply.setdefault(uid, {})
        if now_ts - user_bot_cooldowns.get(bot_id, 0) >= 0.2:
            user_bot_cooldowns[bot_id] = now_ts
            try:
                await update.message.reply_text(random.choice(REPLY_RYUK_TEXTS), reply_to_message_id=update.message.message_id)
            except:
                pass

    if update.message.from_user.is_bot:
        return

    if chat_id in swipe_mode:
        name_arg = swipe_mode[chat_id]
        template = random.choice(SWIPE_TEXTS)
        try:
            await update.message.reply_text(template.replace("NAME", name_arg))
        except:
            pass

async def tracker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.effective_chat:
            return
        chat_id = update.effective_chat.id
        if chat_id < 0:
            add_group_db(context.bot.token, chat_id)
            # Track bot presence
            await update_bot_group_cache(context.bot.id, chat_id)
    except:
        pass

async def kicked_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bot kicked/left notifications"""
    if not update.my_chat_member:
        return

    try:
        chat_id = update.my_chat_member.chat.id
        new_status = update.my_chat_member.new_chat_member.status

        if new_status in ["kicked", "left"]:

            try:
                bot_me = await context.bot.get_me()
                bot_name = f"@{bot_me.username}" if bot_me.username else f"Bot {bot_me.id}"
            except:
                bot_name = "Unknown Bot"

            try:
                chat_info = await context.bot.get_chat(chat_id)
                chat_name = chat_info.title or f"Chat {chat_id}"
            except:
                chat_name = f"Chat {chat_id}"

            for bot_id in list(bot_group_cache.keys()):
                if chat_id in bot_group_cache.get(bot_id, set()):
                    bot_group_cache[bot_id].discard(chat_id)

            status_text = "🚫 KICKED" if new_status == "kicked" else "👋 LEFT"

            try:
                await context.bot.send_message(
                    chat_id=OWNER_ID,
                    text=f"{status_text}\n\n`{bot_name}` has been {new_status} from `{chat_name}`",
                    parse_mode="Markdown"
                )
            except:
                pass

    except:
        pass
# ╔════════════════════════════════════════════════════════════════╗
# ║                  BOT INITIALIZATION                            ║
# ╚════════════════════════════════════════════════════════════════╝

def build_app(token):
    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("ping", ping_cmd))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("o", optimize_cmd))
    app.add_handler(CommandHandler("stopall", stopall_cmd))
    
    app.add_handler(CommandHandler("gcnc", gcnc))
    app.add_handler(CommandHandler("ncemo", ncemo_cmd))
    app.add_handler(CommandHandler("pyramidnc", pyramidnc_cmd))
    app.add_handler(CommandHandler("stopgcnc", stopgcnc))
    app.add_handler(CommandHandler("delaync", delaync_cmd))
    
    app.add_handler(CommandHandler("spm", spm_cmd))
    app.add_handler(CommandHandler("stopspm", stopspm_cmd))
    app.add_handler(CommandHandler("stopallspm", stopallspm_cmd))
    app.add_handler(CommandHandler("delaygcspm", delaygcspm_cmd))
    
    app.add_handler(CommandHandler("slidespam", slidespam))
    app.add_handler(CommandHandler("stopslidespam", stopslidespam))
    app.add_handler(CommandHandler("targetslide", targetslide))
    app.add_handler(CommandHandler("stoptargetslide", stoptargetslide))
    
    app.add_handler(CommandHandler("stickerspm", stickerspm_cmd))
    app.add_handler(CommandHandler("stopstickerspm", stopstickerspm_cmd))
    app.add_handler(CommandHandler("gifspm", gifspm_cmd))
    app.add_handler(CommandHandler("stopgifspm", stopgifspm_cmd))
    app.add_handler(CommandHandler("mediaspm", mediaspm_cmd))
    app.add_handler(CommandHandler("stopmediaspm", stopmediaspm_cmd))
    app.add_handler(CommandHandler("voicespm", voicespm_cmd))
    app.add_handler(CommandHandler("stopvoicespm", stopvoicespm_cmd))
    
    app.add_handler(CommandHandler("save", save_cmd))
    app.add_handler(CommandHandler("del", del_cmd))
    app.add_handler(CommandHandler("setpfp", setpfp_cmd))
    app.add_handler(CommandHandler("pfp", pfp_cmd))
    app.add_handler(CommandHandler("stoppfp", stoppfp_cmd))
    
    app.add_handler(CommandHandler("swipe", swipe))
    app.add_handler(CommandHandler("stopswipe", stopswipe))
    app.add_handler(CommandHandler("replyryuk", replyryuk_cmd))
    app.add_handler(CommandHandler("stopreplyryuk", stopreplyryuk_cmd))
    
    app.add_handler(CommandHandler("mute", mute_cmd))
    app.add_handler(CommandHandler("unmute", unmute_cmd))
    app.add_handler(CommandHandler("mutelist", mutelist_cmd))
    app.add_handler(CommandHandler("promote", promote_cmd))
    app.add_handler(CommandHandler("demote", demote_cmd))
    app.add_handler(CommandHandler("promoteallbots", promoteallbots))
    app.add_handler(CommandHandler("promoteall", promoteall))
    app.add_handler(CommandHandler("addsudo", addsudo_cmd))
    app.add_handler(CommandHandler("delsudo", delsudo_cmd))
    app.add_handler(CommandHandler("listsudo", listsudo_cmd))
    
    app.add_handler(CommandHandler("activebots", activebots))
    app.add_handler(CommandHandler("leave", leave_cmd))
    app.add_handler(CommandHandler("addbots", addbots))
    app.add_handler(CommandHandler("listbots", listbots))
    app.add_handler(CommandHandler("listallbots", listallbots_cmd))
    app.add_handler(CommandHandler("rnbots", rnbots_cmd))
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^tk_"))
    app.add_handler(CommandHandler("getallgclinks", getallgclinks_cmd))
    app.add_handler(CommandHandler("leaveallgroups", leaveallgroups_cmd))
    
    # Plus prefix commands
    app.add_handler(CommandHandler("stop", plus_stop))
    app.add_handler(CommandHandler("optimize", plus_optimize))
    app.add_handler(CommandHandler("flood", plus_flood))
    app.add_handler(CommandHandler("wave", plus_wave))
    app.add_handler(CommandHandler("halt", plus_halt))
    app.add_handler(CommandHandler("haltlock", plus_haltlock))
    app.add_handler(CommandHandler("killall", plus_killall))
    app.add_handler(CommandHandler("phase", plus_phase))
    
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^tk_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, plus_command_router), group=-1)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, token_receiver), group=0)
    app.add_handler(MessageHandler(filters.ALL, auto_replies), group=1)
    app.add_handler(MessageHandler(filters.ALL, tracker), group=2)
    
    return app

async def run_worker(token):
    if token in ACTIVE_BOTS:
        return
    try:
        app = build_app(token)
        apps.append(app)
        bots.append(app.bot)
        bot_tokens.append(token)
        ACTIVE_BOTS[token] = True
        RUNNING_APPLICATIONS[token] = app
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        me = await app.bot.get_me()
        bot_usernames.append(me.username)
        add_bot_db(token, me.username)
        logging.info(f"✅ @{me.username} Connected!")
    except Exception as e:
        logging.error(f"❌ Failed to connect bot: {e}")
        # Remove invalid token
        if token in bot_tokens:
            bot_tokens.remove(token)
        if token in ACTIVE_BOTS:
            del ACTIVE_BOTS[token]
        remove_bot_db(token)

class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.strip().rstrip('/').lower()
        
        # Serve Dashboard on main URLs
        if path in ["", "/", "/dashboard", "/health"]:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            
            active_bots = len(bots) if 'bots' in globals() else 0
            ping_interval = PING_INTERVAL if 'PING_INTERVAL' in globals() else 300
            
            html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Ryuk S1 Manager Dashboard</title>
    <meta http-equiv="refresh" content="10">
    <style>
        body {{ background:#0a0a0a; color:#00ff00; font-family:Arial, sans-serif; padding:20px; text-align:center; }}
        .container {{ max-width:900px; margin:auto; background:#111; padding:25px; border-radius:12px; border:1px solid #00ff00; }}
        h1 {{ color:#00ff41; }}
        .status {{ background:#1a1a1a; padding:15px; margin:15px 0; border-radius:8px; }}
        table {{ margin:20px auto; border-collapse:collapse; width:80%; }}
        th, td {{ padding:10px; border:1px solid #333; }}
        th {{ background:#222; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔥 Ryuk S1 Manager Dashboard</h1>
        <p><strong>Service:</strong> <span style="color:#00ff00;">🟢 ONLINE</span></p>
        <p><strong>URL:</strong> {os.environ.get('SELF_URL', 'Not Set')}</p>
        <p><strong>Current Time:</strong> {time.strftime("%Y-%m-%d %H:%M:%S")}</p>
        
        <div class="status">
            <h2>📊 System Info</h2>
            <p><strong>Active Bots:</strong> {active_bots}</p>
            <p><strong>Memory Usage:</strong> {psutil.Process().memory_info().rss / (1024*1024):.1f} MB</p>
        </div>
        
        <div class="status">
            <h2>🔄 Self-Ping Status</h2>
            <p>Enabled • Interval: {ping_interval} seconds</p>
        </div>
        
        <h2>🤖 Connected Bots</h2>
        <table>
            <tr><th>Username</th><th>Status</th></tr>
"""
            
            if active_bots > 0:
                for bot in bots:
                    try:
                        uname = getattr(bot, 'username', None) or 'Unknown'
                        html += f"<tr><td>@{uname}</td><td style='color:#00ff00'>✅ Connected</td></tr>"
                    except:
                        html += "<tr><td>Unknown</td><td>Checking...</td></tr>"
            else:
                html += "<tr><td colspan='2'>No bots connected yet...</td></tr>"
            
            html += """
        </table>
        <p style="color:#666; margin-top:20px;">Auto-refreshing every 10 seconds</p>
    </div>
</body>
</html>"""
            self.wfile.write(html.encode('utf-8'))
            return

        # Simple health check fallback
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass


def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), _HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"🌐 Health server + Dashboard running on port {port}")
    logger.info(f"🌐 Health server + Dashboard started on port {port}")


async def self_ping_loop():
    SELF_URL = os.environ.get("SELF_URL", "").strip()
    if not SELF_URL:
        logger.warning("⚠️ SELF_URL environment variable is not set")
        return
    
    logger.info(f"🔄 Self-ping loop started: {SELF_URL}")
    interval = int(os.environ.get("SELF_PING_INTERVAL", 300))
    
    while True:
        try:
            urllib.request.urlopen(SELF_URL, timeout=15).read()
            logger.info(f"✅ Self-ping successful: {SELF_URL}")
        except Exception as e:
            logger.error(f"❌ Self-ping failed: {e}")
        
        await asyncio.sleep(interval)

async def safe_worker(token):
    try:
        await run_worker(token)
    except Exception as e:
        logger.error(f"❌ Worker crashed for token {token[:10]}: {e}")


async def main():
    start_health_server()
    asyncio.create_task(self_ping_loop())

    init_db()

    valid_tokens = []
    tasks = []

    for token in TOKENS:
        token = token.strip()
        if not token:
            continue

        try:
            is_valid = await validate_bot_token(token)

            if is_valid:
                valid_tokens.append(token)
                add_bot_db(token)

                tasks.append(
                    asyncio.create_task(safe_worker(token))
                )
            else:
                logger.warning(f"❌ Invalid token (removing): {token[:20]}...")
                remove_bot_db(token)

        except Exception as e:
            logger.error(f"❌ Token error: {e}")

    logger.info(f"RYUK MANAGER ONLINE - {len(valid_tokens)} BOTS READY")

    # 🔥 PROPER KEEP-ALIVE (INSIDE MAIN)
    while True:
        await asyncio.sleep(3600)


# ===== ENTRY POINT =====
if __name__ == "__main__":
    asyncio.run(main())
