import os
import uuid
import cv2
from flask import Blueprint, request, jsonify
from backend.database.db import db_session
from backend.models.database_models import User
from backend.security.crypto import hash_password, verify_password, generate_jwt_token
from backend.services.recognition_service import RecognitionService
from backend.services.liveness_service import LivenessAuthenticationPipeline
from backend.services.audit_service import AuditService
from backend.config import UPLOAD_DIR

auth_bp = Blueprint("auth_bp", __name__)
pipeline = LivenessAuthenticationPipeline()
recognition_service = RecognitionService()

@auth_bp.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", "user")

    if not name or not email or not password:
        return jsonify({"status": "error", "message": "Name, email and password are required"}), 400

    existing = db_session.query(User).filter_by(email=email).first()
    if existing:
        return jsonify({"status": "error", "message": "An account with this email already exists"}), 409

    pwd_hash = hash_password(password)
    user = User(name=name, email=email, password_hash=pwd_hash, role=role)
    db_session.add(user)
    db_session.commit()

    token = generate_jwt_token(user.id, user.role)
    return jsonify({
        "status": "success",
        "message": "User registered successfully",
        "user": user.to_dict(),
        "token": token
    }), 201

@auth_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = db_session.query(User).filter_by(email=email).first()
    if not user or not verify_password(password, user.password_hash):
        return jsonify({"status": "error", "message": "Invalid email or credentials"}), 401

    token = generate_jwt_token(user.id, user.role)
    return jsonify({
        "status": "success",
        "message": f"Welcome back, {user.name}!",
        "user": user.to_dict(),
        "token": token
    })

@auth_bp.route("/api/enroll-face", methods=["POST"])
def enroll_face():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    image_base64 = data.get("image")
    angle = data.get("angle", "frontal")

    if not user_id or not image_base64:
        return jsonify({"status": "error", "message": "user_id and base64 image required"}), 400

    img_bgr = RecognitionService.decode_image_base64(image_base64)
    if img_bgr is None:
        return jsonify({"status": "error", "message": "Could not decode image"}), 400

    result = recognition_service.enroll_face_for_user(int(user_id), img_bgr, angle)
    if not result["success"]:
        return jsonify({"status": "error", "message": result["message"]}), 400

    return jsonify({
        "status": "success",
        "message": result["message"],
        "template_id": result.get("template_id"),
        "quality_score": result.get("quality_score")
    })

@auth_bp.route("/api/authenticate", methods=["POST"])
def authenticate():
    """
    Main real-time webcam frame authentication endpoint.
    Executes detection, alignment, ArcFace matching, MultiFTNet, MiniFASNet, LSTM, and Fusion.
    """
    data = request.get_json() or {}
    image_base64 = data.get("image")
    target_user_id = data.get("user_id")
    simulate_attack = data.get("simulate_attack") # e.g. "printed_photo", "mobile_screen", "3d_mask"

    if not image_base64:
        return jsonify({"status": "error", "message": "No image frame provided"}), 400

    img_bgr = RecognitionService.decode_image_base64(image_base64)
    if img_bgr is None:
        return jsonify({"status": "error", "message": "Invalid image payload"}), 400

    res = pipeline.process_frame(
        img_bgr,
        target_user_id=int(target_user_id) if target_user_id else None,
        simulate_attack=simulate_attack
    )

    if not res.get("face_detected"):
        return jsonify({
            "status": "warning",
            "decision": "NO_FACE_DETECTED",
            "message": "No face detected in frame",
            "latency_ms": res.get("latency_ms", 0)
        })

    verdict = res["verdict"]
    matched_user = res["matched_user"]
    client_ip = request.remote_addr or "127.0.0.1"

    # Save frame snippet if spoof detected
    saved_frame_path = None
    if verdict["decision"] == "SPOOF_DETECTED":
        filename = f"spoof_{uuid.uuid4().hex[:8]}.jpg"
        save_path = UPLOAD_DIR / filename
        cv2.imwrite(str(save_path), img_bgr)
        saved_frame_path = f"/data/uploads/{filename}"

        # Record Spoof Report
        AuditService.log_spoof_attempt(
            attack_type=verdict["attack_type"],
            confidence=verdict["overall_confidence"],
            frequency_score=verdict["scores_breakdown"]["multiftnet_fourier"],
            color_score=verdict["scores_breakdown"]["minifasnet_color"],
            temporal_score=verdict["scores_breakdown"]["lstm_temporal"],
            frame_path=saved_frame_path,
            ip_address=client_ip
        )

    # Record Authentication Audit Log
    AuditService.log_authentication(
        user_id=matched_user["id"] if matched_user else None,
        identity_score=verdict["identity_score"],
        liveness_score=verdict["fused_liveness_score"],
        decision=verdict["decision"],
        ip_address=client_ip,
        details=verdict["status_message"]
    )

    return jsonify({
        "status": "success",
        "decision": verdict["decision"],
        "granted": verdict["granted"],
        "user": matched_user,
        "box": res["box"],
        "landmarks": res["landmarks"],
        "confidence": verdict["overall_confidence"],
        "identity_score": verdict["identity_score"],
        "liveness_score": verdict["fused_liveness_score"],
        "scores_breakdown": verdict["scores_breakdown"],
        "attack_type": verdict["attack_type"],
        "status_message": verdict["status_message"],
        "reason_code": verdict["reason_code"],
        "quality": res["quality"],
        "latency_ms": res["latency_ms"]
    })
