#!/bin/bash
# ABOUTME: Complete GitHub enrichment and create profiles for high-value unmatched users
# ABOUTME: Enriches remaining profiles and optionally creates people records

echo "============================================================"
echo "🚀 Complete GitHub Profile Processing"
echo "============================================================"
echo ""

# Step 1: Enrich the remaining 46 profiles
echo "📊 Step 1: Enriching remaining 46 profiles..."
python3 github_enrichment.py --limit 50

echo ""
echo "============================================================"
echo ""

# Step 2: Run the fixed matching
echo "🔗 Step 2: Running improved matching..."
python3 match_github_profiles.py

echo ""
echo "============================================================"
echo ""

# Step 3: Analyze high-value unmatched profiles
echo "📋 Step 3: Analyzing high-value unmatched profiles..."
echo ""

python3 -c "
import sqlite3
from config import Config

conn = sqlite3.connect(Config.DB_PATH)
cursor = conn.cursor()

# Find high-value unmatched profiles
cursor.execute('''
    SELECT 
        github_username,
        github_name,
        github_email,
        github_company,
        github_location,
        followers,
        public_repos,
        github_bio
    FROM github_profiles
    WHERE person_id IS NULL
    AND followers > 10000
    ORDER BY followers DESC
    LIMIT 20
''')

high_value = cursor.fetchall()

if high_value:
    print('🌟 HIGH-VALUE UNMATCHED PROFILES (>10k followers)')
    print('='*60)
    
    for row in high_value:
        username, name, email, company, location, followers, repos, bio = row
        print(f'\\n@{username} ({followers:,} followers)')
        print(f'  Name: {name or \"Unknown\"}')
        if email:
            print(f'  Email: {email}')
        if company:
            print(f'  Company: {company}')
        if location:
            print(f'  Location: {location}')
        print(f'  Public repos: {repos}')
        if bio:
            bio_short = bio[:100] + '...' if len(bio) > 100 else bio
            print(f'  Bio: {bio_short}')
    
    print('\\n' + '='*60)
    print('\\n💡 These are influential developers not in your database.')
    print('Consider creating person records for them if they are:')
    print('  • Potential hires or advisors')
    print('  • Industry influencers')
    print('  • Open source maintainers in your tech stack')

# Overall stats
cursor.execute('''
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN person_id IS NOT NULL THEN 1 ELSE 0 END) as linked,
        SUM(CASE WHEN followers > 1000 THEN 1 ELSE 0 END) as influential,
        SUM(CASE WHEN github_email IS NOT NULL AND person_id IS NULL THEN 1 ELSE 0 END) as has_email_unmatched
    FROM github_profiles
''')

total, linked, influential, has_email = cursor.fetchone()

print(f'\\n📊 FINAL STATISTICS')
print('='*60)
print(f'Total GitHub profiles:          {total:,}')
print(f'Linked to people:              {linked:,} ({linked/total*100:.1f}%)')
print(f'Influential (>1k followers):    {influential:,}')
print(f'Unmatched with emails:         {has_email:,} (could create people records)')

conn.close()
"

echo ""
echo "============================================================"
echo ""

# Optional: Create people records for high-value profiles
echo "Would you like to create person records for high-value unmatched profiles?"
echo "(This will create new people for GitHub users with >10k followers)"
echo ""
read -p "Create new person records? (y/n): " create_people

if [ "$create_people" = "y" ] || [ "$create_people" = "Y" ]; then
    python3 -c "
import sqlite3
import hashlib
from datetime import datetime
from config import Config

conn = sqlite3.connect(Config.DB_PATH)
cursor = conn.cursor()

# Get high-value profiles to convert
cursor.execute('''
    SELECT 
        github_profile_id,
        github_username,
        github_name,
        github_email,
        github_company,
        github_location,
        followers
    FROM github_profiles
    WHERE person_id IS NULL
    AND followers > 10000
    AND github_name IS NOT NULL
''')

profiles = cursor.fetchall()
created = 0

for profile in profiles:
    profile_id, username, name, email, company, location, followers = profile
    
    # Parse name
    name_parts = name.split() if name else [username]
    first_name = name_parts[0] if name_parts else username
    last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
    
    # Generate person_id
    person_id = hashlib.md5(f'{username}_github'.encode()).hexdigest()[:12]
    
    # Create person record
    try:
        cursor.execute('''
            INSERT INTO people (
                person_id, first_name, last_name, full_name,
                primary_email, location, data_quality_score,
                created_at, updated_at, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            person_id, first_name, last_name, name,
            email, location, 0.8,  # High quality score for verified GitHub users
            datetime.now().isoformat(), datetime.now().isoformat(),
            f'High-value GitHub user: {followers:,} followers'
        ))
        
        # Link GitHub profile
        cursor.execute('''
            UPDATE github_profiles
            SET person_id = ?
            WHERE github_profile_id = ?
        ''', (person_id, profile_id))
        
        # Add to social_profiles
        cursor.execute('''
            INSERT INTO social_profiles (person_id, platform, profile_url, username)
            VALUES (?, 'github', ?, ?)
        ''', (person_id, f'https://github.com/{username}', username))
        
        # Add employment if company exists
        if company:
            cursor.execute('''
                INSERT INTO employment (person_id, company_name, is_current)
                VALUES (?, ?, 1)
            ''', (person_id, company))
        
        created += 1
        print(f'✅ Created person record for {name} (@{username})')
        
    except sqlite3.IntegrityError:
        print(f'⚠️  Skipped {username} (already exists)')
        continue

conn.commit()
conn.close()

print(f'\\n✅ Created {created} new person records for high-value GitHub users')
"
fi

echo ""
echo "============================================================"
echo "✅ GitHub Processing Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "1. Review unmatched profiles with emails - could be valuable contacts"
echo "2. Re-run matching after importing new people from CSVs"
echo "3. Consider reaching out to high-value profiles for recruiting"
echo ""
