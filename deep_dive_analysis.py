#!/usr/bin/env python3
"""
COMPREHENSIVE DATABASE DEEP DIVE ANALYSIS
==========================================
Analyzes data quality, coverage, and gaps across:
- People profiles and enrichment
- Company data (LinkedIn, GitHub, funding)
- VC portfolios and ecosystem coverage
- Identifies specific gaps and opportunities for data enrichment

Generated: October 21, 2025
"""

import psycopg2
import psycopg2.extras
from datetime import datetime
from collections import defaultdict
import json

# Database connection
def get_connection():
    return psycopg2.connect(
        host='localhost',
        port='5432',
        database='talent',
        user='charlie.kerr'
    )

def format_number(num):
    """Format number with commas"""
    if num is None:
        return "0"
    return f"{num:,}"

def format_percent(numerator, denominator):
    """Calculate and format percentage"""
    if denominator == 0:
        return "0.00%"
    return f"{(numerator / denominator * 100):.2f}%"

def print_section(title, level=1):
    """Print a formatted section header"""
    if level == 1:
        print(f"\n{'='*80}")
        print(f"{title}")
        print(f"{'='*80}\n")
    elif level == 2:
        print(f"\n{'-'*80}")
        print(f"{title}")
        print(f"{'-'*80}\n")
    else:
        print(f"\n{title}")
        print(f"{'-'*len(title)}\n")

