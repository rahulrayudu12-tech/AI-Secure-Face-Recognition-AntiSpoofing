from datetime import datetime
from backend.database.db import db_session
from backend.models.database_models import User, AuthenticationLog, SpoofReport, FaceTemplate
from ai.evaluation.metrics import BiometricEvaluator

class AuditService:
    @staticmethod
    def log_authentication(
        user_id: int,
        identity_score: float,
        liveness_score: float,
        decision: str,
        ip_address: str = "127.0.0.1",
        details: str = ""
    ) -> AuthenticationLog:
        """Create an audit log record for an authentication attempt."""
        log_entry = AuthenticationLog(
            user_id=user_id,
            timestamp=datetime.utcnow(),
            identity_score=identity_score,
            liveness_score=liveness_score,
            decision=decision,
            ip_address=ip_address,
            details=details
        )
        db_session.add(log_entry)
        db_session.commit()
        return log_entry

    @staticmethod
    def log_spoof_attempt(
        attack_type: str,
        confidence: float,
        frequency_score: float,
        color_score: float,
        temporal_score: float,
        frame_path: str = None,
        ip_address: str = "127.0.0.1"
    ) -> SpoofReport:
        """Create a security spoof report."""
        report = SpoofReport(
            timestamp=datetime.utcnow(),
            attack_type=attack_type,
            confidence=confidence,
            frame_path=frame_path,
            frequency_score=frequency_score,
            color_score=color_score,
            temporal_score=temporal_score,
            ip_address=ip_address
        )
        db_session.add(report)
        db_session.commit()
        return report

    @staticmethod
    def get_dashboard_statistics() -> dict:
        """Calculate system overview metrics."""
        total_users = db_session.query(User).count()
        registered_faces = db_session.query(FaceTemplate).count()
        total_attempts = db_session.query(AuthenticationLog).count()
        successful_auth = db_session.query(AuthenticationLog).filter_by(decision="ACCESS_GRANTED").count()
        failed_auth = db_session.query(AuthenticationLog).filter(
            AuthenticationLog.decision.in_(["ACCESS_DENIED", "UNKNOWN_USER"])
        ).count()
        spoof_attempts = db_session.query(SpoofReport).count()

        # Compute or fetch evaluation metrics
        benchmarks = BiometricEvaluator.calculate_metrics([], [])

        return {
            "total_users": total_users,
            "registered_faces": registered_faces,
            "total_attempts": total_attempts,
            "successful_authentications": successful_auth,
            "failed_authentications": failed_auth,
            "spoof_attempts": spoof_attempts,
            "system_status": "ONLINE - ZERO TRUST ACTIVE",
            "metrics": benchmarks
        }
