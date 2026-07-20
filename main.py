import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler

TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)

# Basic landing page taaki browser mein check kar sakein zinda hai ya nahi
@app.route('/')
def home():
    return "GigHub Server is Running Perfectly! 🚀"

# Alag routing banate hain sirf telegram messages ke liye
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        try:
            # initialize application locally inside function to prevent loop issues
            tg_app = ApplicationBuilder().token(TOKEN).build()
            
            # Register your handlers here
            async def start(update, context):
                await update.message.reply_text("Bhai! GigHub Bot is live. Freelancers and Clients direct connection coming soon! 🔥")
                
            tg_app.add_handler(CommandHandler("start", start))
            
            # Process incoming update
            update = Update.de_json(request.get_json(force=True), tg_app.bot)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(tg_app.process_update(update))
            loop.close()
            
            return "OK", 200
        except Exception as e:
            print(f"Error handling webhook: {e}")
            return "Error", 500
    return "Invalid Method", 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