def main():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    print(f"""
{'='*80}
COMPREHENSIVE DATABASE DEEP DIVE ANALYSIS
{'='*80}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Database: PostgreSQL 'talent' @ localhost:5432
{'='*80}
""")
    
    # ========================================================================
    # SECTION 1: PEOPLE PROFILES - GRANULAR ENRICHMENT BREAKDOWN
    # ========================================================================
    print_section("SECTION 1: PEOPLE PROFILES - ENRICHMENT ANALYSIS", level=1)
    
    # Basic people counts
    cur.execute("SELECT COUNT(*) as total FROM person")
    total_people = cur.fetchone()['total']
    print(f"📊 Total People in Database: {format_number(total_people)}\n")
    
    # Detailed field coverage
    print_section("Field-by-Field Coverage", level=3)
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(full_name) as has_full_name,
            COUNT(first_name) as has_first_name,
            COUNT(last_name) as has_last_name,
            COUNT(linkedin_url) as has_linkedin,
            COUNT(linkedin_slug) as has_linkedin_slug,
            COUNT(location) as has_location,
            COUNT(headline) as has_headline,
            COUNT(description) as has_description,
            COUNT(followers_count) as has_followers,
            COUNT(profile_img_url) as has_profile_img,
            COUNT(is_hiring_bool) as has_hiring_status,
            COUNT(open_to_work_bool) as has_open_to_work,
            COUNT(refreshed_at) as has_refreshed_at
        FROM person
    """)
    coverage = cur.fetchone()
    
    fields = [
        ('Full Name', coverage['has_full_name']),
        ('First Name', coverage['has_first_name']),
        ('Last Name', coverage['has_last_name']),
        ('LinkedIn URL', coverage['has_linkedin']),
        ('LinkedIn Slug', coverage['has_linkedin_slug']),
        ('Location', coverage['has_location']),
        ('Headline', coverage['has_headline']),
        ('Description/Bio', coverage['has_description']),
        ('Follower Count', coverage['has_followers']),
        ('Profile Image', coverage['has_profile_img']),
        ('Hiring Status', coverage['has_hiring_status']),
        ('Open to Work', coverage['has_open_to_work']),
        ('Last Refreshed', coverage['has_refreshed_at']),
    ]
    
    print(f"{'Field':<25} {'Count':>15} {'Coverage':>12} {'Gap':>15}")
    print(f"{'-'*70}")
    for field_name, count in fields:
        gap = total_people - count
        print(f"{field_name:<25} {format_number(count):>15} {format_percent(count, total_people):>12} {format_number(gap):>15}")
    
    # Email coverage
    print_section("Email Coverage", level=3)
    cur.execute("""
        SELECT 
            COUNT(DISTINCT person_id) as people_with_emails,
            COUNT(*) as total_emails,
            COUNT(DISTINCT email) as unique_emails,
            COUNT(CASE WHEN is_primary THEN 1 END) as primary_emails,
            COUNT(CASE WHEN email_type = 'work' THEN 1 END) as work_emails,
            COUNT(CASE WHEN email_type = 'personal' THEN 1 END) as personal_emails,
            COUNT(CASE WHEN verified THEN 1 END) as verified_emails
        FROM person_email
    """)
    email_stats = cur.fetchone()
    
    print(f"People with Emails: {format_number(email_stats['people_with_emails'])} ({format_percent(email_stats['people_with_emails'], total_people)})")
    print(f"Total Email Records: {format_number(email_stats['total_emails'])}")
    print(f"Unique Emails: {format_number(email_stats['unique_emails'])}")
    print(f"Primary Emails: {format_number(email_stats['primary_emails'])}")
    print(f"Work Emails: {format_number(email_stats['work_emails'])}")
    print(f"Personal Emails: {format_number(email_stats['personal_emails'])}")
    print(f"Verified Emails: {format_number(email_stats['verified_emails'])}")
    print(f"\n❌ Email Gap: {format_number(total_people - email_stats['people_with_emails'])} people ({format_percent(total_people - email_stats['people_with_emails'], total_people)})")
    
    # GitHub profile coverage
    print_section("GitHub Profile Coverage", level=3)
    cur.execute("""
        SELECT 
            COUNT(*) as total_github_profiles,
            COUNT(DISTINCT github_username) as unique_usernames,
            COUNT(person_id) as linked_to_person,
            COUNT(*) - COUNT(person_id) as not_linked,
            COUNT(github_name) as has_name,
            COUNT(github_email) as has_email,
            COUNT(github_company) as has_company,
            COUNT(location) as has_location,
            COUNT(bio) as has_bio,
            COUNT(twitter_username) as has_twitter,
            COUNT(CASE WHEN followers > 0 THEN 1 END) as has_followers,
            COUNT(CASE WHEN public_repos > 0 THEN 1 END) as has_repos,
            ROUND(AVG(followers), 2) as avg_followers,
            ROUND(AVG(public_repos), 2) as avg_repos
        FROM github_profile
    """)
    github_stats = cur.fetchone()
    
    cur.execute("""
        SELECT COUNT(DISTINCT gp.person_id) as people_with_github
        FROM github_profile gp
        WHERE gp.person_id IS NOT NULL
    """)
    people_with_github = cur.fetchone()['people_with_github']
    
    print(f"Total GitHub Profiles: {format_number(github_stats['total_github_profiles'])}")
    print(f"Profiles Linked to People: {format_number(github_stats['linked_to_person'])} ({format_percent(github_stats['linked_to_person'], github_stats['total_github_profiles'])})")
    print(f"Unlinked GitHub Profiles: {format_number(github_stats['not_linked'])} (potential matching opportunities)")
    print(f"People with GitHub: {format_number(people_with_github)} ({format_percent(people_with_github, total_people)})")
    print(f"\n❌ GitHub Gap: {format_number(total_people - people_with_github)} people ({format_percent(total_people - people_with_github, total_people)})")
    
    print(f"\nGitHub Profile Field Coverage:")
    print(f"  - Has Display Name: {format_number(github_stats['has_name'])} ({format_percent(github_stats['has_name'], github_stats['total_github_profiles'])})")
    print(f"  - Has Email: {format_number(github_stats['has_email'])} ({format_percent(github_stats['has_email'], github_stats['total_github_profiles'])})")
    print(f"  - Has Company: {format_number(github_stats['has_company'])} ({format_percent(github_stats['has_company'], github_stats['total_github_profiles'])})")
    print(f"  - Has Location: {format_number(github_stats['has_location'])} ({format_percent(github_stats['has_location'], github_stats['total_github_profiles'])})")
    print(f"  - Has Bio: {format_number(github_stats['has_bio'])} ({format_percent(github_stats['has_bio'], github_stats['total_github_profiles'])})")
    print(f"  - Has Twitter: {format_number(github_stats['has_twitter'])} ({format_percent(github_stats['has_twitter'], github_stats['total_github_profiles'])})")
    print(f"  - Has Followers: {format_number(github_stats['has_followers'])} (avg: {github_stats['avg_followers']})")
    print(f"  - Has Repos: {format_number(github_stats['has_repos'])} (avg: {github_stats['avg_repos']})")
    
    # Education coverage
    print_section("Education Coverage", level=3)
    cur.execute("""
        SELECT 
            COUNT(DISTINCT person_id) as people_with_education,
            COUNT(*) as total_education_records,
            COUNT(school_name) as has_school,
            COUNT(degree) as has_degree,
            COUNT(field_of_study) as has_field,
            COUNT(start_date) as has_start_date,
            COUNT(end_date) as has_end_date
        FROM education
    """)
    edu_stats = cur.fetchone()
    
    print(f"People with Education Records: {format_number(edu_stats['people_with_education'])} ({format_percent(edu_stats['people_with_education'], total_people)})")
    print(f"Total Education Records: {format_number(edu_stats['total_education_records'])}")
    print(f"❌ Education Gap: {format_number(total_people - edu_stats['people_with_education'])} people ({format_percent(total_people - edu_stats['people_with_education'], total_people)})")
    
    # Employment coverage
    print_section("Employment Coverage", level=3)
    cur.execute("""
        SELECT 
            COUNT(DISTINCT person_id) as people_with_employment,
            COUNT(*) as total_employment_records,
            ROUND(COUNT(*)::numeric / NULLIF(COUNT(DISTINCT person_id), 0), 2) as avg_jobs_per_person,
            COUNT(CASE WHEN end_date IS NULL THEN 1 END) as current_jobs,
            COUNT(title) as has_title,
            COUNT(start_date) as has_start_date,
            COUNT(end_date) as has_end_date,
            COUNT(department) as has_department
        FROM employment
    """)
    emp_stats = cur.fetchone()
    
    print(f"People with Employment Records: {format_number(emp_stats['people_with_employment'])} ({format_percent(emp_stats['people_with_employment'], total_people)})")
    print(f"Total Employment Records: {format_number(emp_stats['total_employment_records'])}")
    print(f"Average Jobs per Person: {emp_stats['avg_jobs_per_person']}")
    print(f"Current Jobs: {format_number(emp_stats['current_jobs'])}")
    print(f"With Job Title: {format_number(emp_stats['has_title'])} ({format_percent(emp_stats['has_title'], emp_stats['total_employment_records'])})")
    print(f"With Start Date: {format_number(emp_stats['has_start_date'])} ({format_percent(emp_stats['has_start_date'], emp_stats['total_employment_records'])})")
    
    # ========================================================================
    # SECTION 2: COMPANIES - DETAILED ANALYSIS
    # ========================================================================
    print_section("SECTION 2: COMPANIES - ENRICHMENT & COVERAGE", level=1)
    
    cur.execute("SELECT COUNT(*) as total FROM company")
    total_companies = cur.fetchone()['total']
    print(f"📊 Total Companies in Database: {format_number(total_companies)}\n")
    
    # Company field coverage
    print_section("Company Field Coverage", level=3)
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(company_name) as has_name,
            COUNT(linkedin_url) as has_linkedin,
            COUNT(website_url) as has_website,
            COUNT(industry) as has_industry,
            COUNT(size_bucket) as has_size,
            COUNT(hq) as has_location,
            COUNT(founded_year) as has_founded_year,
            COUNT(DISTINCT linkedin_url) as unique_linkedin
        FROM company
    """)
    comp_coverage = cur.fetchone()
    
    print(f"{'Field':<25} {'Count':>15} {'Coverage':>12} {'Gap':>15}")
    print(f"{'-'*70}")
    comp_fields = [
        ('Company Name', comp_coverage['has_name']),
        ('LinkedIn URL', comp_coverage['has_linkedin']),
        ('Website', comp_coverage['has_website']),
        ('Industry', comp_coverage['has_industry']),
        ('Company Size', comp_coverage['has_size']),
        ('Location', comp_coverage['has_location']),
        ('Founded Year', comp_coverage['has_founded_year']),
    ]
    for field_name, count in comp_fields:
        gap = total_companies - count
        print(f"{field_name:<25} {format_number(count):>15} {format_percent(count, total_companies):>12} {format_number(gap):>15}")
    
    # GitHub organization/repository coverage
    print_section("Company GitHub Coverage", level=3)
    cur.execute("""
        SELECT 
            COUNT(DISTINCT company_id) as companies_with_repos,
            COUNT(*) as total_repos,
            COUNT(DISTINCT owner_username) as unique_orgs,
            COUNT(language) as repos_with_language,
            COUNT(DISTINCT language) as unique_languages,
            ROUND(AVG(stars), 2) as avg_stars,
            ROUND(AVG(forks), 2) as avg_forks
        FROM github_repository
        WHERE company_id IS NOT NULL
    """)
    comp_github = cur.fetchone()
    
    cur.execute("""
        SELECT COUNT(*) as orphan_repos
        FROM github_repository
        WHERE company_id IS NULL
    """)
    orphan_repos = cur.fetchone()['orphan_repos']
    
    print(f"Companies with GitHub Repos: {format_number(comp_github['companies_with_repos'])} ({format_percent(comp_github['companies_with_repos'], total_companies)})")
    print(f"❌ Companies without GitHub: {format_number(total_companies - comp_github['companies_with_repos'])} ({format_percent(total_companies - comp_github['companies_with_repos'], total_companies)})")
    print(f"\nTotal Repositories: {format_number(comp_github['total_repos'])}")
    print(f"Repos not linked to companies: {format_number(orphan_repos)} (matching opportunity)")
    print(f"Unique GitHub Orgs/Owners: {format_number(comp_github['unique_orgs'])}")
    print(f"Unique Languages: {format_number(comp_github['unique_languages'])}")
    print(f"Average Stars: {comp_github['avg_stars']}")
    print(f"Average Forks: {comp_github['avg_forks']}")
    
    # Employee vs Non-Employee Contributors
    print_section("GitHub Contributors Analysis", level=3)
    cur.execute("""
        SELECT 
            COUNT(DISTINCT gc.github_profile_id) as total_contributors,
            COUNT(DISTINCT CASE WHEN gp.person_id IS NOT NULL THEN gc.github_profile_id END) as known_employees,
            COUNT(DISTINCT CASE WHEN gp.person_id IS NULL THEN gc.github_profile_id END) as unknown_contributors,
            COUNT(DISTINCT gc.repo_id) as repos_with_contributors,
            SUM(gc.contribution_count) as total_contributions
        FROM github_contribution gc
        LEFT JOIN github_profile gp ON gc.github_profile_id = gp.github_profile_id
    """)
    contrib_stats = cur.fetchone()
    
    print(f"Total Contributors: {format_number(contrib_stats['total_contributors'])}")
    print(f"  - Known Employees (linked to people): {format_number(contrib_stats['known_employees'])} ({format_percent(contrib_stats['known_employees'], contrib_stats['total_contributors'])})")
    print(f"  - External/Unknown Contributors: {format_number(contrib_stats['unknown_contributors'])} ({format_percent(contrib_stats['unknown_contributors'], contrib_stats['total_contributors'])})")
    print(f"Repositories with Contributors: {format_number(contrib_stats['repos_with_contributors'])}")
    print(f"Total Contributions Tracked: {format_number(contrib_stats['total_contributions'])}")
    
    # Company funding data
    print_section("Venture Capital Funding Coverage", level=3)
    
    # Check if funding tables exist
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('company_funding_round', 'funding_rounds')
        ) as funding_exists
    """)
    funding_exists = cur.fetchone()['funding_exists']
    
    if funding_exists:
        # Try both possible table names
        try:
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT company_id) as companies_with_funding,
                    COUNT(*) as total_funding_rounds,
                    COUNT(amount_usd) as rounds_with_amount,
                    COUNT(announced_date) as rounds_with_date,
                    COUNT(round_type) as rounds_with_type,
                    SUM(amount_usd) as total_funding_amount
                FROM company_funding_round
                WHERE company_id IS NOT NULL
            """)
            funding_stats = cur.fetchone()
        except:
            try:
                cur.execute("""
                    SELECT 
                        COUNT(DISTINCT company_id) as companies_with_funding,
                        COUNT(*) as total_funding_rounds,
                        COUNT(amount_usd) as rounds_with_amount,
                        COUNT(announced_date) as rounds_with_date,
                        COUNT(round_type) as rounds_with_type,
                        SUM(amount_usd) as total_funding_amount
                    FROM funding_rounds
                    WHERE company_id IS NOT NULL
                """)
                funding_stats = cur.fetchone()
            except:
                funding_stats = None
        
        if funding_stats and funding_stats['companies_with_funding']:
            print(f"Companies with Funding Data: {format_number(funding_stats['companies_with_funding'])} ({format_percent(funding_stats['companies_with_funding'], total_companies)})")
            print(f"❌ Companies without Funding Data: {format_number(total_companies - funding_stats['companies_with_funding'])} ({format_percent(total_companies - funding_stats['companies_with_funding'], total_companies)})")
            print(f"\nTotal Funding Rounds: {format_number(funding_stats['total_funding_rounds'])}")
            print(f"  - With Amount: {format_number(funding_stats['rounds_with_amount'])} ({format_percent(funding_stats['rounds_with_amount'], funding_stats['total_funding_rounds'])})")
            print(f"  - With Date: {format_number(funding_stats['rounds_with_date'])} ({format_percent(funding_stats['rounds_with_date'], funding_stats['total_funding_rounds'])})")
            print(f"  - With Round Type: {format_number(funding_stats['rounds_with_type'])} ({format_percent(funding_stats['rounds_with_type'], funding_stats['total_funding_rounds'])})")
            
            if funding_stats['total_funding_amount']:
                print(f"Total Funding Tracked: ${funding_stats['total_funding_amount']:,.0f} USD")
                
            # Funding round type breakdown
            try:
                cur.execute("""
                    SELECT round_type, COUNT(*) as count
                    FROM company_funding_round
                    WHERE round_type IS NOT NULL
                    GROUP BY round_type
                    ORDER BY count DESC
                    LIMIT 10
                """)
                print(f"\nTop Funding Round Types:")
                for row in cur.fetchall():
                    print(f"  - {row['round_type']}: {format_number(row['count'])}")
            except:
                pass
        else:
            print(f"⚠️  Funding tables exist but are EMPTY")
            print(f"❌ Companies with Funding Data: 0 (0.00%)")
            print(f"❌ Gap: All {format_number(total_companies)} companies need funding data")
    else:
        print(f"⚠️  No funding tables found in database")
        print(f"❌ Companies with Funding Data: 0 (0.00%)")
        print(f"❌ Gap: All {format_number(total_companies)} companies need funding data")
    
    # ========================================================================
    # SECTION 3: VC PORTFOLIOS & ECOSYSTEMS
    # ========================================================================
    print_section("SECTION 3: VC PORTFOLIOS & CRYPTO ECOSYSTEMS", level=1)
    
    # Check if ecosystem tables exist
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'crypto_ecosystem'
        ) as ecosystem_exists
    """)
    ecosystem_exists = cur.fetchone()['ecosystem_exists']
    
    if ecosystem_exists:
        # VC Portfolio analysis
        print_section("VC Portfolio Coverage", level=3)
        cur.execute("""
            SELECT 
                COUNT(*) as total_ecosystems,
                COUNT(CASE WHEN ecosystem_type = 'vc_portfolio' THEN 1 END) as vc_portfolios,
                COUNT(CASE WHEN ecosystem_type = 'protocol' THEN 1 END) as protocols,
                COUNT(CASE WHEN ecosystem_type IN ('layer1', 'layer2') THEN 1 END) as layer_protocols,
                COUNT(description) as has_description,
                COUNT(website_url) as has_website
            FROM crypto_ecosystem
        """)
        eco_stats = cur.fetchone()
        
        print(f"Total Ecosystems Tracked: {format_number(eco_stats['total_ecosystems'])}")
        print(f"  - VC Portfolios: {format_number(eco_stats['vc_portfolios'])}")
        print(f"  - Protocols: {format_number(eco_stats['protocols'])}")
        print(f"  - Layer 1/2: {format_number(eco_stats['layer_protocols'])}")
        print(f"  - With Description: {format_number(eco_stats['has_description'])}")
        print(f"  - With Website: {format_number(eco_stats['has_website'])}")
        
        if eco_stats['vc_portfolios'] > 0:
            # VC portfolio company coverage
            print_section("VC Portfolio Companies", level=3)
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT ce.company_id) as portfolio_companies,
                    COUNT(DISTINCT ce.ecosystem_id) as vcs_with_portfolio,
                    COUNT(*) as total_relationships
                FROM company_ecosystem ce
                JOIN crypto_ecosystem e ON ce.ecosystem_id = e.ecosystem_id
                WHERE e.ecosystem_type = 'vc_portfolio'
            """)
            vc_comp_stats = cur.fetchone()
            
            print(f"Portfolio Companies Identified: {format_number(vc_comp_stats['portfolio_companies'])}")
            print(f"VCs with Portfolio Data: {format_number(vc_comp_stats['vcs_with_portfolio'])}")
            print(f"Total Company-VC Relationships: {format_number(vc_comp_stats['total_relationships'])}")
            
            # Portfolio company employee coverage
            print_section("VC Portfolio Company - Employee Coverage", level=3)
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT e.person_id) as portfolio_company_employees,
                    COUNT(DISTINCT e.company_id) as companies_with_employees,
                    ROUND(AVG(emp_per_company.emp_count), 2) as avg_employees_per_company
                FROM employment e
                JOIN company_ecosystem ce ON e.company_id = ce.company_id
                JOIN crypto_ecosystem eco ON ce.ecosystem_id = eco.ecosystem_id
                LEFT JOIN (
                    SELECT company_id, COUNT(DISTINCT person_id) as emp_count
                    FROM employment
                    GROUP BY company_id
                ) emp_per_company ON e.company_id = emp_per_company.company_id
                WHERE eco.ecosystem_type = 'vc_portfolio'
            """)
            vc_emp_stats = cur.fetchone()
            
            if vc_emp_stats and vc_emp_stats['portfolio_company_employees']:
                print(f"Portfolio Company Employees: {format_number(vc_emp_stats['portfolio_company_employees'])}")
                print(f"Portfolio Companies with Employee Data: {format_number(vc_emp_stats['companies_with_employees'])}")
                print(f"Avg Employees per Portfolio Company: {vc_emp_stats['avg_employees_per_company']}")
                
                gap = vc_comp_stats['portfolio_companies'] - vc_emp_stats['companies_with_employees']
                print(f"❌ Portfolio Companies without Employee Data: {format_number(gap)}")
            else:
                print(f"⚠️  No employee data linked to portfolio companies yet")
            
            # Portfolio company GitHub coverage
            print_section("VC Portfolio Company - GitHub Coverage", level=3)
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT gr.company_id) as companies_with_github,
                    COUNT(DISTINCT gr.repo_id) as total_repos,
                    COUNT(DISTINCT gc.github_profile_id) as total_contributors,
                    COUNT(DISTINCT CASE WHEN gp.person_id IS NOT NULL THEN gc.github_profile_id END) as known_employee_contributors
                FROM company_ecosystem ce
                JOIN crypto_ecosystem eco ON ce.ecosystem_id = eco.ecosystem_id
                JOIN github_repository gr ON ce.company_id = gr.company_id
                LEFT JOIN github_contribution gc ON gr.repo_id = gc.repo_id
                LEFT JOIN github_profile gp ON gc.github_profile_id = gp.github_profile_id
                WHERE eco.ecosystem_type = 'vc_portfolio'
            """)
            vc_github_stats = cur.fetchone()
            
            if vc_github_stats and vc_github_stats['companies_with_github']:
                print(f"Portfolio Companies with GitHub: {format_number(vc_github_stats['companies_with_github'])}")
                print(f"Total Repositories: {format_number(vc_github_stats['total_repos'])}")
                print(f"Total Contributors: {format_number(vc_github_stats['total_contributors'])}")
                print(f"  - Known Employees: {format_number(vc_github_stats['known_employee_contributors'])}")
                
                gap = vc_comp_stats['portfolio_companies'] - vc_github_stats['companies_with_github']
                print(f"❌ Portfolio Companies without GitHub: {format_number(gap)}")
            else:
                print(f"⚠️  No GitHub data linked to portfolio companies yet")
        
        # Ecosystem repository coverage
        print_section("Ecosystem Repository Coverage", level=3)
        cur.execute("""
            SELECT 
                COUNT(DISTINCT ecosystem_id) as ecosystems_with_repos,
                COUNT(DISTINCT repo_id) as repos_in_ecosystems,
                COUNT(*) as total_mappings
            FROM ecosystem_repository
        """)
        eco_repo_stats = cur.fetchone()
        
        print(f"Ecosystems with Repositories: {format_number(eco_repo_stats['ecosystems_with_repos'])}")
        print(f"Repositories in Ecosystems: {format_number(eco_repo_stats['repos_in_ecosystems'])}")
        print(f"Total Ecosystem-Repo Mappings: {format_number(eco_repo_stats['total_mappings'])}")
        
        # Person ecosystem activity
        print_section("Developer Ecosystem Activity", level=3)
        cur.execute("""
            SELECT 
                COUNT(DISTINCT person_id) as people_in_ecosystems,
                COUNT(DISTINCT ecosystem_id) as ecosystems_with_activity,
                COUNT(*) as total_person_ecosystem_links,
                SUM(contribution_count) as total_contributions,
                ROUND(AVG(contribution_count), 2) as avg_contributions
            FROM person_ecosystem_activity
        """)
        eco_person_stats = cur.fetchone()
        
        if eco_person_stats and eco_person_stats['people_in_ecosystems']:
            print(f"People with Ecosystem Activity: {format_number(eco_person_stats['people_in_ecosystems'])} ({format_percent(eco_person_stats['people_in_ecosystems'], total_people)})")
            print(f"Ecosystems with Developer Activity: {format_number(eco_person_stats['ecosystems_with_activity'])}")
            print(f"Total Contributions: {format_number(eco_person_stats['total_contributions'])}")
            print(f"Average Contributions per Person-Ecosystem: {eco_person_stats['avg_contributions']}")
        else:
            print(f"⚠️  Person ecosystem activity table is empty")
            print(f"   Run update_person_ecosystem_activity() to populate")
    else:
        print(f"⚠️  Ecosystem tables not found in database")
        print(f"   Run migration_scripts/02_ecosystem_schema.sql to create them")
    
    # ========================================================================
    # SECTION 4: GAP ANALYSIS & RECOMMENDATIONS
    # ========================================================================
    print_section("SECTION 4: GAP ANALYSIS & ENRICHMENT PRIORITIES", level=1)
    
    print_section("Critical Data Gaps (Priority Order)", level=3)
    
    gaps = []
    
    # Calculate gap percentages
    email_gap_pct = (total_people - email_stats['people_with_emails']) / total_people * 100
    github_gap_pct = (total_people - people_with_github) / total_people * 100
    education_gap_pct = (total_people - edu_stats['people_with_education']) / total_people * 100
    
    gaps.append({
        'category': 'People - Email Addresses',
        'missing': total_people - email_stats['people_with_emails'],
        'gap_pct': email_gap_pct,
        'priority': 'CRITICAL',
        'action': 'Enrich from GitHub profiles, LinkedIn scraping, or external data sources'
    })
    
    gaps.append({
        'category': 'People - GitHub Profiles',
        'missing': total_people - people_with_github,
        'gap_pct': github_gap_pct,
        'priority': 'HIGH',
        'action': f'Match {format_number(github_stats["not_linked"])} unlinked GitHub profiles; GitHub API enrichment'
    })
    
    gaps.append({
        'category': 'People - Education History',
        'missing': total_people - edu_stats['people_with_education'],
        'gap_pct': education_gap_pct,
        'priority': 'MEDIUM',
        'action': 'LinkedIn profile scraping for education history'
    })
    
    comp_linkedin_gap_pct = (total_companies - comp_coverage['has_linkedin']) / total_companies * 100
    gaps.append({
        'category': 'Companies - LinkedIn URLs',
        'missing': total_companies - comp_coverage['has_linkedin'],
        'gap_pct': comp_linkedin_gap_pct,
        'priority': 'HIGH',
        'action': 'Domain → LinkedIn mapping; external enrichment services'
    })
    
    comp_github_gap_pct = (total_companies - comp_github['companies_with_repos']) / total_companies * 100
    gaps.append({
        'category': 'Companies - GitHub Organizations',
        'missing': total_companies - comp_github['companies_with_repos'],
        'gap_pct': comp_github_gap_pct,
        'priority': 'HIGH',
        'action': f'Match {format_number(orphan_repos)} orphan repos; search GitHub for company orgs'
    })
    
    if funding_exists and funding_stats and funding_stats['companies_with_funding']:
        funding_gap_pct = (total_companies - funding_stats['companies_with_funding']) / total_companies * 100
        gaps.append({
            'category': 'Companies - Funding Data',
            'missing': total_companies - funding_stats['companies_with_funding'],
            'gap_pct': funding_gap_pct,
            'priority': 'MEDIUM',
            'action': 'Crunchbase API, PitchBook, or venture capital databases'
        })
    else:
        gaps.append({
            'category': 'Companies - Funding Data',
            'missing': total_companies,
            'gap_pct': 100.0,
            'priority': 'CRITICAL',
            'action': 'Create and populate funding tables from Crunchbase/PitchBook data'
        })
    
    # Sort by gap percentage
    gaps.sort(key=lambda x: x['gap_pct'], reverse=True)
    
    print(f"{'#':<3} {'Category':<35} {'Missing':>15} {'Gap %':>10} {'Priority':<10} {'Action'}")
    print(f"{'-'*130}")
    for i, gap in enumerate(gaps, 1):
        print(f"{i:<3} {gap['category']:<35} {format_number(gap['missing']):>15} {gap['gap_pct']:>9.2f}% {gap['priority']:<10} {gap['action']}")
    
    print_section("Recommended Enrichment Strategy", level=3)
    print("""
1. **IMMEDIATE PRIORITIES** (Week 1-2):
   - Match unlinked GitHub profiles to people (low-hanging fruit)
   - Map orphan repositories to companies
   - Set up funding data import pipeline

2. **SHORT-TERM** (Month 1):
   - Email enrichment via GitHub API and pattern-based generation
   - Company LinkedIn URL discovery via domain mapping
   - GitHub organization discovery for companies

3. **MEDIUM-TERM** (Months 2-3):
   - Full LinkedIn profile scraping for education/experience gaps
   - Funding data import from Crunchbase/PitchBook
   - Portfolio company mapping for known VCs

4. **ONGOING**:
   - Continuous GitHub contribution tracking
   - Automated profile refreshing for stale data
   - Social profile discovery (Twitter, personal websites)
""")
    
    print_section("Key Metrics Summary", level=3)
    print(f"""
{'='*80}
DATA COVERAGE SCORECARD
{'='*80}

PEOPLE (n={format_number(total_people)}):
  ✅ LinkedIn Profiles:     {format_percent(coverage['has_linkedin'], total_people):<8} ({format_number(coverage['has_linkedin'])})
  {'✅' if email_gap_pct < 50 else '⚠️' if email_gap_pct < 80 else '❌'}  Email Coverage:        {format_percent(email_stats['people_with_emails'], total_people):<8} ({format_number(email_stats['people_with_emails'])})
  {'✅' if github_gap_pct < 50 else '⚠️' if github_gap_pct < 80 else '❌'}  GitHub Coverage:       {format_percent(people_with_github, total_people):<8} ({format_number(people_with_github)})
  {'✅' if education_gap_pct < 50 else '⚠️' if education_gap_pct < 80 else '❌'}  Education Coverage:    {format_percent(edu_stats['people_with_education'], total_people):<8} ({format_number(edu_stats['people_with_education'])})

COMPANIES (n={format_number(total_companies)}):
  ✅ Company Names:         {format_percent(comp_coverage['has_name'], total_companies):<8} ({format_number(comp_coverage['has_name'])})
  {'✅' if comp_linkedin_gap_pct < 20 else '⚠️' if comp_linkedin_gap_pct < 50 else '❌'}  LinkedIn URLs:        {format_percent(comp_coverage['has_linkedin'], total_companies):<8} ({format_number(comp_coverage['has_linkedin'])})
  {'✅' if comp_github_gap_pct < 30 else '⚠️' if comp_github_gap_pct < 70 else '❌'}  GitHub Organizations: {format_percent(comp_github['companies_with_repos'], total_companies):<8} ({format_number(comp_github['companies_with_repos'])})
  {'✅' if funding_exists and funding_stats and funding_stats['companies_with_funding'] > total_companies * 0.3 else '❌'}  Funding Data:         {format_percent(funding_stats['companies_with_funding'] if funding_exists and funding_stats else 0, total_companies):<8} ({format_number(funding_stats['companies_with_funding'] if funding_exists and funding_stats else 0)})

GITHUB DATA:
  Total Profiles:           {format_number(github_stats['total_github_profiles'])}
  Total Repositories:       {format_number(comp_github['total_repos'] + orphan_repos)}
  Total Contributions:      {format_number(contrib_stats['total_contributions'])}
  
ECOSYSTEMS:
  Total Ecosystems:         {format_number(eco_stats['total_ecosystems']) if ecosystem_exists else "0 (not set up)"}
  VC Portfolios:            {format_number(eco_stats['vc_portfolios']) if ecosystem_exists else "0"}

{'='*80}
""")
    
    conn.close()
    
    print(f"\n{'='*80}")
    print(f"ANALYSIS COMPLETE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

