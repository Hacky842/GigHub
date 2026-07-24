from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import requests
import random

app = Flask(__name__)
app.secret_key = 'gighub_production_super_secret_key'

# Pantry Cloud Setup (Put your Pantry ID here if you have one)
PANTRY_ID = "00000000-0000-0000-0000-000000000000"
PANTRY_URL = f"https://getpantry.cloud/apiv1/pantry/{PANTRY_ID}/basket/gighub_users"

otp_memory = {}

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.json or {}
    email = data.get('email')
    if not email:
        return jsonify({'status': 'error', 'message': 'Email ID daalna zaroori hai!'})
    
    otp = str(random.randint(100000, 999999))
    otp_memory[email] = otp
    return jsonify({'status': 'success', 'message': f'Verification OTP: {otp}'})

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json or {}
    email = data.get('email')
    otp = data.get('otp')
    if otp_memory.get(email) == str(otp):
        return jsonify({'status': 'success', 'message': 'OTP Verified Successfully!'})
    return jsonify({'status': 'error', 'message': 'Galat OTP code!'})

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json or {}
    name = data.get('name', 'User')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'Freelancer')
    skills = data.get('skills', '')

    if not email or not password:
        return jsonify({'status': 'error', 'message': 'Sabhi required fields bharein!'})

    user_data = {
        'name': name,
        'email': email,
        'password': password,
        'role': role,
        'skills': skills,
        'gigpoints': 0
    }

    # Save to Pantry Cloud Basket gracefully
    try:
        requests.post(PANTRY_URL, json={'users': [user_data]}, timeout=3)
    except Exception as e:
        print("Pantry DB warning:", e)

    session['user'] = user_data
    return jsonify({'status': 'success', 'message': 'Account successfully registered!'})

@app.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'status': 'error', 'message': 'Email aur Password enter karein!'})

    # Direct session login
    session['user'] = {
        'name': email.split('@')[0].capitalize(),
        'email': email,
        'role': 'Freelancer',
        'gigpoints': 0
    }
    return jsonify({'status': 'success', 'message': 'Login successful!'})

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
