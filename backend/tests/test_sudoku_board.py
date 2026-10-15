import pytest
from backend.solver.sudoku_board import SudokuBoard


def test_board_initialization():
    board = SudokuBoard()
    for r in range(9):
        for c in range(9):
            assert board.get(r, c) == 0
            assert board.is_empty(r, c)


def test_board_set_and_get():
    board = SudokuBoard()
    board.set(0, 0, 5)
    assert board.get(0, 0) == 5
    assert not board.is_empty(0, 0)

    with pytest.raises(ValueError):
        board.set(0, 0, 10)


def test_board_validation_valid():
    # Valid sample
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
    board = SudokuBoard(grid)
    valid, errors = board.validate_board()
    assert valid is True
    assert len(errors) == 0


def test_board_validation_duplicate_row():
    board = SudokuBoard()
    board.set(0, 0, 5)
    board.set(0, 8, 5)
    valid, errors = board.validate_board()
    assert valid is False
    assert any("row 1" in e for e in errors)


def test_board_validation_duplicate_col():
    board = SudokuBoard()
    board.set(0, 0, 5)
    board.set(8, 0, 5)
    valid, errors = board.validate_board()
    assert valid is False
    assert any("column 1" in e for e in errors)


def test_board_validation_duplicate_box():
    board = SudokuBoard()
    board.set(0, 0, 5)
    board.set(2, 2, 5)
    valid, errors = board.validate_board()
    assert valid is False
    assert any("box 1" in e for e in errors)


def test_board_candidates():
    grid = [
        [1, 2, 3, 4, 5, 6, 7, 8, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    board = SudokuBoard(grid)
    cands = board.get_candidates(0, 8)
    assert cands == {9}

