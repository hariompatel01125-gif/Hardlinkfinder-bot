import os
import random
import asyncio
import logging
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from playwright.async_api import async_playwright

# --- 1. RENDER PORT BINDING ---
server = Flask(__name__)
@server.route('/')
def home(): return "Bot is Online!", 200

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server.run(host="0.0.0.0", port=port)

# --- 2. CONFIG ---
TOKEN = "8474116765:AAHjjNIeLc4ToxmCGqQU8Kjfl6QCHMu3DNE"
CUSTOM_IPS = ["152.59.57.190", "152.59.63.46", "152.59.61.103", "152.59.59.248", "152.59.63.219"]
logging.basicConfig(level=logging.INFO)

# --- 3. DEEP TRACE LOGIC WITH FILTER ---
async def deep_trace(url, ip):
    path = []
    async with async_playwright() as p:
        # Browser launch with security bypass
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--ignore-certificate-errors"])
        context = await browser.new_context(
            ignore_https_errors=True, 
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            extra_http_headers={"X-Forwarded-For": ip}
        )
        page = await context.new_page()
        
        # Link Filter: Ye line faltu links ko rokegi
        def is_valid(link):
            bad_words = ['about:blank', 'googletagmanager', 'doubleclick', 'analytics', 'facebook.com/tr/']
            return link.startswith('http') and not any(word in link for word in bad_words)

        page.on("framenavigated", lambda frame: path.append(frame.url) if is_valid(frame.url) and frame.url not in path else None)
        
        try:
            # Load the page and wait for JS
            await page.goto(url, wait_until="load", timeout=60000)
            await asyncio.sleep(4) 
            final = page.url
            if is_valid(final) and final not in path: path.append(final)
        except Exception as e:
            logging.error(f"Error: {e}")
        finally:
            await browser.close()
            
    return path

# --- 4. HANDLERS ---
async def handle_msg(update, context):
    url = update.message.text.strip()
    if not url.startswith("http"): return
    ip = random.choice(CUSTOM_IPS)
    m = await update.message.reply_text(f"🔍 **Deep Scanning...**\n🌐 IP: `{ip}`")
    
    links = await deep_trace(url, ip)
    
    if not links:
        res = "❌ **Could not find any valid redirect path.**"
    else:
        res = "✅ **Clean Redirect Chain Found:**\n\n"
        for i, l in enumerate(links, 1):
            res += f"{i}. `{l}`\n\n"
            
    await m.delete()
    await update.message.reply_text(res, parse_mode='Markdown')

if __name__ == '__main__':
    Thread(target=run_web_server, daemon=True).start()
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_msg))
    application.run_polling()
    
