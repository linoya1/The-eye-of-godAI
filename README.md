# 👁️ The Eye of GodAI - AI Intelligence Dashboard

The Eye of God AI is a deployed full-stack AI intelligence dashboard for monitoring high-signal developments across the AI ecosystem. It ingests AI-related articles and research updates, scores them with Groq-assisted analysis, stores structured events and signals in Supabase, and serves the results through a FastAPI backend and React/Vite frontend.

It is deployed end-to-end as a portfolio project: the frontend runs on Vercel, the backend runs on Render, and Supabase provides authentication and persistence.

## 🚀 Live Demo

- Frontend: [the-eye-of-god-ai-frontend.vercel.app](https://the-eye-of-god-ai-frontend.vercel.app)
- Backend API: [the-eye-of-godai-backend.onrender.com](https://the-eye-of-godai-backend.onrender.com)

## 🧠 Overview

- Ingests AI-related articles and events from public sources.
- Scores each event with backend-computed intelligence signals.
- Stores normalized events, user preferences, and derived signals in Supabase.
- Supports Supabase Auth signup, login, profile sync, and onboarding preferences.
- Displays a personalized dashboard with AI Intelligence Signals, Top Research Signals, and a browsable events feed.
- Uses a manual GitHub Actions ingestion workflow for quality-controlled updates.

## 🧩 Key Features

- AI events feed with filtering by domain.
- Backend-computed AI Intelligence Signals derived from stored events.
- Top Research Signals section with manually curated high-importance research and capability updates.
- Event detail view for inspecting the underlying signal and source information.
- Supabase Auth signup and login.
- Backend-owned profile sync for deterministic user profile creation.
- Onboarding preferences saved to `user_interests`.
- Manual GitHub Actions ingestion workflow for controlled data refreshes.

## 🏗️ Architecture

```text
Public AI sources -> Ingestion script -> Groq/LLM scoring -> Supabase
                                              |
                                              v
                                      FastAPI backend API
                                              |
                                              v
                                     React/Vite frontend
```

- Frontend: React + Vite + TypeScript.
- Backend: FastAPI + Python.
- Database/Auth: Supabase.
- AI scoring: Groq-powered analysis plus backend-computed signal logic.

## 🛠️ Tech Stack

- Frontend: React, Vite, TypeScript
- Backend: FastAPI, Python
- Database: Supabase PostgreSQL
- Authentication: Supabase Auth
- AI / scoring: Groq / LLM-based scoring pipeline
- Deployment: Vercel (frontend), Render (backend)
- Automation: GitHub Actions manual workflow

## 🔄 AI Data Pipeline

The ingestion pipeline is intentionally manual to keep the event stream quality-controlled. The current ingestion entrypoint is `backend/ingest_anthropic.py`.

Pipeline flow:

1. Fetch AI-related articles and research updates from public sources.
2. Normalize and deduplicate incoming events.
3. Score each event with Groq-assisted analysis and backend signal logic.
4. Persist structured events and scores in Supabase.
5. Serve the computed intelligence data through the FastAPI API.

## 📊 Intelligence Analytics

The dashboard surfaces two distinct analytics layers:

- AI Intelligence Signals: dynamic backend-computed signals derived from the stored event database.
- Top Research Signals: a curated section highlighting unusually important research or capability events with human-written intelligence takeaways.

This split keeps the dashboard focused: one layer is computed from the live event stream, and the other is intentionally editorial.

## 🔐 Auth & Personalization

The project uses Supabase Auth for signup and login. After authentication:

- The backend syncs the authenticated user into `user_profiles`.
- Onboarding preferences are stored in `user_interests`.
- The dashboard can tailor the event feed to the selected interests.

## 🚀 Deployment

The project is deployed and functioning end-to-end:

- Frontend: Vercel
- Backend API: Render
- Database and authentication: Supabase

Deployment notes:

- The frontend must be configured with `VITE_API_URL` so it points to the deployed backend in production.
- Supabase Auth redirect URLs should include the deployed frontend URL.
- Backend CORS should allow the deployed frontend origin.

## ⚙️ Local Setup

Backend:

```bash
cd backend
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## ⚙️ Environment Variables

Backend:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `GROQ_API_KEY`

Frontend:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_API_URL`

Notes:

- The frontend can fall back to `http://localhost:8000` locally if `VITE_API_URL` is not set.
- In production, `VITE_API_URL` should be set to the deployed backend URL.
- Example placeholder files are provided in `backend/.env.example` and `frontend/.env.example`.

## 🔄 Manual Ingestion

Manual ingestion is part of the project design. It is used to keep the event stream quality-controlled instead of running on an automatic schedule.

Local command:

```bash
python backend/ingest_anthropic.py
```

GitHub Actions workflow:

- `.github/workflows/manual-ingestion.yml`
- Trigger: `workflow_dispatch` only
- No scheduled trigger is configured

## 🖼️ Screenshots

<img width="1287" height="758" alt="image" src="https://github.com/user-attachments/assets/accd9445-b9a2-4c64-8e27-e64899babf45" />

<img width="777" height="742" alt="image" src="https://github.com/user-attachments/assets/331a1843-964b-48a1-9bc8-cb81d08b74e5" />

<img width="1102" height="822" alt="image" src="https://github.com/user-attachments/assets/55ef702e-41db-4d1e-b51e-95c442314ced" />

<img width="1896" height="902" alt="image" src="https://github.com/user-attachments/assets/b6f7dc5f-b716-4059-aceb-827297090cf2" />

<img width="1221" height="505" alt="image" src="https://github.com/user-attachments/assets/95ce17db-340c-47d3-b905-725173f4308e" />

<img width="1168" height="835" alt="image" src="https://github.com/user-attachments/assets/891c3aa1-7acb-4472-932f-e85ed3101dd4" />

<img width="1222" height="650" alt="image" src="https://github.com/user-attachments/assets/cfc110e7-d813-4728-bc4d-045259f2c333" />

<img width="1162" height="758" alt="image" src="https://github.com/user-attachments/assets/dd6691f4-4786-4524-b047-30d7ce54b101" />


## 💡 Technical Takeaways

- End-to-end full-stack delivery, from ingestion and scoring to presentation in the UI.
- Backend API design with authenticated flows, profile sync, and persistent user preferences.
- Data modeling for structured AI event streams and backend-computed intelligence signals.
- Practical integration of FastAPI, React/Vite, Supabase, and Groq in a production deployment.
- Deployment discipline across Vercel, Render, and Supabase with a manual ingestion workflow for quality control.
- Engineering judgment in separating dynamic analytics from intentionally curated research highlights.

## 🧪 Validation Notes

- The deployed application has been validated end-to-end in production.
- Local checks that remain useful: `python smoke_test.py` and `cd frontend && npm run build`.
- The repository intentionally avoids exposing secrets.
- `.env` files should contain only local values and private keys.
