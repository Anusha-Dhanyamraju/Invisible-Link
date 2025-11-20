from flask import Blueprint, render_template, request, send_file, jsonify, current_app
import os
import time
from werkzeug.utils import secure_filename
import stego
import crypto

bp = Blueprint('main', __name__)

# Lockout storage
lockout_store = {}

def is_locked_out(ip):
    if ip in lockout_store:
        data = lockout_store[ip]
        if time.time() < data.get('lockout_until', 0):
            return True, data['lockout_until'] - time.time()
        if time.time() > data.get('lockout_until', 0) and data.get('lockout_until', 0) > 0:
             lockout_store[ip] = {'attempts': 0, 'lockout_until': 0}
    return False, 0

def record_failure(ip):
    if ip not in lockout_store:
        lockout_store[ip] = {'attempts': 0, 'lockout_until': 0}
    lockout_store[ip]['attempts'] += 1
    if lockout_store[ip]['attempts'] >= 3:
        lockout_store[ip]['lockout_until'] = time.time() + 30
        return True
    return False

@bp.route('/')
def home():
    return render_template('home.html')

@bp.route('/tool')
def tool():
    return render_template('tool.html')

@bp.route('/about')
def about():
    return render_template('about.html')

@bp.route('/hide', methods=['POST'])
def hide():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    file = request.files['image']
    message = request.form.get('message')
    password = request.form.get('password')
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
        
    filename = secure_filename(file.filename)
    input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    output_filename = f"hidden_{int(time.time())}.png"
    output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
    
    file.save(input_path)
    
    try:
        if password:
            message = "ENC:" + crypto.encrypt(message, password)
        stego.encode_message(input_path, message, output_path)
        return jsonify({'success': True, 'image_url': f'/download/{output_filename}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/reveal', methods=['POST'])
def reveal():
    ip = request.remote_addr
    locked, remaining = is_locked_out(ip)
    if locked:
        return jsonify({'error': 'LOCKED_OUT', 'remaining': remaining}), 403

    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
        
    file = request.files['image']
    password = request.form.get('password')
    
    filename = secure_filename(file.filename)
    input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    
    try:
        file.save(input_path)
        hidden_data = stego.decode_message(input_path)
        if not hidden_data:
             return jsonify({'message': 'No hidden message found.'})

        if hidden_data.startswith("ENC:"):
            if not password:
                 return jsonify({'error': 'PASSWORD_REQUIRED'}), 401
            try:
                decrypted = crypto.decrypt(hidden_data[4:], password)
                if ip in lockout_store: lockout_store[ip] = {'attempts': 0, 'lockout_until': 0}
                return jsonify({'message': decrypted})
            except Exception as e:
                print(f"Decryption error: {e}") # Log it
                if record_failure(ip): return jsonify({'error': 'LOCKED_OUT', 'remaining': 30}), 403
                return jsonify({'error': 'WRONG_PASSWORD'}), 401
        else:
            return jsonify({'message': hidden_data})
    except Exception as e:
        print(f"Reveal error: {e}") # Log it
        return jsonify({'error': f"Server Error: {str(e)}"}), 500

@bp.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(current_app.config['OUTPUT_FOLDER'], filename), as_attachment=True)
