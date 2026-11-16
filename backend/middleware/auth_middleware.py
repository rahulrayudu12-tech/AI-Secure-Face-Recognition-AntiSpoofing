from functools import wraps
from flask import request, jsonify, g
from backend.security.crypto import decode_jwt_token
from backend.database.db import db_session
from backend.models.database_models import User

def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"status": "error", "message": "Missing or invalid authorization header"}), 401

        token = auth_header.split(" ", 1)[1]
        decoded = decode_jwt_token(token)
        if "error" in decoded:
            return jsonify({"status": "error", "message": decoded["error"]}), 401

        user = db_session.query(User).filter_by(id=decoded.get("user_id")).first()
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 401

        g.current_user = user
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    @jwt_required
    def decorated(*args, **kwargs):
        if getattr(g, "current_user", None) and g.current_user.role != "admin":
            return jsonify({"status": "error", "message": "Admin privileges required"}), 403
        return f(*args, **kwargs)
    return decorated
