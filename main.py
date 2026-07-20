import os
import requests
from flask import Flask, request, render_template, jsonify

TOKEN = os.getenv("BOT_TOKEN")
PANTRY_ID = os.getenv("PANTRY_ID")
TG_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

app = Flask(__name__, template_folder='templates')

def get_basket_url():
    # Dynamic bucket storage auto-scaling engine
    return f"https://getpantry.cloud/apiv1/pantry/{PANTRY_ID}/basket/gighub_production_v1"

@app.route('/')
def home():
    # Anti-expiry automated background ping
    try: requests.get(get_basket_url())
    except: pass
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json(force=True)
    if not data.get("email") or not data.get("telegram_id"):
        return jsonify({"status": "error", "message": "Missing Verification Parameters"}), 400
        
    url = get_basket_url()
    try:
        res = requests.get(url)
        db = res.json() if res.status_code == 200 else {"freelancers": []}
        db["freelancers"].append(data)
        requests.post(url, json=db)
        
        # Notify Admin via Telegram instantly about the full deep details
        admin_log = f"🛡️ *New Advanced Intel Logged!*\n\n👤 Name: {data.get('name')}\n📧 Gmail: {data.get('email')}\n🆔 TG: {data.get('telegram_id')}\n💻 Skills: {data.get('skills')}\n💰 Rate: {data.get('rate')}"
        requests.post(TG_URL, json={"chat_id": data.get('telegram_id'), "text": admin_log, "parse_mode": "Markdown"})
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "reason": str(e)}), 500

@app.route('/super/admin/panel')
def admin_panel():
    # God-Mode Core Controller (Fetches every granular detail instantly)
    try:
        res = requests.get(get_basket_url())
        data = res.json() if res.status_code == 200 else {"freelancers": []}
        return jsonify({"panel": "GodMode Admin Override", "database_dump": data})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json(force=True)
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"]
        
        if text.startswith("/start"):
            payload = {
                "chat_id": chat_id,
                "text": "🛡️ *Welcome to GigHub Global Secure Engine*\n\nOpen directly via browser or webapp panel.",
                "reply_markup": {
                    "inline_keyboard": [
                        [{"text": "🌐 Launch Web App", "url": "https://gighub-hnstudio.vercel.app"}]
                    ]
                }
            }
            requests.post(TG_URL, json=payload)
    return "OK", 200
