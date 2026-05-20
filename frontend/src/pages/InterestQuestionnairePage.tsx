import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { fetchDomains, getPreferences, setPreferences, syncProfile } from '../api/client';
import { supabase } from '../lib/supabase';
import type { Domain } from '../types';

export default function InterestQuestionnairePage() {
  const navigate = useNavigate();
  const [domains, setDomains] = useState<Domain[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const lastSyncedTokenRef = useRef<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function loadDomains() {
      try {
        const loaded = await fetchDomains();
        if (!mounted) return;
        setDomains(loaded);
      } catch (e) {
        if (!mounted) return;
        setError(e instanceof Error ? e.message : 'Unable to load domains');
      } finally {
        if (mounted) setLoading(false);
      }
    }

    async function syncAndLoadPreferences(accessToken: string) {
      if (!accessToken || lastSyncedTokenRef.current === accessToken) {
        return;
      }

      try {
        console.info('Preferences: token found, syncing profile before loading interests');
        await syncProfile(accessToken);

        console.info('Preferences: loading saved interests');
        const prefs = await getPreferences(accessToken);
        if (!mounted) return;
        setSelected(new Set(prefs));
        setError('');
        lastSyncedTokenRef.current = accessToken;
        console.info('Preferences: loaded', prefs);
      } catch (e) {
        if (!mounted) return;
        setError(e instanceof Error ? e.message : 'Unable to load your profile');
        console.error('Preferences: failed to load preferences', e);
      }
    }

    async function restoreSessionAndLoad() {
      try {
        const { data } = await supabase.auth.getSession();
        const session = (data as any)?.session;
        const accessToken = session?.access_token;
        console.debug('[DEBUG InterestQuestionnairePage] Session check:', { session: !!session, hasToken: !!accessToken, tokenLength: accessToken?.length });

        if (!accessToken) {
          if (mounted) {
            setError('No active session found. Please log in to continue onboarding.');
          }
          return;
        }

        await syncAndLoadPreferences(accessToken);
      } catch (e) {
        if (!mounted) return;
        setError(e instanceof Error ? e.message : 'Unable to verify your session');
      }
    }

    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (_event, session) => {
      const accessToken = session?.access_token;
      if (!accessToken) {
        return;
      }
      await syncAndLoadPreferences(accessToken);
    });

    void loadDomains();
    void restoreSessionAndLoad();

    return () => {
      mounted = false;
      subscription?.unsubscribe();
    };
  }, []);

  function toggleDomain(slug: string) {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(slug)) next.delete(slug);
      else next.add(slug);
      return next;
    });
  }

  function handleSubmit() {
    (async () => {
      setError('');
      try {
        const { data } = await supabase.auth.getSession();
        const session = (data as any)?.session;
        const accessToken = session?.access_token;
        console.debug('[DEBUG handleSubmit] Getting session for save:', { session: !!session, hasToken: !!accessToken });

        if (!accessToken) {
          setError('No active session found. Please log in to continue onboarding.');
          navigate('/login');
          return;
        }

        const interests = Array.from(selected.values());
        console.debug('[DEBUG handleSubmit] About to save interests:', interests);
        try {
          await syncProfile(accessToken);
          const res = await setPreferences(accessToken, interests);
          console.info('Preferences: saved', res.interests);
        } catch (e) {
          setError(e instanceof Error ? e.message : 'Unable to save preferences');
          console.error('Preferences: backend error', e);
          return;
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Unable to read your session');
        console.error('Preferences: failed to read session', e);
        return;
      }

      navigate('/dashboard');
    })();
  }

  return (
    <>
      <Navbar showAuth={true} />
      <div className="questionnaire-page container">
        <div className="questionnaire-header">
          <h1>What AI domains interest you?</h1>
          <p>Select all that apply. Your dashboard will be personalized to your choices.</p>
        </div>

        {error && <div style={{ color: '#ef4444', marginBottom: 16, fontSize: '0.95rem' }}>{error}</div>}

        {loading ? (
          <div className="loading-state">
            <div className="loading-spinner" />
            <p>Loading domains…</p>
          </div>
        ) : (
          <>
            <div className="domains-grid">
              {domains.map(domain => (
                <div
                  key={domain.slug}
                  className={`card domain-card ${selected.has(domain.slug) ? 'selected' : ''}`}
                  onClick={() => toggleDomain(domain.slug)}
                  role="checkbox"
                  aria-checked={selected.has(domain.slug)}
                  tabIndex={0}
                  onKeyDown={e => e.key === 'Enter' && toggleDomain(domain.slug)}
                >
                  <div className="domain-card-top">
                    <span className="domain-icon">{domain.icon}</span>
                    <span className="domain-card-name">{domain.name}</span>
                  </div>
                  <p className="domain-card-desc">{domain.description}</p>
                </div>
              ))}
            </div>

            <div className="questionnaire-footer">
              <p className="selected-count">
                <span>{selected.size}</span> domain{selected.size !== 1 ? 's' : ''} selected
              </p>
              <button
                className="btn btn-primary"
                onClick={handleSubmit}
                disabled={selected.size === 0}
                style={{ minWidth: 200 }}
              >
                Go to my dashboard →
              </button>
            </div>
          </>
        )}
      </div>
    </>
  );
}
