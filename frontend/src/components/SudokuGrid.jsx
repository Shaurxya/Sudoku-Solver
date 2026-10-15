import React, { useEffect } from 'react';

export default function SudokuGrid({
  grid,
  clues,
  candidates = [],
  showCandidates = false,
  selectedCell,
  onSelectCell,
  onCellValueChange,
  hint,
  solvedGrid,
  conflictCells = []
}) {
  // Handle keyboard inputs
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!selectedCell) return;
      const { r, c } = selectedCell;

      if (e.key >= '1' && e.key <= '9') {
        onCellValueChange(r, c, parseInt(e.key, 10));
      } else if (e.key === 'Backspace' || e.key === 'Delete' || e.key === '0') {
        onCellValueChange(r, c, 0);
      } else if (e.key === 'ArrowUp' && r > 0) {
        onSelectCell(r - 1, c);
      } else if (e.key === 'ArrowDown' && r < 8) {
        onSelectCell(r + 1, c);
      } else if (e.key === 'ArrowLeft' && c > 0) {
        onSelectCell(r, c - 1);
      } else if (e.key === 'ArrowRight' && c < 8) {
        onSelectCell(r, c + 1);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedCell, onCellValueChange, onSelectCell]);

  const isPeerOfHint = (r, c) => {
    if (!hint || !hint.highlight_cells) return false;
    return hint.highlight_cells.some(cell => cell.row === r && cell.col === c);
  };

  const isTargetOfHint = (r, c) => {
    return hint && hint.row === r && hint.col === c;
  };

  const isConflict = (r, c) => {
    return conflictCells.some(cell => cell.row === r && cell.col === c);
  };

  return (
    <div className="sudoku-grid">
      {grid.map((row, r) =>
        row.map((val, c) => {
          const isSelected = selectedCell && selectedCell.r === r && selectedCell.c === c;
          const isClue = clues && clues[r][c] !== 0;
          const isTarget = isTargetOfHint(r, c);
          const isPeer = isPeerOfHint(r, c);
          const isConflictCell = isConflict(r, c);
          const cellCandidates = (candidates && candidates[r] && candidates[r][c]) || [];

          // Borders for 3x3 subgrids
          const borderRight = (c === 2 || c === 5) ? 'border-right-thick' : '';
          const borderBottom = (r === 2 || r === 5) ? 'border-bottom-thick' : '';

          let cellClass = 'sudoku-cell';

          if (isClue) {
            cellClass += ' clue';
          } else if (val !== 0) {
            cellClass += ' user-filled';
          }

          if (isSelected) cellClass += ' selected';
          if (isTarget) cellClass += ' highlight-target';
          else if (isPeer) cellClass += ' highlight-peer';
          if (isConflictCell) cellClass += ' conflict';

          return (
            <div
              key={`${r}-${c}`}
              className={`${cellClass} ${borderRight} ${borderBottom}`}
              onClick={() => onSelectCell(r, c)}
            >
              {val !== 0 ? (
                <span>{val}</span>
              ) : showCandidates && cellCandidates.length > 0 ? (
                <div className="pencil-marks-grid">
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((digit) => (
                    <span
                      key={digit}
                      className={`pencil-mark ${cellCandidates.includes(digit) ? 'active' : ''}`}
                    >
                      {cellCandidates.includes(digit) ? digit : ''}
                    </span>
                  ))}
                </div>
              ) : null}
            </div>
          );
        })
      )}
    </div>
  );
}
