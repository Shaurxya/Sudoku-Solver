import React from 'react';
import { Lightbulb, Check, Sparkles } from 'lucide-react';

export default function HintPanel({ hint, onApplyHint }) {
  if (!hint) return null;

  return (
    <div className="hint-card">
      <div className="hint-header">
        <span className="hint-strategy-badge">{hint.strategy}</span>
        <span className="hint-coord">{hint.display_coord}</span>
      </div>

      <p className="hint-explanation">{hint.explanation}</p>

      {hint.candidates && hint.candidates.length > 0 && (
        <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.75rem' }}>
          <strong>Candidates:</strong> {hint.candidates.join(', ')}
        </div>
      )}

      <button
        className="btn btn-emerald"
        style={{ width: '100%', padding: '0.5rem 1rem' }}
        onClick={onApplyHint}
      >
        <Check size={16} /> Apply Deduction ({hint.display_coord} = {hint.value})
      </button>
    </div>
  );
}

