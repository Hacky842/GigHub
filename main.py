import os
import requests
from flask import Flask, request

TOKEN = os.getenv("BOT_TOKEN")
PANTRY_ID = os.getenv("PANTRY_ID")
TG_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

app = Flask(__name__)

@app.route('/')
def home():
    return "GigHub Core Engine Online! 🚀"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json(force=True)
    
    # 1. Normal Message Handler (/start)
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"]
        
        if text.startswith("/start"):
            payload = {
                "chat_id": chat_id,
                "text": "💼 *Welcome to GigHub!*\n\nZero Commission. Direct Connection.",
                "parse_mode": "Markdown",
                "reply_markup": {
                    "inline_keyboard": [
                        [{"text": "🙋‍♂️ Freelancer Register", "callback_data": "reg_free"}],
                        [{"text": "🔍 Find Freelancers", "callback_data": "find_free"}]
                    ]
                }
            }
            requests.post(TG_URL, json=payload)

    # 2. Button Click Handler (Callback Query)
    elif "callback_query" in data:
        chat_id = data["callback_query"]["message"]["chat"]["id"]
        click_data = data["callback_query"]["data"]
        
        if click_data == "reg_free":
            # User ko agla step batana
            payload = {
                "chat_id": chat_id,
                "text": "📝 *Registration Start!*\n\nApna profile banane ke liye is format mein reply karein:\n\n`Name: Tera Naam`\n`Skills: Video Editing, Web Dev`\n`Rate: ₹500/hr`\n\n*(Upar wale text ko copy karke apni details bhar ke bhej do)*",
                "parse_mode": "Markdown"
            }
            requests.post(TG_URL, json=payload)

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
