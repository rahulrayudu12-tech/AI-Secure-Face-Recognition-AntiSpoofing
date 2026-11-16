from flask import Blueprint, request, jsonify
from backend.database.db import db_session
from backend.models.database_models import AuthenticationLog, SpoofReport

logs_bp = Blueprint("logs_bp", __name__)

@logs_bp.route("/api/logs", methods=["GET"])
def get_logs():
    limit = int(request.args.get("limit", 100))
    decision_filter = request.args.get("decision")

    query = db_session.query(AuthenticationLog).order_by(AuthenticationLog.timestamp.desc())
    if decision_filter:
        query = query.filter_by(decision=decision_filter)

    logs = query.limit(limit).all()
    return jsonify({
        "status": "success",
        "total": len(logs),
        "logs": [l.to_dict() for l in logs]
    })

@logs_bp.route("/api/spoof-reports", methods=["GET"])
def get_spoof_reports():
    limit = int(request.args.get("limit", 50))
    reports = db_session.query(SpoofReport).order_by(SpoofReport.timestamp.desc()).limit(limit).all()
    return jsonify({
        "status": "success",
        "total": len(reports),
        "reports": [r.to_dict() for r in reports]
    })

@logs_bp.route("/api/logs", methods=["DELETE"])
def clear_logs():
    db_session.query(AuthenticationLog).delete()
    db_session.query(SpoofReport).delete()
    db_session.commit()
    return jsonify({"status": "success", "message": "All security logs and spoof reports cleared"})
