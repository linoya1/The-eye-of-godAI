import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';

const FEATURES = [
  { icon: '⚡', title: 'Breakthrough Scoring', desc: 'Every AI event scored for significance, novelty, and impact on a 0–10 scale.' },
  { icon: '🛡️', title: 'Risk Signal Detection', desc: 'Cybersecurity risks and safety concerns flagged with severity ratings.' },
  { icon: '📊', title: 'Trend Momentum', desc: 'Know which AI domains are accelerating, updated daily.' },
  { icon: '🎯', title: 'Personalized Feed', desc: 'Select the AI domains you care about. Your dashboard shows only what matters.' },
];

export default function LandingPage() {
  return (
    <>
      <Navbar />
      <section className="hero container">
        <div className="hero-bg-glow" />
        <div className="hero-bg-glow-2" />
        <div className="hero-content">
          <div className="hero-badge"><span>👁️</span><span>AI Intelligence, Not Just News</span></div>
          <h1 className="hero-title">
            See the AI world
            <span className="gradient-text">with clarity.</span>
          </h1>
          <p className="hero-subtitle">
            The Eye of GodAI transforms public AI reports, research papers, and product releases
            into measurable intelligence signals — personalized to your interests.
          </p>
          <div className="hero-actions">
            <Link to="/signup" className="btn btn-primary">Start for free →</Link>
            <Link to="/login" className="btn btn-secondary">Sign in</Link>
          </div>
        </div>
      </section>
      <section className="features-section container">
        <h2>Intelligence, not aggregation</h2>
        <div className="features-grid">
          {FEATURES.map(f => (
            <div key={f.title} className="card feature-card">
              <span className="feature-icon">{f.icon}</span>
              <h3>{f.title}</h3>
              <p style={{ fontSize: '0.85rem', marginTop: 8 }}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
