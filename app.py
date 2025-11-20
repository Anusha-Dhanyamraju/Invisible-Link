from flask import Flask, render_template, request, send_file, jsonify
import os
import time
import stego
import crypto
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Lockout storage: {ip_address: {'attempts': count, 'lockout_until': timestamp}}
lockout_store = {}

def is_locked_out(ip):
    if ip in lockout_store:
        data = lockout_store[ip]
        if time.time() < data.get('lockout_until', 0):
            return True, data['lockout_until'] - time.time()
        # Reset if lockout time passed
        if time.time() > data.get('lockout_until', 0) and data.get('lockout_until', 0) > 0:
             lockout_store[ip] = {'attempts': 0, 'lockout_until': 0}
    return False, 0

def record_failure(ip):
    if ip not in lockout_store:
        lockout_store[ip] = {'attempts': 0, 'lockout_until': 0}
    
    lockout_store[ip]['attempts'] += 1
    
    if lockout_store[ip]['attempts'] >= 3:
        lockout_store[ip]['lockout_until'] = time.time() + 30 # 30 seconds lockout
        return True
    return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/hide', methods=['POST'])
def hide():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    file = request.files['image']
    message = request.form.get('message')
    password = request.form.get('password')
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
        
    filename = secure_filename(file.filename)
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    output_filename = f"hidden_{int(time.time())}.png"
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
    
    file.save(input_path)
    
    try:
        if password:
            message = "ENC:" + crypto.encrypt(message, password)
            
        stego.encode_message(input_path, message, output_path)
        
        # Return URL to download the image
        return jsonify({
            'success': True,
            'image_url': f'/download/{output_filename}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reveal', methods=['POST'])
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
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(input_path)
    
    try:
        hidden_data = stego.decode_message(input_path)
        if not hidden_data:
             return jsonify({'message': 'No hidden message found.'})

        if hidden_data.startswith("ENC:"):
            if not password:
                 return jsonify({'error': 'PASSWORD_REQUIRED'}), 401
            
            try:
                decrypted = crypto.decrypt(hidden_data[4:], password)
                # Success! Reset attempts
                if ip in lockout_store:
                    lockout_store[ip] = {'attempts': 0, 'lockout_until': 0}
                return jsonify({'message': decrypted})
            except:
                # Failed attempt
                is_locked = record_failure(ip)
                if is_locked:
                     return jsonify({'error': 'LOCKED_OUT', 'remaining': 30}), 403
                return jsonify({'error': 'WRONG_PASSWORD'}), 401
        else:
            return jsonify({'message': hidden_data})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['OUTPUT_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
