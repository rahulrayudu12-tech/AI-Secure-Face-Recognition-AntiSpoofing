from backend.config import Config

class DecisionFusionEngine:
    """
    Decision-Level Fusion Engine.
    Fuses MultiFTNet, MiniFASNet, and Temporal LSTM into an integrated
    anti-spoofing verdict, and evaluates ArcFace identity verification
    against zero-trust cybersecurity policies.
    """

    def __init__(
        self,
        identity_threshold: float = Config.IDENTITY_MATCH_THRESHOLD,
        liveness_threshold: float = Config.LIVENESS_THRESHOLD
    ):
        self.identity_threshold = identity_threshold
        self.liveness_threshold = liveness_threshold

    def fuse_and_decide(
        self,
        identity_score: float,
        is_user_known: bool,
        multiftnet_score: float,
        minifasnet_score: float,
        lstm_score: float,
        multiftnet_attack: str = "bona_fide",
        lstm_attack: str = "bona_fide"
    ) -> dict:
        """
        Execute multi-factor biometric fusion logic.
        """
        # Weighted liveness fusion
        # MultiFTNet (Fourier frequency) has highest weight for screening digital screens & dot prints
        fused_liveness = (
            0.45 * multiftnet_score +
            0.35 * minifasnet_score +
            0.20 * lstm_score
        )
        fused_liveness = round(max(0.0, min(1.0, fused_liveness)), 4)

        is_liveness_verified = fused_liveness >= self.liveness_threshold
        is_identity_verified = is_user_known and (identity_score >= self.identity_threshold)

        # Primary Cybersecurity Access Control Decision:
        # IF Identity_Match == True AND Liveness == True: Grant Access ELSE: Reject Access
        if is_liveness_verified and is_identity_verified:
            decision = "ACCESS_GRANTED"
            reason_code = "AUTH_SUCCESS_BIOMETRIC_AND_LIVENESS_VERIFIED"
            attack_type = "none"
            status_message = "Authentication Successful. Identity confirmed and live subject verified."
        elif not is_liveness_verified:
            decision = "SPOOF_DETECTED"
            reason_code = "SECURITY_ALERT_PRESENTATION_ATTACK"
            
            # Identify likely presentation attack vector
            if multiftnet_attack == "screen_replay":
                attack_type = "screen_replay"
                status_message = "Presentation Attack Detected: Mobile/Monitor Screen Replay."
            elif multiftnet_attack == "printed_photo" or lstm_attack == "static_presentation":
                attack_type = "printed_photo"
                status_message = "Presentation Attack Detected: Printed 2D Photograph."
            elif minifasnet_score < 0.40:
                attack_type = "3d_mask"
                status_message = "Presentation Attack Detected: Synthetic Material / 3D Mask."
            else:
                attack_type = "video_replay"
                status_message = "Presentation Attack Detected: Replay Video Artifacts."
        elif not is_user_known:
            decision = "UNKNOWN_USER"
            reason_code = "IDENTITY_NOT_ENROLLED"
            attack_type = "none"
            status_message = "Identity Not Found. Subject is live, but not enrolled in the database."
        else:
            decision = "ACCESS_DENIED"
            reason_code = "IDENTITY_MISMATCH_BELOW_CONFIDENCE"
            attack_type = "none"
            status_message = f"Access Denied. Identity similarity ({identity_score:.1%}) below threshold ({self.identity_threshold:.1%})."

        overall_confidence = round(
            (identity_score * 0.5 + fused_liveness * 0.5) if decision == "ACCESS_GRANTED" else fused_liveness,
            4
        )

        return {
            "decision": decision,
            "granted": decision == "ACCESS_GRANTED",
            "identity_verified": is_identity_verified,
            "liveness_verified": is_liveness_verified,
            "overall_confidence": overall_confidence,
            "identity_score": round(identity_score, 4),
            "fused_liveness_score": fused_liveness,
            "scores_breakdown": {
                "arcface_identity": round(identity_score, 4),
                "multiftnet_fourier": round(multiftnet_score, 4),
                "minifasnet_color": round(minifasnet_score, 4),
                "lstm_temporal": round(lstm_score, 4)
            },
            "attack_type": attack_type,
            "reason_code": reason_code,
            "status_message": status_message
        }
