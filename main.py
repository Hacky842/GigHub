import os
import random
import requests
from flask import Flask, request, render_template, jsonify

TOKEN = os.getenv("BOT_TOKEN")
PANTRY_ID = os.getenv("PANTRY_ID")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

TG_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
PANTRY_URL = f"https://getpantry.cloud/apiv1/pantry/{PANTRY_ID}/basket/gighub_production_v1"

app = Flask(__name__, template_folder='templates')

session_data = {}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json(force=True)
    email = data.get('email')
    name = data.get('name')
    
    otp = str(random.randint(100000, 999999))
    session_data[email] = {"otp": otp, "user_info": data}
    
    # 1. Dispatch Email via Resend API
    if RESEND_API_KEY:
        try:
            headers = {
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            }
            email_payload = {
                "from": "HackyNetworks <onboarding@resend.dev>",
                "to": [email],
                "subject": "Your Verification Code - HackyNetworks",
                "html": f"<div style='font-family:sans-serif; padding:20px; background:#111827; color:#fff; border-radius:10px;'><h2>Welcome to HackyNetworks!</h2><p>Your 6-digit verification code is:</p><h1 style='color:#38bdf8; letter-spacing:4px;'>{otp}</h1><p>Do not share this code with anyone.</p></div>"
            }
            requests.post("https://api.resend.com/emails", json=email_payload, headers=headers)
        except Exception as e:
            print(f"Resend error: {e}")

    # Backup Alert to Telegram Admin Log
    admin_log = f"📩 *New Signup Verification Code*\n\n👤 *Name:* {name}\n📧 *Email:* `{email}`\n🔑 *Code:* `{otp}`"
    try: requests.post(TG_URL, json={"chat_id": "YOUR_ADMIN_CHAT_ID", "text": admin_log, "parse_mode": "Markdown"})
    except: pass

    return jsonify({"status": "sent"}), 200

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json(force=True)
    entered_otp = data.get('otp')
    
    for email, val in session_data.items():
        if val["otp"] == entered_otp:
            user_info = val["user_info"]
            user_info["verified"] = True
            user_info["reports"] = 0
            
            # Sync to Pantry Cloud Database
            try:
                res = requests.get(PANTRY_URL)
                db = res.json() if res.status_code == 200 else {"freelancers": []}
                db["freelancers"].append(user_info)
                requests.post(PANTRY_URL, json=db)
            except: pass
            
            return jsonify({"status": "verified"}), 200
            
    return jsonify({"status": "invalid"}), 400

@app.route('/api/report-user', methods=['POST'])
def report_user():
    data = request.get_json(force=True)
    target = data.get('target')
    reason = data.get('reason')
    
    # Send Report straight to Admin Telegram
    report_msg = f"🚨 *DETAILED USER REPORT SUBMITTED*\n\n👤 *Reported User:* `{target}`\n📝 *Detailed Incident Explanation:*\n\"{reason}\"\n\n⚠️ *Action:* Check Database to verify report history (5 strikes = Ban)."
    try: requests.post(TG_URL, json={"chat_id": "YOUR_ADMIN_CHAT_ID", "text": report_msg, "parse_mode": "Markdown"})
    except: pass
    
    return jsonify({"status": "reported"}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json(force=True)
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"]
        
        if text.startswith("/start"):
            payload = {
                "chat_id": chat_id,
                "text": "👋 *Welcome to HackyNetworks Portal*\n\nAccess our marketplace platform below to find freelancers or offer your services.",
                "parse_mode": "Markdown",
                "reply_markup": {
                    "inline_keyboard": [
                        [{"text": "🌐 Launch App", "web_app": {"url": "https://gighub-hnstudio.vercel.app"}}],
                        [{"text": "💬 Support", "url": "https://t.me/HackyNetworksStudio"}]
                    ]
                }
            }
            requests.post(TG_URL, json=payload)
            
        elif text.startswith("/help"):
            help_msg = (
                "📖 *HackyNetworks Help & Platform Guide*\n\n"
                "1️⃣ *How to Register:* Open the Web App, enter your email and request a 6-digit verification code.\n"
                "2️⃣ *Reporting Rules:* You can report fraudulent users via the Web App. Reports must contain clear detailed explanations.\n"
                "3️⃣ *5-Strike Policy:* Any account reaching 5 verified reports will be permanently banned from our platform.\n"
                "4️⃣ *Support:* For urgent queries, contact @HackyNetworksStudio directly."
            )
            requests.post(TG_URL, json={"chat_id": chat_id, "text": help_msg, "parse_mode": "Markdown"})

        elif text.startswith("/view_pantry"):
            try:
                res = requests.get(PANTRY_URL)
                db = res.json() if res.status_code == 200 else {"freelancers": []}
                records = db.get("freelancers", [])
                
                if not records:
                    msg = "📂 *Database is empty.*"
                else:
                    msg = "📋 *Master Platform Database:* \n\n"
                    for idx, r in enumerate(records, 1):
                        msg += f"#{idx} | {r.get('name')} ({r.get('role')})\n📧 Mail: `{r.get('email')}`\n💻 Skills: {r.get('skills')}\n-------------------\n"
                
                requests.post(TG_URL, json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
            except:
                requests.post(TG_URL, json={"chat_id": chat_id, "text": "❌ Cloud connection failed."})

    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
