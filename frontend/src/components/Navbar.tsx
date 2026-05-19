import { Link, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';


interface NavbarProps { showAuth?: boolean; }

export default function Navbar({ showAuth = true }: NavbarProps) {
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    let mounted = true;
    supabase.auth.getSession().then(({ data }) => {
      if (!mounted) return;
      setUserEmail(data?.session?.user?.email || null);
      console.debug('Navbar: session detected -', data?.session?.user?.email || 'none');
    });
    // Listen for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUserEmail(session?.user?.email || null);
      console.debug('Navbar: auth state changed -', session?.user?.email || 'none');
    });
    return () => {
      mounted = false;
      subscription?.unsubscribe();
    };
  }, []);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    setUserEmail(null);
    console.info('User logged out');
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand">
        <span className="brand-icon">👁️</span>
        <span className="brand-name">The Eye of GodAI</span>
      </Link>
      {showAuth && (
        <div className="navbar-links" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {userEmail ? (
            <>
              <span style={{ fontSize: '0.92em', color: '#444', marginRight: 8 }}>{userEmail}</span>
              <button className="btn btn-secondary" style={{ padding: '8px 16px', fontSize: '0.85rem' }} onClick={handleLogout}>Logout</button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn btn-secondary" style={{ padding: '8px 16px', fontSize: '0.85rem' }}>Login</Link>
              <Link to="/signup" className="btn btn-primary" style={{ padding: '8px 16px', fontSize: '0.85rem' }}>Get Started</Link>
            </>
          )}
        </div>
      )}
    </nav>
  );
}
