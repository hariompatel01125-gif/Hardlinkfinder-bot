import os
import random
import asyncio
import logging
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from playwright.async_api import async_playwright

# --- RENDER WEB SERVICE PORT BINDING ---
# Ye Render ke "Port scan timeout" error ko fix karega
server = Flask(__name__)

@server.route('/')
def home():
    return "Bot is Running 24/7!"

def run_flask():
    # Render hamesha PORT environment variable check karta hai
    port = int(os.environ.get('PORT', 8080))
    server.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# --- BOT CONFIG ---
TOKEN = "8474116765:AAHjjNIeLc4ToxmCGqQU8Kjfl6QCHMu3DNE"
CUSTOM_IPS = ["152.59.57.190", "152.59.63.46", "152.59.61.103", "152.59.59.248", "152.59.63.219"]

logging.basicConfig(level=logging.INFO)

# --- DEEP TRACE LOGIC ---
async def deep_trace(url, ip):
    path = [url]
    async with async_playwright() as p:
        # ignore-certificate-errors video wale security warning ko bypass karta hai
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox", "--ignore-certificate-errors"])
        context = await browser.new_context(
            ignore_https_errors=True, # Video security certificate fix
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            extra_http_headers={"X-Forwarded-For": ip}
        )
        page = await context.new_page()
        
        # Recording every redirect hop
        page.on("framenavigated", lambda frame: path.append(frame.url) if frame.url not in path else None)
        
        try:
            # networkidle slow redirects ke liye wait karta hai
            await page.goto(url, wait_until="networkidle", timeout=60000)
            if page.url not in path: path.append(page.url)
        except Exception as e:
            logging.error(f"Trace Error: {e}")
        finally:
            await browser.close()
    return list(dict.fromkeys(path))

# --- TELEGRAM HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 **Hard Link Finder Pro Live!**\n\nAb main complex redirects aur security warnings bypass kar sakta hoon.")

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith("http"): return
    
    ip = random.choice(CUSTOM_IPS)
    m = await update.message.reply_text(f"🔍 **Deep Scanning...**\n🌐 IP: `{ip}`")
    
    try:
        links = await deep_trace(url, ip)
        res = "✅ **Redirect Chain Found:**\n\n"
        for i, l in enumerate(links, 1):
            res += f"{i}. `{l}`\n\n"
        await m.delete()
        await update.message.reply_text(res, parse_mode='Markdown')
    except Exception as e:
        await m.edit_text(f"❌ Error: {str(e)}")

if __name__ == '__main__':
    keep_alive() # Render port binding fix
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_msg))
    app.run_polling()
    
