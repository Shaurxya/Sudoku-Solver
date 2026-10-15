"""
Logical Move Predictor and Hint Engine.
Finds human-understandable next moves with detailed explanations and step highlighting.
"""
from typing import Optional, Dict, Any, List, Set, Tuple
from .sudoku_board import SudokuBoard
from .solver import SudokuSolver


class LogicalHint:
    def __init__(
        self,
        row: int,
        col: int,
        value: int,
        strategy: str,
        explanation: str,
        highlight_cells: Optional[List[Tuple[int, int]]] = None,
        candidates: Optional[List[int]] = None,
    ):
        self.row = row
        self.col = col
        self.value = value
        self.strategy = strategy
        self.explanation = explanation
        self.highlight_cells = highlight_cells or []
        self.candidates = candidates or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "row": self.row,
            "col": self.col,
            "display_coord": f"R{self.row + 1}C{self.col + 1}",
            "value": self.value,
            "strategy": self.strategy,
            "explanation": self.explanation,
            "highlight_cells": [{"row": r, "col": c} for r, c in self.highlight_cells],
            "candidates": self.candidates,
        }


class SudokuLogicEngine:
    """Predicts next logical moves using standard human Sudoku strategies."""

    @classmethod
    def get_next_move(cls, board: SudokuBoard) -> Optional[LogicalHint]:
        """
        Find the next most logical move.
        Evaluation priority:
        1. Naked Single (sole candidate in cell)
        2. Hidden Single in Box
        3. Hidden Single in Row
        4. Hidden Single in Column
        5. Fallback to verified solver solution
        """
        valid, errors = board.validate_board()
        if not valid:
            return None

        # 1. Check Naked Single
        for r in range(9):
            for c in range(9):
                if board.is_empty(r, c):
                    cands = board.get_candidates(r, c)
                    if len(cands) == 1:
                        val = next(iter(cands))
                        # Identify peer cells that forced this single
                        peers = []
                        for i in range(9):
                            if i != c and board.get(r, i) != 0:
                                peers.append((r, i))
                            if i != r and board.get(i, c) != 0:
                                peers.append((i, c))
                        br, bc = 3 * (r // 3), 3 * (c // 3)
                        for i in range(3):
                            for j in range(3):
                                pr, pc = br + i, bc + j
                                if (pr != r or pc != c) and board.get(pr, pc) != 0:
                                    if (pr, pc) not in peers:
                                        peers.append((pr, pc))

                        other_digits = [d for d in range(1, 10) if d != val]
                        return LogicalHint(
                            row=r,
                            col=c,
                            value=val,
                            strategy="Naked Single",
                            explanation=(
                                f"Cell R{r+1}C{c+1} has only one possible candidate: {val}. "
                                f"All other digits (1-9 except {val}) appear in its row, column, or 3x3 box."
                            ),
                            highlight_cells=peers,
                            candidates=[val],
                        )

        # 2. Check Hidden Single in 3x3 Boxes
        for box_idx in range(9):
            br = (box_idx // 3) * 3
            bc = (box_idx % 3) * 3
            cells_in_box = [(br + i, bc + j) for i in range(3) for j in range(3)]
            
            for digit in range(1, 10):
                # If digit already in box, continue
                if any(board.get(r, c) == digit for r, c in cells_in_box):
                    continue
                
                possible_cells = [
                    (r, c) for (r, c) in cells_in_box
                    if board.is_empty(r, c) and digit in board.get_candidates(r, c)
                ]
                if len(possible_cells) == 1:
                    r, c = possible_cells[0]
                    # Cells in box as highlight
                    box_peers = [(pr, pc) for pr, pc in cells_in_box if (pr, pc) != (r, c)]
                    return LogicalHint(
                        row=r,
                        col=c,
                        value=digit,
                        strategy="Hidden Single (3x3 Box)",
                        explanation=(
                            f"In Box {box_idx+1}, the digit {digit} can only go in cell R{r+1}C{c+1}. "
                            f"Every other cell in this box cannot contain {digit} due to row or column constraints."
                        ),
                        highlight_cells=box_peers,
                        candidates=sorted(list(board.get_candidates(r, c))),
                    )

        # 3. Check Hidden Single in Rows
        for r in range(9):
            for digit in range(1, 10):
                if any(board.get(r, c) == digit for c in range(9)):
                    continue
                possible_cells = [
                    (r, c) for c in range(9)
                    if board.is_empty(r, c) and digit in board.get_candidates(r, c)
                ]
                if len(possible_cells) == 1:
                    r, c = possible_cells[0]
                    row_peers = [(r, pc) for pc in range(9) if pc != c]
                    return LogicalHint(
                        row=r,
                        col=c,
                        value=digit,
                        strategy="Hidden Single (Row)",
                        explanation=(
                            f"In Row {r+1}, the digit {digit} can only go in column {c+1} (cell R{r+1}C{c+1})."
                        ),
                        highlight_cells=row_peers,
                        candidates=sorted(list(board.get_candidates(r, c))),
                    )

        # 4. Check Hidden Single in Columns
        for c in range(9):
            for digit in range(1, 10):
                if any(board.get(r, c) == digit for r in range(9)):
                    continue
                possible_cells = [
                    (r, c) for r in range(9)
                    if board.is_empty(r, c) and digit in board.get_candidates(r, c)
                ]
                if len(possible_cells) == 1:
                    r, c = possible_cells[0]
                    col_peers = [(pr, c) for pr in range(9) if pr != r]
                    return LogicalHint(
                        row=r,
                        col=c,
                        value=digit,
                        strategy="Hidden Single (Column)",
                        explanation=(
                            f"In Column {c+1}, the digit {digit} can only go in row {r+1} (cell R{r+1}C{c+1})."
                        ),
                        highlight_cells=col_peers,
                        candidates=sorted(list(board.get_candidates(r, c))),
                    )

        # 5. Fallback: solve using solver to find a cell with fewest candidates
        solved = SudokuSolver.solve(board)
        if solved is not None:
            min_cands = 10
            best = None
            for r in range(9):
                for c in range(9):
                    if board.is_empty(r, c):
                        cands = board.get_candidates(r, c)
                        if len(cands) < min_cands and len(cands) > 0:
                            min_cands = len(cands)
                            best = (r, c, cands)
            if best:
                r, c, cands = best
                sol_val = solved.get(r, c)
                return LogicalHint(
                    row=r,
                    col=c,
                    value=sol_val,
                    strategy="Advanced Constraint Deduction",
                    explanation=(
                        f"Advanced deduction determines that cell R{r+1}C{c+1} must be {sol_val} "
                        f"to lead to a valid overall solution."
                    ),
                    highlight_cells=[(r, c)],
                    candidates=sorted(list(cands)),
                )

        return None

