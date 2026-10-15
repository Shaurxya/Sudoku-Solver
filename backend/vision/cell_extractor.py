"""
Cell segmentation and extraction from warped Sudoku grid.
Divides grid into 81 cells, cleans margins, and isolates digit bounding boxes.
"""
from typing import List, Tuple, Optional
import cv2
import numpy as np


class CellExtractor:
    """Segments a 9x9 Sudoku grid into 81 cell images and isolates digits."""

    def __init__(self, grid_size: int = 450, margin_pct: float = 0.12, target_digit_size: int = 28):
        self.grid_size = grid_size
        self.cell_size = grid_size // 9
        self.margin = int(self.cell_size * margin_pct)
        self.target_digit_size = target_digit_size

    def extract_cells(self, warped_image: np.ndarray) -> List[List[Tuple[bool, Optional[np.ndarray], np.ndarray]]]:
        """
        Segments the warped grid into 9x9 cells.
        Returns a 9x9 list of tuples: (is_empty, normalized_digit_image, raw_cell_roi).
        """
        if len(warped_image.shape) == 3:
            gray = cv2.cvtColor(warped_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = warped_image.copy()

        # Resize warped image if not strictly matching grid_size
        if gray.shape[0] != self.grid_size or gray.shape[1] != self.grid_size:
            gray = cv2.resize(gray, (self.grid_size, self.grid_size))

        grid_cells = []

        for r in range(9):
            row_cells = []
            for c in range(9):
                y1 = r * self.cell_size
                y2 = (r + 1) * self.cell_size
                x1 = c * self.cell_size
                x2 = (c + 1) * self.cell_size

                raw_cell = gray[y1:y2, x1:x2]

                # Trim inner margin to remove outer grid lines
                trimmed = raw_cell[self.margin : self.cell_size - self.margin, self.margin : self.cell_size - self.margin]

                is_empty, digit_img = self._isolate_digit(trimmed)
                row_cells.append((is_empty, digit_img, raw_cell))
            grid_cells.append(row_cells)

        return grid_cells

    def _isolate_digit(self, trimmed_cell: np.ndarray) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Detects if trimmed cell contains a digit and centers it into (target_digit_size, target_digit_size).
        """
        h, w = trimmed_cell.shape[:2]
        total_pixels = h * w

        # Otsu thresholding with THRESH_BINARY_INV (digit is white 255, background black 0)
        blur = cv2.GaussianBlur(trimmed_cell, (3, 3), 0)
        thresh = cv2.adaptiveThreshold(
            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )

        # Clear any noise touching the extreme borders
        thresh[0, :] = 0
        thresh[-1, :] = 0
        thresh[:, 0] = 0
        thresh[:, -1] = 0

        # Check total white pixel count
        white_count = cv2.countNonZero(thresh)
        if white_count < 25 or (white_count / float(total_pixels)) < 0.025:
            return True, None

        # Find contours of digit
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return True, None

        # Filter contours by height, width, and area
        valid_contours = []
        for cnt in contours:
            cx, cy, cw, ch = cv2.boundingRect(cnt)
            area = cv2.contourArea(cnt)
            # Digit components should have reasonable size and not be tiny specks
            if ch >= 10 and cw >= 4 and area >= 20:
                valid_contours.append((cnt, cx, cy, cw, ch))

        if not valid_contours:
            return True, None

        # Combine bounding boxes of valid contours
        min_x = min(cx for _, cx, cy, cw, ch in valid_contours)
        min_y = min(cy for _, cx, cy, cw, ch in valid_contours)
        max_x = max(cx + cw for _, cx, cy, cw, ch in valid_contours)
        max_y = max(cy + ch for _, cx, cy, cw, ch in valid_contours)

        digit_w = max_x - min_x
        digit_h = max_y - min_y

        # If bounding box is too tiny or spans almost entire cell (border artifact)
        if digit_h < 12 or digit_w < 5 or digit_h > (h * 0.95) or digit_w > (w * 0.95):
            return True, None

        digit_crop = thresh[min_y:max_y, min_x:max_x]

        # Place into a square padded canvas and resize to target_digit_size x target_digit_size
        max_dim = max(digit_w, digit_h)
        # Pad with 4 pixels on each side for centering
        pad_size = max_dim + 8
        padded = np.zeros((pad_size, pad_size), dtype=np.uint8)

        offset_x = (pad_size - digit_w) // 2
        offset_y = (pad_size - digit_h) // 2
        padded[offset_y : offset_y + digit_h, offset_x : offset_x + digit_w] = digit_crop

        normalized = cv2.resize(padded, (self.target_digit_size, self.target_digit_size), interpolation=cv2.INTER_AREA)

        # Normalize values to [0, 255] binary
        _, normalized = cv2.threshold(normalized, 50, 255, cv2.THRESH_BINARY)

        return False, normalized

