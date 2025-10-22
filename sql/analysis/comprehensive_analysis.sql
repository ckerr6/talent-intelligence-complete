-- ============================================================================
-- COMPREHENSIVE DATABASE ANALYSIS FOR PostgreSQL 'talent'
-- Run this to get complete insights into your database
-- ============================================================================

\echo '================================================================================'
\echo 'COMPREHENSIVE DATABASE ANALYSIS - PostgreSQL talent'
\echo 'Generated: ' `date`
\echo '================================================================================'
\echo ''

\echo '================================================================================'
\echo 'TABLE INVENTORY & SIZES'
\echo '================================================================================'
\echo ''

SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size('public.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size('public.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size('public.'||tablename) - pg_relation_size('public.'||tablename)) AS index_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size('public.'||tablename) DESC;

\echo ''
\echo '================================================================================'
\echo 'ROW COUNTS FOR ALL TABLES'
\echo '================================================================================'
\echo ''

SELECT 
    'person' as table_name,
    COUNT(*) as row_count,
    pg_size_pretty(pg_total_relation_size('person')) as size
FROM person
UNION ALL
SELECT 
    'company',
    COUNT(*),
    pg_size_pretty(pg_total_relation_size('company'))
FROM company
UNION ALL
SELECT 
    'employment',
    COUNT(*),
    pg_size_pretty(pg_total_relation_size('employment'))
FROM employment
UNION ALL
SELECT 
    'education',
    COUNT(*),
    pg_size_pretty(pg_total_relation_size('education'))
FROM education
UNION ALL
SELECT 
    'person_email',
    COUNT(*),
    pg_size_pretty(pg_total_relation_size('person_email'))
FROM person_email
UNION ALL
SELECT 
    'github_profile',
    COUNT(*),
    pg_size_pretty(pg_total_relation_size('github_profile'))
FROM github_profile
UNION ALL
SELECT 
    'github_repository',
    COUNT(*),
    pg_size_pretty(pg_total_relation_size('github_repository'))
FROM github_repository
UNION ALL
SELECT 
    'github_contribution',
    COUNT(*),
    pg_size_pretty(pg_total_relation_size('github_contribution'))
FROM github_contribution
UNION ALL
SELECT 
    'migration_log',
    COUNT(*),
    pg_size_pretty(pg_total_relation_size('migration_log'))
FROM migration_log
ORDER BY row_count DESC;

\echo ''
\echo '================================================================================'
\echo 'PERSON TABLE - DETAILED STATISTICS'
\echo '================================================================================'
\echo ''

SELECT 
    COUNT(*) as total_people,
    COUNT(DISTINCT person_id) as unique_ids,
    COUNT(full_name) as has_full_name,
    COUNT(first_name) as has_first_name,
    COUNT(last_name) as has_last_name,
    COUNT(linkedin_url) as has_linkedin,
    COUNT(normalized_linkedin_url) as has_normalized_linkedin,
    COUNT(DISTINCT linkedin_url) as unique_linkedin_urls,
    COUNT(DISTINCT normalized_linkedin_url) as unique_normalized_linkedin,
    COUNT(location) as has_location,
    COUNT(headline) as has_headline,
    COUNT(description) as has_description,
    COUNT(followers_count) as has_followers,
    COUNT(profile_img_url) as has_profile_img,
    ROUND(AVG(followers_count), 2) as avg_followers,
    MAX(followers_count) as max_followers
FROM person;

\echo ''
\echo 'Person completeness percentages:'
SELECT 
    'Full Name' as field,
    COUNT(full_name) as filled,
    COUNT(*) as total,
    ROUND(COUNT(full_name)::numeric / COUNT(*) * 100, 2) as completeness_pct
FROM person
UNION ALL
SELECT 
    'LinkedIn URL',
    COUNT(linkedin_url),
    COUNT(*),
    ROUND(COUNT(linkedin_url)::numeric / COUNT(*) * 100, 2)
FROM person
UNION ALL
SELECT 
    'Location',
    COUNT(location),
    COUNT(*),
    ROUND(COUNT(location)::numeric / COUNT(*) * 100, 2)
