import os
import requests
from flask import Flask, request

TOKEN = os.getenv("BOT_TOKEN")
PANTRY_ID = os.getenv("PANTRY_ID")
TG_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
PANTRY_URL = f"https://getpantry.cloud/apiv1/pantry/{PANTRY_ID}/basket/gighub_v1"

app = Flask(__name__)

def sync_pantry(data_to_add):
    # Auto-ping + Save data logic
    try:
        res = requests.get(PANTRY_URL)
        current_data = res.json() if res.status_code == 200 else {"freelancers": []}
        
        # Data size limit check (approx safe zone)
        if len(str(current_data)) > 80000: 
            return False # Future fallback for new basket
            
        current_data["freelancers"].append(data_to_add)
        requests.post(PANTRY_URL, json=current_data)
        return True
    except:
        return False

@app.route('/')
def home():
    # Anti-expiry: manual browser hit pings pantry too
    requests.get(PANTRY_URL)
    return "GigHub Core Engine Online! 🚀"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json(force=True)
    
    # 1. Message Handler
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"]
        
        if text.startswith("/start"):
            # Auto-ping Pantry on every /start to keep it alive forever!
            requests.get(PANTRY_URL)
            
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
            
        elif "Name:" in text and "Skills:" in text:
            # Parse user profile inputs
            lines = text.split("\n")
            profile = {"telegram_id": chat_id}
            for line in lines:
                if ":" in line:
                    k, v = line.split(":", 1)
                    profile[k.strip().lower()] = v.strip()
            
            if sync_pantry(profile):
                msg = "🔥 *Profile Registered Successfully!*\nAapka data Cloud Pantry me save ho gaya hai."
            else:
                msg = "❌ Registration failed. System full or network issue."
                
            requests.post(TG_URL, json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})

    # 2. Button Callback
    elif "callback_query" in data:
        chat_id = data["callback_query"]["message"]["chat"]["id"]
        if data["callback_query"]["data"] == "reg_free":
            payload = {
                "chat_id": chat_id,
                "text": "📝 *Format copy karke detail send karein:*\n\n`Name: Tester`\n`Skills: Dev`\n`Rate: ₹500`",
                "parse_mode": "Markdown"
            }
            requests.post(TG_URL, json=payload)

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
