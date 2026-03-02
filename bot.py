import os
import random
import asyncio
import logging
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from playwright.async_api import async_playwright

# --- PORT BINDING FIX FOR RENDER ---
# Ye Render ko "Live" status dikhane mein madad karega
server = Flask(__name__)

@server.route('/')
def home():
    return "Bot is Active and Connected!"

def run_flask():
    # Render environment variable 'PORT' use karta hai
    port = int(os.environ.get('PORT', 8080))
    server.run(host='0.0.0.0', port=port)

# --- BOT CONFIG ---
TOKEN = "8474116765:AAHjjNIeLc4ToxmCGqQU8Kjfl6QCHMu3DNE"
CUSTOM_IPS = ["152.59.57.190", "152.59.63.46", "152.59.61.103", "152.59.59.248", "152.59.63.219"]

logging.basicConfig(level=logging.INFO)

async def deep_trace(url, ip):
    path = [url]
    async with async_playwright() as p:
        # Args bypass security and sandbox issues
        browser = await p.chromium.launch(
            headless=True, 
            args=["--no-sandbox", "--disable-setuid-sandbox", "--ignore-certificate-errors"]
        )
        context = await browser.new_context(
            ignore_https_errors=True, # Bypasses the warning in your video
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            extra_http_headers={"X-Forwarded-For": ip}
        )
        page = await context.new_page()
        
        # Listening for all navigations (Capturing hidden hops)
        page.on("framenavigated", lambda frame: path.append(frame.url) if frame.url not in path else None)
        
        try:
            # We wait longer for JS redirects to execute
            await page.goto(url, wait_until="load", timeout=90000)
            await asyncio.sleep(5) # Give it 5 extra seconds for late JS redirects
            if page.url not in path: path.append(page.url)
        except Exception as e:
            logging.error(f"Trace failed: {e}")
        finally:
            await browser.close()
    
    return list(dict.fromkeys(path))

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith("http"): return
    
    ip = random.choice(CUSTOM_IPS)
    m = await update.message.reply_text(f"🔍 **Deep Scanning...**\n🌐 IP: `{ip}`")
    
    links = await deep_trace(url, ip)
    
    if len(links) <= 1:
        res = "❌ **No redirects found.** Bot might be blocked or link is direct."
    else:
        res = "✅ **Full Redirect Chain Found:**\n\n"
        for i, l in enumerate(links, 1):
            res += f"{i}. `{l}`\n\n"
        
    await m.delete()
    await update.message.reply_text(res, parse_mode='Markdown')

if __name__ == '__main__':
    # Flask ko thread mein start karein taaki Port bind ho jaye
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    # Telegram bot start
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_msg))
    app.run_polling()
    
