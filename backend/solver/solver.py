"""
Sudoku Backtracking Solver with MRV (Minimum Remaining Values) heuristic.
"""
from typing import Optional, List, Tuple
from .sudoku_board import SudokuBoard


class SudokuSolver:
    """Solves Sudoku puzzles efficiently and verifies solution uniqueness."""

    @staticmethod
    def solve(board: SudokuBoard) -> Optional[SudokuBoard]:
        """
        Solve the given SudokuBoard using backtracking with MRV heuristic.
        Returns a new solved SudokuBoard, or None if unsolvable.
        """
        valid, _ = board.validate_board()
        if not valid:
            return None

        solved_grid = [row[:] for row in board.grid]

        def find_best_cell() -> Optional[Tuple[int, int, List[int]]]:
            min_candidates = 10
            best = None
            for r in range(9):
                for c in range(9):
                    if solved_grid[r][c] == 0:
                        # find candidates
                        used = set()
                        for i in range(9):
                            used.add(solved_grid[r][i])
                            used.add(solved_grid[i][c])
                        br, bc = 3 * (r // 3), 3 * (c // 3)
                        for i in range(3):
                            for j in range(3):
                                used.add(solved_grid[br + i][bc + j])
                        candidates = [val for val in range(1, 10) if val not in used]
                        if len(candidates) == 0:
                            return None  # Dead end immediately
                        if len(candidates) < min_candidates:
                            min_candidates = len(candidates)
                            best = (r, c, candidates)
                            if min_candidates == 1:
                                return best
            return best

        def backtrack() -> bool:
            best = find_best_cell()
            if best is None:
                # Either board is full or dead end occurred
                # Check if any empty cell remains
                for r in range(9):
                    for c in range(9):
                        if solved_grid[r][c] == 0:
                            return False
                return True

            r, c, candidates = best
            for val in candidates:
                solved_grid[r][c] = val
                if backtrack():
                    return True
                solved_grid[r][c] = 0
            return False

        if backtrack():
            return SudokuBoard(solved_grid)
        return None

    @staticmethod
    def count_solutions(board: SudokuBoard, max_count: int = 2) -> int:
        """
        Count solutions up to max_count (useful to verify unique solution).
        """
        valid, _ = board.validate_board()
        if not valid:
            return 0

        solved_grid = [row[:] for row in board.grid]
        count = 0

        def find_best_cell():
            min_candidates = 10
            best = None
            for r in range(9):
                for c in range(9):
                    if solved_grid[r][c] == 0:
                        used = set()
                        for i in range(9):
                            used.add(solved_grid[r][i])
                            used.add(solved_grid[i][c])
                        br, bc = 3 * (r // 3), 3 * (c // 3)
                        for i in range(3):
                            for j in range(3):
                                used.add(solved_grid[br + i][bc + j])
                        candidates = [val for val in range(1, 10) if val not in used]
                        if len(candidates) == 0:
                            return None
                        if len(candidates) < min_candidates:
                            min_candidates = len(candidates)
                            best = (r, c, candidates)
                            if min_candidates == 1:
                                return best
            return best

        def backtrack():
            nonlocal count
            if count >= max_count:
                return
            best = find_best_cell()
            if best is None:
                for r in range(9):
                    for c in range(9):
                        if solved_grid[r][c] == 0:
                            return
                count += 1
                return

            r, c, candidates = best
            for val in candidates:
                solved_grid[r][c] = val
                backtrack()
                solved_grid[r][c] = 0
                if count >= max_count:
                    return

        backtrack()
        return count

