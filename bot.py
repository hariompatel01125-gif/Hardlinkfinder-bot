import os
import random
import asyncio
import logging
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from playwright.async_api import async_playwright

# --- 1. RENDER PORT BINDING (SABSE PEHLE) ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is alive!", 200

def run_web_server():
    # Render hamesha PORT variable scan karta hai
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- 2. CONFIG ---
TOKEN = "8474116765:AAHjjNIeLc4ToxmCGqQU8Kjfl6QCHMu3DNE"
CUSTOM_IPS = ["152.59.57.190", "152.59.63.46", "152.59.61.103", "152.59.59.248", "152.59.63.219"]
logging.basicConfig(level=logging.INFO)

# --- 3. DEEP TRACE LOGIC ---
async def deep_trace(url, ip):
    path = [url]
    async with async_playwright() as p:
        # Ignore security warnings from your video
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu", "--ignore-certificate-errors"])
        context = await browser.new_context(
            ignore_https_errors=True, 
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            extra_http_headers={"X-Forwarded-For": ip}
        )
        page = await context.new_page()
        page.on("framenavigated", lambda frame: path.append(frame.url) if frame.url not in path else None)
        
        try:
            # Waiting for slow JS redirects
            await page.goto(url, wait_until="load", timeout=60000)
            await asyncio.sleep(5) 
            if page.url not in path: path.append(page.url)
        except Exception as e:
            logging.error(f"Trace Error: {e}")
        finally:
            await browser.close()
    return list(dict.fromkeys(path))

# --- 4. HANDLERS ---
async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith("http"): return
    ip = random.choice(CUSTOM_IPS)
    m = await update.message.reply_text(f"🔍 **Deep Scanning...**\n🌐 IP: `{ip}`")
    links = await deep_trace(url, ip)
    res = "✅ **Redirect Chain Found:**\n\n" + "\n\n".join([f"{i}. `{l}`" for i, l in enumerate(links, 1)])
    await m.delete()
    await update.message.reply_text(res, parse_mode='Markdown')

# --- 5. MAIN EXECUTION ---
if __name__ == '__main__':
    # Start web server in background immediately to satisfy Render's port scan
    daemon = Thread(target=run_web_server, daemon=True)
    daemon.start()
    
    # Start Telegram Bot
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_msg))
    application.run_polling()
    
