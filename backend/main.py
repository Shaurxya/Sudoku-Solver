"""
FastAPI application for SudokuVision backend.
Provides endpoints for scanning, validation, logical move prediction, and solving.
"""
from typing import List, Optional, Dict, Any
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .vision.pipeline import SudokuPipeline
from .solver.sudoku_board import SudokuBoard
from .solver.solver import SudokuSolver
from .solver.logic_engine import SudokuLogicEngine
from .vision.visualizer import SudokuVisualizer

app = FastAPI(
    title="SudokuVision API",
    description="Computer Vision & AI-Powered Logical Sudoku Solver API",
    version="1.0.0"
)

import os
from fastapi.staticfiles import StaticFiles

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy pipeline singleton
pipeline_instance: Optional[SudokuPipeline] = None


def get_pipeline() -> SudokuPipeline:
    global pipeline_instance
    if pipeline_instance is None:
        pipeline_instance = SudokuPipeline()
    return pipeline_instance


# Pydantic schemas
class GridRequest(BaseModel):
    grid: List[List[int]] = Field(..., description="9x9 Sudoku grid (0 for empty, 1-9 for clues)")


class ValidateResponse(BaseModel):
    is_valid: bool
    errors: List[str]
    is_complete: bool
    is_solvable: bool


class HintResponse(BaseModel):
    success: bool
    hint: Optional[Dict[str, Any]]
    is_complete: bool
    message: Optional[str] = None
    overlay_image: Optional[str] = None


class SolveResponse(BaseModel):
    success: bool
    solved_grid: Optional[List[List[int]]]
    message: Optional[str] = None


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "SudokuVision"}


@app.get("/api/samples")
def get_sample_images():
    """Returns bundled sample puzzle images with base64 data URIs for quick 1-click testing."""
    samples_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples")
    items = []
    if os.path.exists(samples_dir):
        for fname in sorted(os.listdir(samples_dir)):
            if fname.endswith(".png"):
                fpath = os.path.join(samples_dir, fname)
                img = cv2.imread(fpath)
                if img is not None:
                    b64 = SudokuVisualizer.encode_image_base64(img)
                    label = fname.replace("sample_", "").replace(".png", "").capitalize()
                    items.append({
                        "name": fname,
                        "label": label,
                        "image": b64
                    })
    return {"samples": items}


@app.post("/api/candidates")
def get_board_candidates(req: GridRequest):
    """Returns 9x9 matrix of candidate numbers for empty cells."""
    try:
        board = SudokuBoard(req.grid)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"candidates": board.get_all_candidates()}


@app.post("/api/scan")
async def scan_sudoku_image(file: UploadFile = File(...)):
    """
    Accepts an uploaded image of a Sudoku puzzle.
    Executes full pipeline:
    grid detection -> perspective warp -> cell segmentation -> digit recognition ->
    reconstruction -> logical move prediction -> visual highlighting.
    """
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="Could not decode uploaded image.")

        pipeline = get_pipeline()
        result = pipeline.process_image(img)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/validate", response_model=ValidateResponse)
def validate_grid(req: GridRequest):
    """Validates 9x9 grid consistency according to Sudoku rules."""
    try:
        board = SudokuBoard(req.grid)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    is_valid, errors = board.validate_board()
    is_solvable = False
    if is_valid:
        solved = SudokuSolver.solve(board)
        is_solvable = solved is not None

    return {
        "is_valid": is_valid,
        "errors": errors,
        "is_complete": board.is_complete(),
        "is_solvable": is_solvable
    }


@app.post("/api/hint", response_model=HintResponse)
def get_next_logical_move(req: GridRequest):
    """Predicts next logical human move with detailed explanation."""
    try:
        board = SudokuBoard(req.grid)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    is_valid, errors = board.validate_board()
    if not is_valid:
        return {
            "success": False,
            "hint": None,
            "is_complete": False,
            "message": f"Board contains rule conflicts: {'; '.join(errors)}"
        }

    if board.is_complete():
        return {
            "success": True,
            "hint": None,
            "is_complete": True,
            "message": "Sudoku puzzle is already completely and correctly solved!"
        }

    hint = SudokuLogicEngine.get_next_move(board)
    if not hint:
        return {
            "success": False,
            "hint": None,
            "is_complete": False,
            "message": "No logical move or solution found. Please check board numbers."
        }

    hint_dict = hint.to_dict()

    # Generate visual hint overlay
    vis_canvas = SudokuVisualizer.render_overlay(
        grid_size=450,
        recognized_grid=req.grid,
        hint=hint_dict
    )
    overlay_b64 = SudokuVisualizer.encode_image_base64(vis_canvas)

    return {
        "success": True,
        "hint": hint_dict,
        "is_complete": False,
        "message": "Next logical move calculated successfully.",
        "overlay_image": overlay_b64
    }


@app.post("/api/solve", response_model=SolveResponse)
def solve_grid(req: GridRequest):
    """Solves the entire Sudoku puzzle using backtracking."""
    try:
        board = SudokuBoard(req.grid)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    solved = SudokuSolver.solve(board)
    if solved is None:
        return {
            "success": False,
            "solved_grid": None,
            "message": "Sudoku puzzle has no valid solution."
        }

    return {
        "success": True,
        "solved_grid": solved.to_list(),
        "message": "Sudoku solved successfully."
    }


# Mount built React frontend if present
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")


