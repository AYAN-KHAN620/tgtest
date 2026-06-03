import asyncio
import json
import os
import random
import time
import logging
import uuid
import gc
from collections import OrderedDict
from typing import Optional

from telegram import Update, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, 
    CommandHandler, 
    ContextTypes, 
    MessageHandler, 
    CallbackQueryHandler,
    filters
)
from telegram.error import RetryAfter

TOKENS = [
   "7636069318:AAHtsKs5PMTnM4UO4N2kBd3qOVHyunm_G5I"
]


OWNER_ID = 2082618819
SUDO_FILE = None  

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

os.makedirs("downloads/global", exist_ok=True)

class AdminRights:
    def __init__(self, is_sudo=False):
        self.can_change_info = True
        self.can_invite_users = True
        self.can_pin_messages = True
        self.can_promote_members = True
        self.can_manage_chat = True
        self.can_manage_video_chats = True
        self.is_anonymous = False 
        self.can_delete_messages = is_sudo
        self.can_restrict_members = is_sudo

FULL_ADMIN = AdminRights(is_sudo=True)
LIMITED_ADMIN = AdminRights(is_sudo=False)

RAID_TEXTS = [
"2-3 ⱮƛӇƖƝЄ ӇƲЄ ƝƛӇƖ ӇƛƓƝЄ ԼƓЄ ???? 🤣",

"ⱦєяє ɠɦαя кι αυятση кι вяα ƒαα∂ к αρηα кυятα ѕιℓωαυ яη∂ук ???? 🤣",
"ƓƦƖƁ Ɱƛ Ƙ ƁƛƇӇƳ ƓӇƛƦ ⱮЄ ƛƬƬƛ ԼЄ ƛƛ ???? 🤣",
"ƊӇƛƬ яη∂ιкєу ???? 🤣",
"ƬЄƦƖ Ɱƛƛ Ƙƛ ƁӇƧƊƛ ???? 🤣",
"Ƭєяι мα к вσѕ∂є м αιѕα ℓαт мαяυggα ηα gαтє ωαу σƒ ιη∂ια вαη נαєggα ???? 🤣",
"ꪶ  ⱠƲƝ ƬЄ Ɣƛʝ ꪻ♡︎ ???? 🤣",
"уααя αρηι мα мт ηυηgу кя ???? 🤣",
"Ƭяу мσм кє ѕαтн вα∂ мαηηєяѕ кя∂υggα ???? 🤣",
"ƬЄƦƖ Ɱƛ ƇӇƠƊƲƝ ???? 🤣",
"ƬЄƦƖ Ɱƛ Ƙ ƁӇƠƧƊƛ ⱮƛƊƦƇӇƠƊ ???? 🤣",
"ⱮƛƇƇӇƛƦ ƬⱮƘƇ ???? 🤣",
"Ƭєяу мαα кσ qαвαя ηαѕєєв ηα нσ яη∂укє ???? 🤣",
"ƲƬӇ яη∂к кυттє ???? 🤣",
"ƤƛƦԼЄ Ɠ ƘӇƛЄƓƛ ƘƳƛ ƬƠⱮⱮƳ ???? 🤣",
"ƁƖӇƛƦƖ ƓƛƝƓ ƬЄƦƖ Ɱƛ ƇӇƠƊƲƝ ???? 🤣",
"ƬƲⱮ ƧƁ ƘƲƬƬƠ ƘƖ ʝӇƲƝƊ ƘƖ ⱮƘƁ ???? 🤣",
"ƓƇ ԼЄƑƬ ԼЄ яη∂ιвαℓα ???? 🤣",
"Ƭєяι мαα кι ƈнσтι ραкα∂ кє ∂єєωαя мє мααяυηgα ∂нαм ∂нαм кι αωααנ ααуєgι ???? 🤣",
"ƁӇƛƓƝƛ ⱮƛƝƛ ӇƳ ƬⱮƘƁ ???? 🤣",
"ƘƖ ⱮƘƁ ƳƦƦ ƁӇƛƓ ƘЄƧЄ ƦӇЄ ӇƠ ƓƛƦƖƁƠ ???? 🤣",
"ƬⱮƘƇ ???? 🤣",
"ƬⱮƘƁ ???? 🤣",
"ƬƁƘƇ ???? 🤣",
"ƦƝƊƘ ƁƛƇӇƳ ???? 🤣",
"ƠƳЄ ƬƠⱮⱮƳ ƲƬӇ ƁӇƛƓƝƛ ƝƳ ӇƛƖ ???? 🤣"]
NCEMO_EMOJIS = ["👻", "🩷", "😂", "🤣", "♥️", "💦", "😹", "🥶", "🥀", "🎀", "😈", "👑", "😤", "🤷🏻‍♂️", "👅", "🤙🏻", "🤦🏻‍♂️", "😏", "👏🏻", "🔥", "💥", "✌🏾", "🩸", "❤️‍🔥", "💀", "🤪", "😱"]
SWIPE_TEXTS = [
"NAME 𝙆𝙊 𝙋𝙀𝙇𝙏𝙀 𝙃𝙐𝙀 𝙀𝙉𝙏𝙍𝙔 ???? 🤣😎❤️‍🔥",
"NAME 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐈 ̷C̷H̷U̷T̷ 𝙈𝙀 𝐋𝐎𝐔𝐃𝐀 ̷M̷A̷D̷A̷R̷C̷H̷O̷D̷ ???? 😂🩷🤚🏼",
"NAME 𝙍𝙀𝙋𝙇𝙔 𝐊𝐀𝐑 𝙂𝘼𝙍𝙄𝘽 𝐃𝐀𝐑 𝙆𝙔𝙐 𝐑𝐀𝐇𝐀 𝐇 ???? 😁🤙🏼🤍",
"NAME 𝐂𝐇𝐀𝐋 𝙏𝙀𝙍𝙄 𝐌𝐀 ̷C̷H̷O̷D̷U̷ 𝙋𝘼𝙏𝘼𝙆 𝐏𝐀𝐓𝐀𝐊 𝙆𝙀 ???? 🤪👻🩶",
"NAME ̷C̷H̷U̷D̷K̷E̷ 𝙎𝙋𝘼𝙈 𝐘𝐀𝐇𝐈 𝘼𝙐𝙆𝘼𝙏 𝐇 𝙏𝙀𝙍𝙄 𝐆𝐀𝐑𝐈𝐁 ???? 😹🩵🙌🏼",
"𝐂𝐏 𝐊𝐀𝐑 NAME 𝙂𝘼𝙍𝙄𝘽 𝐁𝐇𝐀𝐀𝐆 𝙈𝘼𝙏 𝐂𝐇𝐎𝐓𝐄𝐘 ???? 😂🩶🤚🏼",
"NAME 𝐊𝐈 𝙈𝙐𝙈𝙈𝙔 𝐊𝐎 ̷R̷A̷N̷D̷I̷ 𝘽𝘼𝙉𝘼 𝘿𝙐𝙉𝙂𝘼 𝙃𝙀𝙃𝙀𝙃𝙀 ???? 🤣💖✌🏼",
"NAME 𝐊𝐄 𝐁𝐀𝐀𝐏 𝘼𝙔𝘼𝙉 𝐘𝐄𝐇 𝐇𝐀𝐈 𝐈𝐍𝐊𝐈 𝐌𝐀𝐀 𝐊𝐄 𝐘𝐀𝐀𝐑 ???? 😆🩶🤚🏼",
"𝐊𝐀𝐁𝐀𝐃𝐈 𝙒𝘼𝙇𝙀 NAME 𝐊𝐈 𝙈𝙆𝘽 ???? 🤣👻💗",
"𝐀𝐑𝐄𝐘 NAME 𝐊𝐈 𝙈𝙆𝘽 𝙔𝘼𝘼𝙍 𝐁𝐇𝐀𝐆 𝙆𝘼𝙄𝙎𝙀 𝐑𝐇𝐄 𝐇𝐎 𝙂𝘼𝙍𝙄𝘽𝙊 ???? 😤👻💞",
"𝘼𝙍𝙀𝙔 NAME 𝙈𝘼𝘾𝘾𝙃𝘼𝙍 𝙏𝙈𝙆𝘾 ???? 😂🩷✌🏾",
"NAME 𝙏𝙐 𝙇𝘼𝘿𝙃𝙀𝙂𝘼 𝙃𝙐𝙈𝙎𝙀 𝙏𝙀𝙍𝙄 𝙈𝘼 𝘾𝙊𝘿𝙆𝙀 𝙈𝙄𝙏𝙏𝙄 𝙈𝙀 𝙈𝙄𝙇𝘼𝘿𝙀𝙉𝙂𝙀 𝙃𝙐𝙈 ???? 😂🔥🤸🏻",
"NAME 𝙇𝙀𝘼𝙑𝙀 𝙇𝙀 𝙏𝙐 𝙍𝙉𝘿𝙔𝙆𝙀 𝙋𝘼𝙎𝘼𝙉𝘿 𝙉𝘼𝙄 𝘼𝙔𝘼 𝙈𝙍𝙆𝙊 ???? 😏👋🏼",
"NAME 𝙂𝙍𝙄𝘽 𝙈𝘼 𝙆 𝘽𝘼𝘾𝙃𝙔 𝙂𝙃𝘼𝙍 𝙈𝙀 𝘼𝙏𝙏𝘼 𝙇𝙀 𝘼𝘼 ???? 😂🥲",
"NAME 𝘼𝙐𝙍𝘼𝙏𝙊 𝙆𝘼 𝙆𝘼𝙈 𝙍𝙊𝙏𝙄 𝘽𝙉𝘼𝙉𝘼 𝙃𝙊𝙏𝘼 𝙃 𝙏𝙊 NAME 𝙆𝙄 𝙈𝘼 𝙔𝘼𝙃𝘼 𝙆𝙔𝙐 𝘾𝙃𝙐𝘿𝙍𝙃𝙄 ???? 🤬🤣😭",
"NAME 𝙏𝙀𝙍𝙄 𝙈𝘼 𝙆𝙊 𝙎𝙀𝙉𝘼𝙋𝘼𝙏𝙄 𝙎𝙀 𝘾𝙃𝙐𝘿𝙒𝘼𝘿𝙀𝙉𝙂𝙀 ???? 🪖🖲️🔥",
"NAME 𝙏𝙍𝙔 𝙂𝙉𝘿 𝙈𝙀 𝘼𝙀𝙎𝘼 𝘽𝙃𝘼𝙇𝘼 𝙈𝘼𝙍𝙐𝙂𝘼 𝙎𝙄𝘿𝙃𝘼 𝙈𝙊𝙐𝙉𝙏 𝙀𝙑𝙀𝙍𝙀𝙎𝙏 𝙋𝙀 𝙍𝙐𝙆𝙀𝙂𝘼 ???? 💯🚀💔",
"NAME 𝑻𝑬𝑹𝑰 𝑴𝑨𝑨 ᵀᴬᴷᴸᴵ 𝑯𝑬𝑯𝑬𝑯𝑬 ???? 💖💛💚",
"""NAME 𝙈𝙐𝙅𝙃𝙀 𝙉𝙐𝙈𝘽𝙀𝙍 𝙆𝙄 𝙆𝙔𝘼 𝙕𝘼𝙍𝙐𝙍𝘼𝙏
𝙈𝘼𝙄 𝙃𝙐 𝙀𝙆 𝙋𝙇𝙐𝙈𝘽𝙀𝙍 👨‍🔧
𝙅𝘼𝘽 𝘾𝙃𝙊𝘿𝙉𝙀 𝙆𝘼 𝙈𝘼𝙉𝙉 𝙆𝙍𝙀𝙂𝘼 NAME 𝙆𝙄 𝙈𝘼𝘼 𝘾𝙊𝘿 𝘿𝙐𝙉𝙂𝘼 𝙂𝙃𝘼𝙍 ???? 😂🔧""",
"NAME 𝙏𝙀𝙍𝙔 𝙈𝘼𝘼 𝙆𝙊 𝙌𝘼𝘽𝘼𝙍 𝙉𝘼𝙎𝙀𝙀𝘽 𝙉𝘼 𝙃𝙊 𝙍𝙉𝘿𝙔𝙆𝙀 ???? 😑🖕🏽💔",
"NAME ꪶ 𝗟𝗨𝗡 𝗧𝗘 𝗩𝗔𝗝 ꪻ♡︎ ???? 😂👏🏻✨",
"NAME 𝙏𝙀𝙍𝙔 𝙉𝘼𝙉𝙄 𝘾𝙃𝙐𝘿 𝙂𝙔𝙄 𝘿𝙃𝘼𝙈 𝘿𝙃𝘼𝙈 𝘿𝙃𝘼𝙈 ???? 🥁🔊😍"]
TARGET_SLIDE_TEXTS = [
"𝙉𝙔 𝙉𝙔 𝙉𝙔 𝙈𝙀 𝙆𝙐𝘾𝙃 𝙉𝙔 𝙅𝙉𝙏𝘼 𝘽𝙎 𝙀𝙔 {} 𝙆𝙄 𝙈𝘼 𝙍𝙉𝘿𝙔 𝙀𝙔 🤣🔥",
"𝙊𝙔𝙔 𝙔𝙍𝙍 𝙔𝙀 {} 𝙆𝙄 𝙈𝘼 𝙍𝙊𝙅 𝙍𝙊𝙅 𝙂𝙊𝘽𝘼𝙍 𝙆𝙃𝘼𝙆𝙍 𝘼𝙋𝙉𝘼 𝘽𝙐𝙉𝘿 𝘿𝙀𝙏𝙄 𝙀𝙔 😑🖕🏿🔥😑🖕🏿🔥😑🖕🏿🔥",
"𝙊𝙔𝙔 {} 𝙆𝙈𝙕𝙊𝙍 𝙏𝘼𝙏𝙏𝙀 𝙏𝙀𝙍𝙄 𝙈𝘼 𝙎𝘼𝘽𝙎𝙀 𝙎𝙀 𝘽𝙃𝙄𝙆 𝙌 𝙈𝘼𝙉𝙂𝙏𝙄 𝙀𝙔",
"𝙊𝙔𝙔 {} 𝙏𝙀𝙍𝙄 𝙈𝘼 𝙆𝘼 𝘽𝙐𝙉𝘿 𝙆𝘼𝙇𝘼 𝙌 𝙀𝙔 😑🔥🤣🖕🏿🔥",
"𝙀𝙑𝙀𝙍𝙔𝙏𝙃𝙄𝙉𝙂 𝙄𝙎 𝙊𝙆 𝘽𝙐𝙏 {} 𝙆𝙄 𝙈𝘼 𝘾𝙐𝘿𝙉𝘼 𝙄𝙎 𝙋𝙀𝙍𝙈𝘼𝙉𝙀𝙉𝙏 🤣🔥",
"{} 𝙏𝘼𝙏𝙏𝙀 𝙏𝙀𝙍𝙄 𝙈𝘼 𝙆𝙈𝙕𝙊𝙍 𝙍𝙉𝘿𝙔 𝙀𝙔 𝙔𝘼𝙆𝙄𝙉 𝙉𝙔 𝙀𝙔 𝙏𝙊 𝘼𝙋𝙉𝙀 𝙎𝘼𝘽 𝘽𝘼𝘼𝙋 𝙎𝙀 𝙋𝙐𝘾𝙃𝙇𝙀 😑🔥",
"𝘼𝙉𝘿𝙔 𝙈𝘼𝙉𝘿𝙔 𝙎𝘼𝙉𝘿𝙔 {} 𝙏𝘼𝙏𝙏𝙀 𝙆𝙄 𝙆𝙈𝙕𝙊𝙍 𝙈𝘼 𝙎𝙏𝙍𝙊𝙉𝙂𝙀𝙎𝙏 𝙍𝙉𝘿𝙔 😑🖕🏿🔥🤣🖕🏿🔥😑🔥",
"𝙊𝙔 𝙈𝙀 𝙆𝙐𝘾𝙃 𝙉𝙔 𝙎𝙐𝙉𝙐𝙉𝙂𝘼 𝘽𝙎 𝙔𝙀 {} 𝙆𝙄 𝙈𝘼 𝙈𝙀𝙍𝙄 𝙋𝙑𝙏. 𝙍𝙉𝘿𝙔 𝙀𝙔 😑🔥",
"𝘾𝙃𝙄 𝙔𝙍𝙍 𝙀𝙔 {} 𝙆𝙄 𝙈𝘼 𝘿𝙐𝙎𝙏𝘽𝙄𝙉 𝙎𝙀 𝘿𝙄𝙇𝘿𝙊 𝙉𝙄𝙆𝘼𝙇 𝙆𝙍 𝘼𝙋𝙉𝙀 𝘽𝙐𝙉𝘿 𝙈𝙀 𝘿𝘼𝙇 𝙇𝙀𝙏𝙄 𝙀𝙔 😑🔥",
"𝙊𝙔𝙔 {} 𝙏𝘼𝙏𝙏𝙀 𝙈𝙐𝙅𝙀 𝘽𝘼𝘼𝙋 𝘽𝙉𝘼 𝙇𝙀 𝙉𝙔 𝙏𝙊 𝙏𝙀𝙍𝙄 𝙈𝘼 𝙍𝙉𝘿𝙔"
]

