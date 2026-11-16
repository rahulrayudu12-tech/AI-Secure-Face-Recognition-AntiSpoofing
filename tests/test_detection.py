import unittest
import numpy as np
import cv2
from ai.retinaface.detector import RetinaFaceDetector
from ai.preprocessing.face_aligner import FaceAligner
from ai.arcface.recognizer import ArcFaceRecognizer

class TestFaceDetectionAndRecognition(unittest.TestCase):
    def setUp(self):
        self.detector = RetinaFaceDetector()
        self.aligner = FaceAligner()
        self.recognizer = ArcFaceRecognizer()

    def test_detector_empty_image(self):
        empty_img = np.zeros((100, 100, 3), dtype=np.uint8)
        faces = self.detector.detect_faces(empty_img)
        self.assertEqual(len(faces), 0)

    def test_embedding_extraction_and_similarity(self):
        # Create synthetic face-like crop
        synthetic_face = np.ones((112, 112, 3), dtype=np.uint8) * 180
        # Draw eyes and mouth
        cv2.circle(synthetic_face, (35, 40), 8, (20, 20, 20), -1)
        cv2.circle(synthetic_face, (77, 40), 8, (20, 20, 20), -1)
        cv2.line(synthetic_face, (40, 85), (72, 85), (30, 30, 30), 3)

        emb1 = self.recognizer.extract_embedding(synthetic_face)
        self.assertEqual(len(emb1), 512)
        # Cosine self-similarity should be 1.0
        self_sim = self.recognizer.compute_similarity(emb1, emb1)
        self.assertAlmostEqual(self_sim, 1.0, places=3)

    def test_face_quality_assessment(self):
        sharp_img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        quality = self.aligner.assess_quality(sharp_img)
        self.assertIn("sharpness", quality)
        self.assertIn("valid", quality)

if __name__ == "__main__":
    unittest.main()
