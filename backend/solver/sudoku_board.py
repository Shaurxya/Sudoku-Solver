"""
Sudoku Board representation, validation, and candidate management.
"""
from typing import List, Set, Tuple, Optional
import copy


class SudokuBoard:
    """Represents a 9x9 Sudoku board."""

    def __init__(self, grid: Optional[List[List[int]]] = None):
        """
        Initialize board.
        0 represents an empty cell, 1-9 represent clues/filled digits.
        """
        if grid is not None:
            if len(grid) != 9 or any(len(row) != 9 for row in grid):
                raise ValueError("Grid must be exactly 9x9")
            self.grid = [[int(cell) for cell in row] for row in grid]
        else:
            self.grid = [[0 for _ in range(9)] for _ in range(9)]

    def get(self, r: int, c: int) -> int:
        return self.grid[r][c]

    def set(self, r: int, c: int, val: int) -> None:
        if not (0 <= val <= 9):
            raise ValueError(f"Invalid digit {val}: must be between 0 and 9")
        self.grid[r][c] = val

    def is_empty(self, r: int, c: int) -> bool:
        return self.grid[r][c] == 0

    def is_valid_placement(self, r: int, c: int, val: int) -> bool:
        """Check if placing `val` at (r, c) violates Sudoku rules."""
        if val == 0:
            return True
        # Check row
        for col in range(9):
            if col != c and self.grid[r][col] == val:
                return False
        # Check col
        for row in range(9):
            if row != r and self.grid[row][c] == val:
                return False
        # Check 3x3 box
        box_r, box_c = 3 * (r // 3), 3 * (c // 3)
        for i in range(3):
            for j in range(3):
                curr_r, curr_c = box_r + i, box_c + j
                if (curr_r != r or curr_c != c) and self.grid[curr_r][curr_c] == val:
                    return False
        return True

    def validate_board(self) -> Tuple[bool, List[str]]:
        """
        Check if the current board state has any rule violations.
        Returns (is_valid, list_of_error_messages).
        """
        errors = []
        # Check rows
        for r in range(9):
            seen = {}
            for c in range(9):
                val = self.grid[r][c]
                if val != 0:
                    if val in seen:
                        errors.append(f"Duplicate {val} in row {r+1} (cols {seen[val]+1} and {c+1})")
                    else:
                        seen[val] = c

        # Check cols
        for c in range(9):
            seen = {}
            for r in range(9):
                val = self.grid[r][c]
                if val != 0:
                    if val in seen:
                        errors.append(f"Duplicate {val} in column {c+1} (rows {seen[val]+1} and {r+1})")
                    else:
                        seen[val] = r

        # Check 3x3 boxes
        for box_idx in range(9):
            box_r = (box_idx // 3) * 3
            box_c = (box_idx % 3) * 3
            seen = {}
            for i in range(3):
                for j in range(3):
                    r, c = box_r + i, box_c + j
                    val = self.grid[r][c]
                    if val != 0:
                        if val in seen:
                            errors.append(
                                f"Duplicate {val} in box {box_idx+1} at ({seen[val][0]+1},{seen[val][1]+1}) and ({r+1},{c+1})"
                            )
                        else:
                            seen[val] = (r, c)

        return (len(errors) == 0, errors)

    def get_candidates(self, r: int, c: int) -> Set[int]:
        """Return the set of valid numbers that can be placed at (r, c)."""
        if self.grid[r][c] != 0:
            return set()
        used = set()
        # Row and Col
        for i in range(9):
            used.add(self.grid[r][i])
            used.add(self.grid[i][c])
        # Box
        br, bc = 3 * (r // 3), 3 * (c // 3)
        for i in range(3):
            for j in range(3):
                used.add(self.grid[br + i][bc + j])
        return set(range(1, 10)) - used

    def get_all_candidates(self) -> List[List[List[int]]]:
        """Return 9x9 grid where each empty cell has a sorted list of candidate integers."""
        candidates = []
        for r in range(9):
            row_candidates = []
            for c in range(9):
                if self.grid[r][c] == 0:
                    row_candidates.append(sorted(list(self.get_candidates(r, c))))
                else:
                    row_candidates.append([])
            candidates.append(row_candidates)
        return candidates

    def is_complete(self) -> bool:
        """Check if board is completely filled without empty cells and valid."""
        for r in range(9):
            for c in range(9):
                if self.grid[r][c] == 0:
                    return False
        valid, _ = self.validate_board()
        return valid

    def copy(self) -> 'SudokuBoard':
        return SudokuBoard(copy.deepcopy(self.grid))

    def to_list(self) -> List[List[int]]:
        return copy.deepcopy(self.grid)

    @classmethod
    def from_string(cls, s: str) -> 'SudokuBoard':
        """Parse string of 81 digits (0 or . for empty)."""
        clean = [c for c in s if c.isdigit() or c == '.']
        if len(clean) != 81:
            raise ValueError("String representation must contain exactly 81 cells")
        grid = []
        for i in range(9):
            row = []
            for j in range(9):
                char = clean[i * 9 + j]
                row.append(0 if char == '.' else int(char))
            grid.append(row)
        return cls(grid)

