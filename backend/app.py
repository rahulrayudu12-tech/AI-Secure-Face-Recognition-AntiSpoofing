import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from backend.config import Config, BASE_DIR, UPLOAD_DIR
from backend.database.db import init_db, db_session
from backend.models.database_models import User
from backend.security.crypto import hash_password
from backend.routes.auth_routes import auth_bp
from backend.routes.user_routes import user_bp
from backend.routes.logs_routes import logs_bp
from backend.routes.dashboard_routes import dashboard_bp

def seed_default_users():
    """Seed default administrator and demo user for instant testing."""
    admin_email = "admin@auraid.cyber"
    if not db_session.query(User).filter_by(email=admin_email).first():
        admin = User(
            name="Security Administrator",
            email=admin_email,
            password_hash=hash_password("Admin@12345"),
            role="admin"
        )
        demo_user = User(
            name="Sarah Connor",
            email="demo@auraid.cyber",
            password_hash=hash_password("Demo@12345"),
            role="user"
        )
        db_session.add(admin)
        db_session.add(demo_user)
        db_session.commit()
        print("[INFO] Seeded default admin (admin@auraid.cyber) and demo user (demo@auraid.cyber).")

def create_app():
    app = Flask(__name__, static_folder=str(BASE_DIR / "frontend"))
    app.config.from_object(Config)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialize Database & Seed
    init_db()
    seed_default_users()

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(dashboard_bp)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    # Frontend Route Servicing
    @app.route("/")
    def index():
        return send_from_directory(str(BASE_DIR / "frontend"), "index.html")

    @app.route("/dashboard")
    def dashboard():
        return send_from_directory(str(BASE_DIR / "frontend"), "dashboard.html")

    @app.route("/docs")
    def docs():
        return send_from_directory(str(BASE_DIR / "frontend"), "docs.html")

    @app.route("/css/<path:filename>")
    def serve_css(filename):
        return send_from_directory(str(BASE_DIR / "frontend" / "css"), filename)

    @app.route("/js/<path:filename>")
    def serve_js(filename):
        return send_from_directory(str(BASE_DIR / "frontend" / "js"), filename)

    @app.route("/assets/<path:filename>")
    def serve_assets(filename):
        return send_from_directory(str(BASE_DIR / "frontend" / "assets"), filename)

    @app.route("/data/uploads/<path:filename>")
    def serve_uploads(filename):
        return send_from_directory(str(UPLOAD_DIR), filename)

    @app.route("/api/health")
    def health():
        return jsonify({
            "status": "healthy",
            "service": "AuraID Secure Biometric Authentication Platform",
            "version": "2.4.0",
            "zero_trust": "ENFORCED"
        })

    return app

if __name__ == "__main__":
    app = create_app()
    print(f"[*] Starting AuraID Face Recognition & Anti-Spoofing Server on http://{Config.HOST}:{Config.PORT}")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
