-- DATA QUALITY FIX SQL
-- Generated: 2025-10-20 18:28:42
-- Review and execute each statement carefully

-- HIGH: 2,258 people missing name fields
-- Review people with missing names
SELECT person_id, full_name, first_name, last_name FROM person WHERE full_name IS NULL OR full_name = '';

-- MEDIUM: 1 invalid LinkedIn URL formats
-- Review invalid LinkedIn URLs
SELECT person_id, normalized_linkedin_url FROM person WHERE normalized_linkedin_url NOT LIKE 'linkedin.com/in/%' LIMIT 50;

-- MEDIUM: Low email coverage: 1.7%
-- Consider enriching from additional sources

-- LOW: Low employment coverage: 14.4%
-- Consider importing from LinkedIn data

