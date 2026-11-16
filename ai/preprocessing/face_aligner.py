import cv2
import numpy as np

class FaceAligner:
    """Preprocesses and aligns detected face crops for ArcFace and Anti-Spoofing."""

    def __init__(self, desired_size: int = 112):
        self.desired_size = desired_size

    def assess_quality(self, face_bgr: np.ndarray) -> dict:
        """Assess face image quality: sharpness (Laplacian variance) and illumination."""
        if face_bgr is None or face_bgr.size == 0:
            return {"valid": False, "score": 0.0, "reason": "Empty image"}

        gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        if h < 40 or w < 40:
            return {"valid": False, "score": 0.1, "reason": "Face too small"}

        # Sharpness / Blur estimation
        blur_variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        
        # Illumination balance
        mean_brightness = float(np.mean(gray))
        
        is_clear = blur_variance >= 30.0
        is_lit = 30.0 <= mean_brightness <= 230.0

        score = min(1.0, blur_variance / 300.0)
        
        return {
            "valid": is_clear and is_lit,
            "sharpness": blur_variance,
            "brightness": mean_brightness,
            "score": round(score, 4),
            "reason": "OK" if (is_clear and is_lit) else ("Blurry" if not is_clear else "Poor lighting")
        }

    def align_face(self, image: np.ndarray, landmarks: list, target_size=(112, 112)) -> np.ndarray:
        """Align face using eye landmarks or standard center-affine mapping."""
        if landmarks and len(landmarks) >= 2:
            left_eye, right_eye = landmarks[0], landmarks[1]
            dx = right_eye[0] - left_eye[0]
            dy = right_eye[1] - left_eye[1]
            angle = np.degrees(np.arctan2(dy, dx))

            # Eye center
            eye_center = (float((left_eye[0] + right_eye[0]) / 2), float((left_eye[1] + right_eye[1]) / 2))
            
            # Rotation matrix
            rot_mat = cv2.getRotationMatrix2D(eye_center, angle, scale=1.0)
            aligned = cv2.warpAffine(image, rot_mat, (image.shape[1], image.shape[0]), flags=cv2.INTER_LINEAR)
            return cv2.resize(aligned, target_size)

        return cv2.resize(image, target_size)

    def normalize(self, face_bgr: np.ndarray) -> np.ndarray:
        """Normalize face crop to [-1.0, 1.0] float32 for neural network inference."""
        resized = cv2.resize(face_bgr, (self.desired_size, self.desired_size))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        normalized = (rgb.astype(np.float32) - 127.5) / 128.0
        return normalized
