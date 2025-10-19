#!/bin/bash
# Export random sample of 200 candidates with full profile data

DB="/Users/charlie.kerr/Documents/CK Docs/FINAL_DATABASE/talent_intelligence.db"
OUTPUT="sample_200_candidates.csv"

echo "Exporting random sample of 200 candidates..."

sqlite3 -header -csv "$DB" "
SELECT 
    p.person_id,
    p.first_name,
    p.last_name,
    p.primary_email,
    p.location,
    p.status,
    p.data_quality_score,
    
    -- Current employment
    e.company_name as current_company,
    e.title as current_title,
    c.website as company_website,
    c.linkedin_url as company_linkedin,
    
    -- Social profiles
    (SELECT profile_url FROM social_profiles 
     WHERE person_id = p.person_id AND platform = 'linkedin' LIMIT 1) as linkedin_url,
    (SELECT profile_url FROM social_profiles 
     WHERE person_id = p.person_id AND platform = 'github' LIMIT 1) as github_url,
    (SELECT profile_url FROM social_profiles 
     WHERE person_id = p.person_id AND platform = 'twitter' LIMIT 1) as twitter_url,
    (SELECT profile_url FROM social_profiles 
     WHERE person_id = p.person_id AND platform = 'website' LIMIT 1) as personal_website,
    
    -- GitHub stats (if available)
    gp.github_username,
    gp.followers as github_followers,
    gp.following as github_following,
    gp.public_repos as github_repos,
    gp.num_contributions as github_contributions,
    gp.github_company,
    gp.github_location,
    gp.match_confidence as github_match_confidence,
    gp.match_method as github_match_method,
    
    -- Additional emails
    (SELECT GROUP_CONCAT(email, '; ') FROM emails 
     WHERE person_id = p.person_id AND is_primary = 0) as additional_emails,
    
    -- Metadata
    p.created_at,
    p.updated_at
    
FROM people p
LEFT JOIN employment e ON p.person_id = e.person_id AND e.is_current = 1
LEFT JOIN companies c ON e.company_id = c.company_id
LEFT JOIN github_profiles gp ON p.person_id = gp.person_id

ORDER BY RANDOM()
LIMIT 200;
" > "$OUTPUT"

if [ $? -eq 0 ]; then
    echo "✅ Success! Exported to: $OUTPUT"
    echo ""
    echo "File contains:"
    wc -l "$OUTPUT"
    echo ""
    echo "Preview (first 5 rows):"
    head -6 "$OUTPUT" | cut -c1-120
    echo ""
else
    echo "❌ Export failed"
    exit 1
fi
