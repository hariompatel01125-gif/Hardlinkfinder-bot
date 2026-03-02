import os
import random
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from playwright.async_api import async_playwright

# --- CONFIG ---
TOKEN = "8474116765:AAHjjNIeLc4ToxmCGqQU8Kjfl6QCHMu3DNE"
CUSTOM_IPS = ["152.59.57.190", "152.59.63.46", "152.59.61.103", "152.59.59.248", "152.59.63.219"]

logging.basicConfig(level=logging.INFO)

async def deep_trace(url, ip):
    path = [url]
    async with async_playwright() as p:
        # Bypassing the security warning from your video
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        context = await browser.new_context(
            ignore_https_errors=True, #
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            extra_http_headers={"X-Forwarded-For": ip}
        )
        page = await context.new_page()
        page.on("framenavigated", lambda frame: path.append(frame.url) if frame.url not in path else None)
        
        try:
            # Waiting for network idle to catch slow redirects
            await page.goto(url, wait_until="networkidle", timeout=60000)
            if page.url not in path: path.append(page.url)
        except Exception as e:
            logging.error(f"Error: {e}")
        finally:
            await browser.close()
    return list(dict.fromkeys(path))

async def handle_msg(update, context):
    url = update.message.text.strip()
    if not url.startswith("http"): return
    
    ip = random.choice(CUSTOM_IPS)
    m = await update.message.reply_text(f"🔍 Tracing with IP: `{ip}`...")
    
    links = await deep_trace(url, ip)
    res = "✅ **Redirect Chain Found:**\n\n" + "\n\n".join([f"{i}. `{l}`" for i, l in enumerate(links, 1)])
    await m.edit_text(res, parse_mode='Markdown')

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_msg))
    app.run_polling()
