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
ADMIN_CHAT_ID = None

def sync_pantry(db):
    try: requests.post(PANTRY_URL, json=db)
    except Exception as e: print(f"Pantry sync error: {e}")

def get_pantry_db():
    try:
        res = requests.get(PANTRY_URL)
        if res.status_code == 200:
            data = res.json()
            if "users" not in data: data["users"] = []
            if "reports" not in data: data["reports"] = []
            return data
    except: pass
    return {"users": [], "reports": []}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json(force=True)
    email = data.get('email')
    mode = data.get('mode')
    
    db = get_pantry_db()
    existing_user = next((u for u in db["users"] if u.get("email") == email), None)

    # Prevent Duplicate Registration with Same Email
    if mode == 'signup' and existing_user:
        return jsonify({"message": "Email already registered! Please switch to Existing Login tab."}), 400

    if mode == 'login' and not existing_user:
        return jsonify({"message": "Email not found. Please register first."}), 400

    otp = str(random.randint(100000, 999999))
    session_data[email] = {"otp": otp, "temp_info": data}

    if RESEND_API_KEY:
        try:
            headers = {"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"}
            html_content = f"""
            <div style="background-color: #020617; padding: 35px 20px; font-family: sans-serif; color: #f8fafc; text-align: center;">
                <div style="max-width: 450px; margin: 0 auto; background: #0f172a; border-radius: 16px; padding: 30px; border: 1px solid #1e293b;">
                    <h1 style="color: #38bdf8; font-size: 20px; font-weight: bold; margin-bottom: 8px; white-space: nowrap;">HackyNetworksStudio</h1>
                    <p style="color: #94a3b8; font-size: 13px;">Security Code Verification</p>
                    <div style="margin: 25px 0; background: #1e293b; padding: 18px; border-radius: 12px; border: 1px dashed #38bdf8;">
                        <span style="font-size: 32px; font-weight: bold; letter-spacing: 6px; color: #38bdf8;">{otp}</span>
                    </div>
                    <p style="font-size: 12px; color: #64748b;">Use this 6-digit code to complete your authorization. Valid for 10 minutes.</p>
                </div>
            </div>
            """
            payload = {
                "from": "HackyNetworksStudio <onboarding@resend.dev>",
                "to": [email],
                "subject": f"[{otp}] HackyNetworksStudio Verification Code",
                "html": html_content
            }
            requests.post("https://api.resend.com/emails", json=payload, headers=headers)
        except Exception as e: print(f"Email Dispatch Failure: {e}")

    return jsonify({"status": "sent"}), 200

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json(force=True)
    email = data.get('email')
    entered_otp = data.get('otp')

    if email in session_data and session_data[email]["otp"] == entered_otp:
        temp = session_data[email]["temp_info"]
        db = get_pantry_db()
        
        user = next((u for u in db["users"] if u.get("email") == email), None)
        if not user:
            user = {
                "name": temp.get("name", "User"),
                "email": email,
                "tg_user": temp.get("tg_user", "@None"),
                "role": temp.get("role", "Freelancer"),
                "skills": temp.get("skills", "N/A"),
                "report_count": 0,
                "status": "active"
            }
            db["users"].append(user)
            sync_pantry(db)

        if ADMIN_CHAT_ID:
            msg = f"🟢 *ACCOUNT AUTHORIZED*\n\n👤 *Name:* {user['name']}\n📧 *Email:* `{user['email']}`\n✈️ *Telegram:* {user['tg_user']}\n🎭 *Role:* {user['role']}\n🛠️ *Skills:* {user['skills']}"
            try: requests.post(TG_URL, json={"chat_id": ADMIN_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
            except: pass

        return jsonify({"status": "verified"}), 200

    return jsonify({"message": "Invalid verification code"}), 400

@app.route('/api/report-user', methods=['POST'])
def report_user():
    data = request.get_json(force=True)
    reporter = data.get('reporter')
    target = data.get('target')
    reason = data.get('reason')

    db = get_pantry_db()
    
    report_entry = {"reporter": reporter, "target": target, "reason": reason}
    db["reports"].append(report_entry)

    target_user = next((u for u in db["users"] if u.get("email") == target or u.get("name") == target), None)
    rep_count = 1
    if target_user:
        target_user["report_count"] = target_user.get("report_count", 0) + 1
        rep_count = target_user["report_count"]
        if rep_count >= 5:
            target_user["status"] = "banned"

    sync_pantry(db)

    if ADMIN_CHAT_ID:
        tg_msg = (
            f"🚨 *DETAILED FRAUD INCIDENT REPORT*\n\n"
            f"🕵️ *Reporter:* `{reporter}`\n"
            f"👤 *Reported Target:* `{target}`\n"
            f"📝 *Incident Explanation:*\n\"{reason}\"\n\n"
            f"📊 *Target Report Score:* {rep_count}/5"
        )
        if rep_count >= 5:
            tg_msg += "\n\n🚫 *AUTOMATIC BAN TRIGGERED (5/5 Strikes Reached)*"
            
        try: requests.post(TG_URL, json={"chat_id": ADMIN_CHAT_ID, "text": tg_msg, "parse_mode": "Markdown"})
        except: pass

    return jsonify({"status": "logged"}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    global ADMIN_CHAT_ID
    data = request.get_json(force=True)
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"]
        ADMIN_CHAT_ID = chat_id

        if text.startswith("/start"):
            payload = {
                "chat_id": chat_id,
                "text": "👋 *HackyNetworksStudio Command Center*\n\nAdmin session initialized.",
                "parse_mode": "Markdown",
                "reply_markup": {
                    "inline_keyboard": [
                        [{"text": "🌐 Open Web App", "web_app": {"url": "https://gighub-hnstudio.vercel.app"}}],
                        [{"text": "💬 Direct Admin Support", "url": "https://t.me/HackyNetworksStudio"}]
                    ]
                }
            }
            requests.post(TG_URL, json=payload)

    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
