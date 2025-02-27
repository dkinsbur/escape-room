from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import uuid
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///escape_room.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SECRET_KEY'] = str(uuid.uuid4())
db = SQLAlchemy(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database models
class Lock(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    num_digits = db.Column(db.Integer, nullable=False)
    digit_color = db.Column(db.String(20), default='black')
    correct_code = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    image_path = db.Column(db.String(200))
    video_path = db.Column(db.String(200))
    success_text = db.Column(db.Text)
    success_media_path = db.Column(db.String(200))
    success_sound = db.Column(db.String(200), default='static/sounds/success.mp3')
    error_sound = db.Column(db.String(200), default='static/sounds/error.mp3')
    digit_sound = db.Column(db.String(200), default='static/sounds/click.wav')

# Initialize database
with app.app_context():
    db.create_all()

# Admin routes
@app.route('/')
def admin_panel():
    locks = Lock.query.all()
    return render_template('admin.html', locks=locks)

@app.route('/create_lock', methods=['GET', 'POST'])
def create_lock():
    if request.method == 'POST':
        lock_id = str(uuid.uuid4())
        title = request.form.get('title')
        num_digits = int(request.form.get('num_digits'))
        digit_color = request.form.get('digit_color')
        correct_code = request.form.get('correct_code')
        success_text = request.form.get('success_text')
        
        # Handle file uploads
        image_path = None
        if 'image' in request.files and request.files['image'].filename:
            image = request.files['image']
            image_filename = secure_filename(f"{lock_id}_{image.filename}")
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
            image_path = f"uploads/{image_filename}"
        
        video_path = None
        if 'video' in request.files and request.files['video'].filename:
            video = request.files['video']
            video_filename = secure_filename(f"{lock_id}_{video.filename}")
            video.save(os.path.join(app.config['UPLOAD_FOLDER'], video_filename))
            video_path = f"uploads/{video_filename}"
            
        success_media_path = None
        if 'success_media' in request.files and request.files['success_media'].filename:
            success_media = request.files['success_media']
            success_filename = secure_filename(f"{lock_id}_success_{success_media.filename}")
            success_media.save(os.path.join(app.config['UPLOAD_FOLDER'], success_filename))
            success_media_path = f"uploads/{success_filename}"
            
        # Custom sounds
        success_sound = 'static/sounds/success.mp3'
        if 'success_sound' in request.files and request.files['success_sound'].filename:
            sound = request.files['success_sound']
            sound_filename = secure_filename(f"{lock_id}_success_sound_{sound.filename}")
            sound.save(os.path.join(app.config['UPLOAD_FOLDER'], sound_filename))
            success_sound = f"uploads/{sound_filename}"
            
        error_sound = 'static/sounds/error.mp3'
        if 'error_sound' in request.files and request.files['error_sound'].filename:
            sound = request.files['error_sound']
            sound_filename = secure_filename(f"{lock_id}_error_sound_{sound.filename}")
            sound.save(os.path.join(app.config['UPLOAD_FOLDER'], sound_filename))
            error_sound = f"uploads/{sound_filename}"
            
        digit_sound = 'static/sounds/click.wav'
        if 'digit_sound' in request.files and request.files['digit_sound'].filename:
            sound = request.files['digit_sound']
            sound_filename = secure_filename(f"{lock_id}_digit_sound_{sound.filename}")
            sound.save(os.path.join(app.config['UPLOAD_FOLDER'], sound_filename))
            digit_sound = f"uploads/{sound_filename}"
        
        # Create new lock
        new_lock = Lock(
            id=lock_id,
            title=title,
            num_digits=num_digits,
            digit_color=digit_color,
            correct_code=correct_code,
            image_path=image_path,
            video_path=video_path,
            success_text=success_text,
            success_media_path=success_media_path,
            success_sound=success_sound,
            error_sound=error_sound,
            digit_sound=digit_sound
        )
        db.session.add(new_lock)
        db.session.commit()
        
        return redirect(url_for('admin_panel'))
    
    return render_template('create_lock.html')

@app.route('/edit_lock/<lock_id>', methods=['GET', 'POST'])
def edit_lock(lock_id):
    lock = Lock.query.get_or_404(lock_id)
    
    if request.method == 'POST':
        lock.title = request.form.get('title')
        lock.num_digits = int(request.form.get('num_digits'))
        lock.digit_color = request.form.get('digit_color')
        lock.correct_code = request.form.get('correct_code')
        lock.success_text = request.form.get('success_text')
        
        # Handle file uploads - same as create but only update if a new file is provided
        if 'image' in request.files and request.files['image'].filename:
            image = request.files['image']
            image_filename = secure_filename(f"{lock_id}_{image.filename}")
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
            lock.image_path = f"uploads/{image_filename}"
        
        # Similar handling for other file uploads
        # ...
        
        db.session.commit()
        return redirect(url_for('admin_panel'))
    
    return render_template('edit_lock.html', lock=lock)

@app.route('/delete_lock/<lock_id>', methods=['POST'])
def delete_lock(lock_id):
    lock = Lock.query.get_or_404(lock_id)
    db.session.delete(lock)
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/qr_code/<lock_id>')
def qr_code(lock_id):
    lock = Lock.query.get_or_404(lock_id)
    lock_url = request.host_url + 'lock/' + lock_id
    return render_template('qr_code.html', lock=lock, lock_url=lock_url)

# Player routes
@app.route('/lock/<lock_id>')
def show_lock(lock_id):
    lock = Lock.query.get_or_404(lock_id)
    return render_template('lock.html', lock=lock)

@app.route('/check_code/<lock_id>', methods=['POST'])
def check_code(lock_id):
    lock = Lock.query.get_or_404(lock_id)
    submitted_code = request.form.get('code')
    
    if submitted_code == lock.correct_code:
        return jsonify({
            'success': True,
            'redirect': url_for('success', lock_id=lock_id),
            'sound': lock.success_sound
        })
    else:
        return jsonify({
            'success': False,
            'sound': lock.error_sound
        })

@app.route('/success/<lock_id>')
def success(lock_id):
    lock = Lock.query.get_or_404(lock_id)
    return render_template('success.html', lock=lock)

if __name__ == '__main__':
    # Run the app on 0.0.0.0 to make it accessible from other devices on the network
    app.run(host='0.0.0.0', port=5000, debug=True)