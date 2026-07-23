from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = 'gighub_super_secret_key'

# Database Initialization
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            skills TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    skills = data.get('skills', '') if role == 'Freelancer' else ''

    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (name, email, password, role, skills) VALUES (?, ?, ?, ?, ?)',
                       (name, email, password, role, skills))
        conn.commit()
        conn.close()
        session['user'] = {'name': name, 'email': email, 'role': role}
        return jsonify({'status': 'success', 'message': 'Account created successfully!', 'role': role})
    except sqlite3.IntegrityError:
        return jsonify({'status': 'error', 'message': 'Email already registered!'})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, role FROM users WHERE email = ? AND password = ?', (email, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['user'] = {'name': user[0], 'email': email, 'role': user[1]}
        return jsonify({'status': 'success', 'message': 'Login successful!', 'role': user[1]})
    else:
        return jsonify({'status': 'error', 'message': 'Invalid Email or Password!'})

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('home'))
    user = session['user']
    return f'''
    <body style="background:#030f26; color:#fff; font-family:sans-serif; text-align:center; padding-top:100px;">
        <h1>Welcome, {user['name']}! 🎉</h1>
        <p style="color:#94a3b8;">Logged in as: <strong>{user['role']}</strong></p>
        <p style="margin-top:20px;"><a href="/logout" style="color:#ef4444; text-decoration:none; font-weight:bold;">Logout</a></p>
    </body>
    '''

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
