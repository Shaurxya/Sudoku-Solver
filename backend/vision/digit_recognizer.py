"""
Robust Digit Recognizer for printed Sudoku digits.
Trained on synthetic multi-font renderings using OpenCV Hershey font families,
stroke variations, rotations, and morphological profile feature extraction.
"""
from typing import Tuple, Optional
import os
import pickle
import numpy as np
import cv2
from sklearn.neural_network import MLPClassifier


class DigitRecognizer:
    """Classifies isolated 28x28 digit images into digits 1-9."""

    def __init__(self, model_path: Optional[str] = None):
        if model_path is None:
            model_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(model_dir, "digit_model.pkl")
        self.model_path = model_path
        self.model: Optional[MLPClassifier] = None
        self._load_or_train()

    def _load_or_train(self) -> None:
        """Loads cached model or trains a new one if not present."""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, "rb") as f:
                    self.model = pickle.load(f)
                return
            except Exception:
                pass

        # Train new model
        self.train_synthetic_model()

    def extract_features(self, digit_img_28x28: np.ndarray) -> np.ndarray:
        """
        Extracts 784 normalized pixel values plus horizontal and vertical projection profiles.
        Total features: 840.
        """
        img_norm = (digit_img_28x28.astype(np.float32) / 255.0).flatten()
        
        # Horizontal projection (row sums normalized)
        h_proj = np.sum(digit_img_28x28 > 128, axis=1, dtype=np.float32) / 28.0
        # Vertical projection (col sums normalized)
        v_proj = np.sum(digit_img_28x28 > 128, axis=0, dtype=np.float32) / 28.0

        return np.hstack([img_norm, h_proj, v_proj])

    def train_synthetic_model(self) -> None:
        """Generates synthetic multi-font dataset and trains MLP classifier."""
        X = []
        y = []

        cv_fonts = [
            cv2.FONT_HERSHEY_SIMPLEX,
            cv2.FONT_HERSHEY_DUPLEX,
            cv2.FONT_HERSHEY_COMPLEX,
            cv2.FONT_HERSHEY_TRIPLEX,
            cv2.FONT_HERSHEY_COMPLEX_SMALL,
        ]
        scales = [0.75, 0.9, 1.05]
        thicknesses = [1, 2]

        for digit in range(1, 10):
            for font in cv_fonts:
                for sc in scales:
                    for th in thicknesses:
                        canvas = np.zeros((56, 56), dtype=np.uint8)
                        text = str(digit)
                        (t_w, t_h), base = cv2.getTextSize(text, font, sc, th)
                        org_x = (56 - t_w) // 2
                        org_y = (56 + t_h) // 2
                        cv2.putText(canvas, text, (org_x, org_y), font, sc, 255, th, cv2.LINE_AA)
                        
                        contours, _ = cv2.findContours(canvas, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        if not contours:
                            continue
                        x, cy, cw, ch = cv2.boundingRect(np.vstack(contours))
                        crop = canvas[cy : cy + ch, x : x + cw]
                        max_d = max(cw, ch)
                        pad = max_d + 8
                        padded = np.zeros((pad, pad), dtype=np.uint8)
                        ox = (pad - cw) // 2
                        oy = (pad - ch) // 2
                        padded[oy : oy + ch, ox : ox + cw] = crop
                        resized = cv2.resize(padded, (28, 28), interpolation=cv2.INTER_AREA)

                        for angle in [-8, -4, 0, 4, 8]:
                            center = (14, 14)
                            rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
                            rot_img = cv2.warpAffine(resized, rot_mat, (28, 28))
                            _, rot_thresh = cv2.threshold(rot_img, 50, 255, cv2.THRESH_BINARY)
                            X.append(self.extract_features(rot_thresh))
                            y.append(digit)

        X = np.array(X, dtype=np.float32)
        y = np.array(y, dtype=np.int32)

        # Train high-accuracy MLP Classifier
        mlp = MLPClassifier(
            hidden_layer_sizes=(96, 48),
            activation="relu",
            solver="adam",
            max_iter=30,
            random_state=42
        )
        mlp.fit(X, y)
        self.model = mlp

        # Cache model
        try:
            with open(self.model_path, "wb") as f:
                pickle.dump(mlp, f)
        except Exception:
            pass

    def predict(self, digit_img_28x28: np.ndarray) -> Tuple[int, float]:
        """
        Predicts digit (1-9) from normalized 28x28 image.
        Returns (digit, confidence).
        """
        if self.model is None:
            self._load_or_train()

        feats = self.extract_features(digit_img_28x28).reshape(1, -1)
        probs = self.model.predict_proba(feats)[0]
        classes = self.model.classes_

        best_idx = int(np.argmax(probs))
        predicted_digit = int(classes[best_idx])
        confidence = float(probs[best_idx])

        # Structural sanity check for digit 1
        contours, _ = cv2.findContours(digit_img_28x28, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            _, _, w, h = cv2.boundingRect(np.vstack(contours))
            aspect_ratio = float(w) / max(float(h), 1.0)
            if aspect_ratio < 0.42 and predicted_digit != 1:
                one_idx = list(classes).index(1) if 1 in classes else None
                if one_idx is not None and probs[one_idx] > 0.15:
                    predicted_digit = 1
                    confidence = float(probs[one_idx])

        return predicted_digit, confidence

