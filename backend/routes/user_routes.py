from flask import Blueprint, request, jsonify
from backend.database.db import db_session
from backend.models.database_models import User, FaceTemplate
from backend.security.crypto import hash_password

user_bp = Blueprint("user_bp", __name__)

@user_bp.route("/api/users", methods=["GET"])
def get_users():
    users = db_session.query(User).order_by(User.id.desc()).all()
    return jsonify({
        "status": "success",
        "total": len(users),
        "users": [u.to_dict() for u in users]
    })

@user_bp.route("/api/users/<int:user_id>", methods=["GET"])
def get_user_by_id(user_id):
    user = db_session.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404
    return jsonify({"status": "success", "user": user.to_dict()})

@user_bp.route("/api/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    user = db_session.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    data = request.get_json() or {}
    if "name" in data:
        user.name = data["name"].strip()
    if "email" in data:
        user.email = data["email"].strip().lower()
    if "role" in data:
        user.role = data["role"]
    if "password" in data and data["password"]:
        user.password_hash = hash_password(data["password"])

    db_session.commit()
    return jsonify({"status": "success", "message": "User updated", "user": user.to_dict()})

@user_bp.route("/api/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = db_session.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    db_session.delete(user)
    db_session.commit()
    return jsonify({"status": "success", "message": f"User {user_id} deleted successfully"})

@user_bp.route("/api/users/<int:user_id>/templates", methods=["DELETE"])
def clear_user_templates(user_id):
    db_session.query(FaceTemplate).filter_by(user_id=user_id).delete()
    db_session.commit()
    return jsonify({"status": "success", "message": f"Face templates cleared for user {user_id}"})
