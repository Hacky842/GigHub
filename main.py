import os
import requests
from flask import Flask, request, render_template, jsonify

TOKEN = os.getenv("BOT_TOKEN")
PANTRY_ID = os.getenv("PANTRY_ID")
TG_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
PANTRY_URL = f"https://getpantry.cloud/apiv1/pantry/{PANTRY_ID}/basket/gighub_production_v1"

app = Flask(__name__, template_folder='templates')

@app.route('/')
def home():
    try: requests.get(PANTRY_URL)
    except: pass
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json(force=True)
    try:
        res = requests.get(PANTRY_URL)
        db = res.json() if res.status_code == 200 else {"freelancers": []}
        db["freelancers"].append(data)
        requests.post(PANTRY_URL, json=db)
        
        # Immediate Intel Broadcast Notification
        admin_log = f"🛡️ *HackyNetworks Data Update!*\n\n👤 Name: {data.get('name')}\n📧 Gmail: {data.get('email')}\n🆔 TG: {data.get('telegram_id')}\n💻 Skills: {data.get('skills')}\n💰 Rate: {data.get('rate')}"
        requests.post(TG_URL, json={"chat_id": data.get('telegram_id'), "text": admin_log, "parse_mode": "Markdown"})
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "reason": str(e)}), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json(force=True)
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"]
        
        if text.startswith("/start"):
            payload = {
                "chat_id": chat_id,
                "text": "🛡️ *HackyNetworksStudio Core Engaged.*\n\nLaunch the integrated modular layout below.",
                "parse_mode": "Markdown",
                "reply_markup": {
                    "inline_keyboard": [
                        [{"text": "🌐 Launch Identity App", "web_app": {"url": "https://gighub-hnstudio.vercel.app"}}],
                        [{"text": "👑 Owner Connection", "url": "https://t.me/HackyNetworksStudio"}]
                    ]
                }
            }
            requests.post(TG_URL, json=payload)
            
        elif text.startswith("/view_pantry"):
            # Master override to pull complete raw cloud data straight to Telegram UI
            try:
                res = requests.get(PANTRY_URL)
                db = res.json() if res.status_code == 200 else {"freelancers": []}
                freelancers = db.get("freelancers", [])
                
                if not freelancers:
                    msg = "📂 *Cloud Database is empty.*"
                else:
                    msg = "📡 *HackyNetworks Master Database Dump:*\n\n"
                    for idx, f in enumerate(freelancers, 1):
                        msg += f"📦 *Record #{idx}*\n"
                        msg += f"👤 *Name:* {f.get('name')}\n"
                        msg += f"📧 *Gmail:* {f.get('email')}\n"
                        msg += f"🆔 *ChatID:* {f.get('telegram_id')}\n"
                        msg += f"💻 *Skills:* {f.get('skills')}\n"
                        msg += f"💰 *Rate:* {f.get('rate')}\n"
                        msg += "-------------------------\n"
                
                requests.post(TG_URL, json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
            except:
                requests.post(TG_URL, json={"chat_id": chat_id, "text": "❌ Cloud database sync timeout."})
                
    return "OK", 200
