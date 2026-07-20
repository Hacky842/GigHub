import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

TOKEN = os.getenv("BOT_TOKEN")

# Initialize Flask app
flask_app = Flask(__name__)

# Initialize Telegram Application
# We don't use .run_polling() here because Vercel handles requests via Webhook
tg_app = ApplicationBuilder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bhai! GigHub Bot is live. Freelancers and Clients direct connection coming soon! 🔥")

# Add handlers
tg_app.add_handler(CommandHandler("start", start))

# Root route for checking if server is alive
@flask_app.route('/')
def index():
    return "GigHub Server is Running!"

# Webhook route where Telegram will send updates
@flask_app.route(f'/', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), tg_app.bot)
        
        # Run the update through Telegram's asynchronous framework
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(tg_app.process_update(update))
        loop.close()
        
        return "OK", 200

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
