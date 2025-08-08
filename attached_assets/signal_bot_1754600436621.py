from telethon import TelegramClient, events
import re

# ----------- تنظیمات API و کانال‌ها -----------
api_id = 29278288
api_hash = '8baff9421321d1ef6f14b0511209fbe2'
session_name = 'signal_bot'

from_channels = [1467736193, 2123816390, 1286609636]  # آیدی عددی کانال‌ها
to_channel = 'sjkalalsk'  # یوزرنیم یا آی‌دی کانال مقصد

# ----------- اتصال به تلگرام -----------
client = TelegramClient(session_name, api_id, api_hash)

# ----------- تابع تشخیص و فرمت سیگنال -----------
def parse_signal(message):
    text = message.message
    
    # بررسی وجود کلمات کلیدی پایه‌ای
    if not any(k in text.lower() for k in ["entry", "tp", "sl"]):
        return None

    lines = text.strip().splitlines()
    
    symbol = ""
    position = ""
    entry = ""
    sl = ""
    r_r = ""
    tps = []

    for line in lines:
        l = line.strip()

        # نماد (symbol)
        if "#" in l or re.match(r"^[A-Z]{3,6}/?[A-Z]*$", l):
            symbol = l.replace("#", "").strip().upper()

        # نوع پوزیشن
        if any(pos in l.upper() for pos in ["BUY", "SELL"]):
            position = l.title()

        # Entry
        if "entry" in l.lower():
            entry_match = re.search(r"[\d.]+", l)
            if entry_match:
                entry = entry_match.group()

        # Stop Loss
        if "sl" in l.lower():
            sl_match = re.search(r"[\d.]+", l)
            if sl_match:
                sl = sl_match.group()

        # Risk/Reward
        if "risk" in l.lower() and "/" in l:
            r_r = l.split(":")[-1].strip()
        elif "risk" in l.lower() and re.search(r"\d+\s*:\s*\d+", l):
            r_r = re.search(r"\d+\s*:\s*\d+", l).group()

        # Take Profits
        if "tp" in l.lower():
            tp_match = re.search(r"[\d.]+", l)
            if tp_match:
                tps.append(tp_match.group())

    if not (symbol and position and entry and sl and tps):
        return None  # سیگنال ناقص است

    # ساخت پیام نهایی
    signal_text = f"📊 #{symbol}\n"
    signal_text += f"📉 Position: {position}\n"
    if r_r and message.chat_id != 1286609636:
        signal_text += f"❗️ R/R : {r_r}\n"
    signal_text += f"💲 Entry Price : {entry}\n"
    for idx, tp in enumerate(tps):
        signal_text += f"✔️ TP{idx+1} : {tp}\n"
    signal_text += f"🚫 Stop Loss : {sl}"

    return signal_text

# ----------- مانیتورینگ پیام‌ها -----------
@client.on(events.NewMessage(chats=from_channels))
async def handler(event):
    signal = parse_signal(event.message)
    if signal:
        await client.send_message(to_channel, signal)

# ----------- شروع ربات -----------
print("[+] Bot is running... Press Ctrl+C to stop.")
client.start()
client.run_until_disconnected()


import asyncio
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is running"

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()