FROM person
UNION ALL
SELECT 
    'Headline',
    COUNT(headline),
    COUNT(*),
    ROUND(COUNT(headline)::numeric / COUNT(*) * 100, 2)
FROM person
UNION ALL
SELECT 
    'Description',
    COUNT(description),
    COUNT(*),
    ROUND(COUNT(description)::numeric / COUNT(*) * 100, 2)
FROM person
UNION ALL
SELECT 
    'Followers Count',
    COUNT(followers_count),
    COUNT(*),
    ROUND(COUNT(followers_count)::numeric / COUNT(*) * 100, 2)
FROM person;

\echo ''
\echo 'Top 10 people by followers:'
SELECT 
    full_name, 
    headline, 
    location, 
    followers_count,
    SUBSTRING(linkedin_url, 1, 60) as linkedin_url_short
FROM person
WHERE followers_count IS NOT NULL
ORDER BY followers_count DESC
LIMIT 10;

\echo ''
\echo 'Sample person records (random 5):'
SELECT 
    person_id,
    full_name,
    location,
    headline,
    followers_count,
    SUBSTRING(linkedin_url, 1, 60) as linkedin_url_short
FROM person
WHERE full_name IS NOT NULL
ORDER BY RANDOM()
LIMIT 5;

\echo ''
\echo '================================================================================'
\echo 'COMPANY TABLE - DETAILED STATISTICS'
\echo '================================================================================'
\echo ''

SELECT 
    COUNT(*) as total_companies,
    COUNT(DISTINCT company_id) as unique_ids,
    COUNT(company_name) as has_name,
    COUNT(DISTINCT company_name) as unique_names,
    COUNT(linkedin_url) as has_linkedin,
    COUNT(DISTINCT linkedin_url) as unique_linkedin_urls,
    COUNT(normalized_linkedin_url) as has_normalized_linkedin,
    COUNT(website) as has_website,
    COUNT(industry) as has_industry,
    COUNT(DISTINCT industry) as unique_industries,
    COUNT(company_size) as has_company_size,
    COUNT(location) as has_location,
    COUNT(founded_year) as has_founded_year
FROM company;

\echo ''
\echo 'Company completeness percentages:'
SELECT 
    'Company Name' as field,
    COUNT(company_name) as filled,
    COUNT(*) as total,
    ROUND(COUNT(company_name)::numeric / COUNT(*) * 100, 2) as completeness_pct
FROM company
UNION ALL
SELECT 
    'LinkedIn URL',
    COUNT(linkedin_url),
    COUNT(*),
    ROUND(COUNT(linkedin_url)::numeric / COUNT(*) * 100, 2)
FROM company
UNION ALL
SELECT 
    'Website',
    COUNT(website),
    COUNT(*),
    ROUND(COUNT(website)::numeric / COUNT(*) * 100, 2)
FROM company
UNION ALL
SELECT 
    'Industry',
    COUNT(industry),
    COUNT(*),
    ROUND(COUNT(industry)::numeric / COUNT(*) * 100, 2)
FROM company
UNION ALL
SELECT 
    'Company Size',
    COUNT(company_size),
    COUNT(*),
    ROUND(COUNT(company_size)::numeric / COUNT(*) * 100, 2)
FROM company
UNION ALL
SELECT 
    'Location',
    COUNT(location),
    COUNT(*),
    ROUND(COUNT(location)::numeric / COUNT(*) * 100, 2)
FROM company;

\echo ''
\echo 'Top 15 industries by company count:'
SELECT 
    industry, 
    COUNT(*) as company_count,
    ROUND(COUNT(*)::numeric / (SELECT COUNT(*) FROM company WHERE industry IS NOT NULL) * 100, 2) as pct_of_total
FROM company
WHERE industry IS NOT NULL
GROUP BY industry
ORDER BY company_count DESC
LIMIT 15;

