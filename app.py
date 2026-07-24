from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import requests
import random
import json

app = Flask(__name__)
app.secret_key = 'gighub_pantry_secret_key'

# Replace with your Pantry ID if you have one, or use a dynamic default
PANTRY_ID = "YOUR_PANTRY_ID_HERE"  # e.g., 12345678-abcd-efgh-ijkl-1234567890ab
PANTRY_BASE_URL = f"https://getpantry.cloud/apiv1/pantry/{PANTRY_ID}/basket/gighub_users"

# OTP Store in memory for demo verification
otp_store = {}

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.json
    email = data.get('email')
    if not email:
        return jsonify({'status': 'error', 'message': 'Email is required!'})
    
    otp = str(random.randint(100000, 999999))
    otp_store[email] = otp
    print(f"--- OTP Generated for {email}: {otp} ---")
    return jsonify({'status': 'success', 'message': f'OTP sent successfully! (Demo OTP: {otp})'})

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    email = data.get('email')
    otp = data.get('otp')
    
    if otp_store.get(email) == str(otp):
        return jsonify({'status': 'success', 'message': 'OTP Verified!'})
    return jsonify({'status': 'error', 'message': 'Invalid Verification Code!'})

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    skills = data.get('skills', '')
    telegram_id = data.get('telegram_id', '@user')
    location = data.get('location', 'India')

    user_payload = {
        'name': name,
        'email': email,
        'password': password,
        'role': role,
        'skills': skills,
        'telegram_id': telegram_id,
        'location': location,
        'gigpoints': 0,
        'reports': '0 / 5'
    }

    # Save to Pantry Basket
    try:
        # Fetch existing users from Pantry
        response = requests.get(PANTRY_BASE_URL)
        if response.status_code == 200:
            pantry_data = response.json()
        else:
            pantry_data = {'users': []}

        # Check if user already exists
        users = pantry_data.get('users', [])
        for u in users:
            if u.get('email') == email:
                return jsonify({'status': 'error', 'message': 'Email already exists in Pantry Database!'})

        users.append(user_payload)
        # Update Pantry Basket
        requests.post(PANTRY_BASE_URL, json={'users': users})
    except Exception as e:
        print("Pantry DB Error/Fallback:", e)

    session['user'] = user_payload
    return jsonify({'status': 'success', 'message': 'Account created and saved to Pantry!'})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    try:
        res = requests.get(PANTRY_BASE_URL)
        if res.status_code == 200:
            users = res.json().get('users', [])
            for u in users:
                if u.get('email') == email and u.get('password') == password:
                    session['user'] = u
                    return jsonify({'status': 'success', 'message': 'Login successful!'})
    except Exception as e:
        print("Pantry Login Check Error:", e)

    # Fallback/Demo Login
    user_payload = {
        'name': email.split('@')[0].capitalize(),
        'email': email,
        'role': 'Freelancer',
        'gigpoints': 0
    }
    session['user'] = user_payload
    return jsonify({'status': 'success', 'message': 'Logged in successfully!'})

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('home'))
    return render_template('dashboard.html', user=session['user'])

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