REPLY_MAFI_TEXTS = [
    
"𝙄𝙕𝙕𝘼𝙏 𝙆𝙍𝙊 𝙏𝙐𝙈𝙃𝘼𝙍𝙀 𝘽𝘼𝘼𝙋 𝘼𝙔𝘼𝙉 𝙆𝙄 😑🙌🏾",
"𝙂𝘼𝘿𝘿𝙃𝘼 𝘿𝙄𝙆𝙃𝘼 𝙆𝙃𝙊𝘿 𝘿𝙄𝙔𝘼 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝘿𝙄𝙆𝙃𝙄 𝘾𝙃𝙊𝘿 𝘿𝙄𝙔𝘼 🙊🤦🏾😂",
"𝘼𝙔𝘼𝙉 𝘽𝘿𝙈𝙊𝙎𝙃 𝙎𝙋𝙀𝘼𝙆𝙄𝙉𝙂 𝙁𝙍𝙊𝙈 𝙏𝙀𝙍𝙄 𝙈𝙆𝘽🤦🏾☎️ ",
"𝘾𝙐𝘿𝙉𝘼 𝙈𝙉𝘼 𝙃𝘼𝙄 😩🤟🏻",
"𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝘾𝙊𝘿 𝙆𝙀 𝙈𝘼𝙍 𝘿𝙐𝙉𝙂𝘼 🤣🖕🏾",
"𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝘾𝙐𝘿 𝙍𝙃𝙄 𝙃𝘼𝙄 𝙉𝘼𝘾𝙃𝙊 👻🕺",
"𝙃𝙔 𝘾𝙊𝙏𝙐 😉✌🏾",
"𝘾𝙔𝘼 ",
"𝙁𝘼𝙎𝙏 𝙇𝙄𝙆𝙃",
"𝙌 ❓🤨",
"𝘾𝙐𝘿 𝙆𝙀 𝙈𝙍𝙂𝙔𝘼 𝙆𝙔𝘼 💀😹",
"𝙃𝙇𝙒 𝙋𝙂𝙇 𝘽𝙃𝘼𝙂 𝙈𝙏 🏃‍♂️💨",
"𝘼𝙔𝘼𝙉 𝘾𝙃𝙊𝘿 𝙍𝙃𝘼 𝙃𝘼𝙄 👻🔥",
"𝘾𝙔𝘼?",
"𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 ❓",
"𝙏𝙀𝙍𝙄 𝘽𝙃𝙀𝙉 𝙈𝘼𝙍𝘿𝙐 ❓",
"𝙃𝙀𝙇𝙋 𝙃𝙀𝙇𝙋 𝙈𝙏 𝙆𝙍 𝘾𝙊𝙏𝙐 😩👍🏾",
"𝙋𝙐𝙅𝘼 𝙆𝙍 𝙏𝙀𝙍𝙀 𝘽𝘼𝘼𝙋 𝘼𝙔𝘼𝙉 𝙆𝙄 🙏🏾🔥🙏🏾🔥🙏🏾🔥🙏🏾🔥",
"𝙃𝙇𝙒 𝙃𝙇𝙒 𝙃𝘼𝙈𝙇𝘼 𝙃𝙊𝙂𝙔𝘼 𝙏𝙀𝙍𝙄 𝙈𝙆𝘽 𝙈𝙀 😱😂",
"𝙏𝙀𝙍𝙄 𝘽𝙆𝘾 𝙈𝙀 𝘽𝙄𝙂𝘽𝙊𝙎𝙎 📺😆",
"𝙃𝙇𝙒 𝙍𝙀𝙋𝙇𝙔 𝙁𝘼𝙎𝙏 ",
"𝙁𝘼𝙎𝙏 𝙏𝙔𝙋𝙀 𝙆𝙍 𝘿𝘼𝙍 𝙈𝙏 😤⌨️",
"𝙃𝙀𝙇𝙋 𝙃𝙀𝙇𝙋 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝘾𝙃𝙐𝘿 𝙂𝙔𝙄 😩",
"𝘼𝙔𝘼𝙉 𝘼𝘽𝘽𝙐 𝙋𝙀𝙇 𝙍𝙃𝙀 𝙃𝘼𝙄 👻💪",
"𝙃𝙔 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙈𝙍 𝙂𝙔𝙄 𝙆𝙔𝘼 😶💔",
"𝘼𝙒𝙒 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙆𝙊 𝙋𝙊𝙊𝙆𝙄𝙀 𝘽𝙉𝘼𝙆𝙀 𝙈𝘼𝙍𝙐𝙉𝙂𝘼 🤣🎀",
"𝙆𝙔𝘼 ❓😑",
"𝙍𝙊 𝙈𝙏 😂🤟🏻",
"𝙎𝙊𝙍𝙏 𝙉𝙃𝙄 𝙆𝙍𝙐𝙉𝙂𝘼 𝘾𝙐𝘿 𝙏𝙐 𝘽𝙄𝙉𝘼 𝙍𝙐𝙆𝙀 😹🖕🏾🖕🏾💔😹💔🖕🏾🖕🏾",
"𝙏𝘼𝙆𝙀 𝙔𝙊𝙐𝙍 𝙏𝙄𝙈𝙀 𝙁𝙄𝙍 𝘾𝙐𝘿 😉✌🏾😉✌🏾😉✌🏾",
"𝙃𝙇𝙒 𝙆𝙐𝙏𝙄𝙔𝘼 𝙆𝙀 𝙇𝙍𝙆𝙀 🐶😆",
"𝙃𝙇𝙒 𝙃𝙇𝙒 𝙈𝙅𝘼 𝘼𝘼𝙍𝙃𝘼 𝘾𝙐𝘿𝙉𝙀 𝙈𝙀 😜🔥",
"𝘼𝙔𝘼𝙉 𝙂𝙉𝘿 𝙈𝘼𝘼𝙍 𝙍𝙃𝙀 𝙃𝘼𝙄 👻",
"𝙃𝙔 𝘾𝙊𝙏𝙐 𝘽𝙃𝙂 𝙈𝙏 𝙍𝙉𝘿𝙔 𝙆𝙀 🔥😑👍🏾",
"𝘽𝙃𝘼𝙂𝙉𝘼 𝙈𝘼𝙉𝘼 𝙃𝘼𝙄 𝙅𝙄 🚫😎",
"𝘼𝙔𝘼𝙉 𝘼𝘽𝘽𝙐 𝘼𝘼𝙂𝙔𝙀 🤣🩷🙌🏾",
"𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙈𝘼𝙍𝙆𝙀 𝙈𝙅𝘿𝙐𝙍𝙄 𝙆𝙃𝙏𝙈 👍🏾👍🏾👍🏾👍🏾👍🏾",
"𝙆𝙔𝘼 𝘼𝙔𝘼𝙉 𝙏𝙀𝙍𝘼 𝘽𝘼𝘼𝙋 𝙃𝘼𝙄 👻❓",
"𝙆𝙔𝘼 𝙈𝙏𝙇𝘽 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝘼𝙔𝘼𝙉 𝙉𝙀 𝘾𝙊𝘿𝙄 😹🖕🏾😹🖕🏾💔",
"𝙏𝙀𝙍𝙄 𝘽𝙃𝙀𝙉 𝙈𝘼𝙍𝙆𝙀 𝘽𝙃𝘼𝙂 𝙅𝘼𝙐𝙉𝙂𝘼 🙋🏾🤪",
"𝙏𝙀𝙍𝙄 𝘽𝙃𝙀𝙉 𝙈𝘼𝙍𝙆𝙀 𝘼𝙔𝘼𝙉 𝘽𝙃𝘼𝙂 𝙂𝙔𝘼 🤦🏾💔",
"𝘽𝙃𝘼𝙂 𝙌 𝙍𝙃𝘼 𝙃𝘼𝙄 ❓",
"𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙈𝙐𝙈𝘽𝘼𝙄 𝙈𝙀 𝘾𝙐𝘿𝙀𝙂𝙄 😌🩷🙌🏾",
"𝙏𝙔𝙋𝙀 𝙆𝙍 𝙉𝘼 𝘼𝘽 𝙏𝙀𝙍𝙀 𝘽𝘼𝘼𝙋 𝙆𝙀 𝙎𝘼𝙈𝙉𝙀 ⁉️",
"𝙆𝙍 𝙏𝙔𝙋𝙀 𝙏𝙈𝙆𝘾 😂🤟🏻😂🤟🏻",
"𝙅𝙇𝘿𝙄 𝘾𝙐𝘿 🤢",
"𝘽𝙄𝙉𝘼 𝙍𝙐𝙆𝙀 𝙏𝙃𝙐𝙆𝘼𝙄 𝙃𝙊𝙂𝙄 𝙏𝙀𝙍𝙄 😁😂",
"𝘽𝙃𝘼𝙂𝙀𝙂𝘼 𝙏𝙊 𝘾𝙊𝘿 𝙆𝙀 𝙈𝘼𝙍𝘿𝙐𝙉𝙂𝘼 😑🙌🏾😑🙌🏾😑🙌🏾",
"𝙄𝘿𝙃𝙍 𝘼𝙅𝘼 𝘾𝙃𝙊𝙏𝙀𝙔 👶🍼",
"𝘽𝙃𝘼𝙂 𝙈𝙏 𝙆𝙐𝙏𝙏𝙄 𝙆𝙀 🙊😂",
"𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙆𝙊 𝘽𝙀𝙉10 𝙈𝙀 𝘾𝙊𝘿𝙐𝙉𝙂𝘼 👽😱",
"𝙄𝙕𝙕𝘼𝙏 𝙆𝙍𝙀𝙂𝘼 𝘼𝘼𝙅𝙎𝙀 𝘼𝙔𝘼𝙉 𝘼𝘽𝘽𝙐 𝙆𝙄 😂🤟🏻😂🤟🏻",
"𝙏𝙀𝙍𝙄 𝘽𝙃𝙀𝙉 𝙆𝙄 𝙋𝙊𝙊𝙆𝙄𝙀 𝙂𝙓𝙉𝘿 𝙈𝙀 𝙇𝙐𝙉 🎀",
"𝘽𝙃𝘼𝙂 𝙈𝙏 𝘽𝙀𝙏𝙀 😑🙌🏾😑🙌🏾",
"𝙄𝘿𝙃𝙍 𝘼𝙅𝘼 𝙇𝘼𝘿𝙇𝙀 😉❤️",
"𝙏𝙀𝙍𝙄 𝙂𝙀𝙉𝘿 𝙈𝙀 100 𝙃𝘼𝙏𝙃 💯🔥",
"𝙆𝙍 𝘼𝘽 𝙃𝘼𝙒𝘼𝘽𝘼𝘼𝙕𝙄?",
"𝙇𝙀 𝘼𝘼𝙂𝙔𝘼 𝙏𝙀𝙍𝘼 𝘽𝘼𝘼𝙋 𝘼𝙔𝘼𝙉 👻👑",
"𝘽𝙃𝘼𝙂𝙉𝙀 𝙎𝙀 𝙆𝙐𝘾𝙃 𝙉𝙃𝙄 𝙃𝙊𝙂𝘼 🐕❌",
"𝘽𝙃𝘼𝙂 𝘽𝙃𝘼𝙂 𝙏𝙈𝙆𝘾 😑😹",
"𝘽𝙃𝘼𝙂𝘼 𝘽𝙃𝘼𝙂𝘼 𝙆𝙀 𝙈𝘼𝙍𝙐𝙉𝙂𝘼 🤣🩷🙌🏾",
"𝘽𝙉 𝘼𝘽 𝙁𝙔𝙏𝙍 🤦🏾😎😂",
"𝙆𝙍 𝙉𝘼 𝙁𝙔𝙏 😁🔥",
"𝘽𝙃𝘼𝙂𝙀𝙂𝘼 ❓",
"𝘽𝙃𝘼𝙂 𝙅𝙇𝘿𝙄 🐕🏳️‍🌈",
"𝙃𝙇𝙒 𝘾𝙐𝘿𝙂𝙔𝙄 𝙆𝙔𝘼 💀😹",
"𝘼𝙔𝘼𝙉 𝘼𝘼𝙂𝙔𝘼 👻🔥",
"𝙏𝙀𝙍𝙀 𝘽𝘼𝘼𝙋 𝘼𝙔𝘼𝙉 𝙆𝙄 𝙀𝙉𝙏𝙍𝙔 👻😂",
"𝙍𝙀𝙈𝙀𝙈𝘽𝙀𝙍 𝙏𝙃𝙀 𝙂𝙊𝘿 𝙆𝙀𝙉𝙂 𝘼𝙔𝘼𝙉 👻👑"
]

