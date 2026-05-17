import { useState } from 'react';

export default function ScoreLegend() {
  const [isOpen, setIsOpen] = useState(false);

  if (!isOpen) {
    return (
      <button 
        className="score-legend-toggle"
        onClick={() => setIsOpen(true)}
      >
        ℹ️ How to read these scores?
      </button>
    );
  }

  return (
    <div className="card score-legend">
      <div className="score-legend-header">
        <h4>How our AI scores events</h4>
        <button className="close-btn" onClick={() => setIsOpen(false)}>×</button>
      </div>
      <div className="score-legend-grid">
        <div className="legend-item">
          <span className="score-badge breakthrough">⚡ Breakthrough</span>
          <p>How much this event advances general AI capabilities or solves a previously unsolvable problem. (0-10)</p>
        </div>
        <div className="legend-item">
          <span className="score-badge risk-high">⚠️ Risk</span>
          <p>How much this event poses a danger to users, corporations, or society. (0-10)</p>
        </div>
        <div className="legend-item">
          <span className="score-badge evidence">📄 Evidence</span>
          <p>How reliable the information is (e.g., rumor, news, paper, peer-reviewed).</p>
        </div>
        <div className="legend-item">
          <span className="score-badge momentum-up">↑ Momentum</span>
          <p>Whether this topic is gaining traction or cooling down in the industry.</p>
        </div>
      </div>
    </div>
  );
}