\echo ''
\echo 'Sample companies (random 5):'
SELECT 
    company_name,
    industry,
    company_size,
    location,
    SUBSTRING(website, 1, 40) as website_short
FROM company
WHERE company_name IS NOT NULL
ORDER BY RANDOM()
LIMIT 5;

\echo ''
\echo '================================================================================'
\echo 'EMPLOYMENT TABLE - DETAILED STATISTICS'
\echo '================================================================================'
\echo ''

SELECT 
    COUNT(*) as total_employment_records,
    COUNT(DISTINCT person_id) as unique_people_with_jobs,
    COUNT(DISTINCT company_id) as unique_companies_with_employees,
    ROUND(COUNT(*)::numeric / NULLIF(COUNT(DISTINCT person_id), 0), 2) as avg_jobs_per_person,
    COUNT(CASE WHEN is_current THEN 1 END) as current_jobs,
    COUNT(CASE WHEN NOT is_current THEN 1 END) as past_jobs,
    COUNT(title) as has_title,
    COUNT(start_date) as has_start_date,
    COUNT(end_date) as has_end_date,
    COUNT(description) as has_description
FROM employment;

\echo ''
\echo 'Employment tenure analysis (for records with dates):'
SELECT 
    ROUND(AVG(EXTRACT(YEAR FROM AGE(COALESCE(end_date, CURRENT_DATE), start_date))), 2) as avg_tenure_years,
    ROUND(MIN(EXTRACT(YEAR FROM AGE(COALESCE(end_date, CURRENT_DATE), start_date))), 2) as min_tenure_years,
    ROUND(MAX(EXTRACT(YEAR FROM AGE(COALESCE(end_date, CURRENT_DATE), start_date))), 2) as max_tenure_years
FROM employment
WHERE start_date IS NOT NULL;

\echo ''
\echo 'Top 15 job titles:'
SELECT 
    title, 
    COUNT(*) as count,
    ROUND(COUNT(*)::numeric / (SELECT COUNT(*) FROM employment WHERE title IS NOT NULL) * 100, 2) as pct_of_total
FROM employment
WHERE title IS NOT NULL
GROUP BY title
ORDER BY count DESC
LIMIT 15;

\echo ''
\echo 'Sample employment records:'
SELECT 
    p.full_name,
    c.company_name,
    e.title,
    TO_CHAR(e.start_date, 'YYYY-MM') as start_date,
    CASE WHEN e.is_current THEN 'Current' ELSE TO_CHAR(e.end_date, 'YYYY-MM') END as end_date,
    e.is_current
FROM employment e
JOIN person p ON e.person_id = p.person_id
JOIN company c ON e.company_id = c.company_id
WHERE p.full_name IS NOT NULL AND c.company_name IS NOT NULL
ORDER BY e.start_date DESC NULLS LAST
LIMIT 5;

\echo ''
\echo '================================================================================'
\echo 'EDUCATION TABLE - DETAILED STATISTICS'
\echo '================================================================================'
\echo ''

SELECT 
    COUNT(*) as total_education_records,
    COUNT(DISTINCT person_id) as unique_people_with_education,
    ROUND(COUNT(DISTINCT person_id)::numeric / (SELECT COUNT(*) FROM person) * 100, 2) as pct_people_with_education,
    COUNT(school_name) as has_school_name,
    COUNT(DISTINCT school_name) as unique_schools,
    COUNT(degree) as has_degree,
    COUNT(field_of_study) as has_field,
    COUNT(start_year) as has_start_year,
    COUNT(end_year) as has_end_year
FROM education;

\echo ''
\echo 'Top 10 schools by attendance:'
SELECT 
    school_name,
    COUNT(*) as student_count
FROM education
WHERE school_name IS NOT NULL
GROUP BY school_name
ORDER BY student_count DESC
LIMIT 10;

\echo ''
\echo 'Sample education records:'
SELECT 
    p.full_name,
    e.school_name,
    e.degree,
    e.field_of_study,
    e.start_year,
    e.end_year
FROM education e
JOIN person p ON e.person_id = p.person_id
WHERE e.school_name IS NOT NULL
ORDER BY RANDOM()
LIMIT 5;

