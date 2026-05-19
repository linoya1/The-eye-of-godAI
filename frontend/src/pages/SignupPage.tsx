import { useState } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { supabase } from '../lib/supabase';

export default function SignupPage() {
  const [form, setForm] = useState({ name: '', email: '', password: '' });
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
      const { error: signupError } = await supabase.auth.signUp({
        email: form.email,
        password: form.password,
        options: {
          data: {
            full_name: form.name,
          },
          emailRedirectTo: `${window.location.origin}/onboarding`,
        },
      });

      if (signupError) {
        setError(signupError.message);
        setLoading(false);
        return;
      }

      // On successful signup with email confirmation, show message
      // User will receive confirmation email and redirect back to /onboarding
      setError(''); // Clear error
      console.info('Signup successful. Confirmation email sent.');
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
          <h3 style={{ marginBottom: 4, fontSize: '1.1rem' }}>Create your account</h3>
          <p style={{ fontSize: '0.82rem', marginBottom: 24 }}>Start receiving personalized AI intelligence.</p>

          <form onSubmit={handleSubmit}>
            {error && <div style={{ color: '#ef4444', marginBottom: 16, fontSize: '0.9rem' }}>{error}</div>}
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
            {!error && !loading && <p style={{ fontSize: '0.8rem', color: '#666', marginTop: 8, textAlign: 'center' }}>You'll receive a confirmation email to complete signup.</p>}
          </form>

          <p className="auth-footer">
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
        </div>
      </div>
    </>
  );
}
