import cv2
import numpy as np
from backend.vision.digit_recognizer import DigitRecognizer


def test_digit_recognizer_prediction():
    recognizer = DigitRecognizer()

    # Test digits 1 through 9 rendered with OpenCV
    correct = 0
    total = 9

    for digit in range(1, 10):
        # Render clean digit image
        canvas = np.zeros((50, 50), dtype=np.uint8)
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = str(digit)
        (tw, th), _ = cv2.getTextSize(text, font, 0.9, 2)
        tx = (50 - tw) // 2
        ty = (50 + th) // 2
        cv2.putText(canvas, text, (tx, ty), font, 0.9, 255, 2, cv2.LINE_AA)

        contours, _ = cv2.findContours(canvas, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        assert len(contours) > 0
        x, y, w, h = cv2.boundingRect(np.vstack(contours))
        crop = canvas[y : y + h, x : x + w]
        max_d = max(w, h)
        pad = max_d + 6
        padded = np.zeros((pad, pad), dtype=np.uint8)
        ox = (pad - w) // 2
        oy = (pad - h) // 2
        padded[oy : oy + h, ox : ox + w] = crop
        img28 = cv2.resize(padded, (28, 28), interpolation=cv2.INTER_AREA)
        _, img28 = cv2.threshold(img28, 50, 255, cv2.THRESH_BINARY)

        pred, conf = recognizer.predict(img28)
        if pred == digit:
            correct += 1

    # Should achieve high accuracy across all standard digits
    assert correct >= 8

