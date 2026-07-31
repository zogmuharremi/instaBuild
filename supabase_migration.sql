-- Run this in Supabase SQL Editor to create the projects table
CREATE TABLE IF NOT EXISTS projects (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id text NOT NULL,
  name text NOT NULL DEFAULT 'Untitled',
  items jsonb NOT NULL DEFAULT '[]',
  total_cost int DEFAULT 0,
  budget int DEFAULT 100000,
  created_at text,
  updated_at text
);

CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_updated ON projects(updated_at DESC);

-- Optional: submissions table for contact form
CREATE TABLE IF NOT EXISTS submissions (
  id bigserial PRIMARY KEY,
  name text,
  email text,
  phone text,
  project_type text,
  message text,
  timestamp text
);

-- Policy to allow all operations (your backend uses service_role key)
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all" ON projects FOR ALL USING (true);

ALTER TABLE submissions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all" ON submissions FOR ALL USING (true);
