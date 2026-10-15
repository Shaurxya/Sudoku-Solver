# SudokuVision 🔢✨

**SudokuVision** is an end-to-end Computer Vision and AI-assisted Sudoku application. It accepts photos of Sudoku puzzles (even skewed, tilted, or taken at an angle), automatically extracts and segments the grid, recognizes the printed digits, reconstructs the board state, predicts the next logical move with human-readable reasoning, and overlays visual highlights directly onto the image.

---

## 🌟 Key Features

1. **Complete Computer Vision Pipeline**:
   - **Image Preprocessing**: Grayscale conversion, Gaussian noise filtering, and adaptive thresholding.
   - **Grid Detection**: Contour polygon approximation and 4-corner quad detection with convex hull fallback.
   - **Perspective Correction**: Homography matrix computation warping distorted or skewed photos into a canonical 450×450 square grid.
   - **Cell Segmentation**: Precise 9×9 slicing (81 cells) with inner margin trimming to eliminate outer grid lines and borders.
   - **Digit Recognition**: Multi-font machine-learning digit classifier trained on printed font typography with morphological profile analysis.
   - **Sudoku Reconstruction**: Generates a verified 9×9 digital board with per-cell OCR confidence scoring.
   - **Logical Move Prediction**: Human-like deduction engine identifying **Naked Singles**, **Hidden Singles (Box, Row, Column)**, and step-by-step candidate elimination.
   - **Visual Highlighting & Projection**: Highlights target cells and peer constraints on the warped grid and inverse-projects annotations back onto the original photo perspective.

2. **FastAPI High-Performance Backend**:
   - `/api/scan`: Upload any puzzle photo and receive reconstructed grid, hints, solution, and visual base64 image overlays.
   - `/api/hint`: Calculates the next logical move with step-by-step explanation.
   - `/api/solve`: Instantly solves the puzzle using backtracking with MRV (Minimum Remaining Values) heuristic.
   - `/api/validate`: Verifies grid consistency and reports duplicate row, column, or 3×3 box violations.
   - `/api/candidates`: Computes 9×9 candidate pencil marks for all empty cells.
   - `/api/samples`: Serves bundled test photos with pre-generated previews.
   - `/api/health`: Health status monitor.
   - Built-in static mounting to serve the compiled React frontend directly.

3. **Modern React Frontend**:
   - Responsive Glassmorphic Dark UI built with Vite and React.
   - Drag-and-drop image upload, 1-click test photos, and browser webcam/camera capture.
   - Live visual perspective toggling ("Photo Perspective" vs "Warped Grid").
   - Interactive 9×9 editable board with keyboard navigation and virtual keypad.
   - Real-time candidate pencil marks toggle.
   - Auto-Play step-by-step solver with animated visual deduction walkthrough.
   - Preset puzzle loader (Easy, Medium, Hard).

---

## 🏗️ Architecture

```
Sudoku/
├── backend/
│   ├── main.py                     # FastAPI application & API endpoints
│   ├── vision/
│   │   ├── preprocessor.py         # Grayscale, blur, adaptive thresholding
│   │   ├── grid_detector.py        # 4-corner contour detection & ordering
│   │   ├── perspective.py          # Perspective warp & inverse projection
│   │   ├── cell_extractor.py       # 81-cell segmentation & digit centering
│   │   ├── digit_recognizer.py     # Multi-font synthetic OCR model
│   │   ├── visualizer.py           # Highlight overlays & base64 rendering
│   │   └── pipeline.py             # Pipeline coordinator
│   ├── solver/
│   │   ├── sudoku_board.py         # 9x9 board representation & candidate tracker
│   │   ├── solver.py               # Backtracking solver with MRV
│   │   └── logic_engine.py         # Human-like next move hints & explanations
│   └── tests/
│       ├── test_sudoku_board.py    # Unit tests for board model
│       ├── test_solver.py          # Unit tests for backtracking solver
│       ├── test_logic_engine.py    # Unit tests for logical move engine
│       ├── test_grid_detector.py   # Unit tests for 4-corner detection
│       ├── test_cell_extractor.py  # Unit tests for cell extraction
│       ├── test_digit_recognizer.py# Unit tests for digit OCR
│       ├── test_visualizer.py      # Unit tests for highlight overlays
│       ├── test_pipeline.py        # Integration test for end-to-end pipeline
│       ├── test_api.py             # FastAPI endpoint tests
│       └── synthetic_sudoku.py     # Deterministic image generator for testing
├── frontend/
│   ├── index.html                  # HTML entry point
│   ├── vite.config.js              # Vite configuration with API proxy
│   ├── package.json                # React dependencies and scripts
│   └── src/
│       ├── App.jsx                 # Main state coordinator
│       ├── index.css               # Glassmorphic dark styling & animations
│       ├── samplePuzzles.js        # Built-in presets (Easy, Medium, Hard)
│       └── components/
│           ├── SudokuGrid.jsx      # Interactive 9x9 board
│           ├── ImageUploader.jsx   # Drag-and-drop & image preview toggle
│           └── HintPanel.jsx       # Logical move explanation card
├── samples/                        # Sample Sudoku puzzle images
│   ├── sample_easy.png
│   ├── sample_medium.png
│   └── sample_skewed.png
├── requirements.txt                # Python dependencies
└── pytest.ini                      # Pytest configuration
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.9+
- Node.js 18+ and npm

### 2. Setup Backend
```bash
# In the workspace root
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Setup Frontend
```bash
cd frontend
npm install
npm run build
cd ..
```

