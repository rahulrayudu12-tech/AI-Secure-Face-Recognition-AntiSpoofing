import base64
import cv2
import numpy as np
from backend.database.db import db_session
from backend.models.database_models import FaceTemplate, User
from ai.retinaface.detector import RetinaFaceDetector
from ai.preprocessing.face_aligner import FaceAligner
from ai.arcface.recognizer import ArcFaceRecognizer

class RecognitionService:
    def __init__(self):
        self.detector = RetinaFaceDetector()
        self.aligner = FaceAligner(desired_size=112)
        self.recognizer = ArcFaceRecognizer(embedding_size=512)

    @staticmethod
    def decode_image_base64(image_base64: str) -> np.ndarray:
        """Decode a base64 or data URL string into an OpenCV BGR image."""
        if not image_base64:
            return None
        if "base64," in image_base64:
            image_base64 = image_base64.split("base64,")[1]
        raw_bytes = base64.b64decode(image_base64)
        np_arr = np.frombuffer(raw_bytes, np.uint8)
        img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        return img_bgr

    def enroll_face_for_user(self, user_id: int, image_bgr: np.ndarray, angle: str = "frontal") -> dict:
        """
        Enroll a user's facial template into the database.
        Detects face, validates sharpness/lighting, aligns, generates embedding.
        """
        user = db_session.query(User).filter_by(id=user_id).first()
        if not user:
            return {"success": False, "message": "User does not exist"}

        faces = self.detector.detect_faces(image_bgr)
        if not faces:
            return {"success": False, "message": "No face detected in the frame. Please look directly at the camera."}

        primary_face = faces[0]
        crop = primary_face["crop"]

        # Quality check
        quality = self.aligner.assess_quality(crop)
        if not quality["valid"]:
            return {
                "success": False, 
                "message": f"Image quality unacceptable: {quality['reason']}. Please ensure good lighting and steady camera."
            }

        # Face alignment
        aligned_crop = self.aligner.align_face(crop, primary_face.get("landmarks", []))
        
        # Extract 512-D ArcFace embedding
        embedding = self.recognizer.extract_embedding(aligned_crop)
        raw_bytes = self.recognizer.serialize_embedding(embedding)

        # Save to database
        template = FaceTemplate(
            user_id=user.id,
            embedding=raw_bytes,
            angle=angle,
            quality_score=quality["score"]
        )
        db_session.add(template)
        db_session.commit()

        return {
            "success": True,
            "message": f"Face enrolled successfully for {user.name} ({angle} angle).",
            "template_id": template.id,
            "quality_score": quality["score"]
        }

    def match_probe(self, probe_embedding: np.ndarray) -> tuple:
        """
        Match a probe embedding against all enrolled gallery templates in database.
        Returns: (best_user, best_similarity, best_template)
        """
        templates = db_session.query(FaceTemplate).all()
        if not templates:
            return None, 0.0, None

        best_score = -1.0
        best_template = None
        best_user = None

        for tmpl in templates:
            gallery_emb = self.recognizer.deserialize_embedding(tmpl.embedding)
            score = self.recognizer.compute_similarity(probe_embedding, gallery_emb)
            if score > best_score:
                best_score = score
                best_template = tmpl
                best_user = tmpl.user

        return best_user, best_score, best_template
