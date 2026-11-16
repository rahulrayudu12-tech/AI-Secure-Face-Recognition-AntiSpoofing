from flask import Blueprint, jsonify
from backend.services.audit_service import AuditService
from backend.database.db import db_session
from backend.models.database_models import AuthenticationLog, SpoofReport

dashboard_bp = Blueprint("dashboard_bp", __name__)

@dashboard_bp.route("/api/dashboard/stats", methods=["GET"])
def get_dashboard_stats():
    stats = AuditService.get_dashboard_statistics()
    return jsonify({"status": "success", "data": stats})

@dashboard_bp.route("/api/dashboard/analytics", methods=["GET"])
def get_dashboard_analytics():
    # Attack type counts
    reports = db_session.query(SpoofReport).all()
    attack_counts = {
        "screen_replay": 0,
        "printed_photo": 0,
        "3d_mask": 0,
        "video_replay": 0
    }
    for r in reports:
        if r.attack_type in attack_counts:
            attack_counts[r.attack_type] += 1
        else:
            attack_counts[r.attack_type] = 1

    # Simulated ROC curve data for presentation display
    thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    apcer_curve = [0.12, 0.08, 0.05, 0.03, 0.018, 0.015, 0.0125, 0.008, 0.003]
    bpcer_curve = [0.001, 0.003, 0.006, 0.010, 0.014, 0.016, 0.0180, 0.035, 0.075]

    return jsonify({
        "status": "success",
        "attack_distribution": attack_counts,
        "roc_curve": {
            "thresholds": thresholds,
            "apcer": apcer_curve,
            "bpcer": bpcer_curve
        }
    })