---

## 🧪 Running Tests

To run the complete test suite (25 unit and integration tests):
```bash
./venv/bin/python3 -m pytest -v
```

All 25 tests pass in ~1.5s:
- `test_health`: API healthcheck
- `test_api_validate`: Validation endpoint tests
- `test_api_hint`: Next move prediction endpoint tests
- `test_api_solve`: Solver endpoint tests
- `test_api_scan`: End-to-end image upload & scan endpoint tests
- `test_perspective_warp`: Perspective transformation tests
- `test_cell_segmentation`: 9x9 cell segmentation & empty detection
- `test_digit_recognizer_prediction`: OCR recognition accuracy tests
- `test_grid_detection_clean`: Boundary & corner detection
- `test_corner_ordering`: Mathematical TL/TR/BR/BL corner sorting
- `test_naked_single_detection`: Naked single logic engine tests
- `test_hidden_single_in_box`: Hidden single logic engine tests
- `test_end_to_end_pipeline`: Complete computer vision pipeline tests
- `test_solver_solves_standard_puzzle`: Backtracking solver correctness
- `test_solver_unsolvable_puzzle`: Contradiction handling
- `test_count_solutions_unique`: Solution uniqueness verification
- `test_board_initialization`: Board data structure tests
- `test_board_set_and_get`: Board accessors
- `test_board_validation_valid`: Board validation logic
- `test_board_validation_duplicate_row`: Duplicate row conflict detection
- `test_board_validation_duplicate_col`: Duplicate column conflict detection
- `test_board_validation_duplicate_box`: Duplicate 3x3 box conflict detection
- `test_board_candidates`: Candidate set calculation
- `test_visualizer_render_overlay`: Visual overlay canvas rendering
- `test_visualizer_project_overlay`: Inverse perspective unwarping

---

## 💻 Running the Application

### Option A: Unified FastAPI Server (Serves Backend & Built React UI)
```bash
./venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

### Option B: Separate Development Servers
Run the FastAPI backend:
```bash
./venv/bin/uvicorn backend.main:app --reload --port 8000
```
In another terminal, run the Vite React dev server:
```bash
cd frontend
npm run dev
```
Open **[http://localhost:5173](http://localhost:5173)** in your browser.

---

## 📡 API Reference

### 1. `POST /api/scan`
Uploads a Sudoku image file (`multipart/form-data`).
**Response**:
```json
{
  "success": true,
  "grid": [[5, 3, 0, ...], ...],
  "confidences": [[1.0, 1.0, 1.0, ...], ...],
  "is_valid": true,
  "validation_errors": [],
  "is_solvable": true,
  "solved_grid": [[5, 3, 4, ...], ...],
  "next_move": {
    "row": 0,
    "col": 2,
    "display_coord": "R1C3",
    "value": 4,
    "strategy": "Naked Single",
    "explanation": "Cell R1C3 has only one possible candidate: 4...",
    "highlight_cells": [{"row": 0, "col": 0}, ...],
    "candidates": [4]
  },
  "images": {
    "original_annotated": "data:image/png;base64,...",
    "warped_annotated": "data:image/png;base64,..."
  }
}
```

### 2. `POST /api/hint`
Calculates the next logical move for the provided 9×9 board.
**Request**: `{"grid": [[...]]}`
**Response**:
```json
{
  "success": true,
  "hint": {
    "row": 0,
    "col": 8,
    "display_coord": "R1C9",
    "value": 9,
    "strategy": "Naked Single",
    "explanation": "...",
    "highlight_cells": [...],
    "candidates": [9]
  },
  "overlay_image": "data:image/png;base64,..."
}
```

### 3. `POST /api/solve`
Solves the entire board using backtracking with MRV heuristic.
**Request**: `{"grid": [[...]]}`
**Response**:
```json
{
  "success": true,
  "solved_grid": [[...]]
}
```

### 4. `POST /api/validate`
Checks Sudoku rules and solvability without altering state.
**Request**: `{"grid": [[...]]}`
**Response**:
```json
{
  "is_valid": true,
  "errors": [],
  "is_complete": false,
  "is_solvable": true
}
```
