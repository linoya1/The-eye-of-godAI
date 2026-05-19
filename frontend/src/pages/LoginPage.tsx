import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { supabase } from '../lib/supabase';

export default function LoginPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const { error: loginError } = await supabase.auth.signInWithPassword({
        email: form.email,
        password: form.password,
      });

      if (loginError) {
        setError(loginError.message);
        setLoading(false);
        return;
      }

      // On successful login, redirect to dashboard
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setLoading(false);
    }
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
          <h3 style={{ marginBottom: 4, fontSize: '1.1rem' }}>Welcome back</h3>
          <p style={{ fontSize: '0.82rem', marginBottom: 24 }}>Sign in to your intelligence dashboard.</p>

          <form onSubmit={handleSubmit}>
            {error && <div style={{ color: '#ef4444', marginBottom: 16, fontSize: '0.9rem' }}>{error}</div>}
            <div className="form-group">
              <label className="form-label">Email</label>
              <input className="form-input" type="email" name="email" placeholder="you@example.com" value={form.email} onChange={handleChange} required />
            </div>
            <div className="form-group">
              <label className="form-label">Password</label>
              <input className="form-input" type="password" name="password" placeholder="Your password" value={form.password} onChange={handleChange} required />
            </div>
            <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
              {loading ? 'Signing in…' : 'Sign in →'}
            </button>
          </form>

          <p className="auth-footer">
            No account yet? <Link to="/signup">Create one free</Link>
          </p>
        </div>
      </div>
    </>
  );
}
