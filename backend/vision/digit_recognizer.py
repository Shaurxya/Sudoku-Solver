"""
Robust Digit Recognizer for printed Sudoku digits.
Trained on synthetic TrueType font typography (Arial, Helvetica, Times, Geneva, Georgia, Verdana, etc.)
with multi-scale, rotation, stroke variations, and structural density features.
"""
from typing import Tuple, List, Optional
import os
import pickle
import numpy as np
import cv2
from PIL import Image, ImageFont, ImageDraw
from sklearn.ensemble import RandomForestClassifier


class DigitRecognizer:
    """Classifies isolated 28x28 digit images into digits 1-9."""

    def __init__(self, model_path: Optional[str] = None):
        if model_path is None:
            model_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(model_dir, "digit_model.pkl")
        self.model_path = model_path
        self.model: Optional[RandomForestClassifier] = None
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

    @staticmethod
    def extract_features(digit_img_28x28: np.ndarray) -> np.ndarray:
        """
        Extracts 784 normalized pixel values, 28 horizontal + 28 vertical projection profiles,
        and 4 quadrant densities.
        """
        norm = digit_img_28x28.astype(np.float32) / 255.0
        flat = norm.flatten()
        
        # Horizontal and Vertical projections
        h_proj = np.sum(norm > 0.5, axis=1, dtype=np.float32) / 28.0
        v_proj = np.sum(norm > 0.5, axis=0, dtype=np.float32) / 28.0
        
        # 4-quadrant densities
        q_tl = float(np.mean(norm[:14, :14]))
        q_tr = float(np.mean(norm[:14, 14:]))
        q_bl = float(np.mean(norm[14:, :14]))
        q_br = float(np.mean(norm[14:, 14:]))
        
        extra = np.array([q_tl, q_tr, q_bl, q_br], dtype=np.float32)
        return np.hstack([flat, h_proj, v_proj, extra])

    def train_synthetic_model(self) -> None:
        """Generates synthetic multi-font dataset and trains high-accuracy classifier."""
        X = []
        y = []

        font_paths = [
            "/System/Library/Fonts/Geneva.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/SFNSMono.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
            "/System/Library/Fonts/Supplemental/Georgia.ttf",
            "/System/Library/Fonts/Supplemental/Verdana.ttf",
            "/System/Library/Fonts/Supplemental/Courier New.ttf",
            "/Library/Fonts/Arial.ttf",
        ]

        def render_digit(digit: int, font) -> np.ndarray:
            img = Image.new("L", (56, 56), 0)
            draw = ImageDraw.Draw(img)
            text = str(digit)
            bbox = draw.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text(((56 - tw) // 2 - bbox[0], (56 - th) // 2 - bbox[1]), text, fill=255, font=font)
            arr = np.array(img, dtype=np.uint8)
            cnts, _ = cv2.findContours(arr, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not cnts:
                return np.zeros((28, 28), dtype=np.uint8)
            x, cy, cw, ch = cv2.boundingRect(np.vstack(cnts))
            crop = arr[cy : cy + ch, x : x + cw]
            max_d = max(cw, ch)
            pad = max_d + 8
            canvas = np.zeros((pad, pad), dtype=np.uint8)
            canvas[(pad - ch) // 2 : (pad - ch) // 2 + ch, (pad - cw) // 2 : (pad - cw) // 2 + cw] = crop
            norm = cv2.resize(canvas, (28, 28), interpolation=cv2.INTER_AREA)
            _, norm = cv2.threshold(norm, 50, 255, cv2.THRESH_BINARY)
            return norm

        # 1. Render using TrueType system fonts
        for digit in range(1, 10):
            for fp in font_paths:
                if not os.path.exists(fp):
                    continue
                for sz in [24, 28, 32]:
                    try:
                        font = ImageFont.truetype(fp, sz)
                        base = render_digit(digit, font)
                        for ang in [-8, -4, 0, 4, 8]:
                            M = cv2.getRotationMatrix2D((14, 14), ang, 1.0)
                            rot = cv2.warpAffine(base, M, (28, 28))
                            _, rot = cv2.threshold(rot, 50, 255, cv2.THRESH_BINARY)
                            for dil in [0, 1]:
                                d_img = cv2.dilate(rot, np.ones((2, 2), np.uint8)) if dil else rot
                                X.append(self.extract_features(d_img))
                                y.append(digit)
                    except Exception:
                        pass

        # 2. Add OpenCV fonts fallback
        cv_fonts = [
            cv2.FONT_HERSHEY_SIMPLEX,
            cv2.FONT_HERSHEY_DUPLEX,
            cv2.FONT_HERSHEY_COMPLEX,
            cv2.FONT_HERSHEY_TRIPLEX,
        ]
        for digit in range(1, 10):
            for font in cv_fonts:
                for sc in [0.75, 0.9, 1.05]:
                    for th in [1, 2]:
                        canvas = np.zeros((56, 56), dtype=np.uint8)
                        text = str(digit)
                        (t_w, t_h), _ = cv2.getTextSize(text, font, sc, th)
                        cv2.putText(canvas, text, ((56 - t_w) // 2, (56 + t_h) // 2), font, sc, 255, th, cv2.LINE_AA)
                        cnts, _ = cv2.findContours(canvas, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        if not cnts:
                            continue
                        x, cy, cw, ch = cv2.boundingRect(np.vstack(cnts))
                        crop = canvas[cy : cy + ch, x : x + cw]
                        pad = max(cw, ch) + 8
                        padded = np.zeros((pad, pad), dtype=np.uint8)
                        padded[(pad - ch) // 2 : (pad - ch) // 2 + ch, (pad - cw) // 2 : (pad - cw) // 2 + cw] = crop
                        resized = cv2.resize(padded, (28, 28), interpolation=cv2.INTER_AREA)
                        _, thresh_res = cv2.threshold(resized, 50, 255, cv2.THRESH_BINARY)
                        for ang in [-6, 0, 6]:
                            M = cv2.getRotationMatrix2D((14, 14), ang, 1.0)
                            rot = cv2.warpAffine(thresh_res, M, (28, 28))
                            _, rot = cv2.threshold(rot, 50, 255, cv2.THRESH_BINARY)
                            X.append(self.extract_features(rot))
                            y.append(digit)

        X = np.array(X, dtype=np.float32)
        y = np.array(y, dtype=np.int32)

        clf = RandomForestClassifier(n_estimators=120, random_state=42, n_jobs=-1)
        clf.fit(X, y)
        self.model = clf

        try:
            with open(self.model_path, "wb") as f:
                pickle.dump(clf, f)
        except Exception:
            pass

    def predict_ranked(self, digit_img_28x28: np.ndarray, top_k: int = 4) -> List[Tuple[int, float]]:
        """
        Returns top-k candidate digits and their confidence probabilities: [(digit, prob), ...].
        """
        if self.model is None:
            self._load_or_train()

        feats = self.extract_features(digit_img_28x28).reshape(1, -1)
        probs = self.model.predict_proba(feats)[0]
        classes = self.model.classes_

        sorted_indices = np.argsort(probs)[::-1]
        results = []
        for idx in sorted_indices[:top_k]:
            results.append((int(classes[idx]), float(probs[idx])))

        return results

    def predict(self, digit_img_28x28: np.ndarray) -> Tuple[int, float]:
        """Predicts single most likely digit."""
        ranked = self.predict_ranked(digit_img_28x28, top_k=1)
        return ranked[0]