class LRUCache:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity
    def add(self, key):
        self.cache[key] = None
        if len(self.cache) > self.capacity: self.cache.popitem(last=False)
    def __contains__(self, key): return key in self.cache

global_replied_messages = LRUCache(5000) 

SUDO_USERS = {OWNER_ID}

def save_sudo():
    pass  # render in-memory sudo storage

apps, bots, bot_usernames = [], [], []
group_tasks = {}       
pyramid_tasks = {}
slide_targets = set()  
slidespam_tasks = {}   
targetslide_tasks = {}
swipe_mode = {}        
spm_loop_tasks = {}    
sticker_spm_tasks = {}
gif_spm_tasks = {}
media_spm_tasks = {}
voice_spm_tasks = {}
pfp_tasks = {}

nc_delays = {}
spm_delays = {}
pfp_delays = {}
REPLY_MAFI_DELAY = 0.2 

known_chats = set()    
known_users = set()    
replymafi_targets = set()  
last_mafi_reply = {}   
muted_users = set()    
active_menus = {} 

async def safe_reply(update: Update, text: str, **kwargs):
    if not update.message: return
    unique_msg_id = f"{update.message.chat_id}_{update.message.message_id}"
    if unique_msg_id in global_replied_messages: return
    global_replied_messages.add(unique_msg_id)
    try: await update.message.reply_text(text, **kwargs)
    except Exception: pass

