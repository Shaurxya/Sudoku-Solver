"""
End-to-End SudokuVision Pipeline.
Coordinates:
Sudoku image → grid detection → perspective correction → cell segmentation →
digit recognition → Sudoku reconstruction → logical move prediction → visual highlighting.
"""
from typing import Dict, Any, Optional
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

        # 5. Digit Recognition & 6. Reconstruction
        reconstructed_grid = [[0 for _ in range(9)] for _ in range(9)]
        confidences = [[1.0 for _ in range(9)] for _ in range(9)]

        for r in range(9):
            for c in range(9):
                is_empty, digit_img, _ = grid_cells[r][c]
                if is_empty or digit_img is None:
                    reconstructed_grid[r][c] = 0
                    confidences[r][c] = 1.0
                else:
                    digit, conf = self.recognizer.predict(digit_img)
                    reconstructed_grid[r][c] = digit
                    confidences[r][c] = round(conf, 3)

        # 7. Board Representation & Validation
        board = SudokuBoard(reconstructed_grid)
        is_valid, validation_errors = board.validate_board()

        # 8. Logical Move Prediction & Solution
        hint_dict = None
        solved_grid = None
        is_solvable = False

        if is_valid:
            # Check solvability
            solved_board = SudokuSolver.solve(board)
            if solved_board is not None:
                is_solvable = True
                solved_grid = solved_board.to_list()
                hint = SudokuLogicEngine.get_next_move(board)
                if hint:
                    hint_dict = hint.to_dict()

        # 9. Visual Highlighting
        # Warped visualization with hint overlay
        warped_vis = self.visualizer.render_overlay(
            grid_size=450,
            recognized_grid=reconstructed_grid,
            solved_grid=None,
            hint=hint_dict,
            base_warped=warped
        )

        # Highlighting on original image
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

