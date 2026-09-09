"""
TeleLearn AI – Flask Application Entry Point
Run: python app.py
"""

import os
import sys

# Ensure project root is on the path so imports work from any directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, redirect, url_for
from config import Config
from database.db_init import init_db

# ── Blueprint imports ─────────────────────────────
from routes.auth      import auth_bp
from routes.dashboard import dashboard_bp
from routes.chatbot   import chatbot_bp
from routes.topics    import topics_bp
from routes.materials import materials_bp
from routes.quiz      import quiz_bp
from routes.profile   import profile_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
    app.secret_key = Config.SECRET_KEY

    # ── Ensure directories exist ──────────────────
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)

    # ── Init database ─────────────────────────────
    init_db()

    # ── Register blueprints ───────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(topics_bp)
    app.register_blueprint(materials_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(profile_bp)

    # ── Landing page / root route ─────────────────
    from flask import Blueprint, session
    main_bp = Blueprint('main', __name__)

    @main_bp.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('dashboard.index'))
        return render_template('index.html')

    app.register_blueprint(main_bp)

    # ── Global error handlers ─────────────────────
    @app.errorhandler(404)
    def not_found(e):
        from flask import request
        if request.path.startswith('/api') or request.is_json:
            from flask import jsonify
            return jsonify({'error': 'Not found'}), 404
        return render_template('base.html'), 404

    @app.errorhandler(413)
    def file_too_large(e):
        from flask import jsonify
        return jsonify({'error': 'File too large. Maximum size is 16 MB.'}), 413

    @app.errorhandler(500)
    def server_error(e):
        from flask import jsonify, request
        if request.is_json:
            return jsonify({'error': 'An internal server error occurred.'}), 500
        return render_template('base.html'), 500

    # ── Jinja2 globals ────────────────────────────
    @app.template_filter('filesizeformat')
    def filesizeformat(value):
        try:
            v = int(value)
            if v < 1024: return f"{v} B"
            elif v < 1024**2: return f"{v/1024:.1f} KB"
            else: return f"{v/1024**2:.1f} MB"
        except Exception:
            return str(value)

    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    debug = Config.DEBUG
    print(f"""
╔══════════════════════════════════════════════════╗
║          TeleLearn AI – Starting Up              ║
╠══════════════════════════════════════════════════╣
║  URL:   http://127.0.0.1:{port:<5}                   ║
║  Debug: {str(debug):<43} ║
╚══════════════════════════════════════════════════╝

📡 Database initialized
🤖 Groq AI service ready (set GROQ_API_KEY in .env)
📚 RAG knowledge base ready
""")
    app.run(debug=debug, host='0.0.0.0', port=port)
