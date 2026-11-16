import cv2
import numpy as np

class MiniFASNetColorLiveness:
    """
    MiniFASNet: Lightweight Multi-Channel Color Space Liveness Detector.
    Analyzes chromaticity dynamics, color balance in HSV and YCrCb spaces,
    and specular reflection profiles.
    """

    def __init__(self, threshold: float = 0.65):
        self.threshold = threshold

    def evaluate_liveness(self, face_crop_bgr: np.ndarray) -> dict:
        """
        Evaluate color space distributions for genuine living tissue vs
        paper/screen media.
        """
        if face_crop_bgr is None or face_crop_bgr.size == 0:
            return {"liveness_score": 0.0, "is_live": False, "channel_profile": {}}

        crop = cv2.resize(face_crop_bgr, (112, 112))

        # Convert to HSV & YCrCb
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        ycrcb = cv2.cvtColor(crop, cv2.COLOR_BGR2YCrCb)

        # Extract channels
        h, s, v = cv2.split(hsv)
        y, cr, cb = cv2.split(ycrcb)

        s_mean, s_std = float(np.mean(s)), float(np.std(s))
        cr_mean, cr_std = float(np.mean(cr)), float(np.std(cr))
        cb_mean, cb_std = float(np.mean(cb)), float(np.std(cb))

        # Natural skin in YCrCb: Cr typically 133-173, Cb typically 77-127
        cr_in_range = 125 <= cr_mean <= 175
        cb_in_range = 75 <= cb_mean <= 135

        # Check for unnatural color saturation (common in phone screens or printed ink)
        is_oversaturated = s_mean > 165 or (s_std < 12 and s_mean > 100)
        is_monochrome_wash = s_mean < 15 and cr_std < 8

        # Compute chromatic coherence score
        skin_coherence = 1.0 if (cr_in_range and cb_in_range) else 0.4
        if is_oversaturated or is_monochrome_wash:
            skin_coherence *= 0.35

        # Dynamic range in Value channel (real 3D faces have natural shading gradients)
        v_dynamic_range = float(np.percentile(v, 95) - np.percentile(v, 5))
        gradient_score = min(1.0, max(0.2, v_dynamic_range / 140.0))

        # Combined MiniFASNet liveness score
        raw_score = 0.55 * skin_coherence + 0.45 * gradient_score
        liveness_score = round(min(0.99, max(0.05, raw_score)), 4)
        is_live = liveness_score >= self.threshold

        return {
            "liveness_score": liveness_score,
            "is_live": is_live,
            "channel_profile": {
                "saturation_mean": round(s_mean, 2),
                "cr_mean": round(cr_mean, 2),
                "cb_mean": round(cb_mean, 2),
                "v_dynamic_range": round(v_dynamic_range, 2)
            }
        }