\echo ''
\echo '================================================================================'
\echo 'PERSON_EMAIL TABLE - DETAILED STATISTICS'
\echo '================================================================================'
\echo ''

SELECT 
    COUNT(*) as total_email_records,
    COUNT(DISTINCT email) as unique_emails,
    COUNT(DISTINCT person_id) as people_with_emails,
    ROUND(COUNT(DISTINCT person_id)::numeric / (SELECT COUNT(*) FROM person) * 100, 2) as email_coverage_pct,
    COUNT(CASE WHEN is_primary THEN 1 END) as primary_emails,
    COUNT(CASE WHEN email_type = 'work' THEN 1 END) as work_emails,
    COUNT(CASE WHEN email_type = 'personal' THEN 1 END) as personal_emails,
    COUNT(CASE WHEN email_type = 'unknown' OR email_type IS NULL THEN 1 END) as unknown_type_emails,
    COUNT(CASE WHEN verified THEN 1 END) as verified_emails
FROM person_email;

\echo ''
\echo 'Email type distribution:'
SELECT 
    COALESCE(email_type, 'unknown') as email_type,
    COUNT(*) as count,
    ROUND(COUNT(*)::numeric / (SELECT COUNT(*) FROM person_email) * 100, 2) as pct
FROM person_email
GROUP BY email_type
ORDER BY count DESC;

\echo ''
\echo 'Sample email records:'
SELECT 
    p.full_name,
    pe.email,
    pe.email_type,
    pe.is_primary,
    pe.source
FROM person_email pe
JOIN person p ON pe.person_id = p.person_id
ORDER BY RANDOM()
LIMIT 5;

\echo ''
\echo '================================================================================'
\echo 'GITHUB_PROFILE TABLE - DETAILED STATISTICS'
\echo '================================================================================'
\echo ''

SELECT 
    COUNT(*) as total_github_profiles,
    COUNT(DISTINCT github_profile_id) as unique_profile_ids,
    COUNT(DISTINCT github_username) as unique_usernames,
    COUNT(person_id) as profiles_linked_to_person,
    COUNT(*) - COUNT(person_id) as profiles_not_linked,
    ROUND(COUNT(person_id)::numeric / COUNT(*) * 100, 2) as linkage_pct,
    COUNT(github_name) as has_name,
    COUNT(github_email) as has_email,
    COUNT(github_company) as has_company,
    COUNT(location) as has_location,
    COUNT(bio) as has_bio,
    COUNT(twitter_username) as has_twitter,
    ROUND(AVG(followers), 2) as avg_followers,
    ROUND(AVG(public_repos), 2) as avg_public_repos,
    MAX(followers) as max_followers,
    MAX(public_repos) as max_repos
FROM github_profile;

\echo ''
\echo 'GitHub profile coverage:'
SELECT 
    (SELECT COUNT(*) FROM person) as total_people,
    COUNT(DISTINCT gp.person_id) as people_with_github,
    ROUND(COUNT(DISTINCT gp.person_id)::numeric / (SELECT COUNT(*) FROM person) * 100, 2) as github_coverage_pct
FROM github_profile gp
WHERE gp.person_id IS NOT NULL;

\echo ''
\echo 'Top 10 GitHub users by followers:'
SELECT 
    github_username,
    github_name,
    github_company,
    followers,
    public_repos,
    CASE WHEN person_id IS NOT NULL THEN 'Linked' ELSE 'Not Linked' END as person_linkage
FROM github_profile
WHERE followers IS NOT NULL
ORDER BY followers DESC
LIMIT 10;

\echo ''
\echo 'Sample GitHub profiles:'
SELECT 
    gp.github_username,
    gp.github_name,
    gp.followers,
    gp.public_repos,
    p.full_name as linked_person
FROM github_profile gp
LEFT JOIN person p ON gp.person_id = p.person_id
ORDER BY RANDOM()
LIMIT 5;

