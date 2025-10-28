from datetime import datetime, timedelta
import os
import pytz
import supabase
from dotenv import load_dotenv
from dateutil import parser 
from flask import Flask, redirect, render_template, request, session, url_for, jsonify, make_response, flash 
from markupsafe import Markup
from werkzeug.utils import secure_filename
import hashlib
import uuid
from worker import Worker

def get_local_timestamp():
    local_tz = pytz.timezone('Asia/Karachi')
    utc_now = datetime.now(pytz.utc)
    local_now = utc_now.astimezone(local_tz)
    return local_now.strftime('%Y-%m-%d %H:%M:%S')


app = Flask(__name__)
app.secret_key = os.urandom(24)
app.permanent_session_lifetime = timedelta(days=30)

load_dotenv()

ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
SUPABASE_URL = os.getenv('SUPABASE_URL')
# Prefer a server-side service role key for server operations (bypasses RLS). Fall back to anon key.
SUPABASE_KEY = (
    os.getenv('SUPABASE_SERVICE_ROLE_KEY') or
    os.getenv('SUPERBASE_SERVICE_ROLE_KEY') or
    os.getenv('SUPERBASE_ANON_KEY') or
    os.getenv('SUPABASE_ANON_KEY')
)

if os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPERBASE_SERVICE_ROLE_KEY'):
    print("WARNING: Using Supabase service role key for server operations. Keep this secret and never expose it to browsers.")
BLOG_IMAGES_BUCKET = os.getenv('BLOG_IMAGES_BUCKET') or os.getenv('SUPERBASE_IMAGES_BUCKET_NAME') or 'blog_images'
BLOG_VIDEOS_BUCKET = os.getenv('BLOG_VIDEOS_BUCKET') or os.getenv('SUPERBASE_VIDEOS_BUCKET_NAME') or 'blog_videos'

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Warning: SUPABASE_URL or SUPERBASE_ANON_KEY is not set. Supabase operations will likely fail.")

supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)
worker = Worker(videos_bucket=BLOG_VIDEOS_BUCKET, SUPABASE_KEY=SUPABASE_KEY, SUPABASE_URL=SUPABASE_URL)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'mp4', 'mov', 'avi', 'mkv', 'webm'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

TIMESTAMP_FIELD = None


def resolve_timestamp_field():
    global TIMESTAMP_FIELD
    candidates = ('timestamp', 'created_at', 'published_at', 'posted_at', 'time', 'date', 'ts', 'createdat')
    try:
        resp = supabase_client.table('posts').select('*').limit(1).execute()
        data = resp.data
        if data and isinstance(data, list) and len(data) > 0:
            keys = set(data[0].keys())
            for c in candidates:
                if c in keys:
                    TIMESTAMP_FIELD = c
                    print(f"Using timestamp field: {TIMESTAMP_FIELD}")
                    return TIMESTAMP_FIELD
    except Exception as e:
        print(f"resolve_timestamp_field: probing posts failed: {e}")

    TIMESTAMP_FIELD = 'timestamp'
    print("Falling back to timestamp field: 'timestamp'")
    return TIMESTAMP_FIELD

resolve_timestamp_field()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.before_request
def check_persistent_login():
    if 'admin' in session:
        return

    remember_me_token = request.cookies.get('remember_me')

    if remember_me_token:
        hashed_token = hashlib.sha256(remember_me_token.encode()).hexdigest()
        try:
            # Query Supabase for the persistent login token
            response = supabase_client.table('persistent_logins').select('*').eq('token', hashed_token).execute()
            
            if response.data and len(response.data) > 0:
                login_record = response.data[0]
                expires_at_str = login_record.get('expires_at')
                if expires_at_str:
                    expires_at = datetime.fromisoformat(expires_at_str)
                    current_utc = datetime.now(pytz.utc)
                    if expires_at > current_utc:
                        session['admin'] = True
                        session.permanent = True
                    else:
                        response = make_response(redirect(url_for('home')))
                        response.delete_cookie('remember_me')
                        supabase_client.table('persistent_logins').delete().eq('token', hashed_token).execute()
                        return response
            else:
                response = make_response(redirect(url_for('home')))
                response.delete_cookie('remember_me')
                return response
        except Exception as e:
            print(f"Error checking persistent login: {e}")
            return redirect(url_for('home'))


