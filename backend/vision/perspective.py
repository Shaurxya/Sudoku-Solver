"""
Perspective correction and inverse transformation for Sudoku images.
"""
from typing import Tuple
import cv2
import numpy as np


class PerspectiveTransformer:
    """Handles perspective warping and unwarping of grids."""

    def __init__(self, output_size: int = 450):
        self.output_size = output_size

    def get_matrices(self, corners: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculates forward perspective matrix (original -> square grid)
        and inverse perspective matrix (square grid -> original).
        corners: (4, 2) ordered float32 points [TL, TR, BR, BL].
        """
        dst = np.array([
            [0, 0],
            [self.output_size - 1, 0],
            [self.output_size - 1, self.output_size - 1],
            [0, self.output_size - 1]
        ], dtype="float32")

        matrix = cv2.getPerspectiveTransform(corners, dst)
        inv_matrix = cv2.getPerspectiveTransform(dst, corners)
        return matrix, inv_matrix

    def warp(self, image: np.ndarray, corners: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Warps input image into a canonical square top-down view.
        Returns:
            warped: (output_size, output_size, C) or (output_size, output_size)
            matrix: 3x3 forward transformation matrix
            inv_matrix: 3x3 inverse transformation matrix
        """
        matrix, inv_matrix = self.get_matrices(corners)
        warped = cv2.warpPerspective(
            image,
            matrix,
            (self.output_size, self.output_size),
            flags=cv2.INTER_LINEAR
        )
        return warped, matrix, inv_matrix

    @staticmethod
    def unwarp(overlay: np.ndarray, inv_matrix: np.ndarray, target_shape: Tuple[int, int]) -> np.ndarray:
        """
        Transforms a warped overlay image back into original image perspective.
        target_shape: (height, width)
        """
        h, w = target_shape
        unwarped = cv2.warpPerspective(
            overlay,
            inv_matrix,
            (w, h),
            flags=cv2.INTER_LINEAR
        )
        return unwarped

