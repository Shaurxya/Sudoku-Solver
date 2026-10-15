import numpy as np
from backend.vision.perspective import PerspectiveTransformer
from backend.vision.cell_extractor import CellExtractor
from backend.tests.synthetic_sudoku import generate_synthetic_sudoku_image


def test_perspective_warp():
    grid = [[0 for _ in range(9)] for _ in range(9)]
    img, corners = generate_synthetic_sudoku_image(grid, image_size=450, with_perspective=True)

    transformer = PerspectiveTransformer(output_size=450)
    warped, matrix, inv_matrix = transformer.warp(img, corners)

    assert warped.shape == (450, 450, 3)
    assert matrix.shape == (3, 3)
    assert inv_matrix.shape == (3, 3)


def test_cell_segmentation():
    grid = [[0 for _ in range(9)] for _ in range(9)]
    grid[0][0] = 5
    grid[1][1] = 7

    img, corners = generate_synthetic_sudoku_image(grid, image_size=450, margin=0)
    extractor = CellExtractor(grid_size=450)
    cells = extractor.extract_cells(img)

    assert len(cells) == 9
    assert len(cells[0]) == 9

    # Cell (0, 0) should not be empty
    is_empty_00, digit_img_00, _ = cells[0][0]
    assert not is_empty_00
    assert digit_img_00 is not None
    assert digit_img_00.shape == (28, 28)

    # Cell (0, 1) should be empty
    is_empty_01, digit_img_01, _ = cells[0][1]
    assert is_empty_01
    assert digit_img_01 is None