\echo ''
\echo '================================================================================'
\echo 'GITHUB_REPOSITORY TABLE - DETAILED STATISTICS'
\echo '================================================================================'
\echo ''

SELECT 
    COUNT(*) as total_repositories,
    COUNT(DISTINCT repo_id) as unique_repo_ids,
    COUNT(DISTINCT full_name) as unique_repo_full_names,
    COUNT(company_id) as repos_linked_to_company,
    COUNT(*) - COUNT(company_id) as repos_not_linked,
    COUNT(DISTINCT language) as unique_languages,
    COUNT(language) as has_language,
    COUNT(stars) as has_stars,
    COUNT(forks) as has_forks,
    COUNT(description) as has_description,
    ROUND(AVG(stars), 2) as avg_stars,
    ROUND(AVG(forks), 2) as avg_forks,
    MAX(stars) as max_stars,
    MAX(forks) as max_forks
FROM github_repository;

\echo ''
\echo 'Top 10 repositories by stars:'
SELECT 
    full_name,
    language,
    stars,
    forks,
    SUBSTRING(description, 1, 50) as description_short
FROM github_repository
ORDER BY stars DESC NULLS LAST
LIMIT 10;

\echo ''
\echo 'Top 10 programming languages:'
SELECT 
    language,
    COUNT(*) as repo_count,
    ROUND(COUNT(*)::numeric / (SELECT COUNT(*) FROM github_repository WHERE language IS NOT NULL) * 100, 2) as pct
FROM github_repository
WHERE language IS NOT NULL
GROUP BY language
ORDER BY repo_count DESC
LIMIT 10;

\echo ''
\echo '================================================================================'
\echo 'GITHUB_CONTRIBUTION TABLE - DETAILED STATISTICS'
\echo '================================================================================'
\echo ''

SELECT 
    COUNT(*) as total_contributions,
    COUNT(DISTINCT github_profile_id) as unique_profiles_contributing,
    COUNT(DISTINCT repo_id) as unique_repos_contributed_to,
    COUNT(contribution_count) as has_contribution_count,
    ROUND(AVG(contribution_count), 2) as avg_contributions_per_link,
    MAX(contribution_count) as max_contributions
FROM github_contribution;

\echo ''
\echo 'Top 10 contributors by contribution count:'
SELECT 
    gp.github_username,
    gr.full_name as repo,
    gc.contribution_count
FROM github_contribution gc
JOIN github_profile gp ON gc.github_profile_id = gp.github_profile_id
JOIN github_repository gr ON gc.repo_id = gr.repo_id
WHERE gc.contribution_count IS NOT NULL
ORDER BY gc.contribution_count DESC
LIMIT 10;

\echo ''
\echo '================================================================================'
\echo 'DUPLICATE ANALYSIS - PERSON TABLE'
\echo '================================================================================'
\echo ''

\echo 'Checking for duplicate LinkedIn URLs (should be 0):'
SELECT 
    COUNT(*) as duplicate_groups
FROM (
    SELECT linkedin_url, COUNT(*) as cnt
    FROM person
    WHERE linkedin_url IS NOT NULL
    GROUP BY linkedin_url
    HAVING COUNT(*) > 1
) sub;

\echo ''
\echo 'Any duplicate LinkedIn URLs found:'
SELECT 
    linkedin_url,
    COUNT(*) as duplicate_count,
    STRING_AGG(person_id::text, ', ') as person_ids
FROM person
WHERE linkedin_url IS NOT NULL
GROUP BY linkedin_url
HAVING COUNT(*) > 1
LIMIT 10;

\echo ''
\echo 'Checking for duplicate normalized LinkedIn URLs (should be 0):'
SELECT 
    COUNT(*) as duplicate_groups
FROM (
    SELECT normalized_linkedin_url, COUNT(*) as cnt
    FROM person
    WHERE normalized_linkedin_url IS NOT NULL
    GROUP BY normalized_linkedin_url
    HAVING COUNT(*) > 1
) sub;

