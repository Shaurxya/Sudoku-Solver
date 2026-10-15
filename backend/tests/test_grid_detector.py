import numpy as np
from backend.vision.preprocessor import ImagePreprocessor
from backend.vision.grid_detector import GridDetector
from backend.tests.synthetic_sudoku import generate_synthetic_sudoku_image


def test_grid_detection_clean():
    sample_grid = [[0 for _ in range(9)] for _ in range(9)]
    sample_grid[0][0] = 5
    sample_grid[4][4] = 9

    img, expected_corners = generate_synthetic_sudoku_image(sample_grid, image_size=450, margin=30)
    _, thresh = ImagePreprocessor.preprocess_for_grid(img)

    detected_corners, _ = GridDetector.detect_grid(thresh)
    assert detected_corners is not None
    assert detected_corners.shape == (4, 2)

    # Corners should be within 5 pixels of expected
    diff = np.abs(detected_corners - expected_corners)
    assert np.max(diff) < 10


def test_corner_ordering():
    # Unordered corners
    raw_corners = np.array([
        [400, 400], # BR
        [10, 10],   # TL
        [400, 10],  # TR
        [10, 400]   # BL
    ], dtype="float32")

    ordered = GridDetector.order_points(raw_corners)
    assert np.allclose(ordered[0], [10, 10])   # TL
    assert np.allclose(ordered[1], [400, 10])  # TR
    assert np.allclose(ordered[2], [400, 400]) # BR
    assert np.allclose(ordered[3], [10, 400])  # BL
