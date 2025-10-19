
-- Sample Queries for Talent Intelligence Database
-- Generated: 2025-10-17 17:52:56.150654

-- 1. Find all candidates from a specific company
SELECT 
    p.first_name, p.last_name, p.primary_email,
    e.title, e.company_name
FROM people p
JOIN employment e ON p.person_id = e.person_id
WHERE LOWER(e.company_name) LIKE '%uniswap%'
AND e.is_current = 1;

-- 2. Find candidates with both LinkedIn and GitHub
SELECT 
    p.first_name, p.last_name, p.primary_email,
    sp1.profile_url as linkedin_url,
    sp2.profile_url as github_url
FROM people p
JOIN social_profiles sp1 ON p.person_id = sp1.person_id AND sp1.platform = 'linkedin'
JOIN social_profiles sp2 ON p.person_id = sp2.person_id AND sp2.platform = 'github';

-- 3. Find high-quality candidates (quality score > 0.7)
SELECT 
    first_name, last_name, primary_email,
    data_quality_score
FROM people
WHERE data_quality_score > 0.7
ORDER BY data_quality_score DESC;

-- 4. Get complete profile for a specific person
SELECT 
    p.*,
    GROUP_CONCAT(DISTINCT sp.platform || ': ' || sp.profile_url, '
') as social_profiles,
    GROUP_CONCAT(DISTINCT em.email, ', ') as all_emails,
    e.company_name, e.title
FROM people p
LEFT JOIN social_profiles sp ON p.person_id = sp.person_id
LEFT JOIN emails em ON p.person_id = em.person_id
LEFT JOIN employment e ON p.person_id = e.person_id AND e.is_current = 1
WHERE p.primary_email = 'example@email.com'
GROUP BY p.person_id;

-- 5. Count candidates by location
SELECT 
    location,
    COUNT(*) as candidate_count
FROM people
WHERE location IS NOT NULL
GROUP BY location
ORDER BY candidate_count DESC
LIMIT 20;

-- 6. Find candidates missing LinkedIn profiles
SELECT 
    first_name, last_name, primary_email
FROM people p
WHERE NOT EXISTS (
    SELECT 1 FROM social_profiles sp 
    WHERE sp.person_id = p.person_id 
    AND sp.platform = 'linkedin'
)
AND primary_email IS NOT NULL;

-- 7. Get all emails for people at a specific company
SELECT 
    p.first_name, p.last_name,
    GROUP_CONCAT(em.email, ', ') as all_emails
FROM people p
JOIN employment e ON p.person_id = e.person_id
JOIN emails em ON p.person_id = em.person_id
WHERE LOWER(e.company_name) LIKE '%coinbase%'
AND e.is_current = 1
GROUP BY p.person_id;

-- 8. Find potential duplicate candidates (same name, different person_id)
SELECT 
    first_name, last_name,
    COUNT(*) as count,
    GROUP_CONCAT(primary_email, ', ') as emails
FROM people
WHERE first_name IS NOT NULL AND last_name IS NOT NULL
GROUP BY LOWER(first_name), LOWER(last_name)
HAVING COUNT(*) > 1;
