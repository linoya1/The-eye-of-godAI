# The Eye of God AI
# The Eye of GodAI — Architecture Plan

## 1. Product Definition

**What it is:** A full-stack AI progress and risk intelligence system that collects public AI publications, classifies them into domains, scores them with measurable intelligence signals, and delivers personalized insights to users.

**Who it's for:** Developers, researchers, security engineers, and AI-curious professionals who want curated, scored, and structured AI intelligence — not raw news.

**Why it's more than a news aggregator:**
- Events are scored (Breakthrough, Risk, Evidence, Impact, Trend)
- Events are linked in a graph (domain relationships, bridge connections)
- Users get personalized feeds based on selected AI interests
- The system tracks *momentum* — whether a domain is accelerating or declining
- Insights are computed, not just fetched

---

## 2. Recommended MVP Scope

### ✅ Build in MVP
- User registration & login (Supabase Auth)
- AI interest questionnaire (8 domains, multi-select)
- Daily pipeline: collect ~20–40 items from 5–8 trusted RSS/API sources
- Classify events into domains using keyword rules + optional LLM call
- Calculate: Breakthrough Score, Risk Signal, Evidence Level, Impact Area, Trend Momentum
- Store events + scores in Supabase PostgreSQL
- Dashboard: personalized event feed based on selected interests
- Event detail page with scores and source link
- GitHub Actions daily cron job

### ❌ Do NOT build yet (MVP+)
- Graph view / graph algorithms (centrality, bridges, SCCs)
- Bridge Score & Graph Centrality scores
- Entity extraction (people, companies, models)
- Advanced NLP / embeddings / vector search
- Notification system / email digests
- Admin dashboard / pipeline monitoring UI
- Multi-language support
- Mobile app

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Vite + React + TS)          │
│  Vercel Deployment                                       │
│  - Auth pages (Login / Signup)                           │
│  - Interest Questionnaire                                │
│  - Dashboard (personalized event feed)                   │
│  - Event Detail Page                                     │
│  - Insights Panel / Trend Charts                         │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTPS REST API
┌───────────────────────▼─────────────────────────────────┐
│                  BACKEND (FastAPI + Python)               │
│  (Run locally in MVP / Render/Railway in v2)             │
│  - Auth validation (Supabase JWT)                        │
│  - GET /events, /events/{id}                             │
│  - GET /insights/personalized                            │
│  - GET/POST /user/interests                              │
│  - GET /domains                                          │
│  - POST /admin/ingest/run (trigger pipeline)             │
│  - GET /pipeline/status                                  │
└──────────────┬──────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────┐
│              SUPABASE (PostgreSQL + Auth)                 │
│  - users, user_interests, ai_domains                     │
│  - sources, events, event_scores                         │
│  - event_domains, graph_edges, daily_insights            │
│  - pipeline_runs                                         │
└──────────────────────────────────────────────────────────┘
               ▲
