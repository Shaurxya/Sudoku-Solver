import React, { useState, useEffect, useRef } from 'react';
import SudokuGrid from './components/SudokuGrid';
import ImageUploader from './components/ImageUploader';
import HintPanel from './components/HintPanel';
import { SAMPLE_PUZZLES } from './samplePuzzles';
import {
  Lightbulb,
  Zap,
  CheckCircle2,
  RotateCcw,
  Sparkles,
  Info,
  Trash2,
  Play,
  Pause,
  Edit3
} from 'lucide-react';

export default function App() {
  const [grid, setGrid] = useState(SAMPLE_PUZZLES.Medium);
  const [clues, setClues] = useState(SAMPLE_PUZZLES.Medium);
  const [candidates, setCandidates] = useState([]);
  const [showCandidates, setShowCandidates] = useState(false);
  const [selectedCell, setSelectedCell] = useState(null);
  const [hint, setHint] = useState(null);
  const [solvedGrid, setSolvedGrid] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [originalImagePreview, setOriginalImagePreview] = useState(null);
  const [statusMessage, setStatusMessage] = useState(null);
  const [isError, setIsError] = useState(false);
  const [isAutoPlaying, setIsAutoPlaying] = useState(false);

  const autoPlayRef = useRef(false);
  autoPlayRef.current = isAutoPlaying;

  // Fetch candidates whenever grid changes or showCandidates is enabled
  useEffect(() => {
    if (showCandidates) {
      fetch('/api/candidates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ grid }),
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.candidates) setCandidates(data.candidates);
        })
        .catch(() => {});
    }
  }, [grid, showCandidates]);

  // Set cell value
  const handleCellValueChange = (r, c, val) => {
    const newGrid = grid.map((row, ri) =>
      row.map((colVal, ci) => (ri === r && ci === c ? val : colVal))
    );
    setGrid(newGrid);
    setHint(null);
    setSolvedGrid(null);
    setStatusMessage(null);
  };

  // Upload image to backend
  const handleImageSelected = async (file) => {
    setIsScanning(true);
    setStatusMessage(null);
    setIsError(false);
    setHint(null);
    setSolvedGrid(null);
    setIsAutoPlaying(false);

    // Local preview
    const reader = new FileReader();
    reader.onload = (e) => setOriginalImagePreview(e.target.result);
    reader.readAsDataURL(file);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/scan', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to scan image.');
      }

      const data = await res.json();
      setScanResult(data);
      setGrid(data.grid);
      setClues(data.grid);

      if (data.next_move) {
        setHint(data.next_move);
      }
      if (data.solved_grid) {
        setSolvedGrid(data.solved_grid);
      }

      setStatusMessage('Sudoku extracted and reconstructed successfully from photo!');
    } catch (err) {
      setIsError(true);
      setStatusMessage(err.message);
    } finally {
      setIsScanning(false);
    }
  };

  // Get Next Logical Move Hint
  const handleGetHint = async (currentGrid = grid) => {
    setStatusMessage(null);
    setIsError(false);
    try {
      const res = await fetch('/api/hint', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ grid: currentGrid }),
      });
      const data = await res.json();
      if (!data.success) {
        setIsError(true);
        setStatusMessage(data.message || 'Could not find a valid hint.');
        return null;
      }
      if (data.is_complete) {
        setStatusMessage(data.message);
        return null;
      }

      setHint(data.hint);
      setSelectedCell({ r: data.hint.row, c: data.hint.col });
      return data.hint;
    } catch (err) {
      setIsError(true);
      setStatusMessage('Error requesting hint: ' + err.message);
      return null;
    }
  };

  // Apply Hint
  const handleApplyHint = () => {
    if (!hint) return;
    handleCellValueChange(hint.row, hint.col, hint.value);
    setHint(null);
  };

  // Auto-Play Step-by-Step
  const toggleAutoPlay = async () => {
    if (isAutoPlaying) {
      setIsAutoPlaying(false);
      return;
    }

    setIsAutoPlaying(true);
    let workingGrid = grid.map((r) => [...r]);

    const runStep = async () => {
      if (!autoPlayRef.current) return;

      const nextHint = await handleGetHint(workingGrid);
      if (!nextHint) {
        setIsAutoPlaying(false);
        return;
      }

      // Commit the step
      workingGrid[nextHint.row][nextHint.col] = nextHint.value;
      setGrid([...workingGrid.map((r) => [...r])]);

      if (autoPlayRef.current) {
        setTimeout(runStep, 800);
      }
    };

    runStep();
  };

  // Solve Complete
  const handleSolve = async () => {
    setIsAutoPlaying(false);
    setStatusMessage(null);
    setIsError(false);
    try {
      const res = await fetch('/api/solve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ grid }),
      });
      const data = await res.json();
      if (!data.success) {
        setIsError(true);
        setStatusMessage(data.message || 'Puzzle cannot be solved.');
        return;
      }

      setGrid(data.solved_grid);
      setSolvedGrid(data.solved_grid);
      setHint(null);
      setStatusMessage('Puzzle solved successfully!');
    } catch (err) {
      setIsError(true);
      setStatusMessage('Error solving puzzle: ' + err.message);
    }
  };

  // Validate
  const handleValidate = async () => {
    setStatusMessage(null);
    setIsError(false);
    try {
      const res = await fetch('/api/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ grid }),
      });
      const data = await res.json();
      if (!data.is_valid) {
        setIsError(true);
        setStatusMessage('Rule conflicts: ' + data.errors.join('; '));
      } else if (data.is_complete) {
        setStatusMessage('Congratulations! The Sudoku is completely and correctly solved.');
      } else if (!data.is_solvable) {
        setIsError(true);
        setStatusMessage('Board is currently consistent, but leads to no valid solution.');
      } else {
        setStatusMessage('Board is valid and solvable!');
      }
    } catch (err) {
      setIsError(true);
      setStatusMessage('Error validating: ' + err.message);
    }
  };

  // Reset
  const handleReset = () => {
    setIsAutoPlaying(false);
    setGrid(clues);
    setHint(null);
    setSolvedGrid(null);
    setStatusMessage(null);
    setIsError(false);
  };

  // Clear All
  const handleClearAll = () => {
    setIsAutoPlaying(false);
    const emptyGrid = Array(9).fill(null).map(() => Array(9).fill(0));
    setGrid(emptyGrid);
    setClues(emptyGrid);
    setCandidates([]);
    setHint(null);
    setSolvedGrid(null);
    setScanResult(null);
    setOriginalImagePreview(null);
    setStatusMessage(null);
    setIsError(false);
  };

  // Load Preset
  const handleLoadPreset = (name) => {
    setIsAutoPlaying(false);
    const p = SAMPLE_PUZZLES[name];
    setGrid(p);
    setClues(p);
    setHint(null);
    setSolvedGrid(null);
    setStatusMessage(`Loaded preset ${name} puzzle.`);
    setIsError(false);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* App Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo-area">
            <div className="logo-icon">9</div>
            <div>
              <h1 className="logo-title">SudokuVision</h1>
              <p style={{ fontSize: '0.75rem', color: '#64748b' }}>Computer Vision & Logical Move AI</p>
            </div>
            <span className="logo-badge">End-to-End Pipeline</span>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Presets:</span>
            {Object.keys(SAMPLE_PUZZLES).map((name) => (
              <button
                key={name}
                className="preset-chip"
                onClick={() => handleLoadPreset(name)}
              >
                {name}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-container">
        {/* Left Side: Image upload and Vision Pipeline Visuals */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <ImageUploader
            onImageSelected={handleImageSelected}
            isScanning={isScanning}
            scanResult={scanResult}
            originalImagePreview={originalImagePreview}
          />

          <div className="glass-panel" style={{ padding: '1.25rem' }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Info size={16} color="#38bdf8" /> How the Pipeline Operates
            </h3>
            <ol style={{ fontSize: '0.82rem', color: '#94a3b8', paddingLeft: '1.2rem', lineHeight: 1.6 }}>
              <li><strong>Grid Detection:</strong> Adaptive thresholding and contour polygon approximation locate the 4 board corners.</li>
              <li><strong>Perspective Correction:</strong> Homography matrix warps skewed photos into a top-down 450x450 grid.</li>
              <li><strong>Cell Segmentation:</strong> Extracts 81 cells, cleans grid border margins, and centers digit ROIs.</li>
              <li><strong>Digit Recognition:</strong> Classifies clues using multi-font model with morphological profile analysis.</li>
              <li><strong>Logical Move Prediction:</strong> Deduce next move (Naked Single, Hidden Single, Box-Line reduction) with step-by-step human explanations.</li>
              <li><strong>Visual Highlighting:</strong> Projects highlighted move and peer constraints back onto your photo perspective.</li>
            </ol>
          </div>
        </div>

        {/* Right Side: Interactive Sudoku Board and Controls */}
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <div className="sudoku-board-container">
            <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', maxWidth: '468px', marginBottom: '0.75rem', alignItems: 'center' }}>
              <span style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
                Interactive Board
              </span>
              <button
                className={`preset-chip ${showCandidates ? 'selected' : ''}`}
                style={{
                  background: showCandidates ? '#2563eb' : '#1e293b',
                  color: showCandidates ? '#fff' : '#94a3b8',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.3rem',
                  fontSize: '0.75rem'
                }}
                onClick={() => setShowCandidates(!showCandidates)}
              >
                <Edit3 size={13} /> Pencil Marks
              </button>
            </div>

            <SudokuGrid
              grid={grid}
              clues={clues}
              candidates={candidates}
              showCandidates={showCandidates}
              selectedCell={selectedCell}
              onSelectCell={(r, c) => setSelectedCell({ r, c })}
              onCellValueChange={handleCellValueChange}
              hint={hint}
              solvedGrid={solvedGrid}
            />

            {/* Virtual Keypad */}
            <div className="keypad">
              {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((num) => (
                <button
                  key={num}
                  className="keypad-btn"
                  onClick={() => selectedCell && handleCellValueChange(selectedCell.r, selectedCell.c, num)}
                >
                  {num}
                </button>
              ))}
              <button
                className="keypad-btn erase"
                title="Erase cell"
                onClick={() => selectedCell && handleCellValueChange(selectedCell.r, selectedCell.c, 0)}
              >
                <Trash2 size={16} />
              </button>
            </div>

            {/* Action Bar */}
            <div className="action-bar">
              <button className="btn btn-emerald" onClick={() => handleGetHint()} style={{ flex: '1 1 auto' }}>
                <Lightbulb size={18} /> Next Move / Hint
              </button>
              <button
                className="btn btn-secondary"
                onClick={toggleAutoPlay}
                style={{
                  background: isAutoPlaying ? 'rgba(245, 158, 11, 0.2)' : '#1e293b',
                  borderColor: isAutoPlaying ? '#f59e0b' : 'var(--border-subtle)',
                  color: isAutoPlaying ? '#f59e0b' : 'var(--text-primary)'
                }}
              >
                {isAutoPlaying ? <Pause size={18} /> : <Play size={18} />}
                {isAutoPlaying ? 'Pause Auto' : 'Auto Play'}
              </button>
              <button className="btn btn-primary" onClick={handleSolve} style={{ flex: '1 1 auto' }}>
                <Zap size={18} /> Solve All
              </button>
              <button className="btn btn-secondary" onClick={handleValidate} title="Validate board">
                <CheckCircle2 size={18} />
              </button>
              <button className="btn btn-secondary" onClick={handleReset} title="Reset to clues">
                <RotateCcw size={18} />
              </button>
              <button className="btn btn-secondary" onClick={handleClearAll} title="Clear board">
                <Trash2 size={18} />
              </button>
            </div>

            {/* Status Message */}
            {statusMessage && (
              <div
                style={{
                  marginTop: '1rem',
                  padding: '0.75rem 1rem',
                  borderRadius: '8px',
                  width: '100%',
                  maxWidth: '468px',
                  fontSize: '0.85rem',
                  background: isError ? 'rgba(244, 63, 94, 0.15)' : 'rgba(59, 130, 246, 0.15)',
                  border: `1px solid ${isError ? 'rgba(244, 63, 94, 0.3)' : 'rgba(59, 130, 246, 0.3)'}`,
                  color: isError ? '#fb7185' : '#93c5fd',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}
              >
                {isError ? '⚠️' : 'ℹ️'} {statusMessage}
              </div>
            )}

            {/* Next Move Hint Explanation Card */}
            <HintPanel hint={hint} onApplyHint={handleApplyHint} />
          </div>
        </div>
      </main>
    </div>
  );
}
