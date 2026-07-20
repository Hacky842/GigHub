import os
import requests
from flask import Flask, request

TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

app = Flask(__name__)

@app.route('/')
def home():
    return "GigHub Server is Running Perfectly! 🚀"

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        data = request.get_json(force=True)
        
        # Check if it's a message and contains text
        if "message" in data and "text" in data["message"]:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"]["text"]
            
            # Agar user ne /start bheja
            if text.startswith("/start"):
                reply = "Bhai! GigHub Bot is live. Freelancers and Clients direct connection coming soon! 🔥"
                
                # Simple POST request to Telegram API
                payload = {
                    "chat_id": chat_id,
                    "text": reply
                }
                requests.post(TELEGRAM_API, json=payload)
                
        return "OK", 200
    return "Invalid Method", 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
