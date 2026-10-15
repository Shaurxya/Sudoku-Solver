from backend.vision.pipeline import SudokuPipeline
from backend.tests.synthetic_sudoku import generate_synthetic_sudoku_image


def test_end_to_end_pipeline():
    # Puzzle grid with distinct clues
    grid = [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9],
    ]

    img, _ = generate_synthetic_sudoku_image(grid, image_size=450, margin=30)

    pipeline = SudokuPipeline()
    result = pipeline.process_image(img)

    assert result["success"] is True
    assert "grid" in result
    assert "is_valid" in result
    assert "images" in result
    assert "original_annotated" in result["images"]
    assert "warped_annotated" in result["images"]
    assert result["images"]["original_annotated"].startswith("data:image/png;base64,")
    assert result["images"]["warped_annotated"].startswith("data:image/png;base64,")

    # If valid and solvable, next_move hint should be produced
    if result["is_solvable"]:
        assert result["next_move"] is not None
        assert "strategy" in result["next_move"]
        assert "explanation" in result["next_move"]
