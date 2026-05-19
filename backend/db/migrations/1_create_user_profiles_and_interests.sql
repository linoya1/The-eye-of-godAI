-- 1_create_user_profiles_and_interests.sql
BEGIN;

-- Ensure pgcrypto is available for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Add user_profiles table (additive)
CREATE TABLE IF NOT EXISTS public.user_profiles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  auth_uid text UNIQUE,
  email text,
  full_name text,
  metadata jsonb DEFAULT '{}'::jsonb,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_user_profiles_auth_uid ON public.user_profiles (auth_uid);
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON public.user_profiles (email);

-- Add user_interests table (normalized)
CREATE TABLE IF NOT EXISTS public.user_interests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
  domain_slug text NOT NULL REFERENCES public.domains(slug) ON DELETE CASCADE,
  created_at timestamptz DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_user_interests_user_domain ON public.user_interests (user_id, domain_slug);

COMMIT;
