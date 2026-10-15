"""
Visual Highlighting and Grid Annotation.
Draws detected grids, solution overlays, and logical next-move highlights
both on the perspective-corrected grid and projected back onto the original photo.
"""
from typing import Optional, List, Dict, Any, Tuple
import base64
import cv2
import numpy as np


class SudokuVisualizer:
    """Renders overlays, hints, and solved states on Sudoku images."""

    @staticmethod
    def encode_image_base64(img: np.ndarray, format_ext: str = ".png") -> str:
        """Converts an OpenCV image to a base64 data URI."""
        success, encoded = cv2.imencode(format_ext, img)
        if not success:
            return ""
        b64_str = base64.b64encode(encoded.tobytes()).decode("utf-8")
        return f"data:image/png;base64,{b64_str}"

    @classmethod
    def highlight_grid_on_original(
        cls,
        original_img: np.ndarray,
        corners: np.ndarray,
        color: Tuple[int, int, int] = (0, 220, 100),
        thickness: int = 3
    ) -> np.ndarray:
        """Draws the detected quadrilateral boundary and corner markers on the original photo."""
        annotated = original_img.copy()
        pts = corners.astype(np.int32).reshape((-1, 1, 2))
        cv2.polylines(annotated, [pts], isClosed=True, color=color, thickness=thickness)

        # Draw corner circles
        for pt in pts:
            x, y = pt[0]
            cv2.circle(annotated, (x, y), 7, (0, 0, 255), -1)
            cv2.circle(annotated, (x, y), 9, (255, 255, 255), 2)

        return annotated

    @classmethod
    def render_overlay(
        cls,
        grid_size: int = 450,
        recognized_grid: Optional[List[List[int]]] = None,
        solved_grid: Optional[List[List[int]]] = None,
        hint: Optional[Dict[str, Any]] = None,
        base_warped: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Renders cell values and highlights onto a 450x450 warped canvas.
        If base_warped is provided, blends onto it; otherwise creates clean white canvas.
        """
        cell_size = grid_size // 9

        if base_warped is not None:
            if len(base_warped.shape) == 2:
                canvas = cv2.cvtColor(base_warped, cv2.COLOR_GRAY2BGR)
            else:
                canvas = base_warped.copy()
            if canvas.shape[0] != grid_size or canvas.shape[1] != grid_size:
                canvas = cv2.resize(canvas, (grid_size, grid_size))
        else:
            canvas = np.full((grid_size, grid_size, 3), 255, dtype=np.uint8)

        overlay = canvas.copy()

        # 1. Highlight peer cells if hint exists
        if hint and "highlight_cells" in hint:
            for peer in hint["highlight_cells"]:
                pr = peer["row"]
                pc = peer["col"]
                y1, y2 = pr * cell_size, (pr + 1) * cell_size
                x1, x2 = pc * cell_size, (pc + 1) * cell_size
                cv2.rectangle(overlay, (x1, y1), (x2, y2), (255, 220, 180), -1)

        # 2. Highlight target hint cell
        if hint:
            hr, hc = hint["row"], hint["col"]
            y1, y2 = hr * cell_size, (hr + 1) * cell_size
            x1, x2 = hc * cell_size, (hc + 1) * cell_size
            # Vibrant emerald/gold highlight
            cv2.rectangle(overlay, (x1, y1), (x2, y2), (100, 240, 100), -1)

        # Blend semi-transparent highlight with canvas
        alpha = 0.4
        cv2.addWeighted(overlay, alpha, canvas, 1 - alpha, 0, canvas)

        # 3. Draw target cell border if hint
        if hint:
            hr, hc = hint["row"], hint["col"]
            y1, y2 = hr * cell_size, (hr + 1) * cell_size
            x1, x2 = hc * cell_size, (hc + 1) * cell_size
            cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 180, 0), 3)

        # 4. Draw grid lines
        for i in range(10):
            th = 3 if i % 3 == 0 else 1
            color = (50, 50, 50) if i % 3 == 0 else (180, 180, 180)
            # horizontal
            cv2.line(canvas, (0, i * cell_size), (grid_size, i * cell_size), color, th)
            # vertical
            cv2.line(canvas, (i * cell_size, 0), (i * cell_size, grid_size), color, th)

        # 5. Draw digits
        font = cv2.FONT_HERSHEY_SIMPLEX
        for r in range(9):
            for c in range(9):
                is_hint_cell = (hint and hint["row"] == r and hint["col"] == c)
                orig_val = recognized_grid[r][c] if recognized_grid else 0

                val_to_draw = None
                color = (0, 0, 0)

                if orig_val > 0:
                    val_to_draw = orig_val
                    color = (20, 20, 20)  # Original clue (dark gray/black)
                elif is_hint_cell:
                    val_to_draw = hint["value"]
                    color = (0, 140, 0)  # Highlighted hint digit (vivid green)
                elif solved_grid and solved_grid[r][c] > 0:
                    val_to_draw = solved_grid[r][c]
                    color = (200, 70, 20)  # Solved digit (blue/indigo in BGR)

                if val_to_draw:
                    text = str(val_to_draw)
                    scale = 0.9 if is_hint_cell else 0.8
                    th = 2 if is_hint_cell else 2
                    (tw, th_val), base = cv2.getTextSize(text, font, scale, th)
                    tx = c * cell_size + (cell_size - tw) // 2
                    ty = r * cell_size + (cell_size + th_val) // 2
                    cv2.putText(canvas, text, (tx, ty), font, scale, color, th, cv2.LINE_AA)

        return canvas

    @classmethod
    def project_overlay_to_original(
        cls,
        original_img: np.ndarray,
        warped_overlay: np.ndarray,
        inv_matrix: np.ndarray,
        corners: np.ndarray
    ) -> np.ndarray:
        """
        Projects the warped overlay back onto the original photo's perspective.
        Blends cleanly onto the grid region.
        """
        h, w = original_img.shape[:2]
        unwarped = cv2.warpPerspective(warped_overlay, inv_matrix, (w, h), flags=cv2.INTER_LINEAR)

        # Create mask of the grid polygon
        mask = np.zeros((h, w), dtype=np.uint8)
        pts = corners.astype(np.int32).reshape((-1, 1, 2))
        cv2.fillPoly(mask, [pts], 255)

        # Blend unwarped overlay onto original inside mask
        annotated = original_img.copy()
        grid_roi = cv2.bitwise_and(annotated, annotated, mask=mask)
        unwarped_roi = cv2.bitwise_and(unwarped, unwarped, mask=mask)

        # Alpha blend within the grid area
        blended_roi = cv2.addWeighted(grid_roi, 0.25, unwarped_roi, 0.75, 0)

        # Insert back into original image
        inv_mask = cv2.bitwise_not(mask)
        bg = cv2.bitwise_and(annotated, annotated, mask=inv_mask)
        result = cv2.add(bg, cv2.bitwise_and(blended_roi, blended_roi, mask=mask))

        # Re-draw the boundary line for crisp look
        cv2.polylines(result, [pts], isClosed=True, color=(0, 220, 100), thickness=2)
        return result

