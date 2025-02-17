from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from markupsafe import Markup
from datetime import datetime
import sqlite3
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from datetime import datetime
import pytz

def get_local_timestamp():
    local_tz = pytz.timezone('Asia/Karachi')
    utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
    local_now = utc_now.astimezone(local_tz)
    return local_now.strftime('%Y-%m-%d %H:%M:%S')

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generates a secure random key

load_dotenv()

ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    with sqlite3.connect('blog.db') as conn:
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, title TEXT, content TEXT, image TEXT, timestamp TEXT)")
        conn.commit()


@app.route('/')
def home():
    admin_logged_in = session.get('admin', False)
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    c.execute("SELECT id, title, content, image, timestamp FROM posts ORDER BY timestamp DESC")
    posts = [(post[0], post[1], Markup(post[2]), post[3], post[4]) for post in c.fetchall()]
    conn.close()
    return render_template('index.html', admin=admin_logged_in, posts=posts, dark_mode=True)

@app.route('/filter', methods=['GET'])
def filter_posts():
    filter_type = request.args.get('filter_type', 'all')
    filter_value = request.args.get('filter_value', '')
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    
    if filter_type == 'year':
        c.execute("SELECT * FROM posts WHERE strftime('%Y', timestamp) = ? ORDER BY timestamp DESC", (filter_value,))
    elif filter_type == 'month':
        c.execute("SELECT * FROM posts WHERE strftime('%Y-%m', timestamp) = ? ORDER BY timestamp DESC", (filter_value,))
    elif filter_type == 'day':
        c.execute("SELECT * FROM posts WHERE strftime('%Y-%m-%d', timestamp) = ? ORDER BY timestamp DESC", (filter_value,))
    else:
        c.execute("SELECT * FROM posts ORDER BY timestamp DESC")
    
    posts = [(post[0], post[1], Markup(post[2]), post[3], post[4]) for post in c.fetchall()]
    conn.close()
    return render_template('index.html', posts=posts, dark_mode=True, admin=('admin' in session))

@app.route('/summary')
def summary():
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    c.execute("SELECT strftime('%Y-%m', timestamp) as month, COUNT(*) FROM posts GROUP BY month ORDER BY month DESC")
    summaries = c.fetchall()
    conn.close()
    return render_template('summary.html', summaries=summaries, dark_mode=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session.permanent = True  # Makes the session last beyond browser close
            session['admin'] = True
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)  # Remove admin session
    return redirect(url_for('home'))

@app.route('/new', methods=['GET', 'POST'])
def new_post():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image = None
        
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                filepath = filepath.replace("\\", "/")  # Ensure correct path formatting
                file.save(filepath) 
                image = filepath
           
        timestamp = get_local_timestamp()
        
        conn = sqlite3.connect('blog.db')
        c = conn.cursor()
        c.execute("INSERT INTO posts (title, content, image, timestamp) VALUES (?, ?, ?, ?)", (title, content, image, timestamp))
        conn.commit()
        conn.close()
        return redirect(url_for('home'))
    
    return render_template('new.html', dark_mode=True)

@app.route('/delete/<int:post_id>')
def delete_post(post_id):
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    c.execute("DELETE FROM posts WHERE id=?", (post_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

@app.route('/check_session')
def check_session():
    return jsonify({"admin": session.get("admin", True)})

@app.route('/set_session', methods=['POST'])
def set_session():
    data = request.json  # Get JSON data from JavaScript
    if data.get("admin") == True:  
        session["admin"] = True  # Set admin session
        return jsonify({"message": "Session updated", "admin": True})
    else:
        session.pop("admin", None)  # Remove admin session
        return jsonify({"message": "Session removed", "admin": False})

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    init_db()
    app.run(port=8080)
