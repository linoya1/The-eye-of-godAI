import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { fetchDomains, getPreferences, setPreferences } from '../api/client';
import { supabase } from '../lib/supabase';
import type { Domain } from '../types';

export default function InterestQuestionnairePage() {
  const navigate = useNavigate();
  const [domains, setDomains] = useState<Domain[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDomains()
      .then(setDomains)
      .catch(() => {})
      .finally(async () => {
        setLoading(false);

        try {
          const { data } = await supabase.auth.getSession();
          const session = (data as any)?.session;
          const accessToken = session?.access_token;
          console.debug('[DEBUG InterestQuestionnairePage] Session check:', { session: !!session, hasToken: !!accessToken, tokenLength: accessToken?.length });
          if (!accessToken) {
            console.info('Preferences: no active session found');
            return;
          }

          console.info('Preferences: token found, loading saved interests');
          const prefs = await getPreferences(accessToken);
          console.info('Preferences: loaded', prefs);
          setSelected(new Set(prefs));
        } catch (e) {
          console.error('Preferences: failed to load preferences', e);
        }
      });
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
      try {
        const { data } = await supabase.auth.getSession();
        const session = (data as any)?.session;
        const accessToken = session?.access_token;
        console.debug('[DEBUG handleSubmit] Getting session for save:', { session: !!session, hasToken: !!accessToken });

        if (!accessToken) {
          console.info('Preferences: no active session, skipping save');
          navigate('/dashboard');
          return;
        }

        const interests = Array.from(selected.values());
        console.debug('[DEBUG handleSubmit] About to save interests:', interests);
        try {
          const res = await setPreferences(accessToken, interests);
          console.info('Preferences: saved', res.interests);
        } catch (e) {
          console.error('Preferences: backend error', e);
        }
      } catch (e) {
        console.error('Preferences: failed to read session', e);
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
