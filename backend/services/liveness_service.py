import time
import cv2
import numpy as np
from ai.retinaface.detector import RetinaFaceDetector
from ai.preprocessing.face_aligner import FaceAligner
from ai.arcface.recognizer import ArcFaceRecognizer
from ai.multiftnet.fourier_antispoof import MultiFTNetAntiSpoof
from ai.minifasnet.color_liveness import MiniFASNetColorLiveness
from ai.lstm.temporal_liveness import TemporalLSTMAnalyzer
from ai.fusion.decision_engine import DecisionFusionEngine
from backend.services.recognition_service import RecognitionService

class LivenessAuthenticationPipeline:
    """
    Unified Production Authentication & Anti-Spoofing Pipeline.
    Runs the 10-step authentication pipeline:
    Webcam Frame -> Face Detection -> Alignment -> ArcFace ID -> MultiFTNet -> MiniFASNet -> LSTM -> Fusion -> Decision -> Audit
    """

    def __init__(self):
        self.detector = RetinaFaceDetector()
        self.aligner = FaceAligner(desired_size=112)
        self.recognizer = ArcFaceRecognizer(embedding_size=512)
        self.multiftnet = MultiFTNetAntiSpoof()
        self.minifasnet = MiniFASNetColorLiveness()
        self.lstm = TemporalLSTMAnalyzer()
        self.fusion = DecisionFusionEngine()
        self.recognition_service = RecognitionService()

    def process_frame(
        self,
        image_bgr: np.ndarray,
        target_user_id: int = None,
        simulate_attack: str = None
    ) -> dict:
        """
        Execute full authentication and anti-spoofing pipeline.
        simulate_attack: None, "printed_photo", "mobile_screen", "3d_mask", "replay_video"
        """
        start_time = time.perf_counter()

        if image_bgr is None or image_bgr.size == 0:
            return {
                "success": False,
                "decision": "ACCESS_DENIED",
                "message": "Empty or corrupted image frame received.",
                "latency_ms": 0.0
            }

        # Step 2: Face Detection
        faces = self.detector.detect_faces(image_bgr)
        if not faces:
            return {
                "success": False,
                "face_detected": False,
                "decision": "NO_FACE_DETECTED",
                "message": "No face detected in camera field of view.",
                "latency_ms": round((time.perf_counter() - start_time) * 1000, 2)
            }

        primary_face = faces[0]
        face_crop = primary_face["crop"]
        landmarks = primary_face.get("landmarks", [])
        box = primary_face.get("box", [0, 0, 0, 0])

        # Step 3: Face Alignment & Quality
        quality = self.aligner.assess_quality(face_crop)
        aligned_face = self.aligner.align_face(face_crop, landmarks)

        # Step 4: Identity Verification (ArcFace)
        probe_embedding = self.recognizer.extract_embedding(aligned_face)

        if target_user_id:
            # Match against specific claimed user
            from backend.database.db import db_session
            from backend.models.database_models import User, FaceTemplate
            user = db_session.query(User).filter_by(id=target_user_id).first()
            if user and user.templates:
                best_sim = max([
                    self.recognizer.compute_similarity(probe_embedding, self.recognizer.deserialize_embedding(t.embedding))
                    for t in user.templates
                ])
                matched_user = user
            else:
                matched_user, best_sim = None, 0.0
        else:
            # 1:N Gallery Matching against all enrolled users
            matched_user, best_sim, _ = self.recognition_service.match_probe(probe_embedding)

        # Step 5: MultiFTNet Fourier Frequency Anti-Spoofing
        ft_result = self.multiftnet.analyze_frequency_spectrum(face_crop)

        # Step 6: MiniFASNet Multi-Channel Color Liveness
        color_result = self.minifasnet.evaluate_liveness(face_crop)

        # Step 7: Temporal Micro-Motion LSTM
        lstm_result = self.lstm.update_and_evaluate(face_crop)

        # Apply Attack Simulation override if requested (for testing and demonstration)
        multiftnet_score = ft_result["liveness_score"]
        minifasnet_score = color_result["liveness_score"]
        lstm_score = lstm_result["temporal_score"]
        multiftnet_attack = ft_result["attack_type"]
        lstm_attack = lstm_result.get("attack_type", "bona_fide")

        if simulate_attack == "printed_photo":
            multiftnet_score = 0.18
            minifasnet_score = 0.32
            lstm_score = 0.08
            multiftnet_attack = "printed_photo"
            lstm_attack = "static_presentation"
        elif simulate_attack == "mobile_screen":
            multiftnet_score = 0.22
            minifasnet_score = 0.41
            lstm_score = 0.52
            multiftnet_attack = "screen_replay"
        elif simulate_attack == "3d_mask":
            multiftnet_score = 0.35
            minifasnet_score = 0.26
            lstm_score = 0.44
            multiftnet_attack = "3d_mask"
        elif simulate_attack == "replay_video":
            multiftnet_score = 0.42
            minifasnet_score = 0.55
            lstm_score = 0.25
            multiftnet_attack = "video_replay"
            lstm_attack = "unstable_replay"

        # Step 8: Decision-Level Fusion
        fusion_verdict = self.fusion.fuse_and_decide(
            identity_score=best_sim,
            is_user_known=matched_user is not None,
            multiftnet_score=multiftnet_score,
            minifasnet_score=minifasnet_score,
            lstm_score=lstm_score,
            multiftnet_attack=multiftnet_attack,
            lstm_attack=lstm_attack
        )

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "success": True,
            "face_detected": True,
            "box": box,
            "landmarks": landmarks,
            "matched_user": matched_user.to_dict() if matched_user else None,
            "verdict": fusion_verdict,
            "quality": quality,
            "latency_ms": latency_ms
        }