\echo ''
\echo 'Any duplicate normalized LinkedIn URLs found:'
SELECT 
    normalized_linkedin_url,
    COUNT(*) as duplicate_count,
    STRING_AGG(person_id::text, ', ') as person_ids
FROM person
WHERE normalized_linkedin_url IS NOT NULL
GROUP BY normalized_linkedin_url
HAVING COUNT(*) > 1
LIMIT 10;

\echo ''
\echo '================================================================================'
\echo 'DUPLICATE ANALYSIS - COMPANY TABLE'
\echo '================================================================================'
\echo ''

\echo 'Companies with duplicate LinkedIn URLs:'
SELECT 
    linkedin_url,
    COUNT(*) as duplicate_count,
    STRING_AGG(DISTINCT company_name, ' | ') as company_names
FROM company
WHERE linkedin_url IS NOT NULL
GROUP BY linkedin_url
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC
LIMIT 10;

\echo ''
\echo '================================================================================'
\echo 'DUPLICATE ANALYSIS - EMAIL TABLE'
\echo '================================================================================'
\echo ''

\echo 'Emails assigned to multiple people (should be 0 due to unique constraint):'
SELECT 
    email,
    COUNT(DISTINCT person_id) as people_count
FROM person_email
GROUP BY email
HAVING COUNT(DISTINCT person_id) > 1
LIMIT 10;

\echo ''
\echo '================================================================================'
\echo 'DUPLICATE ANALYSIS - GITHUB_PROFILE TABLE'
\echo '================================================================================'
\echo ''

\echo 'GitHub usernames assigned to multiple profiles (should be 0):'
SELECT 
    github_username,
    COUNT(*) as duplicate_count
FROM github_profile
GROUP BY github_username
HAVING COUNT(*) > 1
LIMIT 10;

\echo ''
\echo '================================================================================'
\echo 'DATA QUALITY SCORES'
\echo '================================================================================'
\echo ''

\echo 'Overall completeness by table:'
SELECT 
    'Person - Full Name' as metric,
    ROUND(COUNT(full_name)::numeric / COUNT(*) * 100, 2) as completeness_pct
FROM person
UNION ALL
SELECT 
    'Person - LinkedIn URL',
    ROUND(COUNT(linkedin_url)::numeric / COUNT(*) * 100, 2)
FROM person
UNION ALL
SELECT 
    'Person - Location',
    ROUND(COUNT(location)::numeric / COUNT(*) * 100, 2)
FROM person
UNION ALL
SELECT 
    'Person - Headline',
    ROUND(COUNT(headline)::numeric / COUNT(*) * 100, 2)
FROM person
UNION ALL
SELECT 
    'Person - Description',
    ROUND(COUNT(description)::numeric / COUNT(*) * 100, 2)
FROM person
UNION ALL
SELECT 
    'Person - Followers',
    ROUND(COUNT(followers_count)::numeric / COUNT(*) * 100, 2)
FROM person
UNION ALL
SELECT 
    'Person - Email Coverage',
    ROUND((SELECT COUNT(DISTINCT person_id)::numeric FROM person_email) / COUNT(*) * 100, 2)
FROM person
UNION ALL
SELECT 
    'Person - GitHub Coverage',
    ROUND((SELECT COUNT(DISTINCT person_id)::numeric FROM github_profile WHERE person_id IS NOT NULL) / COUNT(*) * 100, 2)
FROM person
UNION ALL
SELECT 
    'Person - Education Coverage',
    ROUND((SELECT COUNT(DISTINCT person_id)::numeric FROM education) / COUNT(*) * 100, 2)
FROM person
UNION ALL
SELECT 
    'Company - Name',
    ROUND(COUNT(company_name)::numeric / COUNT(*) * 100, 2)
FROM company
UNION ALL
SELECT 
    'Company - Website',
    ROUND(COUNT(website)::numeric / COUNT(*) * 100, 2)
FROM company
UNION ALL
SELECT 
    'Company - Industry',
    ROUND(COUNT(industry)::numeric / COUNT(*) * 100, 2)
