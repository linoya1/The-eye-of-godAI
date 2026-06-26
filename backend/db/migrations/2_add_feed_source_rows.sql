-- 2_add_feed_source_rows.sql
--
-- Adds source rows for the four feed publishers that were missing from the
-- sources table.  This is an ADDITIVE migration — no existing rows are
-- modified or deleted, and no events are re-linked.
--
-- Run this in the Supabase SQL Editor BEFORE the next ingestion run.
--
-- Idempotent: ON CONFLICT (id) DO NOTHING means running it twice is safe.
--
-- Canonical sources already present (for reference, NOT re-inserted here):
--   s1  Anthropic Research     0.95
--   s2  TIME Magazine          0.85
--   s3  The AI Digest          0.80
--   s4  The Guardian           0.88
--   s5  Reuters                0.92
--   s6  OpenAI Research        0.95
--   s7  NVIDIA Architecture    0.90
--   s8  SWE-bench              0.88
--
-- Credibility-score rationale
-- ───────────────────────────
-- The existing scale uses the following rough tiers:
--   0.95  Primary AI-lab research output   (Anthropic, OpenAI)
--   0.90  Verified industry / hardware     (NVIDIA Architecture)
--   0.88  Standardized benchmark authority (SWE-bench, The Guardian)
--   0.85  Established mainstream press     (TIME)
--   0.80  AI-focused newsletter            (The AI Digest)
--
-- New sources are placed on this scale as follows:
--
--   s9  Hugging Face Blog    0.87
--       Hugging Face is the de-facto community hub for ML model releases and
--       technical writing.  Posts are authored or reviewed by model authors.
--       It sits just below The Guardian (0.88) because it is a company blog
--       rather than an independent editorial outlet, but above The AI Digest
--       (0.80) because of its direct connection to primary ML artefacts.
--
--  s10  Google Research Blog  0.92
--       Direct output of Google Research and Google DeepMind teams.  Papers
--       referenced here are peer-reviewed or internally validated.  Placed
--       at the same tier as Reuters (0.92) — factual, primary-source technical
--       content — but just below Anthropic/OpenAI (0.95) because Google Blog
--       posts can mix product marketing with research.
--
--  s11  Google Blog           0.82
--       General Google announcements and product news.  Less rigorous than
--       the Research Blog; primarily product-focused.  Placed between The AI
--       Digest (0.80) and TIME Magazine (0.85).
--
--  s12  Made By Agents        0.75
--       Emerging AI-agent focused publication with a small editorial team.
--       Relevant domain coverage but limited editorial track record.  Placed
--       below The AI Digest (0.80) to reflect the nascent status.

BEGIN;

INSERT INTO sources (id, name, credibility_score) VALUES
  ('s9',  'Hugging Face Blog',    0.87),
  ('s10', 'Google Research Blog', 0.92),
  ('s11', 'Google Blog',          0.83),
  ('s12', 'Made By Agents',       0.75)
ON CONFLICT (id) DO NOTHING;

COMMIT;
