import unittest
import numpy as np
from ai.multiftnet.fourier_antispoof import MultiFTNetAntiSpoof
from ai.minifasnet.color_liveness import MiniFASNetColorLiveness
from ai.lstm.temporal_liveness import TemporalLSTMAnalyzer
from ai.fusion.decision_engine import DecisionFusionEngine

class TestAntiSpoofingAndFusion(unittest.TestCase):
    def setUp(self):
        self.multiftnet = MultiFTNetAntiSpoof()
        self.minifasnet = MiniFASNetColorLiveness()
        self.lstm = TemporalLSTMAnalyzer()
        self.fusion = DecisionFusionEngine()

    def test_multiftnet_analysis(self):
        synthetic_crop = np.random.randint(50, 200, (112, 112, 3), dtype=np.uint8)
        res = self.multiftnet.analyze_frequency_spectrum(synthetic_crop)
        self.assertIn("liveness_score", res)
        self.assertIn("high_freq_ratio", res)
        self.assertGreaterEqual(res["liveness_score"], 0.0)
        self.assertLessEqual(res["liveness_score"], 1.0)

    def test_decision_fusion_grant_access(self):
        # Case 1: Known user, high identity match, high liveness
        verdict = self.fusion.fuse_and_decide(
            identity_score=0.92,
            is_user_known=True,
            multiftnet_score=0.88,
            minifasnet_score=0.82,
            lstm_score=0.79
        )
        self.assertEqual(verdict["decision"], "ACCESS_GRANTED")
        self.assertTrue(verdict["granted"])

    def test_decision_fusion_spoof_detection(self):
        # Case 2: Presentation attack (low liveness score)
        verdict = self.fusion.fuse_and_decide(
            identity_score=0.95,
            is_user_known=True,
            multiftnet_score=0.20,
            minifasnet_score=0.35,
            lstm_score=0.10,
            multiftnet_attack="screen_replay"
        )
        self.assertEqual(verdict["decision"], "SPOOF_DETECTED")
        self.assertFalse(verdict["granted"])
        self.assertEqual(verdict["attack_type"], "screen_replay")

if __name__ == "__main__":
    unittest.main()
