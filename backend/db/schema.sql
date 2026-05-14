-- The Eye of GodAI - Database Schema (MVP)

-- 1. Domains Table
CREATE TABLE domains (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    icon TEXT
);

-- 2. Sources Table
CREATE TABLE sources (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    credibility_score NUMERIC(3,2) DEFAULT 0.0
);

-- 3. Events Table
CREATE TABLE events (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT,
    url TEXT UNIQUE NOT NULL,
    published_at TIMESTAMPTZ,
    source_id TEXT REFERENCES sources(id) ON DELETE CASCADE,
    
    -- EventScore fields flattened directly into the event table for MVP simplicity
    breakthrough_score NUMERIC(4,2),
    risk_signal NUMERIC(4,2),
    evidence_level TEXT,
    impact_areas TEXT[],
    trend_momentum NUMERIC(4,2),
    
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 4. Event-Domain Junction Table (Many-to-Many)
-- Connects a single event to multiple AI domains.
CREATE TABLE event_domains (
    event_id TEXT REFERENCES events(id) ON DELETE CASCADE,
    domain_id TEXT REFERENCES domains(id) ON DELETE CASCADE,
    PRIMARY KEY (event_id, domain_id)
);

-- 5. Insights Table
CREATE TABLE insights (
    id TEXT PRIMARY KEY,
    domain_slug TEXT REFERENCES domains(slug) ON DELETE CASCADE,
    summary_text TEXT NOT NULL,
    top_event_ids TEXT[],
    momentum_delta NUMERIC(4,2),
    date TEXT, -- Stored as text (YYYY-MM-DD) to match the Pydantic model for MVP
    created_at TIMESTAMPTZ DEFAULT now()
);