def only_sudo(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message: return
        if update.effective_user.id not in SUDO_USERS:
            return await safe_reply(update, "❌ 𝙔𝙤𝙪 𝙖𝙧𝙚 𝙣𝙤𝙩 𝙎𝙐𝘿𝙊.")
        return await func(update, context)
    return wrapper

def only_owner(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message: return
        if update.effective_user.id != OWNER_ID:
            return await safe_reply(update, "❌ 𝙊𝙣𝙡𝙮 𝙊𝙒𝙉𝙀𝙍 𝙘𝙖𝙣 𝙙𝙤 𝙩𝙝𝙞𝙨.")
        return await func(update, context)
    return wrapper

async def notify_missing(context, chat_id, error_msg, bot_username):
    link = f"https://t.me/{bot_username}?startgroup=true"
    msg = f"⚠️ **Bot Missing From Chat!**\n\n**Chat ID:** `{chat_id}`\n**Bot:** @{bot_username}\n**Error:** {error_msg}\n\n👉 [CLICK HERE TO ADD BOT BACK]({link})"
    for uid in list(SUDO_USERS):
        try: await context.bot.send_message(uid, msg, parse_mode="Markdown", disable_web_page_preview=True)
        except: pass

def extract_command_text(raw_text: Optional[str]) -> str:
    if not raw_text: return ""
    parts = raw_text.split(" ", 1)
    if len(parts) == 1: return ""
    return parts[1].strip()

async def get_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message: return update.message.reply_to_message.from_user.id
    if update.message.entities:
        for entity in update.message.entities:
            if entity.type == 'text_mention':
                return entity.user.id
    if context.args:
        arg = context.args[0]
        try: return int(arg)
        except ValueError:
            if arg.startswith("@"):
                try: return (await context.bot.get_chat(arg)).id
                except: pass
    return None

async def get_mention_from_id(context, uid):
    try: return f"[{(await context.bot.get_chat(uid)).first_name}](tg://user?id={uid})"
    except: return f"`{uid}`"

async def bot_loop(bot, chat_id, base, mode):
    i = 0
    bot_uname = (await bot.get_me()).username
    while True:
        try:
            current_delay = nc_delays.get(chat_id, 0.9)
            text = f"{base} {RAID_TEXTS[i % len(RAID_TEXTS)]}" if mode == "raid" else f"{base} {NCEMO_EMOJIS[i % len(NCEMO_EMOJIS)]}"
            i += 1  
            await bot.set_chat_title(chat_id, text)
            await asyncio.sleep(current_delay)
        except Exception as e:
            if "Chat not found" in str(e):
                await notify_missing(bot, chat_id, str(e), bot_uname)
                break
            await asyncio.sleep(nc_delays.get(chat_id, 0.9))

async def pyramid_loop_worker(bot, chat_id, name):
    bot_uname = (await bot.get_me()).username
    base_text = f"{name} 𝙏𝙀𝙍𝙄 𝙈𝘼 𝙋𝙔𝙍𝘼𝙈𝙄𝘿 𝙈 𝘾𝙃𝙐𝘿 𝙍𝙃𝙄 🎖️ "
    chars_left = 128 - len(base_text)
    max_stars = max(1, min(15, chars_left // 2))
    
    while True:
        try:
            current_delay = nc_delays.get(chat_id, 0.9)
            star_count = random.randint(1, max_stars)
            frame_to_set = base_text + "⭐️" * star_count
            await bot.set_chat_title(chat_id, frame_to_set)
            await asyncio.sleep(current_delay)
        except Exception as e:
            if "Chat not found" in str(e):
                await notify_missing(bot, chat_id, str(e), bot_uname)
                break
            await asyncio.sleep(nc_delays.get(chat_id, 0.9))

async def spm_loop_sender(bot, chat_id: int, text: str):
    bot_uname = (await bot.get_me()).username
    while True:
        try:
            current_delay = spm_delays.get(chat_id, 0.9)
            await bot.send_message(chat_id=chat_id, text=text, disable_web_page_preview=True)
            await asyncio.sleep(current_delay)
        except asyncio.CancelledError: break
        except Exception as e: 
            if "Chat not found" in str(e):
                await notify_missing(bot, chat_id, str(e), bot_uname)
                break
            await asyncio.sleep(3)

async def slidespam_worker(bot, chat_id: int, message_id: int, text: str):
    while True:
        try:
            current_delay = spm_delays.get(chat_id, 0.9)
            await bot.send_message(chat_id=chat_id, text=text, reply_to_message_id=message_id, disable_web_page_preview=True)
            await asyncio.sleep(current_delay)
        except asyncio.CancelledError: break
        except Exception: await asyncio.sleep(2)

async def targetslide_worker(bot, chat_id: int, message_id: int, name: str):
    while True:
        try:
            current_delay = spm_delays.get(chat_id, 0.9)
            msg = random.choice(TARGET_SLIDE_TEXTS).format(name)
            await bot.send_message(chat_id=chat_id, text=msg, reply_to_message_id=message_id, disable_web_page_preview=True)
            await asyncio.sleep(current_delay)
        except asyncio.CancelledError: break
        except Exception: await asyncio.sleep(2)

async def media_spm_sender(bot, chat_id: int, media_type: str, file_id: str):
    bot_uname = (await bot.get_me()).username
    while True:
        try:
            current_delay = spm_delays.get(chat_id, 0.9)
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
            await asyncio.sleep(current_delay)
        except asyncio.CancelledError: break
        except Exception as e: 
            if "Chat not found" in str(e):
                await notify_missing(bot, chat_id, str(e), bot_uname)
                break
            await asyncio.sleep(3)

async def pfp_loop_worker(bot, chat_id: int):
    bot_uname = (await bot.get_me()).username
    while True:
        try:
            delay = pfp_delays.get(chat_id, 0.9) 
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
        except asyncio.CancelledError: break
        except Exception as e:
            if "Chat not found" in str(e):
                await notify_missing(bot, chat_id, str(e), bot_uname)
                break
            await asyncio.sleep(2)

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
    if row: keyboard.append(row)
    
    keyboard.append([
        InlineKeyboardButton("🔘 𝙎𝙚𝙡𝙚𝙘𝙩 𝘼𝙡𝙡", callback_data=f"tk_{task_id}_all"),
        InlineKeyboardButton("⚪️ 𝙉𝙤𝙣𝙚", callback_data=f"tk_{task_id}_none")
    ])
    keyboard.append([InlineKeyboardButton("🚀 𝙎𝙏𝘼𝙍𝙏 𝙇𝘼𝙐𝙉𝘾𝙃", callback_data=f"tk_{task_id}_start")])
    return InlineKeyboardMarkup(keyboard)

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id not in SUDO_USERS:
        return await query.answer("❌ You are not SUDO/Owner. Access Denied.", show_alert=True)
        
    data = query.data.split("_")
    task_id = data[1]
    action = data[2]
    
    if task_id not in active_menus:
        return await query.answer("❌ Menu expired or task already running.", show_alert=True)
        
    menu = active_menus[task_id]
    
    if action == "tgl":
        await query.answer() 
        idx = int(data[3])
        if idx in menu["selected"]: menu["selected"].remove(idx)
        else: menu["selected"].add(idx)
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
            return await query.answer("⚠️ Select at least one bot!", show_alert=True)
            
        await query.answer("🚀 Firing tasks!", show_alert=False)
        await query.edit_message_text(f"✅ 𝙎𝙩𝙖𝙧𝙩𝙚𝙙 **{menu['cmd'].upper()}** 𝙬𝙞𝙩𝙝 {len(menu['selected'])} 𝙗𝙤𝙩𝙨!", parse_mode="Markdown")
        
        chat_id = menu["chat_id"]
        for idx in menu["selected"]:
            b = bots[idx]
            if menu["cmd"] == "pfp":
                t = asyncio.create_task(pfp_loop_worker(b, chat_id))
                pfp_tasks.setdefault(chat_id, []).append(t)
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

@only_sudo
async def optimize_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global_replied_messages.cache.clear()
    gc.collect()
    await safe_reply(update, "✨ 𝙎𝙮𝙨𝙩𝙚𝙢 𝙤𝙥𝙩𝙞𝙢𝙞𝙯𝙚𝙙 𝙖𝙣𝙙 𝙘𝙖𝙘𝙝𝙚 𝙘𝙡𝙚𝙖𝙧𝙚𝙙.")

@only_owner
async def stopall_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dicts_to_clear = [group_tasks, pyramid_tasks, slidespam_tasks, targetslide_tasks, 
                      spm_loop_tasks, sticker_spm_tasks, gif_spm_tasks, pfp_tasks, 
                      media_spm_tasks, voice_spm_tasks]
    for d in dicts_to_clear:
        for task_list in d.values():
            if isinstance(task_list, list):
                for t in task_list: t.cancel()
            elif isinstance(task_list, dict):
                for t in task_list.values(): t.cancel()
        d.clear()
    swipe_mode.clear()
    replymafi_targets.clear()
    await safe_reply(update, "🛑 𝘼𝙡𝙡 𝙤𝙥𝙚𝙧𝙖𝙩𝙞𝙤𝙣𝙨 𝙝𝙖𝙫𝙚 𝙗𝙚𝙚𝙣 𝙩𝙚𝙧𝙢𝙞𝙣𝙖𝙩𝙚𝙙 𝙜𝙡𝙤𝙗𝙖𝙡𝙡𝙮.")

@only_sudo
async def save_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        return await safe_reply(update, "⚠️ 𝙍𝙚𝙥𝙡𝙮 𝙩𝙤 𝙖 𝙥𝙝𝙤𝙩𝙤 𝙬𝙞𝙩𝙝 `/save`", parse_mode="Markdown")
        
    chat_id = update.message.chat_id
    photo = update.message.reply_to_message.photo[-1] 
    file = await context.bot.get_file(photo.file_id)
    
    os.makedirs(f"downloads/{chat_id}", exist_ok=True)
    path = f"downloads/{chat_id}/{photo.file_unique_id}.jpg"
    await file.download_to_drive(path)
    await safe_reply(update, "📸 𝙋𝙝𝙤𝙩𝙤 𝙨𝙖𝙫𝙚𝙙 𝙡𝙤𝙘𝙖𝙡𝙡𝙮 𝙛𝙤𝙧 𝙩𝙝𝙞𝙨 𝙜𝙧𝙤𝙪𝙥!")

@only_sudo
async def del_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        return await safe_reply(update, "⚠️ 𝙍𝙚𝙥𝙡𝙮 𝙩𝙤 𝙩𝙝𝙚 𝙨𝙖𝙫𝙚𝙙 𝙥𝙝𝙤𝙩𝙤 𝙬𝙞𝙩𝙝 `/del`", parse_mode="Markdown")
        
    chat_id = update.message.chat_id
    uid = update.message.reply_to_message.photo[-1].file_unique_id
    path = f"downloads/{chat_id}/{uid}.jpg"
    
    if os.path.exists(path):
        os.remove(path)
        await safe_reply(update, "🗑 𝙋𝙝𝙤𝙩𝙤 𝙙𝙚𝙡𝙚𝙩𝙚𝙙 𝙛𝙧𝙤𝙢 𝙩𝙝𝙞𝙨 𝙜𝙧𝙤𝙪𝙥'𝙨 𝙨𝙩𝙤𝙧𝙖𝙜𝙚!")
    else:
        await safe_reply(update, "⚠️ 𝙏𝙝𝙞𝙨 𝙥𝙝𝙤𝙩𝙤 𝙞𝙨 𝙣𝙤𝙩 𝙞𝙣 𝙩𝙝𝙚 𝙨𝙩𝙤𝙧𝙖𝙜𝙚.")

@only_sudo
async def gsave_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        return await safe_reply(update, "⚠️ 𝙍𝙚𝙥𝙡𝙮 𝙩𝙤 𝙖 𝙥𝙝𝙤𝙩𝙤 𝙬𝙞𝙩𝙝 `/gsave`", parse_mode="Markdown")
        
    photo = update.message.reply_to_message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    
    path = f"downloads/global/{photo.file_unique_id}.jpg"
    await file.download_to_drive(path)
    await safe_reply(update, "🌍 𝙋𝙝𝙤𝙩𝙤 𝙨𝙖𝙫𝙚𝙙 𝙩𝙤 𝙂𝙇𝙊𝘽𝘼𝙇 𝙨𝙩𝙤𝙧𝙖𝙜𝙚!")

@only_sudo
async def gpfp_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global_files = [f for f in os.listdir("downloads/global") if f.endswith('.jpg')]
    if not global_files:
        return await safe_reply(update, "⚠️ 𝙉𝙤 𝙥𝙝𝙤𝙩𝙤𝙨 𝙞𝙣 𝙂𝙇𝙊𝘽𝘼𝙇 𝙨𝙩𝙤𝙧𝙖𝙜𝙚. 𝙐𝙨𝙚 `/gsave` 𝙛𝙞𝙧𝙨𝙩.", parse_mode="Markdown")
        
    unique_msg_id = f"{update.message.chat_id}_{update.message.message_id}"
    if unique_msg_id in global_replied_messages: return
    global_replied_messages.add(unique_msg_id)
    
    msg = await update.message.reply_text("🌍 𝙐𝙥𝙙𝙖𝙩𝙞𝙣𝙜 𝘼𝙇𝙇 𝙜𝙧𝙤𝙪𝙥 𝙋𝙁𝙋𝙨 𝙜𝙡𝙤𝙗𝙖𝙡𝙡𝙮...", parse_mode="Markdown")
    success = 0
    
    for cid in list(known_chats):
        if cid > 0: continue 
        pic = random.choice(global_files)
        for bot in bots:
            try:
                with open(f"downloads/global/{pic}", 'rb') as f:
                    await bot.set_chat_photo(cid, photo=f)
                success += 1
                break 
            except Exception: pass
            
    await msg.edit_text(f"✅ 𝙂𝙡𝙤𝙗𝙖𝙡 𝙋𝙁𝙋 𝙪𝙥𝙙𝙖𝙩𝙚 𝙘𝙤𝙢𝙥𝙡𝙚𝙩𝙚! 𝘾𝙝𝙖𝙣𝙜𝙚𝙙 𝙞𝙣 {success} 𝙜𝙧𝙤𝙪𝙥𝙨.", parse_mode="Markdown")

@only_sudo
async def pfp_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    folder = f"downloads/{chat_id}"
    if not os.path.exists(folder) or not os.listdir(folder):
        return await safe_reply(update, "⚠️ 𝙉𝙤 𝙥𝙝𝙤𝙩𝙤𝙨 𝙨𝙖𝙫𝙚𝙙 𝙛𝙤𝙧 𝙩𝙝𝙞𝙨 𝙜𝙧𝙤𝙪𝙥. 𝙐𝙨𝙚 `/save` 𝙛𝙞𝙧𝙨𝙩.", parse_mode="Markdown")
        
    unique_msg_id = f"{chat_id}_{update.message.message_id}"
    if unique_msg_id in global_replied_messages: return
    global_replied_messages.add(unique_msg_id)
    
    task_id = str(uuid.uuid4())[:8]
    active_menus[task_id] = {"cmd": "pfp", "chat_id": chat_id, "payload": "", "selected": set()}
    
    await update.message.reply_text("📸 **PFP LOOP MENU**\nSelect bots to run the profile picture loop:", reply_markup=get_selector_keyboard(task_id), parse_mode="Markdown")

@only_sudo
async def stoppfp_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in pfp_tasks and pfp_tasks[chat_id]:
        for t in pfp_tasks[chat_id]: t.cancel()
        pfp_tasks[chat_id] = []
        await safe_reply(update, "🛑 𝙋𝙁𝙋 𝙡𝙤𝙤𝙥𝙨 𝙨𝙩𝙤𝙥𝙥𝙚𝙙.")

@only_sudo
async def stickerspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.sticker:
        return await safe_reply(update, "⚠️ 𝙍𝙚𝙥𝙡𝙮 𝙩𝙤 𝙖 𝙨𝙩𝙞𝙘𝙠𝙚𝙧 𝙬𝙞𝙩𝙝 `/stickerspm`", parse_mode="Markdown")
        
    file_id = update.message.reply_to_message.sticker.file_id
    chat_id = update.message.chat_id
    
    unique_msg_id = f"{chat_id}_{update.message.message_id}"
    if unique_msg_id in global_replied_messages: return
    global_replied_messages.add(unique_msg_id)
    
    task_id = str(uuid.uuid4())[:8]
    active_menus[task_id] = {"cmd": "stickerspm", "chat_id": chat_id, "payload": file_id, "selected": set()}
    await update.message.reply_text("🎭 **STICKER SPAM MENU**\nSelect bots to launch sticker attack:", reply_markup=get_selector_keyboard(task_id), parse_mode="Markdown")

@only_sudo
async def stopstickerspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in sticker_spm_tasks and sticker_spm_tasks[chat_id]:
        for t in sticker_spm_tasks[chat_id]: t.cancel()
        sticker_spm_tasks[chat_id] = []
        await safe_reply(update, "🛑 𝙎𝙩𝙞𝙘𝙠𝙚𝙧 𝙎𝙋𝙈 𝙨𝙩𝙤𝙥𝙥𝙚𝙙.")

@only_sudo
async def gifspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.animation:
        return await safe_reply(update, "⚠️ 𝙍𝙚𝙥𝙡𝙮 𝙩𝙤 𝙖 𝙂𝙄𝙁 𝙬𝙞𝙩𝙝 `/gifspm`", parse_mode="Markdown")
        
    file_id = update.message.reply_to_message.animation.file_id
    chat_id = update.message.chat_id
    
    unique_msg_id = f"{chat_id}_{update.message.message_id}"
    if unique_msg_id in global_replied_messages: return
    global_replied_messages.add(unique_msg_id)
    
    task_id = str(uuid.uuid4())[:8]
    active_menus[task_id] = {"cmd": "gifspm", "chat_id": chat_id, "payload": file_id, "selected": set()}
    await update.message.reply_text("🎥 **GIF SPAM MENU**\nSelect bots to launch GIF attack:", reply_markup=get_selector_keyboard(task_id), parse_mode="Markdown")

@only_sudo
async def stopgifspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in gif_spm_tasks and gif_spm_tasks[chat_id]:
        for t in gif_spm_tasks[chat_id]: t.cancel()
        gif_spm_tasks[chat_id] = []
        await safe_reply(update, "🛑 𝙂𝙄𝙁 𝙎𝙋𝙈 𝙨𝙩𝙤𝙥𝙥𝙚𝙙.")

@only_sudo
async def mediaspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not (update.message.reply_to_message.photo or update.message.reply_to_message.video):
        return await safe_reply(update, "⚠️ 𝙍𝙚𝙥𝙡𝙮 𝙩𝙤 𝙖 𝙥𝙝𝙤𝙩𝙤 𝙤𝙧 𝙫𝙞𝙙𝙚𝙤 𝙬𝙞𝙩𝙝 `/mediaspm`", parse_mode="Markdown")
        
    if update.message.reply_to_message.photo:
        file_id = update.message.reply_to_message.photo[-1].file_id
        media_type = "photo"
    else:
        file_id = update.message.reply_to_message.video.file_id
        media_type = "video"

    chat_id = update.message.chat_id
    unique_msg_id = f"{chat_id}_{update.message.message_id}"
    if unique_msg_id in global_replied_messages: return
    global_replied_messages.add(unique_msg_id)
    
    task_id = str(uuid.uuid4())[:8]
    active_menus[task_id] = {"cmd": "mediaspm", "type": media_type, "chat_id": chat_id, "payload": file_id, "selected": set()}
    await update.message.reply_text("🖼️ **MEDIA SPAM MENU**\nSelect bots to launch media attack:", reply_markup=get_selector_keyboard(task_id), parse_mode="Markdown")

@only_sudo
async def stopmediaspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in media_spm_tasks and media_spm_tasks[chat_id]:
        for t in media_spm_tasks[chat_id]: t.cancel()
        media_spm_tasks[chat_id] = []
        await safe_reply(update, "🛑 𝙈𝙚𝙙𝙞𝙖 𝙎𝙋𝙈 𝙨𝙩𝙤𝙥𝙥𝙚𝙙.")

@only_sudo
async def voicespm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.voice:
        return await safe_reply(update, "⚠️ 𝙍𝙚𝙥𝙡𝙮 𝙩𝙤 𝙖 𝙫𝙤𝙞𝙘𝙚 𝙣𝙤𝙩𝙚 𝙬𝙞𝙩𝙝 `/voicespm`", parse_mode="Markdown")
        
    file_id = update.message.reply_to_message.voice.file_id
    chat_id = update.message.chat_id
    unique_msg_id = f"{chat_id}_{update.message.message_id}"
    if unique_msg_id in global_replied_messages: return
    global_replied_messages.add(unique_msg_id)
    
    task_id = str(uuid.uuid4())[:8]
    active_menus[task_id] = {"cmd": "voicespm", "chat_id": chat_id, "payload": file_id, "selected": set()}
    await update.message.reply_text("🎤 **VOICE SPAM MENU**\nSelect bots to launch voice attack:", reply_markup=get_selector_keyboard(task_id), parse_mode="Markdown")

@only_sudo
async def stopvoicespm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in voice_spm_tasks and voice_spm_tasks[chat_id]:
        for t in voice_spm_tasks[chat_id]: t.cancel()
        voice_spm_tasks[chat_id] = []
        await safe_reply(update, "🛑 𝙑𝙤𝙞𝙘𝙚 𝙎𝙋𝙈 𝙨𝙩𝙤𝙥𝙥𝙚𝙙.")

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_reply(update, "💗 𝙒𝙚𝙡𝙘𝙤𝙢𝙚 𝙩𝙤 𝙈𝙖𝙛𝙞𝙖 𝘽𝙤𝙩!\n✨ 𝙐𝙨𝙚 `/help` 𝙩𝙤 𝙨𝙚𝙚 𝙖𝙡𝙡 𝙘𝙤𝙢𝙢𝙖𝙣𝙙𝙨.", parse_mode="Markdown")

@only_sudo
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "𝘼𝙔𝘼𝙉 𝗡𝗘𝗧𝗪𝗢𝗥𝗞 𝗩3 (𝗨𝗟𝗧𝗜𝗠𝗔𝗧𝗘)❤️‍🔥\n\n"
        "🤍 𝗡𝗖 (𝗡𝗮𝗺𝗲 𝗖𝗵𝗮𝗻𝗴𝗲)\n"
        "• `/gcnc <text>` : 𝙏𝙚𝙭𝙩 𝙉𝙖𝙢𝙚 𝘾𝙝𝙖𝙣𝙜𝙚\n"
        "• `/ncemo <text>` : 𝙀𝙢𝙤𝙟𝙞 𝙉𝙖𝙢𝙚 𝘾𝙝𝙖𝙣𝙜𝙚\n"
        "• `/pyramidnc <name>` : 𝙋𝙮𝙧𝙖𝙢𝙞𝙙 𝙉𝙖𝙢𝙚 𝘾𝙝𝙖𝙣𝙜𝙚\n"
        "• `/stopgcnc` : 𝙎𝙩𝙤𝙥 𝙉𝙖𝙢𝙚 𝘾𝙝𝙖𝙣𝙜𝙚\n"
        "• `/stoppyramidnc` : 𝙎𝙩𝙤𝙥 𝙋𝙮𝙧𝙖𝙢𝙞𝙙\n"
        "• `/delaync <sec>` : 𝙉𝙖𝙢𝙚 𝘾𝙝𝙖𝙣𝙜𝙚 𝘿𝙚𝙡𝙖𝙮\n\n"
        "📸 𝗣𝗙𝗣 & 𝗠𝗘𝗗𝗜𝗔 𝗦𝗣𝗔𝗠\n"
        "• `/save` (reply) : 𝙎𝙖𝙫𝙚 𝙂𝙧𝙤𝙪𝙥 𝙋𝙁𝙋\n"
        "• `/del` (reply) : 𝘿𝙚𝙡𝙚𝙩𝙚 𝙂𝙧𝙤𝙪𝙥 𝙋𝙁𝙋\n"
        "• `/gsave` (reply) : 𝙎𝙖𝙫𝙚 𝙂𝙡𝙤𝙗𝙖𝙡 𝙋𝙁𝙋\n"
        "• `/gpfp` : 𝙂𝙡𝙤𝙗𝙖𝙡 𝙋𝙁𝙋 𝙐𝙥𝙙𝙖𝙩𝙚\n"
        "• `/pfp` : 𝙋𝙁𝙋 𝙇𝙤𝙤𝙥 𝙈𝙚𝙣𝙪\n"
        "• `/stoppfp` : 𝙎𝙩𝙤𝙥 𝙋𝙁𝙋 𝙇𝙤𝙤𝙥\n"
        "• `/delaypfp <sec>` : 𝙋𝙁𝙋 𝘿𝙚𝙡𝙖𝙮\n"
        "• `/stickerspm` (reply) : 𝙎𝙩𝙞𝙘𝙠𝙚𝙧 𝙎𝙥𝙖𝙢\n"
        "• `/stopstickerspm` : 𝙎𝙩𝙤𝙥 𝙎𝙩𝙞𝙘𝙠𝙚𝙧 𝙎𝙥𝙖𝙢\n"
        "• `/gifspm` (reply) : 𝙂𝙄𝙁 𝙎𝙥𝙖𝙢\n"
        "• `/stopgifspm` : 𝙎𝙩𝙤𝙥 𝙂𝙄𝙁 𝙎𝙥𝙖𝙢\n"
        "• `/mediaspm` (reply) : 𝙋𝙝𝙤𝙩𝙤/𝙑𝙞𝙙𝙚𝙤 𝙎𝙥𝙖𝙢\n"
        "• `/stopmediaspm` : 𝙎𝙩𝙤𝙥 𝙈𝙚𝙙𝙞𝙖 𝙎𝙥𝙖𝙢\n"
        "• `/voicespm` (reply) : 𝙑𝙤𝙞𝙘𝙚 𝙎𝙥𝙖𝙢\n"
        "• `/stopvoicespm` : 𝙎𝙩𝙤𝙥 𝙑𝙤𝙞𝙘𝙚 𝙎𝙥𝙖𝙢\n\n"
        "💦 𝗦𝗟𝗜𝗗𝗘 & 𝗦𝗣𝗔𝗠\n"
        "• `/targetslide <name>` (reply) : 𝙏𝙖𝙧𝙜𝙚𝙩 𝙎𝙡𝙞𝙙𝙚\n"
        "• `/stoptargetslide` : 𝙎𝙩𝙤𝙥 𝙏𝙖𝙧𝙜𝙚𝙩 𝙎𝙡𝙞𝙙𝙚\n"
        "• `/slidespam <text>` (reply) : 𝙏𝙖𝙧𝙜𝙚𝙩 𝙇𝙤𝙘𝙠 𝙎𝙥𝙖𝙢\n"
        "• `/stopslidespam` : 𝙎𝙩𝙤𝙥 𝙏𝙖𝙧𝙜𝙚𝙩 𝙇𝙤𝙘𝙠\n"
        "• `/spm <text>` : 𝙎𝙥𝙖𝙢 𝙇𝙤𝙤𝙥\n"
        "• `/stopspm` : 𝙎𝙩𝙤𝙥 𝙎𝙥𝙖𝙢 𝙇𝙤𝙤𝙥\n"
        "• `/stopallspm` : 𝙎𝙩𝙤𝙥 𝘼𝙡𝙡 𝙎𝙥𝙖𝙢𝙨\n"
        "• `/delaygcspm <sec>` : 𝙎𝙥𝙖𝙢 𝘿𝙚𝙡𝙖𝙮\n\n"
        "🥱 𝗥𝗘𝗣𝗟𝗬 𝗠𝗔𝗙𝗜 & 𝗦𝗪𝗜𝗣𝗘\n"
        "• `/replymafi` (reply/tag) : 𝘼𝙪𝙩𝙤 𝙄𝙣𝙨𝙪𝙡𝙩 𝙍𝙚𝙥𝙡𝙮\n"
        "• `/stopreplymafi` (reply/tag) : 𝙎𝙩𝙤𝙥 𝘼𝙪𝙩𝙤 𝙍𝙚𝙥𝙡𝙮\n"
        "• `/swipe <name>` : 𝘼𝙪𝙩𝙤 𝙉𝙖𝙢𝙚 𝙍𝙚𝙥𝙡𝙖𝙘𝙚\n"
        "• `/stopswipe` : 𝙎𝙩𝙤𝙥 𝙉𝙖𝙢𝙚 𝙍𝙚𝙥𝙡𝙖𝙘𝙚\n\n"
        "🤫 𝗠𝗨𝗧𝗘 & 𝗔𝗗𝗠𝗜𝗡\n"
        "• `/mute` (reply/tag) : 𝙈𝙪𝙩𝙚 𝙐𝙨𝙚𝙧\n"
        "• `/unmute` (reply/tag) : 𝙐𝙣𝙢𝙪𝙩𝙚 𝙐𝙨𝙚𝙧\n"
        "• `/mutelist` : 𝙈𝙪𝙩𝙚𝙙 𝙐𝙨𝙚𝙧𝙨 𝙇𝙞𝙨𝙩\n"
        "• `/promoteall` : 𝙋𝙧𝙤𝙢𝙤𝙩𝙚 𝘼𝙡𝙡 𝙐𝙨𝙚𝙧𝙨\n"
        "• `/promoteallbots` : 𝙋𝙧𝙤𝙢𝙤𝙩𝙚 𝘼𝙡𝙡 𝘽𝙤𝙩𝙨\n"
        "• `/addsudo` (reply/tag) : 𝘼𝙙𝙙 𝙎𝙪𝙙𝙤 𝙐𝙨𝙚𝙧\n"
        "• `/delsudo` (reply/tag) : 𝙍𝙚𝙢𝙤𝙫𝙚 𝙎𝙪𝙙𝙤\n"
        "• `/listsudo` : 𝙎𝙪𝙙𝙤 𝙐𝙨𝙚𝙧𝙨 𝙇𝙞𝙨𝙩\n\n"
        "😆 𝗠𝗜𝗦𝗖𝗘𝗟𝗟𝗔𝗡𝗘𝗢𝗨𝗦\n"
        "• `/stopall` : 𝙎𝙩𝙤𝙥 𝘼𝙡𝙡 𝙏𝙖𝙨𝙠𝙨 (𝙊𝙬𝙣𝙚𝙧)\n"
        "• `/o` : 𝙊𝙥𝙩𝙞𝙢𝙞𝙯𝙚 & 𝘾𝙡𝙚𝙖𝙧 𝘾𝙖𝙘𝙝𝙚\n"
        "• `/activebots` : 𝘼𝙘𝙩𝙞𝙫𝙚 𝘽𝙤𝙩𝙨 𝙎𝙩𝙖𝙩𝙪𝙨\n"
        "• `/leave` : 𝘼𝙡𝙡 𝘽𝙤𝙩𝙨 𝙇𝙚𝙖𝙫𝙚 𝙂𝙧𝙤𝙪𝙥\n"
        "• `/missingbots` : 𝘾𝙝𝙚𝙘𝙠 𝙈𝙞𝙨𝙨𝙞𝙣𝙜 𝘽𝙤𝙩𝙨\n"
        "• `/getallactivelinks` : 𝙂𝙚𝙩 𝙂𝙧𝙤𝙪𝙥 𝙇𝙞𝙣𝙠𝙨\n"
        "• `/ping` : 𝘽𝙤𝙩 𝙋𝙞𝙣𝙜 𝙎𝙩𝙖𝙩𝙪𝙨"
    )
    await safe_reply(update, help_text, parse_mode="Markdown")

@only_sudo
async def activebots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not bots: return await safe_reply(update, "❌ 𝙉𝙤 𝙖𝙘𝙩𝙞𝙫𝙚 𝙗𝙤𝙩𝙨 𝙧𝙪𝙣𝙣𝙞𝙣𝙜.")
    text = "🤖 𝘼𝙘𝙩𝙞𝙫𝙚 𝘽𝙤𝙩𝙨:\n\n" + "\n".join(f"• @{me}" for me in bot_usernames) + f"\n\n✅ 𝙏𝙤𝙩𝙖𝙡 𝘽𝙤𝙩𝙨: {len(bots)}"
    await safe_reply(update, text, parse_mode="Markdown")

@only_sudo
async def leave_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    await safe_reply(update, "👋 𝘼𝙡𝙡 𝙗𝙤𝙩𝙨 𝙖𝙧𝙚 𝙡𝙚𝙖𝙫𝙞𝙣𝙜 𝙩𝙝𝙞𝙨 𝙜𝙧𝙤𝙪𝙥!")
    for bot in bots:
        try: await bot.leave_chat(chat_id)
        except: pass

@only_sudo
async def missingbots_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    unique_msg_id = f"{chat_id}_{update.message.message_id}"
    if unique_msg_id in global_replied_messages: return
    global_replied_messages.add(unique_msg_id)
    
    missing = []
    for bot, uname in zip(bots, bot_usernames):
        try:
            m = await bot.get_chat_member(chat_id, bot.id)
            if m.status in ['left', 'kicked', 'banned']: missing.append(uname)
        except Exception: missing.append(uname)
        
    if not missing: return await update.message.reply_text("✅ 𝘼𝙡𝙡 𝙗𝙤𝙩𝙨 𝙖𝙧𝙚 𝙖𝙡𝙧𝙚𝙖𝙙𝙮 𝙞𝙣 𝙩𝙝𝙞𝙨 𝙜𝙧𝙤𝙪𝙥!")
    await update.message.reply_text("🕵️‍♂️ **Missing Bots:**\n\n" + "\n".join(f"• @{u}" for u in missing), parse_mode="Markdown")

async def ping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_reply(update, f"🏓 𝙋𝙤𝙣𝙜! ✅ {random.randint(30,90)} 𝙢𝙨")

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_reply(update, f"🆔 𝙔𝙤𝙪𝙧 𝙄𝘿: `{update.effective_user.id}`", parse_mode="Markdown")

@only_owner
async def addsudo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = await get_target_user(update, context)
    if uid:
        SUDO_USERS.add(uid)
        save_sudo()
        mention = await get_mention_from_id(context, uid)
        await safe_reply(update, f"👑 {mention} 𝙖𝙙𝙙𝙚𝙙 𝙖𝙨 𝙎𝙐𝘿𝙊 ✅", parse_mode="Markdown")
    else: await safe_reply(update, "⚠️ 𝙍𝙚𝙥𝙡𝙮 𝙤𝙧 𝙩𝙖𝙜 𝙖 𝙪𝙨𝙚𝙧.")

@only_owner
async def delsudo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = await get_target_user(update, context)
    if uid and uid in SUDO_USERS:
        SUDO_USERS.remove(uid)
        save_sudo()
        mention = await get_mention_from_id(context, uid)
        await safe_reply(update, f"🗑 {mention} 𝙧𝙚𝙢𝙤𝙫𝙚𝙙 𝙛𝙧𝙤𝙢 𝙎𝙐𝘿𝙊 ❌", parse_mode="Markdown")
    else: await safe_reply(update, "⚠️ 𝙏𝙝𝙞𝙨 𝙪𝙨𝙚𝙧 𝙞𝙨 𝙣𝙤𝙩 𝙎𝙐𝘿𝙊.")

@only_sudo
async def listsudo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "👑 𝙎𝙐𝘿𝙊 𝙐𝙨𝙚𝙧𝙨:\n\n"
    for uid in SUDO_USERS:
        mention = await get_mention_from_id(context, uid)
        text += f"• {mention}\n"
    await safe_reply(update, text, parse_mode="Markdown")

@only_sudo
async def mute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = await get_target_user(update, context)
    if not uid: return await safe_reply(update, "⚠️ 𝙍𝙚𝙥𝙡𝙮 𝙤𝙧 𝙩𝙖𝙜 𝙖 𝙪𝙨𝙚𝙧.")
    muted_users.add(uid)
    mention = await get_mention_from_id(context, uid)
    await safe_reply(update, f"🔇 𝙐𝙨𝙚𝙧 {mention} 𝙢𝙪𝙩𝙚𝙙.", parse_mode="Markdown")

@only_sudo
async def unmute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = await get_target_user(update, context)
    if not uid: return
    muted_users.discard(uid)
    mention = await get_mention_from_id(context, uid)
    await safe_reply(update, f"🔊 𝙐𝙨𝙚𝙧 {mention} 𝙪𝙣𝙢𝙪𝙩𝙚𝙙.", parse_mode="Markdown")

@only_sudo
async def mutelist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not muted_users: return await safe_reply(update, "📭 𝙉𝙤 𝙢𝙪𝙩𝙚𝙙 𝙪𝙨𝙚𝙧𝙨.")
    text = "🔇 𝙈𝙪𝙩𝙚𝙙 𝙐𝙨𝙚𝙧𝙨:\n\n"
    for uid in muted_users:
        mention = await get_mention_from_id(context, uid)
        text += f"• {mention}\n"
    await safe_reply(update, text, parse_mode="Markdown")

@only_sudo
async def promote_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = await get_target_user(update, context)
    if not uid: return await safe_reply(update, "⚠️ 𝙍𝙚𝙥𝙡𝙮 𝙤𝙧 𝙩𝙖𝙜 𝙖 𝙪𝙨𝙚𝙧.")
    rights = FULL_ADMIN if (uid in SUDO_USERS or uid == OWNER_ID or any(bot.id == uid for bot in bots)) else LIMITED_ADMIN
    try:
        await context.bot.promote_chat_member(
            chat_id=update.message.chat_id, user_id=uid,
            can_change_info=rights.can_change_info, can_delete_messages=rights.can_delete_messages,
            can_invite_users=rights.can_invite_users, can_restrict_members=rights.can_restrict_members,
            can_pin_messages=rights.can_pin_messages, can_promote_members=rights.can_promote_members,
            can_manage_chat=rights.can_manage_chat, can_manage_video_chats=rights.can_manage_video_chats,
            is_anonymous=rights.is_anonymous
        )
        mention = await get_mention_from_id(context, uid)
        await safe_reply(update, f"✅ {mention} 𝙋𝙧𝙤𝙢𝙤𝙩𝙚𝙙 𝙨𝙪𝙘𝙘𝙚𝙨𝙨𝙛𝙪𝙡𝙡𝙮.", parse_mode="Markdown")
    except Exception as e: await safe_reply(update, f"❌ 𝙀𝙧𝙧𝙤𝙧: {e}")

@only_sudo
async def demote_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = await get_target_user(update, context)
    if not uid: return
    try:
        await context.bot.promote_chat_member(
            chat_id=update.message.chat_id, user_id=uid,
            can_change_info=False, can_delete_messages=False, can_invite_users=False,
            can_restrict_members=False, can_pin_messages=False, can_promote_members=False,
            can_manage_chat=False, can_manage_video_chats=False, is_anonymous=False
        )
        mention = await get_mention_from_id(context, uid)
        await safe_reply(update, f"🛑 {mention} 𝘿𝙚𝙢𝙤𝙩𝙚𝙙.", parse_mode="Markdown")
    except Exception as e: await safe_reply(update, f"❌ 𝙀𝙧𝙧𝙤𝙧: {e}")

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
        except Exception: pass
    await safe_reply(update, f"🤖 𝙋𝙧𝙤𝙢𝙤𝙩𝙚𝙙 {success} 𝙗𝙤𝙩𝙨.")

@only_sudo
async def promoteall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if not known_users: return await safe_reply(update, "⚠️ 𝙉𝙤 𝙪𝙨𝙚𝙧𝙨 𝙞𝙣 𝙘𝙖𝙘𝙝𝙚 𝙮𝙚𝙩.")
    
    unique_msg_id = f"{chat_id}_{update.message.message_id}"
    if unique_msg_id in global_replied_messages: return
    global_replied_messages.add(unique_msg_id)
    
    msg = await update.message.reply_text("⏳ 𝘼𝙩𝙩𝙚𝙢𝙥𝙩𝙞𝙣𝙜 𝙩𝙤 𝙥𝙧𝙤𝙢𝙤𝙩𝙚 𝙖𝙡𝙡 𝙠𝙣𝙤𝙬𝙣 𝙪𝙨𝙚𝙧𝙨...", parse_mode="Markdown")
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
        except Exception: pass
    await msg.edit_text(f"✅ 𝙋𝙧𝙤𝙢𝙤𝙩𝙚𝙙 {success} 𝙪𝙨𝙚𝙧𝙨.", parse_mode="Markdown")

@only_sudo
async def delaync_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await safe_reply(update, "⚠️ 𝙐𝙨𝙖𝙜𝙚: `/delaync <sec>`", parse_mode="Markdown")
    try:
        val = float(context.args[0])
        nc_delays[update.message.chat_id] = max(0.1, val)
        await safe_reply(update, f"✅ 𝙉𝙖𝙢𝙚 𝘾𝙝𝙖𝙣𝙜𝙚 𝙙𝙚𝙡𝙖𝙮 𝙨𝙚𝙩 𝙩𝙤 `{val}` 𝙨𝙚𝙘𝙨 𝙛𝙤𝙧 𝙩𝙝𝙞𝙨 𝙜𝙧𝙤𝙪𝙥.", parse_mode="Markdown")
    except ValueError:
        await safe_reply(update, "❌ 𝙄𝙣𝙫𝙖𝙡𝙞𝙙 𝙣𝙪𝙢𝙗𝙚𝙧.")

@only_sudo
async def delaygcspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await safe_reply(update, "⚠️ 𝙐𝙨𝙖𝙜𝙚: `/delaygcspm <sec>`", parse_mode="Markdown")
    try:
        val = float(context.args[0])
        spm_delays[update.message.chat_id] = max(0.1, val)
        await safe_reply(update, f"✅ 𝙎𝙋𝙈 𝙙𝙚𝙡𝙖𝙮 𝙨𝙚𝙩 𝙩𝙤 `{val}` 𝙨𝙚𝙘𝙨 𝙛𝙤𝙧 𝙩𝙝𝙞𝙨 𝙜𝙧𝙤𝙪𝙥.", parse_mode="Markdown")
    except ValueError:
        await safe_reply(update, "❌ 𝙄𝙣𝙫𝙖𝙡𝙞𝙙 𝙣𝙪𝙢𝙗𝙚𝙧.")

@only_sudo
async def delaypfp_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await safe_reply(update, "⚠️ 𝙐𝙨𝙖𝙜𝙚: `/delaypfp <sec>`", parse_mode="Markdown")
    try:
        val = float(context.args[0])
        pfp_delays[update.message.chat_id] = max(0.1, val) 
        await safe_reply(update, f"✅ 𝙋𝙁𝙋 𝙙𝙚𝙡𝙖𝙮 𝙨𝙚𝙩 𝙩𝙤 `{val}` 𝙨𝙚𝙘𝙨 𝙛𝙤𝙧 𝙩𝙝𝙞𝙨 𝙜𝙧𝙤𝙪𝙥.", parse_mode="Markdown")
    except ValueError:
        await safe_reply(update, "❌ 𝙄𝙣𝙫𝙖𝙡𝙞𝙙 𝙣𝙪𝙢𝙗𝙚𝙧.")

@only_sudo
async def gcnc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await safe_reply(update, "⚠️ 𝙐𝙨𝙖𝙜𝙚: `/gcnc <text>`", parse_mode="Markdown")
    base = " ".join(context.args)
    chat_id = update.message.chat_id
    group_tasks.setdefault(chat_id, {})
    for bot in bots:
        if bot.id not in group_tasks[chat_id]:
            group_tasks[chat_id][bot.id] = asyncio.create_task(bot_loop(bot, chat_id, base, "raid"))
    await safe_reply(update, "🔄 𝙂𝘾 𝙣𝙖𝙢𝙚 𝙡𝙤𝙤𝙥 𝙨𝙩𝙖𝙧𝙩𝙚𝙙 𝙬𝙞𝙩𝙝 𝙧𝙖𝙞𝙙 𝙩𝙚𝙭𝙩𝙨.")

@only_sudo
async def ncemo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await safe_reply(update, "⚠️ 𝙐𝙨𝙖𝙜𝙚: `/ncemo <text>`", parse_mode="Markdown")
    base = " ".join(context.args)
    chat_id = update.message.chat_id
    group_tasks.setdefault(chat_id, {})
    for bot in bots:
        if bot.id not in group_tasks[chat_id]:
            group_tasks[chat_id][bot.id] = asyncio.create_task(bot_loop(bot, chat_id, base, "emo"))
    await safe_reply(update, "🔄 𝙂𝘾 𝙣𝙖𝙢𝙚 𝙡𝙤𝙤𝙥 𝙨𝙩𝙖𝙧𝙩𝙚𝙙 𝙬𝙞𝙩𝙝 𝙚𝙢𝙤𝙟𝙞𝙨.")

@only_sudo
async def stopgcnc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in group_tasks:
        for task in group_tasks[chat_id].values(): task.cancel()
        group_tasks[chat_id] = {}
        await safe_reply(update, "🛑 𝙇𝙤𝙤𝙥 𝙨𝙩𝙤𝙥𝙥𝙚𝙙 𝙞𝙣 𝙩𝙝𝙞𝙨 𝙂𝘾.")

@only_sudo
async def pyramidnc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await safe_reply(update, "⚠️ 𝙐𝙨𝙖𝙜𝙚: `/pyramidnc <name>`", parse_mode="Markdown")
    name = " ".join(context.args)
    chat_id = update.message.chat_id
    pyramid_tasks.setdefault(chat_id, {})
    for bot in bots:
        if bot.id not in pyramid_tasks[chat_id]:
            pyramid_tasks[chat_id][bot.id] = asyncio.create_task(pyramid_loop_worker(bot, chat_id, name))
    await safe_reply(update, f"🔺 𝙋𝙮𝙧𝙖𝙢𝙞𝙙 𝙉𝙖𝙢𝙚 𝘾𝙝𝙖𝙣𝙜𝙚 𝙡𝙤𝙤𝙥 𝙨𝙩𝙖𝙧𝙩𝙚𝙙 𝙛𝙤𝙧 `{name}`!", parse_mode="Markdown")

@only_sudo
async def stoppyramidnc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in pyramid_tasks:
        for task in pyramid_tasks[chat_id].values(): task.cancel()
        pyramid_tasks[chat_id] = {}
        await safe_reply(update, "🛑 𝙋𝙮𝙧𝙖𝙢𝙞𝙙 𝙉𝘾 𝙡𝙤𝙤𝙥 𝙨𝙩𝙤𝙥𝙥𝙚𝙙.")

# xmafi
@only_sudo
async def targetslide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message: return await safe_reply(update, "⚠️ 𝙍𝙚𝙥𝙡𝙮 𝙩𝙤 𝙖 𝙢𝙚𝙨𝙨𝙖𝙜𝙚", parse_mode="Markdown")
    uid = update.message.reply_to_message.from_user.id
    name = " ".join(context.args) if context.args else update.message.reply_to_message.from_user.first_name
    
    if uid in targetslide_tasks:
        for t in targetslide_tasks[uid]: t.cancel()
    targetslide_tasks[uid] = []
    chat_id = update.message.chat_id
    msg_id = update.message.reply_to_message.message_id
    for bot in bots:
        task = asyncio.create_task(targetslide_worker(bot, chat_id, msg_id, name))
        targetslide_tasks[uid].append(task)
    await safe_reply(update, f"🎯 𝙏𝙖𝙧𝙜𝙚𝙩 𝙎𝙡𝙞𝙙𝙚 𝙡𝙤𝙘𝙠𝙚𝙙 𝙤𝙣 𝙢𝙚𝙨𝙨𝙖𝙜𝙚!", parse_mode="Markdown")

@only_sudo
async def stoptargetslide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message: return await safe_reply(update, "⚠️ 𝙍𝙚𝙥𝙡𝙮 𝙩𝙤 𝙖 𝙢𝙚𝙨𝙨𝙖𝙜𝙚", parse_mode="Markdown")
    uid = update.message.reply_to_message.from_user.id
    if uid in targetslide_tasks:
        for t in targetslide_tasks[uid]: t.cancel()
        del targetslide_tasks[uid]
        await safe_reply(update, "🛑 𝙏𝙖𝙧𝙜𝙚𝙩 𝙎𝙡𝙞𝙙𝙚 𝙡𝙤𝙤𝙥 𝙨𝙩𝙤𝙥𝙥𝙚𝙙.")

@only_sudo
async def slidespam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message: return await safe_reply(update, "⚠️ 𝙍𝙚𝙥𝙡𝙮 𝙩𝙤 𝙖 𝙢𝙚𝙨𝙨𝙖𝙜𝙚", parse_mode="Markdown")
    uid = update.message.reply_to_message.from_user.id
    text = extract_command_text(update.message.text)
    if not text: return await safe_reply(update, "⚠️ 𝙐𝙨𝙖𝙜𝙚: `/slidespam <text>`", parse_mode="Markdown")
    if uid in slidespam_tasks:
        for t in slidespam_tasks[uid]: t.cancel()
    slidespam_tasks[uid] = []
    chat_id = update.message.chat_id
    msg_id = update.message.reply_to_message.message_id
    for bot in bots:
        task = asyncio.create_task(slidespam_worker(bot, chat_id, msg_id, text))
        slidespam_tasks[uid].append(task)
    await safe_reply(update, f"💥 𝙎ْل𝙞𝙙𝙚𝙎𝙥𝙖𝙢 𝙡𝙤𝙘𝙠𝙚𝙙 𝙤𝙣 𝙢𝙚𝙨𝙨𝙖𝙜𝙚!", parse_mode="Markdown")

@only_sudo
async def stopslidespam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message: return await safe_reply(update, "⚠️ 𝙍𝙚𝙥𝙡𝙮 𝙩𝙤 𝙖 𝙢𝙚𝙨𝙨𝙖𝙜𝙚", parse_mode="Markdown")
    uid = update.message.reply_to_message.from_user.id
    if uid in slidespam_tasks:
        for t in slidespam_tasks[uid]: t.cancel()
        del slidespam_tasks[uid]
        await safe_reply(update, "🛑 𝙎ْل𝙞𝙙𝙚𝙎𝙥𝙖𝙢 𝙡𝙤𝙤𝙥 𝙨𝙩𝙤𝙥𝙥𝙚𝙙.")

@only_sudo
async def spm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = extract_command_text(update.message.text)
    chat_id = update.message.chat_id
    if not text: return await safe_reply(update, "⚠️ 𝙐𝙨𝙖𝙜𝙚: `/spm <text>`", parse_mode="Markdown")
    task = asyncio.create_task(spm_loop_sender(context.application.bot, chat_id, text))
    spm_loop_tasks.setdefault(chat_id, []).append(task)
    await safe_reply(update, f"✅ 𝙎𝙋𝙈 𝙡𝙤𝙤𝙥 𝙨𝙩𝙖𝙧𝙩𝙚𝙙.", parse_mode="Markdown")

@only_sudo
async def stopspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in spm_loop_tasks and spm_loop_tasks[chat_id]:
        for t in spm_loop_tasks[chat_id]: t.cancel()
        spm_loop_tasks[chat_id] = []
        await safe_reply(update, "🛑 𝙎𝙋𝙈 𝙡𝙤𝙤𝙥s 𝙨𝙩𝙤𝙥𝙥𝙚𝙙 𝙞𝙣 𝙩𝙝𝙞𝙨 𝙘𝙝𝙖𝙩.")

@only_sudo
async def stopallspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for tasks in spm_loop_tasks.values():
        for t in tasks: t.cancel()
    spm_loop_tasks.clear()
    await safe_reply(update, "🛑 𝘼𝙡𝙡 𝙎𝙋𝙈 𝙡𝙤𝙤𝙥𝙨 𝙨𝙩𝙤𝙥𝙥𝙚𝙙 (𝙜𝙡𝙤𝙗𝙖𝙡𝙡𝙮).")

@only_sudo
async def swipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await safe_reply(update, "⚠️ 𝙐𝙨𝙖𝙜𝙚: `/swipe <name>`", parse_mode="Markdown")
    swipe_mode[update.message.chat_id] = " ".join(context.args)
    await safe_reply(update, f"⚡ 𝙎𝙬𝙞𝙥𝙚 𝙈𝙤𝙙𝙚 𝙊𝙉", parse_mode="Markdown")

@only_sudo
async def stopswipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    swipe_mode.pop(update.message.chat_id, None)
    await safe_reply(update, "🛑 𝙎𝙬𝙞𝙥𝙚 𝙈𝙤𝙙𝙚 𝙨𝙩𝙤𝙥𝙥𝙚𝙙.")

@only_sudo
async def replymafi_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = await get_target_user(update, context)
    if not uid: return await safe_reply(update, "⚠️ 𝙍𝙚𝙥𝙡𝙮 𝙤𝙧 𝙩𝙖𝙜 𝙖 𝙪𝙨𝙚𝙧", parse_mode="Markdown")
    replymafi_targets.add(uid)
    await safe_reply(update, "💬 𝙍𝙚𝙥𝙡𝙮𝙈𝙖𝙛𝙞 𝙚𝙣𝙖𝙗𝙡𝙚𝙙 𝙛𝙤𝙧 𝙩𝙝𝙞𝙨 𝙪𝙨𝙚𝙧.")

@only_sudo
async def stopreplymafi_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = await get_target_user(update, context)
    if not uid: return await safe_reply(update, "⚠️ 𝙍𝙚𝙥𝙡𝙮 𝙤𝙧 𝙩𝙖𝙜 𝙖 𝙪𝙨𝙚𝙧", parse_mode="Markdown")
    replymafi_targets.discard(uid)
    last_mafi_reply.pop(uid, None)
    await safe_reply(update, "🛑 𝙍𝙚𝙥𝙡𝙮𝙈𝙖𝙛𝙞 𝙨𝙩𝙤𝙥𝙥𝙚𝙙 𝙛𝙤𝙧 𝙩𝙝𝙞𝙨 𝙪𝙨𝙚𝙧.")

async def auto_replies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.from_user: return
    chat_id = update.message.chat_id
    uid = update.message.from_user.id
    known_chats.add(chat_id) 
    known_users.add(uid)

    if uid in muted_users:
        try: await update.message.delete()
        except Exception: pass
        return 

    if uid in replymafi_targets and REPLY_MAFI_TEXTS:
        now_ts = time.time()
        bot_id = context.bot.id
        user_bot_cooldowns = last_mafi_reply.setdefault(uid, {})
        
        if now_ts - user_bot_cooldowns.get(bot_id, 0) >= REPLY_MAFI_DELAY:
            user_bot_cooldowns[bot_id] = now_ts + 0.9 
            try: await update.message.reply_text(random.choice(REPLY_MAFI_TEXTS), reply_to_message_id=update.message.message_id)
            except Exception: pass

    if update.message.from_user.is_bot: return

    if chat_id in swipe_mode:
        name_arg = swipe_mode[chat_id]
        template = random.choice(SWIPE_TEXTS)
        try: await update.message.reply_text(template.replace("NAME", name_arg))
        except Exception: pass

@only_sudo
async def getlink_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await safe_reply(update, "⚠️ 𝙐𝙨𝙖𝙜𝙚: `/getlink <chat_id>`", parse_mode="Markdown")
    try:
        chat_id = int(context.args[0])
        chat = await context.bot.get_chat(chat_id)
        link = await context.bot.create_chat_invite_link(chat_id=chat.id)
        await safe_reply(update, f"🩷🫧 𝙄𝙣𝙫𝙞𝙩𝙚 𝙡𝙞𝙣𝙠:\n{link.invite_link}", parse_mode="Markdown")
    except Exception as e:
        await safe_reply(update, f"❌ 𝙀𝙧𝙧𝙤𝙧: {e}")

# mafi keng 
@only_sudo
async def getallactivelinks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not known_chats: return await safe_reply(update, "⚠️ 𝙉𝙤 𝙠𝙣𝙤𝙬𝙣 𝙘𝙝𝙖𝙩𝙨 𝙮𝙚𝙩.")
    unique_msg_id = f"{update.message.chat_id}_{update.message.message_id}"
    if unique_msg_id in global_replied_messages: return
    global_replied_messages.add(unique_msg_id)
    
    try: msg = await update.message.reply_text("⏳ 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙜𝙧𝙤𝙪𝙥𝙨: `0/0...`", parse_mode="Markdown")
    except: msg = None
    
    links = []
    for i, cid in enumerate(list(known_chats), 1):
        if cid > 0: continue 
        try:
            chat = await context.bot.get_chat(cid)
            link = await context.bot.create_chat_invite_link(chat_id=cid)
            links.append(f"• **{chat.title}**: {link.invite_link}")
        except Exception: pass
        if msg and i % 3 == 0:
            try: await msg.edit_text(f"⏳ 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙜𝙧𝙤𝙪𝙥𝙨: `{i}/{len(known_chats)}...`", parse_mode="Markdown")
            except Exception: pass
            
    final_text = "🔗 **𝘼𝙘𝙩𝙞𝙫𝙚 𝙂𝙧𝙤𝙪𝙥 𝙇𝙞𝙣𝙠𝙨:**\n\n" + "\n".join(links) if links else "❌ 𝘾𝙤𝙪𝙡𝙙 𝙣𝙤𝙩 𝙜𝙚𝙣𝙚𝙧𝙖𝙩𝙚 𝙖𝙣𝙮 𝙡𝙞𝙣𝙠𝙨."
    if msg:
        try: await msg.edit_text(final_text, parse_mode="Markdown", disable_web_page_preview=True)
        except Exception:
            await msg.delete()
            for chunk in [final_text[i:i+4000] for i in range(0, len(final_text), 4000)]:
                try: await update.message.reply_text(chunk, parse_mode="Markdown", disable_web_page_preview=True)
                except: pass

def build_app(token):
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("activebots", activebots))
    app.add_handler(CommandHandler("missingbots", missingbots_cmd))
    app.add_handler(CommandHandler("leave", leave_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("ping", ping_cmd))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("o", optimize_cmd))
    app.add_handler(CommandHandler("stopall", stopall_cmd))

    app.add_handler(CommandHandler("gcnc", gcnc))
    app.add_handler(CommandHandler("ncemo", ncemo_cmd))
    app.add_handler(CommandHandler("stopgcnc", stopgcnc))
    app.add_handler(CommandHandler("pyramidnc", pyramidnc_cmd))
    app.add_handler(CommandHandler("stoppyramidnc", stoppyramidnc_cmd))
    app.add_handler(CommandHandler("delaync", delaync_cmd))
    
    app.add_handler(CommandHandler("slidespam", slidespam))
    app.add_handler(CommandHandler("stopslidespam", stopslidespam))
    app.add_handler(CommandHandler("targetslide", targetslide))
    app.add_handler(CommandHandler("stoptargetslide", stoptargetslide))
    app.add_handler(CommandHandler("spm", spm_cmd))
    app.add_handler(CommandHandler("stopspm", stopspm_cmd))
    app.add_handler(CommandHandler("stopallspm", stopallspm_cmd))
    app.add_handler(CommandHandler("delaygcspm", delaygcspm_cmd))
    app.add_handler(CommandHandler("swipe", swipe))
    app.add_handler(CommandHandler("stopswipe", stopswipe))
    app.add_handler(CommandHandler("replymafi", replymafi_cmd))
    app.add_handler(CommandHandler("stopreplymafi", stopreplymafi_cmd))

    app.add_handler(CommandHandler("save", save_cmd))
    app.add_handler(CommandHandler("del", del_cmd))
    app.add_handler(CommandHandler("gsave", gsave_cmd))
    app.add_handler(CommandHandler("gpfp", gpfp_cmd))
    app.add_handler(CommandHandler("pfp", pfp_cmd))
    app.add_handler(CommandHandler("stoppfp", stoppfp_cmd))
    app.add_handler(CommandHandler("delaypfp", delaypfp_cmd))

    app.add_handler(CommandHandler("stickerspm", stickerspm_cmd))
    app.add_handler(CommandHandler("stopstickerspm", stopstickerspm_cmd))
    app.add_handler(CommandHandler("gifspm", gifspm_cmd))
    app.add_handler(CommandHandler("stopgifspm", stopgifspm_cmd))
    app.add_handler(CommandHandler("mediaspm", mediaspm_cmd))
    app.add_handler(CommandHandler("stopmediaspm", stopmediaspm_cmd))
    app.add_handler(CommandHandler("voicespm", voicespm_cmd))
    app.add_handler(CommandHandler("stopvoicespm", stopvoicespm_cmd))

    app.add_handler(CommandHandler("addsudo", addsudo_cmd))
    app.add_handler(CommandHandler("delsudo", delsudo_cmd))
    app.add_handler(CommandHandler("listsudo", listsudo_cmd))
    app.add_handler(CommandHandler("mute", mute_cmd))
    app.add_handler(CommandHandler("unmute", unmute_cmd))
    app.add_handler(CommandHandler("mutelist", mutelist_cmd))

    app.add_handler(CommandHandler("getlink", getlink_cmd))
    app.add_handler(CommandHandler("getallactivelinks", getallactivelinks_cmd))
    app.add_handler(CommandHandler("promote", promote_cmd))
    app.add_handler(CommandHandler("demote", demote_cmd))
    app.add_handler(CommandHandler("promoteallbots", promoteallbots))
    app.add_handler(CommandHandler("promoteall", promoteall))
    
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^tk_"))
    app.add_handler(MessageHandler(filters.ALL, auto_replies), group=1)
    return app


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args):
        pass

def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), _HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

async def self_ping_loop():
    SELF_URL = os.environ.get("SELF_URL")
    if not url:
        return
    while True:
        try:
            urllib.request.urlopen(SELF_URL, timeout=10).read()
        except Exception:
            pass
        await asyncio.sleep(int(os.environ.get("SELF_PING_INTERVAL", "300")))


async def run_all_bots():
    global apps, bots, bot_usernames
    start_health_server()\n    asyncio.create_task(self_ping_loop())\n    print("\n⏳ INITIALIZING...\n")
    for token in TOKENS:
        if token.strip():
            try:
                app = build_app(token)
                apps.append(app)
                bots.append(app.bot)
            except Exception as e: 
                logger.error(f"❌ Failed to build app for a token: {e}")

    for app in apps:
        try:
            await app.initialize()
            me = await app.bot.get_me()
            bot_usernames.append(me.username)
            await app.start() 
            await app.updater.start_polling(drop_pending_updates=True) 
            print(f"✅ CONNECTED SUCCESSFULLY: @{me.username}")
        except Exception as e:
            print(f"❌ Error starting a bot: {e}")

    print("\nMAFI V3 STARTED!\n")
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_all_bots())
    except KeyboardInterrupt:
        print("\n🛑 SHUTTING DOWN MAFIA...")
