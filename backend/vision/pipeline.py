"""
End-to-End SudokuVision Pipeline.
Coordinates:
Sudoku image → grid detection → perspective correction → cell segmentation →
digit recognition → constraint-aware Sudoku reconstruction → logical move prediction → visual highlighting.
"""
from typing import Dict, Any, Optional, List, Tuple
import cv2
import numpy as np

from .preprocessor import ImagePreprocessor
from .grid_detector import GridDetector
from .perspective import PerspectiveTransformer
from .cell_extractor import CellExtractor
from .digit_recognizer import DigitRecognizer
from .visualizer import SudokuVisualizer
from ..solver.sudoku_board import SudokuBoard
from ..solver.solver import SudokuSolver
from ..solver.logic_engine import SudokuLogicEngine


class SudokuPipeline:
    """End-to-end vision and reasoning coordinator."""

    def __init__(self, recognizer: Optional[DigitRecognizer] = None):
        self.preprocessor = ImagePreprocessor()
        self.grid_detector = GridDetector()
        self.transformer = PerspectiveTransformer(output_size=450)
        self.cell_extractor = CellExtractor(grid_size=450)
        self.recognizer = recognizer or DigitRecognizer()
        self.visualizer = SudokuVisualizer()

    def _resolve_grid(
        self,
        ranked_choices: List[List[List[Tuple[int, float]]]]
    ) -> Tuple[List[List[int]], List[List[float]]]:
        """
        Takes ranked OCR candidate predictions per cell.
        Uses Sudoku constraint verification to resolve any OCR conflicts into a valid, solvable board.
        """
        # Top choice grid
        grid = [[ranked_choices[r][c][0][0] for c in range(9)] for r in range(9)]
        confs = [[ranked_choices[r][c][0][1] for c in range(9)] for r in range(9)]

        board = SudokuBoard(grid)
        is_valid, _ = board.validate_board()
        if is_valid and SudokuSolver.solve(board) is not None:
            return grid, confs

        # If conflicts exist, search for consistent candidate combination
        def backtrack(state, r=0, c=0):
            if r == 9:
                b = SudokuBoard(state)
                val, _ = b.validate_board()
                if val and SudokuSolver.solve(b) is not None:
                    return True, [row[:] for row in state]
                return False, None

            next_r = r if c < 8 else r + 1
            next_c = c + 1 if c < 8 else 0

            options = ranked_choices[r][c]
            for d, _ in options:
                if d == 0:
                    state[r][c] = 0
                    ok, res = backtrack(state, next_r, next_c)
                    if ok:
                        return True, res
                else:
                    # Check duplicate conflict in row, col, or box
                    conflict = False
                    for i in range(9):
                        if (i != c and state[r][i] == d) or (i != r and state[i][c] == d):
                            conflict = True
                            break
                    if not conflict:
                        br, bc = 3 * (r // 3), 3 * (c // 3)
                        for i in range(3):
                            for j in range(3):
                                if (br + i != r or bc + j != c) and state[br + i][bc + j] == d:
                                    conflict = True
                                    break
                    if not conflict:
                        state[r][c] = d
                        ok, res = backtrack(state, next_r, next_c)
                        if ok:
                            return True, res
                        state[r][c] = 0
            return False, None

        ok, resolved = backtrack([[0] * 9 for _ in range(9)])
        if ok and resolved:
            # Update confidences for resolved choices
            res_confs = [[1.0 for _ in range(9)] for _ in range(9)]
            for r in range(9):
                for c in range(9):
                    for d, prob in ranked_choices[r][c]:
                        if d == resolved[r][c]:
                            res_confs[r][c] = round(prob, 3)
                            break
            return resolved, res_confs

        # Fallback to top choice
        return grid, confs

    def process_image(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Executes the complete SudokuVision pipeline on an input image.
        """
        # Ensure BGR
        if len(image.shape) == 2:
            image_bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else:
            image_bgr = image.copy()

        # 1. Preprocess
        gray, thresh = self.preprocessor.preprocess_for_grid(image_bgr)

        # 2. Grid Detection
        corners, contour = self.grid_detector.detect_grid(thresh)
        if corners is None:
            raise ValueError("Could not detect Sudoku grid in the image.")

        # 3. Perspective Warp
        warped, matrix, inv_matrix = self.transformer.warp(image_bgr, corners)

        # 4. Cell Segmentation
        grid_cells = self.cell_extractor.extract_cells(warped)

        # 5. Digit Recognition with Ranked Probabilities
        ranked_choices: List[List[List[Tuple[int, float]]]] = []

        for r in range(9):
            row_choices = []
            for c in range(9):
                is_empty, digit_img, _ = grid_cells[r][c]
                if is_empty or digit_img is None:
                    row_choices.append([(0, 1.0)])
                else:
                    ranked = self.recognizer.predict_ranked(digit_img, top_k=3)
                    # Filter candidates with reasonable probability
                    filtered = [(d, p) for d, p in ranked if p >= 0.05]
                    if not filtered:
                        filtered = [ranked[0]]
                    row_choices.append(filtered)
            ranked_choices.append(row_choices)

        # 6. Constraint-Aware Sudoku Reconstruction
        reconstructed_grid, confidences = self._resolve_grid(ranked_choices)

        # 7. Board Representation & Validation
        board = SudokuBoard(reconstructed_grid)
        is_valid, validation_errors = board.validate_board()

        # 8. Logical Move Prediction & Solution
        hint_dict = None
        solved_grid = None
        is_solvable = False

        if is_valid:
            solved_board = SudokuSolver.solve(board)
            if solved_board is not None:
                is_solvable = True
                solved_grid = solved_board.to_list()
                hint = SudokuLogicEngine.get_next_move(board)
                if hint:
                    hint_dict = hint.to_dict()

        # 9. Visual Highlighting
        warped_vis = self.visualizer.render_overlay(
            grid_size=450,
            recognized_grid=reconstructed_grid,
            solved_grid=None,
            hint=hint_dict,
            base_warped=warped
        )

        # Highlighting projected back onto original photo perspective
        annotated_original = self.visualizer.project_overlay_to_original(
            image_bgr,
            warped_vis,
            inv_matrix,
            corners
        )

        return {
            "success": True,
            "grid": reconstructed_grid,
            "confidences": confidences,
            "is_valid": is_valid,
            "validation_errors": validation_errors,
            "is_solvable": is_solvable,
            "solved_grid": solved_grid,
            "next_move": hint_dict,
            "corners": corners.tolist(),
            "images": {
                "original_annotated": self.visualizer.encode_image_base64(annotated_original),
                "warped_annotated": self.visualizer.encode_image_base64(warped_vis),
            }
        }
