import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';

export default function SignupPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => { setLoading(false); navigate('/onboarding'); }, 800);
  }

  return (
    <>
      <Navbar showAuth={false} />
      <div className="page-centered">
        <div className="auth-card">
          <div className="auth-logo">
            <span className="logo-icon">👁️</span>
            <h2>The Eye of GodAI</h2>
          </div>
          <h3 style={{ marginBottom: 4, fontSize: '1.1rem' }}>Create your account</h3>
          <p style={{ fontSize: '0.82rem', marginBottom: 24 }}>Start receiving personalized AI intelligence.</p>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Display Name</label>
              <input className="form-input" name="name" placeholder="Your name" value={form.name} onChange={handleChange} required />
            </div>
            <div className="form-group">
              <label className="form-label">Email</label>
              <input className="form-input" type="email" name="email" placeholder="you@example.com" value={form.email} onChange={handleChange} required />
            </div>
            <div className="form-group">
              <label className="form-label">Password</label>
              <input className="form-input" type="password" name="password" placeholder="Min. 8 characters" value={form.password} onChange={handleChange} required />
            </div>
            <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
              {loading ? 'Creating account…' : 'Create account →'}
            </button>
          </form>

          <p className="auth-footer">
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
        </div>
      </div>
    </>
  );
}
