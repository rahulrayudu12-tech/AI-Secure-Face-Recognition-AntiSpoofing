import cv2
import numpy as np

class MultiFTNetAntiSpoof:
    """
    MultiFTNet: Spatial and Frequency Domain (2D-FFT) Anti-Spoofing Detector.
    Detects presentation attacks by analyzing high-frequency Fourier artifacts,
    moiré patterns from screen grids, and halftone print patterns.
    """

    def __init__(self, high_freq_threshold: float = 0.68):
        self.high_freq_threshold = high_freq_threshold

    def analyze_frequency_spectrum(self, face_crop_bgr: np.ndarray) -> dict:
        """
        Compute 2D Fast Fourier Transform on the face crop to isolate
        frequency anomalies characteristic of screens or printed photos.
        """
        if face_crop_bgr is None or face_crop_bgr.size == 0:
            return {"liveness_score": 0.0, "attack_type": "unknown", "is_live": False}

        gray = cv2.cvtColor(face_crop_bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (128, 128))

        # 2D Fast Fourier Transform
        f = np.fft.fft2(gray.astype(np.float32))
        fshift = np.fft.fftshift(f)
        magnitude_spectrum = 20 * np.log(np.abs(fshift) + 1.0)

        # Split into concentric frequency rings (Low, Mid, High)
        h, w = gray.shape
        cy, cx = h // 2, w // 2
        y, x = np.ogrid[:h, :w]
        dist_from_center = np.sqrt((x - cx)**2 + (y - cy)**2)

        low_mask = dist_from_center <= 16
        mid_mask = (dist_from_center > 16) & (dist_from_center <= 45)
        high_mask = dist_from_center > 45

        low_energy = float(np.mean(magnitude_spectrum[low_mask]))
        mid_energy = float(np.mean(magnitude_spectrum[mid_mask]))
        high_energy = float(np.mean(magnitude_spectrum[high_mask]))

        # High-frequency ratio
        total_energy = low_energy + mid_energy + high_energy + 1e-6
        hf_ratio = high_energy / total_energy

        # Detect discrete frequency peaks (screen moiré / raster lines)
        high_band_vals = magnitude_spectrum[high_mask]
        peak_val = float(np.max(high_band_vals))
        peak_to_mean = peak_val / (high_energy + 1e-6)

        # Anti-spoofing rule heuristics based on CelebA-Spoof frequency patterns:
        # 1. Screen attacks: strong periodic high-frequency spikes (high peak_to_mean)
        # 2. Print attacks: severely diminished high-frequency natural skin specular highlights
        attack_type = "bona_fide"
        liveness_score = 0.85

        if peak_to_mean > 2.8 and hf_ratio > 0.28:
            attack_type = "screen_replay"
            liveness_score = max(0.05, 0.45 - (peak_to_mean - 2.8) * 0.15)
        elif high_energy < 18.0 or hf_ratio < 0.18:
            attack_type = "printed_photo"
            liveness_score = max(0.10, 0.50 - (0.18 - hf_ratio) * 2.0)
        else:
            # Genuine biological tissue texture
            liveness_score = min(0.98, max(0.72, 0.75 + (0.26 - abs(0.24 - hf_ratio)) * 0.8))

        is_live = liveness_score >= self.high_freq_threshold

        return {
            "liveness_score": round(float(liveness_score), 4),
            "is_live": is_live,
            "attack_type": attack_type,
            "high_freq_ratio": round(float(hf_ratio), 4),
            "peak_to_mean": round(float(peak_to_mean), 4),
            "low_energy": round(float(low_energy), 2),
            "high_energy": round(float(high_energy), 2)
        }
