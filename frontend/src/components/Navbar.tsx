import { Link } from 'react-router-dom';

interface NavbarProps { showAuth?: boolean; }

export default function Navbar({ showAuth = true }: NavbarProps) {
  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand">
        <span className="brand-icon">👁️</span>
        <span className="brand-name">The Eye of GodAI</span>
      </Link>
      {showAuth && (
        <div className="navbar-links">
          <Link to="/login" className="btn btn-secondary" style={{ padding: '8px 16px', fontSize: '0.85rem' }}>Login</Link>
          <Link to="/signup" className="btn btn-primary" style={{ padding: '8px 16px', fontSize: '0.85rem' }}>Get Started</Link>
        </div>
      )}
    </nav>
  );
}
