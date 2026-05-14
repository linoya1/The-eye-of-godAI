-- The Eye of GodAI - Realistic Supabase Seed Script
-- WARNING: Run this only in your local or dev Supabase SQL Editor.
-- This script clears existing data and populates realistic MVP data.

-- 1. Clear existing data (in correct order to respect foreign keys)
DELETE FROM insights;
DELETE FROM event_domains;
DELETE FROM events;
DELETE FROM sources;
DELETE FROM domains;

-- 2. Insert Domains
INSERT INTO domains (id, name, slug, description, icon) VALUES
('d1', 'AI Model Behavior & Interpretability', 'ai-model-behavior', 'Mechanistic interpretability, internal representations, and model behavior patterns.', '🧠'),
('d2', 'AI Software Engineering', 'ai-software-engineering', 'AI coding agents, code generation, and automated debugging.', '💻'),
('d3', 'AI Cyber Risk & Security', 'ai-cyber-risk', 'Threat intelligence, prompt injection, and enterprise AI security.', '🛡️'),
('d4', 'AI Benchmarks & Evaluation', 'ai-benchmarks', 'Tracking measurable AI capabilities and evaluation frameworks.', '📊'),
('d6', 'AI Agents & Workflows', 'ai-agents', 'Autonomous agents, multi-agent systems, and real-world execution limitations.', '🤖'),
('d7', 'AI Safety & Governance', 'ai-safety-governance', 'Alignment research, hallucinations, deception, and regulation.', '⚖️');

-- 3. Insert Sources
INSERT INTO sources (id, name, credibility_score) VALUES
('s1', 'Anthropic Research', 0.95),
('s2', 'TIME Magazine', 0.85),
('s3', 'The AI Digest', 0.80),
('s4', 'The Guardian', 0.88),
('s5', 'Reuters', 0.92);

-- 4. Insert Events (Using the URLs and topics provided)
INSERT INTO events (id, title, summary, url, published_at, source_id, breakthrough_score, risk_signal, evidence_level, impact_areas, trend_momentum) VALUES
(
    'e1', 
    'Mapping Emotion-Like Concepts in Claude''s Internal Representations', 
    'Anthropic researchers have successfully mapped how specific abstract concepts, including emotion-like states and behavioral traits such as ''sycophancy'' and ''deception'', are represented within Claude''s neural activations. This provides mechanistic evidence of how models encode behavioral tendencies before they are outputted as text.', 
    'https://www.anthropic.com/research/emotion-concepts-function', 
    '2026-05-01T10:00:00Z', 
    's1', 
    8.5, 
    3.2, 
    'Peer-reviewed Research', 
    ARRAY['Mechanistic Interpretability', 'Alignment', 'Neural Activations'], 
    0.15
),
(
    'e2', 
    'AI Village Agents Fail Reliability Benchmarks in Complex Environments', 
    'Large-scale testing by AI Village reveals that current autonomous agents (including ChatGPT, Gemini, and Claude) suffer from significant compounding hallucination rates when executing multi-step workflows. The research highlights severe limitations in agent reliability in unconstrained, real-world environments without human oversight.', 
    'https://time.com/7330795/ai-village-chatgpt-gemini-claude/', 
    '2026-05-10T14:30:00Z', 
    's2', 
    5.0, 
    6.8, 
    'Empirical Benchmark', 
    ARRAY['Autonomous Agents', 'Enterprise Adoption', 'Workflow Reliability'], 
    -0.05
),
(
    'e3', 
    'Anthropic Unveils ''Mythos'': A New Paradigm in Automated Cyber Threats', 
    'A coordinated disclosure details ''Mythos'', a newly identified framework demonstrating how advanced AI models can be weaponized for sophisticated, multi-stage cyberattacks. The report highlights severe prompt injection vulnerabilities and has triggered rapid defensive responses across global financial and critical infrastructures.', 
    'https://www.reuters.com/business/finance/anthropics-mythos-sends-us-banks-rushing-plug-cyber-holes-2026-05-12/?utm_source=chatgpt.com', 
    '2026-05-12T08:15:00Z', 
    's5', 
    9.1, 
    9.8, 
    'Confirmed Incident / Technical Report', 
    ARRAY['Cybersecurity', 'Financial Sector Infrastructure', 'Defensive AI'], 
    0.42
);

-- 5. Insert Event-Domains Mapping
INSERT INTO event_domains (event_id, domain_id) VALUES
('e1', 'd1'), -- e1 to Model Behavior
('e1', 'd7'), -- e1 to Safety & Governance
('e2', 'd6'), -- e2 to AI Agents
('e2', 'd7'), -- e2 to Safety & Governance
('e3', 'd3'); -- e3 to Cyber Risk

-- 6. Insert Insights
INSERT INTO insights (id, domain_slug, summary_text, top_event_ids, momentum_delta, date) VALUES
(
    'i1', 
    'ai-cyber-risk', 
    'Severe spike in cyber risk signals driven by the ''Mythos'' threat framework disclosure. Global financial institutions are actively restructuring defensive AI postures in response to newly demonstrated automated attack vectors.', 
    ARRAY['e3'], 
    0.42, 
    '2026-05-13'
),
(
    'i2', 
    'ai-model-behavior', 
    'Mechanistic interpretability research is rapidly transitioning from theoretical to applied. Researchers are successfully isolating abstract behavioral traits—including deception and emotion-like states—directly within model weights.', 
    ARRAY['e1'], 
    0.15, 
    '2026-05-02'
);
