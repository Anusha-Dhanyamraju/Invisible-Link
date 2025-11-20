from flask import Flask
import os

def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['OUTPUT_FOLDER'] = 'outputs'
    app.secret_key = 'super_secret_key_for_session' # Needed for flash messages if we use them
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

    from . import routes
    app.register_blueprint(routes.bp)

    return app