┌──────────────┴──────────────────────────────────────────┐
│           DAILY PIPELINE (GitHub Actions Cron)           │
│  Runs every day at 06:00 UTC                             │
│  1. Fetch RSS feeds + arXiv + API sources                │
│  2. Deduplicate by URL hash                              │
│  3. Classify into AI domains                             │
│  4. Score each event                                     │
│  5. Write to Supabase                                    │
│  6. Log pipeline run result                              │
└──────────────────────────────────────────────────────────┘
```

---

## 4. Folder Structure (Monorepo)

```
The-eye-of-godAI/
├── frontend/                  # Vite + React + TypeScript
│   ├── src/
│   │   ├── pages/             # Route-level components
│   │   ├── components/        # Reusable UI components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── api/               # Axios/fetch wrappers
│   │   ├── store/             # State management (Zustand or Context)
│   │   └── types/             # Shared TypeScript types
│   ├── index.html
│   └── vite.config.ts
│
├── backend/                   # Python FastAPI
│   ├── main.py                # FastAPI app entry point
│   ├── routes/                # API route handlers
│   ├── services/              # Business logic
│   ├── db/                    # Supabase client + queries
│   ├── models/                # Pydantic data models
│   └── config.py              # Env vars + settings
│
├── pipeline/                  # Daily data ingestion
│   ├── ingest.py              # Main pipeline runner
│   ├── sources/               # One file per source type
│   │   ├── rss_fetcher.py
│   │   ├── arxiv_fetcher.py
│   │   └── normalizer.py
│   ├── classify.py            # Domain classification logic
│   ├── score.py               # Scoring engine
│   └── dedup.py               # Duplicate detection
│
├── .github/
│   └── workflows/
│       └── daily_pipeline.yml # GitHub Actions cron
│
├── docs/                      # Architecture docs, schema diagrams
├── .env.example               # Template for env vars
└── README.md
```

---

## 5. Database Schema

### `ai_domains`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| name | TEXT | e.g. "AI Cyber Risk" |
| slug | TEXT UNIQUE | e.g. "ai-cyber-risk" |
| description | TEXT | |
| icon | TEXT | emoji or icon name |
| created_at | TIMESTAMPTZ | |

### `sources`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| name | TEXT | e.g. "Anthropic Blog" |
| url | TEXT | Base URL |
| feed_url | TEXT | RSS/API endpoint |
| source_type | TEXT | rss / api / arxiv / scrape |
| credibility_score | FLOAT | 0.0–1.0, set manually |
| is_active | BOOLEAN | |

### `users` *(managed by Supabase Auth, extended)*
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | matches Supabase auth.users.id |
| email | TEXT | |
| display_name | TEXT | |
| onboarded | BOOLEAN | false until questionnaire complete |
| created_at | TIMESTAMPTZ | |

### `user_interests`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK → users | |
| domain_id | UUID FK → ai_domains | |
| created_at | TIMESTAMPTZ | |

### `events`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| source_id | UUID FK → sources | |
| title | TEXT | |
| summary | TEXT | AI-generated or excerpt |
| url | TEXT UNIQUE | dedup key |
| url_hash | TEXT UNIQUE | SHA-256 of URL |
| published_at | TIMESTAMPTZ | from source |
| ingested_at | TIMESTAMPTZ | when pipeline ran |
| raw_content | TEXT | optional, raw text |
| is_processed | BOOLEAN | scoring complete? |

### `event_domains`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| event_id | UUID FK → events | |
| domain_id | UUID FK → ai_domains | |
| confidence | FLOAT | 0.0–1.0 classification confidence |

### `event_scores`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| event_id | UUID FK → events | UNIQUE |
| breakthrough_score | FLOAT | 0.0–10.0 |
| risk_signal | FLOAT | 0.0–10.0 |
| evidence_level | TEXT | peer-reviewed / arxiv / blog / etc. |
| impact_areas | TEXT[] | array of impact strings |
| trend_momentum | FLOAT | -1.0 to +1.0 |
| bridge_score | FLOAT | MVP+: how many domains connected |
| graph_centrality | FLOAT | MVP+: importance in graph |
| scored_at | TIMESTAMPTZ | |

### `graph_edges` *(MVP+ only)*
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| source_event_id | UUID FK → events | |
| target_event_id | UUID FK → events | |
| relationship_type | TEXT | same-domain / cites / related |
| weight | FLOAT | edge strength |
| created_at | TIMESTAMPTZ | |

### `daily_insights`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| domain_id | UUID FK → ai_domains | |
| date | DATE | insight date |
| summary_text | TEXT | LLM-generated or template |
| top_events | UUID[] | array of event IDs |
| momentum_delta | FLOAT | change vs previous period |
| created_at | TIMESTAMPTZ | |

### `pipeline_runs`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| started_at | TIMESTAMPTZ | |
| finished_at | TIMESTAMPTZ | |
| status | TEXT | success / partial / failed |
| events_fetched | INT | |
| events_stored | INT | |
| events_skipped | INT | duplicates |
| error_log | TEXT | any errors |

---

## 6. API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Register (delegates to Supabase) |
| POST | `/auth/login` | Login (delegates to Supabase) |
| GET | `/domains` | List all 8 AI domains |
| GET | `/user/interests` | Get current user's interests |
| POST | `/user/interests` | Save interest selections |
| GET | `/events` | List events (filtered by user interests + date) |
| GET | `/events/{id}` | Event detail + scores |
| GET | `/insights/personalized` | Aggregated insights per selected domain |
| GET | `/pipeline/status` | Last pipeline run status |
| POST | `/admin/ingest/run` | Manually trigger pipeline (protected) |

---

## 7. Scoring Model (How Scores Are Calculated)

### Breakthrough Score (0–10)
```
score = (source_credibility × 2.5)
      + (novelty_flag × 2.0)      ← first time this topic appears
      + (benchmark_link × 2.0)    ← cites a benchmark result
      + (evidence_weight × 2.0)   ← peer-reviewed = 2, blog = 0.5
      + (industry_adoption × 1.5) ← major org adoption signal
```

### Risk Signal (0–10)
```
score = (cyber_keywords × 2.0)
      + (safety_keywords × 2.0)
      + (misuse_keywords × 2.0)
      + (hallucination_keywords × 1.5)
      + (agent_autonomy_keywords × 1.5)
      + (data_leak_keywords × 1.0)
