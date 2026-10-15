"""
Image preprocessor for Sudoku grid extraction.
Applies grayscale conversion, Gaussian smoothing, adaptive thresholding, and morphological operations.
"""
from typing import Tuple
import cv2
import numpy as np


class ImagePreprocessor:
    """Preprocesses input images for robust line and contour detection."""

    @staticmethod
    def preprocess_for_grid(image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Takes a BGR or Grayscale image.
        Returns:
            gray: Grayscale normalized image
            thresh: Inverted binary image with emphasized grid lines
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Gaussian blur to filter high-frequency noise
        blurred = cv2.GaussianBlur(gray, (9, 9), 0)

        # Adaptive thresholding: THRESH_BINARY_INV puts grid lines and digits as white (255) on black (0)
        thresh = cv2.adaptiveThreshold(
            blurred,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            11,
            2
        )

        return gray, thresh

    @staticmethod
    def clean_cell_image(cell_img: np.ndarray) -> np.ndarray:
        """
        Cleans an individual segmented cell image for digit recognition.
        Returns inverted binary image (digit white, background black).
        """
        if len(cell_img.shape) == 3:
            gray = cv2.cvtColor(cell_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = cell_img.copy()

        # Otsu thresholding or adaptive
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        return thresh

