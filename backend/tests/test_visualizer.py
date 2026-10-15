import numpy as np
from backend.vision.visualizer import SudokuVisualizer


def test_visualizer_render_overlay():
    recognized = [[0 for _ in range(9)] for _ in range(9)]
    recognized[0][0] = 5

    hint = {
        "row": 0,
        "col": 1,
        "display_coord": "R1C2",
        "value": 3,
        "strategy": "Naked Single",
        "explanation": "Test explanation",
        "highlight_cells": [{"row": 0, "col": 0}],
        "candidates": [3]
    }

    overlay = SudokuVisualizer.render_overlay(
        grid_size=450,
        recognized_grid=recognized,
        hint=hint
    )
    assert overlay.shape == (450, 450, 3)

    b64 = SudokuVisualizer.encode_image_base64(overlay)
    assert b64.startswith("data:image/png;base64,")


def test_visualizer_project_overlay():
    orig = np.full((500, 500, 3), 200, dtype=np.uint8)
    overlay = np.full((450, 450, 3), 255, dtype=np.uint8)
    corners = np.array([[20, 20], [470, 20], [470, 470], [20, 470]], dtype="float32")

    import cv2
    dst = np.array([[0, 0], [449, 0], [449, 449], [0, 449]], dtype="float32")
    inv_matrix = cv2.getPerspectiveTransform(dst, corners)

    projected = SudokuVisualizer.project_overlay_to_original(orig, overlay, inv_matrix, corners)
    assert projected.shape == (500, 500, 3)

