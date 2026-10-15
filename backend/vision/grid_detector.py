"""
Grid Detector for locating Sudoku boundaries in arbitrary images.
"""
from typing import Optional, Tuple
import cv2
import numpy as np


class GridDetector:
    """Detects the outer boundary polygon of the Sudoku grid."""

    @staticmethod
    def order_points(pts: np.ndarray) -> np.ndarray:
        """
        Orders coordinates: top-left, top-right, bottom-right, bottom-left.
        pts shape: (4, 2)
        """
        rect = np.zeros((4, 2), dtype="float32")

        # Sum of coords: top-left has smallest sum, bottom-right has largest sum
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]

        # Difference of coords (x - y): top-right has largest difference, bottom-left has smallest
        diff = np.diff(pts, axis=1).reshape(-1)
        # Note: diff = y - x or x - y. Let's use (x - y):
        # top-right: x is large, y is small => (x - y) is maximal
        # bottom-left: x is small, y is large => (x - y) is minimal
        x_minus_y = pts[:, 0] - pts[:, 1]
        rect[1] = pts[np.argmax(x_minus_y)]
        rect[3] = pts[np.argmin(x_minus_y)]

        return rect

    @classmethod
    def detect_grid(cls, thresh_image: np.ndarray, min_area_ratio: float = 0.05) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Finds the 4 corners of the Sudoku grid.
        Returns:
            corners: (4, 2) float32 ordered points [TL, TR, BR, BL], or None
            contour: The raw contour of the grid, or None
        """
        h, w = thresh_image.shape[:2]
        total_area = float(w * h)

        contours, _ = cv2.findContours(thresh_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            # Fallback: assume the entire image is the grid
            fallback_pts = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype="float32")
            return fallback_pts, None

        # Sort contours by area descending
        sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)

        for c in sorted_contours:
            area = cv2.contourArea(c)
            if area < (total_area * min_area_ratio):
                continue

            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)

            # If 4 points found and contour is convex
            if len(approx) == 4 and cv2.isContourConvex(approx):
                pts = approx.reshape(4, 2).astype("float32")
                ordered = cls.order_points(pts)
                return ordered, c

        # If no strictly 4-point polygon was matched, extract extreme corners of the largest contour
        largest = sorted_contours[0]
        if cv2.contourArea(largest) >= (total_area * min_area_ratio):
            hull = cv2.convexHull(largest)
            pts = hull.reshape(-1, 2).astype("float32")
            if len(pts) >= 4:
                ordered = cls.order_points(pts)
                return ordered, largest

        # Fallback to full image borders
        fallback_pts = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype="float32")
        return fallback_pts, None