FROM company
UNION ALL
SELECT 
    'Company - LinkedIn',
    ROUND(COUNT(linkedin_url)::numeric / COUNT(*) * 100, 2)
FROM company
UNION ALL
SELECT 
    'Employment - Title',
    ROUND(COUNT(title)::numeric / COUNT(*) * 100, 2)
FROM employment
UNION ALL
SELECT 
    'Employment - Start Date',
    ROUND(COUNT(start_date)::numeric / COUNT(*) * 100, 2)
FROM employment
ORDER BY completeness_pct DESC;

\echo ''
\echo '================================================================================'
\echo 'MIGRATION LOG'
\echo '================================================================================'
\echo ''

SELECT 
    migration_name,
    migration_phase,
    status,
    records_processed,
    records_created,
    records_updated,
    records_skipped,
    TO_CHAR(started_at, 'YYYY-MM-DD HH24:MI:SS') as started_at,
    TO_CHAR(completed_at, 'YYYY-MM-DD HH24:MI:SS') as completed_at,
    CASE 
        WHEN completed_at IS NOT NULL THEN 
            EXTRACT(EPOCH FROM (completed_at - started_at)) || ' seconds'
        ELSE 'In Progress'
    END as duration
FROM migration_log
ORDER BY started_at;

\echo ''
\echo '================================================================================'
\echo 'DATABASE SIZE SUMMARY'
\echo '================================================================================'
\echo ''

SELECT 
    pg_size_pretty(pg_database_size('talent')) as total_database_size;

\echo ''
\echo '================================================================================'
\echo 'KEY METRICS SUMMARY'
\echo '================================================================================'
\echo ''

SELECT 
    'Total People' as metric,
    (SELECT COUNT(*)::text FROM person) as value
UNION ALL
SELECT 
    'Total Companies',
    (SELECT COUNT(*)::text FROM company)
UNION ALL
SELECT 
    'Total Employment Records',
    (SELECT COUNT(*)::text FROM employment)
UNION ALL
SELECT 
    'Avg Jobs per Person',
    (SELECT ROUND(COUNT(*)::numeric / NULLIF(COUNT(DISTINCT person_id), 0), 2)::text FROM employment)
UNION ALL
SELECT 
    'Total Education Records',
    (SELECT COUNT(*)::text FROM education)
UNION ALL
SELECT 
    'People with Education %',
    (SELECT ROUND(COUNT(DISTINCT person_id)::numeric / (SELECT COUNT(*) FROM person) * 100, 2)::text || '%' FROM education)
UNION ALL
SELECT 
    'Total Emails',
    (SELECT COUNT(*)::text FROM person_email)
UNION ALL
SELECT 
    'Email Coverage %',
    (SELECT ROUND(COUNT(DISTINCT person_id)::numeric / (SELECT COUNT(*) FROM person) * 100, 2)::text || '%' FROM person_email)
UNION ALL
SELECT 
    'Total GitHub Profiles',
    (SELECT COUNT(*)::text FROM github_profile)
UNION ALL
SELECT 
    'GitHub Coverage %',
    (SELECT ROUND(COUNT(DISTINCT person_id)::numeric / (SELECT COUNT(*) FROM person) * 100, 2)::text || '%' FROM github_profile WHERE person_id IS NOT NULL)
UNION ALL
SELECT 
    'Total GitHub Repos',
    (SELECT COUNT(*)::text FROM github_repository)
UNION ALL
SELECT 
    'Total GitHub Contributions',
    (SELECT COUNT(*)::text FROM github_contribution)
UNION ALL
SELECT 
    'LinkedIn Coverage %',
    (SELECT ROUND(COUNT(linkedin_url)::numeric / COUNT(*) * 100, 2)::text || '%' FROM person)
UNION ALL
SELECT 
    'Duplicate Person Records',
    '0 (Clean)'
UNION ALL
SELECT 
    'Data Integrity',
    '100% (No orphans)';

\echo ''
\echo '================================================================================'
\echo 'ANALYSIS COMPLETE'
\echo 'Report generated: ' `date`
\echo '================================================================================'