@app.route('/')
def home():
    admin_logged_in = session.get('admin', False)
    
    # Select fields dynamically based on the resolved TIMESTAMP_FIELD
    
    select_fields = f"id, title, content, image, {TIMESTAMP_FIELD}, video_id" if TIMESTAMP_FIELD else "id, title, content, image, video_id"
    try:
        response = supabase_client.table('posts').select(select_fields).order(TIMESTAMP_FIELD if TIMESTAMP_FIELD else 'id', desc=True).execute()
        posts_data = response.data or []
    except Exception as e:
        print(f"Error fetching posts ordered by {TIMESTAMP_FIELD}: {e}")
        response = supabase_client.table('posts').select('id, title, content, image, video_id').order('id', desc=True).execute()
        posts_data = response.data or []

    posts = []
    for post in posts_data:
        ts_value = post.get(TIMESTAMP_FIELD) if TIMESTAMP_FIELD else None
        if ts_value:
            try:
                dt_object = parser.parse(ts_value).replace(tzinfo=None)
                formatted_timestamp = dt_object.strftime("%Y-%m-%d %I:%M %p")
            except Exception:
                formatted_timestamp = str(ts_value)
        else:
            formatted_timestamp = ''
        
        videodata = None
        video_id = post.get('video_id')
        if video_id:
            try:
                video_resp = supabase_client.table('videos').select('filepath', 'filename', 'status').eq('id', video_id).single().execute()
                video_record = video_resp.data
                if video_record:
                    videodata = {
                        'id': video_id,
                        'filename': video_record.get('filename'),
                        'filepath': video_record.get('filepath'),
                        'status': video_record.get('status'),
                        'url': video_record.get('filepath')
                    }
            except Exception as e:
                print(f"Error fetching video info for video_id={video_id}: {e}")

        
        posts.append((post.get('id'), post.get('title'), Markup(post.get('content', '')), post.get('image'), formatted_timestamp, videodata))
    
    available_years = []
    available_months = []
    available_days = []
    try:
        if TIMESTAMP_FIELD:
            years_response = supabase_client.table('posts').select(TIMESTAMP_FIELD).order(TIMESTAMP_FIELD, desc=True).execute()
            year_vals = [p.get(TIMESTAMP_FIELD) for p in (years_response.data or []) if p.get(TIMESTAMP_FIELD)]
            available_years = sorted(list({parser.parse(v).strftime('%Y') for v in year_vals}), reverse=True)

            months_response = supabase_client.table('posts').select(TIMESTAMP_FIELD).order(TIMESTAMP_FIELD, desc=False).execute()
            month_vals = [p.get(TIMESTAMP_FIELD) for p in (months_response.data or []) if p.get(TIMESTAMP_FIELD)]
            available_months = sorted(list({parser.parse(v).strftime('%m') for v in month_vals}))

            days_response = supabase_client.table('posts').select(TIMESTAMP_FIELD).order(TIMESTAMP_FIELD, desc=False).execute()
            day_vals = [p.get(TIMESTAMP_FIELD) for p in (days_response.data or []) if p.get(TIMESTAMP_FIELD)]
            available_days = sorted(list({parser.parse(v).strftime('%d') for v in day_vals}))
    except Exception as e:
        print(f"Error fetching available years/months/days: {e}")

    return render_template('index.html', admin=admin_logged_in, posts=posts,
                           available_years=available_years,
                           available_months=available_months,
                           available_days=available_days,
                           dark_mode=True)


