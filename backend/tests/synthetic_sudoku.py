"""
Synthetic Sudoku image generator for deterministic testing.
Renders clean or perspectively transformed Sudoku boards with digits.
"""
from typing import List, Tuple
import cv2
import numpy as np


def generate_synthetic_sudoku_image(
    grid: List[List[int]],
    image_size: int = 450,
    with_perspective: bool = False,
    margin: int = 30
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Renders a synthetic Sudoku image.
    Returns:
        image: BGR image (original or with perspective distortion)
        corners: Expected 4 corners (TL, TR, BR, BL)
    """
    canvas_size = image_size + 2 * margin
    canvas = np.full((canvas_size, canvas_size, 3), 255, dtype=np.uint8)

    cell_size = image_size // 9
    start_x = margin
    start_y = margin

    # Draw outer border
    cv2.rectangle(
        canvas,
        (start_x, start_y),
        (start_x + 9 * cell_size, start_y + 9 * cell_size),
        (0, 0, 0),
        4
    )

    # Draw grid lines
    for i in range(10):
        th = 4 if i % 3 == 0 else 1
        # Horizontal
        cv2.line(
            canvas,
            (start_x, start_y + i * cell_size),
            (start_x + 9 * cell_size, start_y + i * cell_size),
            (0, 0, 0),
            th
        )
        # Vertical
        cv2.line(
            canvas,
            (start_x + i * cell_size, start_y),
            (start_x + i * cell_size, start_y + 9 * cell_size),
            (0, 0, 0),
            th
        )

    # Draw digits
    font = cv2.FONT_HERSHEY_SIMPLEX
    for r in range(9):
        for c in range(9):
            val = grid[r][c]
            if val != 0:
                text = str(val)
                (tw, th), _ = cv2.getTextSize(text, font, 0.9, 2)
                tx = start_x + c * cell_size + (cell_size - tw) // 2
                ty = start_y + r * cell_size + (cell_size + th) // 2
                cv2.putText(canvas, text, (tx, ty), font, 0.9, (0, 0, 0), 2, cv2.LINE_AA)

    corners = np.array([
        [start_x, start_y],
        [start_x + 9 * cell_size, start_y],
        [start_x + 9 * cell_size, start_y + 9 * cell_size],
        [start_x, start_y + 9 * cell_size]
    ], dtype="float32")

    if not with_perspective:
        return canvas, corners

    # Apply perspective tilt
    src = corners.copy()
    dst = np.array([
        [start_x + 20, start_y + 25],
        [start_x + 9 * cell_size - 15, start_y + 10],
        [start_x + 9 * cell_size - 30, start_y + 9 * cell_size - 20],
        [start_x + 35, start_y + 9 * cell_size - 10]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(canvas, M, (canvas_size, canvas_size), borderValue=(240, 240, 240))
    return warped, dst

