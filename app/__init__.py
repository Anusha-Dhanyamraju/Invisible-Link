from flask import Flask
import os

def create_app():
    app = Flask(__name__)
    basedir = os.path.abspath(os.path.dirname(__file__))
    # Go up one level from 'app' package to project root
    project_root = os.path.dirname(basedir)
    
    app.config['UPLOAD_FOLDER'] = os.path.join(project_root, 'uploads')
    app.config['OUTPUT_FOLDER'] = os.path.join(project_root, 'outputs')
    app.secret_key = 'super_secret_key_for_session' 
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

    from . import routes
    app.register_blueprint(routes.bp)

    return app
