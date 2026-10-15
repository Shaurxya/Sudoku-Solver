from backend.solver.sudoku_board import SudokuBoard
from backend.solver.logic_engine import SudokuLogicEngine


def test_naked_single_detection():
    # Board where cell (0, 8) has only 9 as candidate
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
    hint = SudokuLogicEngine.get_next_move(board)
    assert hint is not None
    assert hint.row == 0
    assert hint.col == 8
    assert hint.value == 9
    assert hint.strategy == "Naked Single"
    assert "Naked Single" in hint.strategy
    assert len(hint.explanation) > 10

    d = hint.to_dict()
    assert d["row"] == 0
    assert d["col"] == 8
    assert d["display_coord"] == "R1C9"
    assert d["value"] == 9


def test_hidden_single_in_box():
    # Standard classic puzzle where hidden single or naked single is found
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
    hint = SudokuLogicEngine.get_next_move(board)
    assert hint is not None
    assert 0 <= hint.row < 9
    assert 0 <= hint.col < 9
    assert 1 <= hint.value <= 9
    assert board.is_empty(hint.row, hint.col)