```

### Evidence Level (categorical → numeric weight)
| Level | Weight |
|---|---|
| Peer-reviewed | 1.0 |
| arXiv/preprint | 0.8 |
| Benchmark result | 0.75 |
| Official release | 0.7 |
| Technical blog | 0.5 |
| Company announcement | 0.4 |
| News article | 0.3 |
| Opinion/analysis | 0.2 |

### Trend Momentum (-1 to +1)
```
momentum = (events_this_week - events_last_week) / max(events_last_week, 1)
         × average_score_change_ratio
```
Positive = domain is accelerating. Negative = cooling down.

---

## 8. Data Sources (MVP)

| Source | Type | Domain Focus |
|---|---|---|
| Anthropic Blog | RSS | Safety, Model Behavior, Agents |
| OpenAI Blog | RSS | All domains |
| Google DeepMind Blog | RSS | Research, Benchmarks |
| arXiv cs.AI / cs.CR | API | Research, Cyber |
| GitHub Blog | RSS | Software Engineering |
| Hugging Face Blog | RSS | Models, Benchmarks |
| Krebs on Security | RSS | Cyber Risk |
| METR / ARC Evals | RSS/scrape | Safety, Benchmarks |

---

## 9. User Flow

```
[Landing Page]
      │
      ├─ Not logged in → [Signup] → [Login]
      │
      ▼
[Login] ──► [Check: onboarded?]
                   │
            No ──► [Interest Questionnaire] → save to user_interests
                   │
            Yes ──►▼
              [Dashboard]
                   │
          ┌────────┼────────┐
          ▼        ▼        ▼
    [Event Feed] [Insights] [Trends]
          │
          ▼
    [Event Detail Page]
    (scores, source, domains, summary)
```

---

## 10. Development Roadmap

| Milestone | Goal | Key Deliverables |
|---|---|---|
| M1 | Project Setup | Repo structure, Vite app, FastAPI skeleton, Supabase project |
| M2 | Auth & Interests | Signup/Login, questionnaire, store interests in DB |
| M3 | Database Schema | All tables created in Supabase, seed domains + sources |
| M4 | Mock Dashboard | Static event cards, score badges, domain filter — no real data yet |
| M5 | Ingestion Pipeline | RSS + arXiv fetcher, dedup, normalize, store raw events |
| M6 | Scoring Engine | Keyword-based scoring for all 5 MVP scores |
| M7 | Personalized Feed | API returns events filtered by user interests + scores |
| M8 | Insights Layer | Daily insights text, trend momentum per domain |
| M9 | GitHub Actions | Daily cron job, pipeline_runs logging, error handling |
| M10 | Deployment | Vercel (frontend), Supabase (DB), README, polish |
| M11+ | Graph Features | graph_edges, bridge score, centrality, GraphView component |

---

## 11. Key Risks & Simplifications

| Risk | Simplification |
|---|---|
| LLM API cost for classification | Start with keyword rules only; add LLM later |
| Source scraping brittle | Use RSS feeds only in MVP; scraping is MVP+ |
| Graph algorithms complex | Defer all graph features to M11+ |
| FastAPI hosting cost | Run pipeline as standalone Python script in GitHub Actions; no FastAPI needed in MVP |
| Rate limiting from sources | Add `time.sleep()` between requests; cache raw responses |
| Supabase row limits (free tier) | Limit to 500 events/month; add cleanup job later |

> [!IMPORTANT]
> **Key MVP simplification:** In MVP, the pipeline script runs *directly inside GitHub Actions* — it does not need a deployed FastAPI server. FastAPI is only needed when the frontend wants to read data. You can even skip FastAPI in early milestones and query Supabase directly from the frontend using the Supabase JS client.

---

## 12. Open Questions for You

Before implementation begins, please answer these:

1. **FastAPI vs Supabase direct:** In MVP, do you want to use FastAPI as an intermediary, or query Supabase directly from the React frontend using the Supabase JS SDK? (FastAPI adds structure but complexity; direct is faster to build)

2. **Classification method:** Should domain classification use only keyword rules (simple, free, fast) or should we budget for an LLM API call (OpenAI/Anthropic) per event? (~$0.001–0.01 per event)

3. **Auth provider:** Are you comfortable using Supabase Auth (email/password + magic link), or do you want to add Google OAuth?

4. **Insight summaries:** Should "daily insights" be manually templated text (e.g. "3 new events in AI Safety this week, trend is up") or LLM-generated summaries?

5. **UI library preference:** Do you want pure CSS (as I've planned) or a component library like shadcn/ui, Radix UI, or Chakra UI for faster UI building?