@app.route('/filter', methods=['GET'])
def filter_posts():
    year = request.args.get('year', 'any')
    month = request.args.get('month', 'any')
    day = request.args.get('day', 'any')

    # Build query using the detected timestamp field. If timestamp isn't available, return all posts.
    select_fields = f"id, title, content, image, {TIMESTAMP_FIELD}" if TIMESTAMP_FIELD else "id, title, content, image"
    if not TIMESTAMP_FIELD:
        response = supabase_client.table('posts').select(select_fields).order('id', desc=True).execute()
        posts_data = response.data or []
    else:
        query = supabase_client.table('posts').select(select_fields)

        if year != 'any':
            query = query.gte(TIMESTAMP_FIELD, f"{year}-01-01T00:00:00Z").lt(TIMESTAMP_FIELD, f"{int(year) + 1}-01-01T00:00:00Z")
        if month != 'any':
            current_year = year if year != 'any' else str(datetime.now().year)
            next_month = int(month) + 1
            next_year = int(current_year)
            if next_month > 12:
                next_month = 1
                next_year += 1
            query = query.gte(TIMESTAMP_FIELD, f"{current_year}-{month.zfill(2)}-01T00:00:00Z").lt(TIMESTAMP_FIELD, f"{next_year}-{str(next_month).zfill(2)}-01T00:00:00Z")
        if day != 'any':
            current_year = year if year != 'any' else str(datetime.now().year)
            current_month = month if month != 'any' else str(datetime.now().month)
            next_day = int(day) + 1
            next_month_for_day = int(current_month)
            next_year_for_day = int(current_year)
            if next_day > 28:
                try:
                    datetime(int(current_year), int(current_month), next_day)
                except ValueError:
                    next_day = 1
                    next_month_for_day += 1
                    if next_month_for_day > 12:
                        next_month_for_day = 1
                        next_year_for_day += 1

            query = query.gte(TIMESTAMP_FIELD, f"{current_year}-{current_month.zfill(2)}-{day.zfill(2)}T00:00:00Z").lt(TIMESTAMP_FIELD, f"{current_year}-{current_month.zfill(2)}-{str(next_day).zfill(2)}T00:00:00Z")


        try:
            response = query.order(TIMESTAMP_FIELD, desc=True).execute()
            posts_data = response.data or []
        except Exception as e:
            print(f"Error executing filtered query on {TIMESTAMP_FIELD}: {e}")
            response = supabase_client.table('posts').select('id, title, content, image').order('id', desc=True).execute()
            posts_data = response.data or []

    posts = []
    for post in posts_data:
        ts_value = post.get(TIMESTAMP_FIELD) if TIMESTAMP_FIELD else None
        if ts_value:
            try:
                dt_object = datetime.strptime(ts_value, "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None)
            except Exception:
                try:
                    dt_object = datetime.strptime(ts_value, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    try:
                        dt_object = parser.parse(ts_value).replace(tzinfo=None)
                    except Exception:
                        dt_object = None
        else:
            dt_object = None

        formatted_ts = dt_object.strftime("%Y-%m-%d %I:%M %p") if dt_object else ''
        posts.append((post.get('id'), post.get('title'), Markup(post.get('content', '')), post.get('image'), formatted_ts))

    available_years = []
    available_months = []
    available_days = []
    try:
        if TIMESTAMP_FIELD:
            yrs_resp = supabase_client.table('posts').select(TIMESTAMP_FIELD).order(TIMESTAMP_FIELD, desc=True).execute()
            available_years = sorted(list({parser.parse(p.get(TIMESTAMP_FIELD)).strftime('%Y') for p in (yrs_resp.data or []) if p.get(TIMESTAMP_FIELD)}), reverse=True)

            mos_resp = supabase_client.table('posts').select(TIMESTAMP_FIELD).order(TIMESTAMP_FIELD, desc=False).execute()
            available_months = sorted(list({parser.parse(p.get(TIMESTAMP_FIELD)).strftime('%m') for p in (mos_resp.data or []) if p.get(TIMESTAMP_FIELD)}))

            d_resp = supabase_client.table('posts').select(TIMESTAMP_FIELD).order(TIMESTAMP_FIELD, desc=False).execute()
            available_days = sorted(list({parser.parse(p.get(TIMESTAMP_FIELD)).strftime('%d') for p in (d_resp.data or []) if p.get(TIMESTAMP_FIELD)}))
    except Exception as e:
        print(f"Error building available_years/months/days (filter route): {e}")

    return render_template('index.html', posts=posts,
                           available_years=available_years,
                           available_months=available_months,
                           available_days=available_days,
                           dark_mode=True, admin=('admin' in session))

@app.route('/login', methods=['GET', 'POST'])
def login():
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            remember = request.form.get('remember')
            session['admin'] = True
            response = make_response(redirect(url_for('home')))

            if remember:
                token = str(uuid.uuid4())
                hashed_token = hashlib.sha256(token.encode()).hexdigest()
                
                expires_at = datetime.now(pytz.utc) + timedelta(days=30)

                try:
                    supabase_client.table('persistent_logins').insert({
                        'user_id': 'admin',
                        'token': hashed_token,
                        'expires_at': expires_at.isoformat()
                    }).execute()
                    response.set_cookie('remember_me', token, max_age=30 * 24 * 60 * 60)
                except Exception as e:
                    print(f"Error setting persistent login: {e}")
                    return response
            return response
        else:
                return render_template('login.html', error='Invalid credentials')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)

    # Delete persistent login token from DB and cookie
    remember_me_token = request.cookies.get('remember_me')

    if remember_me_token:
        hashed_token = hashlib.sha256(remember_me_token.encode()).hexdigest()
        try:
            supabase_client.table('persistent_logins').delete().eq('token', hashed_token).execute()
        except Exception as e:
            print(f"Error deleting persistent login token from DB: {e}")

    response = make_response(redirect(url_for('home')))
    response.delete_cookie('remember_me')
    return response

@app.route('/new', methods=['GET', 'POST'])
def new_post():
    if 'admin' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image_url = None
        video_id = None

        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Read file bytes into memory first to avoid stream/closed-file issues
                try:
                    file_bytes = file.read()
                except Exception as e:
                    print(f"Failed to read uploaded file into memory: {e}")
                    file_bytes = None

                if file_bytes:
                    try:
                        response = supabase_client.storage.from_(BLOG_IMAGES_BUCKET).upload(filename, file_bytes, {"content-type": file.content_type})
                        image_url = f"{SUPABASE_URL}/storage/v1/object/public/{BLOG_IMAGES_BUCKET}/{filename}"
                    except Exception as e:
                        print(f"Error uploading image to Superbase: {e}") 
                        try:
                            if int(e.status) == 409:
                                image_url = f"{SUPABASE_URL}/storage/v1/object/public/{BLOG_IMAGES_BUCKET}/{filename}"
                            else:
                                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                                local_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                                with open(local_path, 'wb') as out_f:
                                    out_f.write(file_bytes)
                                image_url = f"/static/uploads/{filename}"
                                print(f"Saved image locally to {local_path}; using {image_url} as image URL")
                        except Exception as e2:
                            print(f"Failed to save image locally: {e2}")
                            image_url = None
                
        if 'video' in request.files:
            file = request.files['video']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                try:
                    worker_response = worker.save_file(file)
                    video_id = worker_response.get('file_id')
                    if video_id:
                        worker.queue_file(video_id)
                        print(f"Queued video file for processing with video_id={video_id}")
                    else:
                        video_id = None
                        print("Failed to get video_id after saving video file")
                except Exception as e:
                    print(f"Error saving or queuing video file: {e}")


        timestamp = get_local_timestamp()

        try:
            max_attempts = 5
            attempt = 0
            inserted = False
            while attempt < max_attempts and not inserted:
                try:
                    max_resp = supabase_client.table('posts').select('id').order('id', desc=True).limit(1).execute()
                    max_rows = max_resp.data or []
                    current_max = int(max_rows[0].get('id')) if max_rows and max_rows[0].get('id') is not None else 0
                    new_id = current_max + 1

                    supabase_client.table('posts').insert({'id': new_id, 'title': title, 'content': content, 'image': image_url, 'timestamp': timestamp, 'video_id': video_id}).execute()
                    print(f"Inserted post with id={new_id}")
                    inserted = True
                except Exception as e:
                    err_s = str(e)
                    if '23505' in err_s or 'duplicate key' in err_s.lower():
                        attempt += 1
                        print(f"Duplicate id conflict on insert (attempt {attempt}), retrying...")
                        continue
                    else:
                        print(f"Error inserting post into Superbase: {e}")
                        break
            if not inserted:
                print("Failed to insert post after retries; skipping.")
            else:
                flash('Post created successfully!', 'success')
        except Exception as e:
            err_s = str(e)
            if '23505' in err_s or 'duplicate key' in err_s.lower():
                print(f"Duplicate key conflict when inserting post; skipping insert. Details: {e}")
            else:
                print(f"Error inserting post into Superbase: {e}")

        return redirect(url_for('new_post'))

    return render_template('new.html', dark_mode=True)

@app.route('/delete/<int:post_id>')
def delete_post(post_id):
    if 'admin' not in session:
        return redirect(url_for('login'))

    try:
        supabase_client.table('posts').delete().eq('id', post_id).execute()
        flash(f'Post: {post_id} deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting post: {post_id}!', 'error')
        print(f"Error deleting post from Superbase: {e}")

    return redirect(url_for('home'))


@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if 'admin' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        current_image_url = request.form.get('current_image_url')
        image_url = current_image_url
        video_id = request.form.get('current_video_id')

        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                try:
                    file_bytes = file.read()
                except Exception as e:
                    print(f"Failed to read uploaded file into memory: {e}")
                    file_bytes = None

                if file_bytes:
                    try:
                        supabase_client.storage.from_(BLOG_IMAGES_BUCKET).upload(filename, file_bytes, {"content-type": file.content_type})
                        image_url = f"{SUPABASE_URL}/storage/v1/object/public/{BLOG_IMAGES_BUCKET}/{filename}"
                    except Exception as e:
                        print(f"Error uploading new image to Supabase: {e}")
                        if hasattr(e, 'statusCode') and e.statusCode == 409:
                            image_url = f"{SUPABASE_URL}/storage/v1/object/public/{BLOG_IMAGES_BUCKET}/{filename}"
                        else:
                            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                            local_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                            with open(local_path, 'wb') as out_f:
                                out_f.write(file_bytes)
                            image_url = f"/static/uploads/{filename}"
                            print(f"Saved image locally to {local_path}; using {image_url} as image URL")

        if 'video' in request.files:
            file = request.files['video']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                try:
                    worker_response = worker.save_file(file)
                    video_id = worker_response.get('file_id')
                    if video_id:
                        worker.queue_file(video_id)
                    else:
                        print("Failed to get video_id after saving video file")
                except Exception as e:
                    print(f"Error saving or queuing video file: {e}")
        try:
            supabase_client.table('posts').update({'title': title, 'content': content, 'image': image_url, 'video_id': video_id}).eq('id', post_id).execute()
            flash('Post updated successfully!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            print(f"Error updating post in Supabase: {e}")
            flash('Failed to update post.', 'error')
            return render_template('edit.html', post=request.form, error="Failed to update post.", dark_mode=True)

    try:
        select_fields = f"id, title, content, image, {TIMESTAMP_FIELD}, video_id" if TIMESTAMP_FIELD else 'id, title, content, image, video_id'
        response = supabase_client.table('posts').select(select_fields).eq('id', post_id).single().execute()
        post = response.data
        if post:
            if post['video_id']:
                video_id = post['video_id']
                try:
                    video_resp = supabase_client.table('videos').select('filepath', 'filename', 'status').eq('id', video_id).single().execute()
                    video_record = video_resp.data
                    if video_record:
                        videodata = {
                            'id': video_id,
                            'filename': video_record.get('filename'),
                            'filepath': video_record.get('filepath'),
                            'status': video_record.get('status'),
                            'url': video_record.get('filepath')
                        }
                        post['video'] = videodata
                except:
                    print(f"Error fetching video info for video_id={video_id}")

            return render_template('edit.html', post=post, dark_mode=True)
        else:
            flash('Post not found.', 'error')
            return redirect(url_for('home'))
    except Exception as e:
        flash(f'Post not found.', 'error')
        return redirect(url_for('home'))

@app.route('/check_session')
def check_session():
    return jsonify({"admin": session.get("admin", True)})

@app.route('/set_session', methods=['POST'])
def set_session():
    data = request.json
    if data.get("admin") == True:
        session["admin"] = True
        return jsonify({"message": "Session updated", "admin": True})
    else:
        session.pop("admin", None)
        return jsonify({"message": "Session removed", "admin": False})

@app.route('/post/<int:post_id>')
def view_post(post_id):
    select_fields = f"id, title, content, image, {TIMESTAMP_FIELD}, video_id" if TIMESTAMP_FIELD else 'id, title, content, image, video_id'
    response = supabase_client.table('posts').select(select_fields).eq('id', post_id).single().execute()
    post = response.data

    if post:
        ts_val = post.get(TIMESTAMP_FIELD) if TIMESTAMP_FIELD else post.get('timestamp')
        formatted_timestamp = ''
        if ts_val:
            try:
                dt_object = parser.parse(ts_val).replace(tzinfo=None)
                formatted_timestamp = dt_object.strftime("%Y-%m-%d %I:%M %p")
            except Exception:
                formatted_timestamp = str(ts_val)

        image_url = post.get('image')

        videodata = None
        video_id = post.get('video_id')
        if video_id:
            try:
                video_resp = supabase_client.table('videos').select('filepath', 'filename', 'status').eq('id', video_id).single().execute()
                video_record = video_resp.data
                if video_record:
                    videodata = {
                        'id': video_id,
                        'filename': video_record.get('filename'),
                        'filepath': video_record.get('filepath'),
                        'status': video_record.get('status'),
                        'url': f"{SUPABASE_URL}/storage/v1/object/public/{BLOG_VIDEOS_BUCKET}/{video_record.get('filename')}"
                    }
            except Exception as e:
                print(f"Error fetching video info for video_id={video_id}: {e}")

        return render_template('post.html', post={
            "id": post.get('id'),
            "title": post.get('title'),
            "content": Markup(post.get('content', '')),
            "image": image_url,
            "timestamp": formatted_timestamp,
            "video": videodata
        }, dark_mode=True)
    else:
        return "Post not found", 404


@app.route('/admin/inspect')
def admin_inspect():
    if 'admin' not in session:
        return jsonify({'error': 'admin only'}), 403

    # Mask the key for safety in logs/UI
    masked_key = None
    if SUPABASE_KEY:
        sk = SUPABASE_KEY
        masked_key = sk[:4] + '...' + sk[-4:] if len(sk) > 8 else '***'

    info = {
        'supabase_url': SUPABASE_URL,
        'supabase_key_masked': masked_key,
        'images_bucket': BLOG_IMAGES_BUCKET,
    }

    try:
        resp = supabase_client.table('posts').select('id').order('id', desc=True).limit(1).execute()
        max_id = None
        if resp and resp.data and len(resp.data) > 0:
            max_id = resp.data[0].get('id')
        info['max_id_seen_by_app'] = max_id
    except Exception as e:
        info['max_id_error'] = str(e)

    try:
        resp2 = supabase_client.table('posts').select('id').execute()
        info['posts_count_seen_by_app'] = len(resp2.data or [])
    except Exception as e:
        info['posts_count_error'] = str(e)

    return jsonify(info)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return redirect(url_for("/tmp/uploads/" + filename, code=301))

if __name__ == '__main__':
    """
    Main entry point for running the Flask application.
    """
    try:
        port = int(os.getenv('PORT', 8080))
        host = os.getenv('HOST', '127.0.0.1')
        print(f"Starting Flask app on {host}:{port} (debug={app.debug})")
        app.run(host=host, port=port, threaded=True)
    except Exception as e:
        import traceback, sys
        traceback.print_exc()
        print(f"Failed to start Flask app: {e}")
        # Exit with non-zero so container/monitoring sees failure
        sys.exit(1)
