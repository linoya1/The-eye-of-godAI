import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { fetchDomains } from '../api/client';
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
      .finally(() => setLoading(false));
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
    navigate('/dashboard');
  }

  return (
    <>
      <Navbar showAuth={false} />
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
