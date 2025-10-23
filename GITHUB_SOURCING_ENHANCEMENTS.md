# GitHub Sourcing Enhancements 🔍

**Date**: October 23, 2025  
**Status**: Phase 1 ✅ Complete | Phase 2 📋 Ready  
**Based on**: Expert sourcer feedback from professionals specializing in GitHub talent discovery

---

## 🎯 **Overview**

This enhancement improves how we present GitHub contribution data to align with expert sourcer workflows. The goal is to help recruiters quickly identify high-quality technical contributors and avoid common pitfalls (fork-only contributions, README changes, unmerged PRs).

---

## ✅ **Phase 1: UI Improvements (COMPLETE)**

### **What Was Implemented:**

#### **1. Expert Sourcer's Verification Checklist** 📋

A prominent card at the top of every profile with GitHub activity that reminds recruiters to:
- ✓ Click commit links to verify merged status
- ✓ Review actual code changes, not just docs
- ✓ For forks, verify if merged to upstream
- ✓ Check for community feedback on PRs

**Visual**: Gradient blue/purple card with checkboxes

**Impact**: Provides immediate context for manual verification workflow

---

#### **2. Reorganized Contributions by Quality** 🌟

Contributions are now grouped into three tiers:

**🌟 High-Quality Contributions (Official Repos)**
- Not forks
- 50+ GitHub stars
- Significant community engagement
- Shows count: "High-Quality Contributions (12)"
- Green left border on cards
- "High Quality" success badge

**💼 Other Contributions**
- Official repos with < 50 stars
- Still valuable, just smaller projects
- Gray left border
- Shows first 5

**🔱 Fork Contributions - Needs Verification**
- All forked repositories
- Yellow warning callout box
- Orange left border
- "Fork - Verify Merge" warning badge
- Explicit instructions to verify upstream merge

---

#### **3. Enhanced Action Links** 🔗

Each contribution now has TWO direct links:

**View All Commits** (GitCommit icon)
- Direct link: `github.com/{repo}/commits?author={username}`
- Shows only this person's commits
- Easy to review code quality

**View Pull Requests** (GitPullRequest icon)
- Direct link: `github.com/{repo}/pulls?q=author:{username}`
- Shows all PRs authored by person
- Can manually check merge status

---

#### **4. Visual Quality Indicators** 🎨

**Colored Left Borders:**
- 🟢 Green = High-quality official repo contribution
- 🟡 Orange = Fork (needs verification)
- ⚪ Gray = Standard contribution

**Badge System:**
- **Success Badge**: "High Quality" for official repos with 50+ stars
- **Warning Badge**: "Fork - Verify Merge" for all forks
- **Info Badge**: Company name (Uniswap, Coinbase, etc.)

**Card Hover Effects:**
- Cards lift on hover
- Better visual feedback

---

#### **5. Better Data Presentation** 📊

Each contribution card now shows:
- **Repository name** (larger, more prominent)
- **Company/Organization** (as badge)
- **Fork status** (with warning)
- **Description** (line-clamped)
- **Language** (with colored dot)
- **Stars & Forks** (social proof)
- **Commit count** (quantitative metric)
- **Action links** (commit history & PRs)

---

## 📊 **Current Data Available**

### **We Already Have:**

| Field | Source | Use Case |
|-------|--------|----------|
| `is_fork` | GitHub API | Flag potential issues |
| `contribution_count` | Our enrichment | Quantitative signal |
| `stars` | GitHub API | Social proof/quality |
| `forks` | GitHub API | Project popularity |
| `language` | GitHub API | Tech stack relevance |
| `owner_company_name` | Our enrichment | Context/credibility |
| `description` | GitHub API | Project understanding |
| `repo_full_name` | GitHub API | Direct linking |

### **We Can Build Links To:**

✅ User's commit history per repo  
✅ User's pull requests per repo  
✅ Repository overview  
✅ User's GitHub profile  

---

## 📋 **Phase 2: Enhanced Data Collection (READY TO BUILD)**

### **Critical Missing Data (Per Expert Sourcers):**

| Priority | Data Point | Why It Matters | Difficulty |
|----------|-----------|----------------|------------|
| 🔥 **CRITICAL** | PR Merge Status | Distinguishes real contributions from forks | Medium |
| 🔥 **CRITICAL** | Lines Added/Deleted | Code volume indicator | Easy |
| 🔥 **CRITICAL** | Merged PR Count | Career contribution metric | Medium |
| High | Verified Account (Pro) | Private repo indicator | Easy |
| High | PR Review Count | Code quality indicator | Medium |
| High | Files Changed | Complexity indicator | Easy |
| Medium | Contribution Type | Code vs docs vs config | Hard |
| Medium | PR Feedback/Comments | Community engagement | Hard |

---

### **Proposed Database Schema Changes:**

```sql
-- Add to github_contribution table
ALTER TABLE github_contribution ADD COLUMN IF NOT EXISTS 
  pr_count INTEGER DEFAULT 0,
  merged_pr_count INTEGER DEFAULT 0,          -- CRITICAL!
  open_pr_count INTEGER DEFAULT 0,
  closed_unmerged_pr_count INTEGER DEFAULT 0,
  lines_added INTEGER DEFAULT 0,              -- CRITICAL!
  lines_deleted INTEGER DEFAULT 0,            -- CRITICAL!
  files_changed INTEGER DEFAULT 0,
  last_merged_pr_date TIMESTAMP,
  contribution_quality_score FLOAT,           -- Computed
  has_code_contributions BOOLEAN DEFAULT TRUE,
  has_doc_contributions BOOLEAN DEFAULT FALSE;

-- Add to github_profile table  
ALTER TABLE github_profile ADD COLUMN IF NOT EXISTS
  is_pro_account BOOLEAN DEFAULT FALSE,       -- Verified indicator
  total_merged_prs INTEGER DEFAULT 0,         -- Career metric
  total_stars_earned INTEGER DEFAULT 0,       -- Social proof
  code_review_count INTEGER DEFAULT 0,        -- Quality signal
  total_lines_contributed INTEGER DEFAULT 0;  -- Volume metric
```

---

### **GitHub API Endpoints to Use:**

#### **1. GraphQL API (Most Efficient)**

```graphql
query GetUserContributions($username: String!, $first: Int!) {
  user(login: $username) {
    contributionsCollection {
      pullRequestContributions(first: $first) {
        nodes {
          pullRequest {
            repository { nameWithOwner }
            merged              # ← CRITICAL!
            mergedAt            # ← CRITICAL!
            additions           # ← Lines added
            deletions           # ← Lines deleted
            changedFiles        # ← Files count
            state               # ← MERGED/CLOSED/OPEN
            reviews(first: 5) { # ← Community feedback
              totalCount
              nodes {
                state
                author { login }
              }
            }
          }
        }
      }
    }
    # Profile info
    hasSponsorshipsAsMaintainer  # Pro indicator
  }
}
```

**Rate Limit**: 5,000 requests/hour (GitHub GraphQL)

**Strategy**: 
- 1 request per user gets ALL their PR data
- Can process ~4,500 users/hour
- Run overnight for full database enrichment

---

#### **2. REST API (Fallback)**

```
GET /repos/{owner}/{repo}/pulls?author={username}&state=all
GET /repos/{owner}/{repo}/commits?author={username}
```

**Rate Limit**: 5,000 requests/hour (authenticated)

**Strategy**: 
- Use for detailed per-repo analysis
- Fallback when GraphQL unavailable

---

### **Proposed Enrichment Script:**

**File**: `enrichment_scripts/07_github_pr_enrichment.py`

```python
"""
GitHub PR Enrichment Script
Fetches PR merge status, lines changed, and quality metrics
"""

import os
import requests
import time
from datetime import datetime
from config import Config

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GRAPHQL_URL = "https://api.github.com/graphql"

def enrich_github_prs(batch_size=100, rate_limit_delay=0.8):
    """
    Enrich GitHub profiles with PR data
    
    Args:
        batch_size: Number of users to process
        rate_limit_delay: Seconds between requests (stay under 5000/hr)
    """
    
    conn = Config.get_pooled_connection()
    cursor = conn.cursor()
    
    # Get users with GitHub profiles but no PR data
    cursor.execute("""
        SELECT gp.github_profile_id, gp.github_username, p.full_name
        FROM github_profile gp
        JOIN person p ON gp.person_id = p.person_id
        WHERE gp.total_merged_prs IS NULL  -- Not yet enriched
        LIMIT %s
    """, (batch_size,))
    
    profiles = cursor.fetchall()
    
    print(f"📊 Processing {len(profiles)} GitHub profiles...")
    
    for i, (profile_id, username, full_name) in enumerate(profiles):
        print(f"[{i+1}/{len(profiles)}] Processing: {full_name} ({username})")
        
        try:
            # Fetch PR data via GraphQL
            pr_data = fetch_user_prs_graphql(username)
            
            if pr_data:
                # Update github_profile
                cursor.execute("""
                    UPDATE github_profile
                    SET 
                        total_merged_prs = %s,
                        is_pro_account = %s,
                        total_lines_contributed = %s
                    WHERE github_profile_id = %s
                """, (
                    pr_data['total_merged_prs'],
                    pr_data['is_pro'],
                    pr_data['total_lines'],
                    profile_id
                ))
                
                # Update contributions per repository
                for repo_name, repo_data in pr_data['repos'].items():
                    cursor.execute("""
                        UPDATE github_contribution
                        SET 
                            pr_count = %s,
                            merged_pr_count = %s,
                            lines_added = %s,
                            lines_deleted = %s,
                            files_changed = %s
                        WHERE github_profile_id = %s 
                        AND repo_id = (
                            SELECT repo_id FROM github_repository 
                            WHERE full_name = %s
                        )
                    """, (
                        repo_data['pr_count'],
                        repo_data['merged_count'],
                        repo_data['lines_added'],
                        repo_data['lines_deleted'],
                        repo_data['files_changed'],
                        profile_id,
                        repo_name
                    ))
                
                conn.commit()
                print(f"  ✓ Updated: {pr_data['total_merged_prs']} merged PRs")
            
            # Rate limiting
            time.sleep(rate_limit_delay)
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            conn.rollback()
    
    cursor.close()
    Config.return_connection(conn)
    print("✅ Enrichment complete!")

def fetch_user_prs_graphql(username):
    """Fetch PR data using GitHub GraphQL API"""
    # Implementation here
    pass
```

---

### **Quality Score Algorithm:**

```python
def calculate_contribution_quality(contrib):
    """
    Score contributors based on multiple signals
    
    Returns: 0-100 quality score
    """
    score = 0
    
    # Base: Official repo vs fork
    if not contrib['is_fork']:
        score += 20
    
    # CRITICAL: Merged PRs to official repos
    if contrib['merged_pr_count'] > 0:
        score += min(contrib['merged_pr_count'] * 5, 30)  # Max 30 points
    
    # Code volume
    if contrib['lines_added'] > 1000:
        score += 15
    elif contrib['lines_added'] > 100:
        score += 10
    
    # Community engagement
    if contrib['stars'] > 1000:
        score += 15
    elif contrib['stars'] > 100:
        score += 10
    elif contrib['stars'] > 50:
        score += 5
    
    # Recency
    if contrib['last_merged_pr_date']:
        days_ago = (datetime.now() - contrib['last_merged_pr_date']).days
        if days_ago < 90:  # Last 3 months
            score += 10
        elif days_ago < 180:  # Last 6 months
            score += 5
    
    # Penalties
    if contrib['is_fork'] and contrib['merged_pr_count'] == 0:
        score -= 10  # Fork with no confirmed upstream merge
    
    return min(max(score, 0), 100)  # Clamp 0-100
```

---

## 🎬 **Next Steps:**

### **Immediate (Ready for Testing):**
1. ✅ Test Phase 1 UI improvements with real profiles
2. ✅ Get feedback from expert sourcers
3. ✅ Iterate on visual hierarchy

### **Phase 2 Implementation (When Ready):**
1. Create SQL migration (`08_github_pr_enrichment.sql`)
2. Implement enrichment script (`07_github_pr_enrichment.py`)
3. Test on 100 profiles
4. Run full enrichment overnight
5. Update UI to show new data:
   - Merged PR badges
   - Quality scores
   - Lines contributed
   - "Verified Account" indicator

---

## 📊 **Expected Impact:**

### **For Recruiters:**
- ✅ Immediately see high-quality vs questionable contributions
- ✅ One-click access to verify merge status
- ✅ Clear checklist of what to verify manually
- ✅ Better signal-to-noise ratio

### **For Candidates:**
- ✅ High-quality contributors stand out immediately
- ✅ Fork contributions don't hurt if merged upstream
- ✅ Real work is properly highlighted

### **For Investors:**
- ✅ Demonstrates deep domain expertise
- ✅ Shows understanding of recruiter workflows
- ✅ Differentiates from LinkedIn/Wellfound
- ✅ Proves we understand GitHub at expert level

---

## 🔍 **Testing Checklist:**

- [ ] View profile with official repo contributions (should show as "High Quality")
- [ ] View profile with only fork contributions (should show verification warning)
- [ ] Click "View All Commits" link (should filter by author)
- [ ] Click "View Pull Requests" link (should filter by author)
- [ ] Verify expert checklist is visible and clear
- [ ] Check mobile responsiveness
- [ ] Test with profile having mix of all three types

---

## 📚 **Expert Sourcer Feedback Incorporated:**

✅ **"Start with clear requirements"** - Quality tiers help focus on requirements  
✅ **"Focus on actual code"** - Direct links to commits and PRs  
✅ **"Verify authentic contributions"** - Fork warnings and verification checklist  
✅ **"Distinguish forks vs official repos"** - Clear visual separation  
✅ **"Check for merged PRs"** - Explicit callout to verify (will be automated in Phase 2)  
✅ **"Review actual code changes"** - Direct commit links with author filter  
✅ **"Community engagement matters"** - Stars/forks prominently displayed  

---

**Phase 1 is live! Ready for expert recruiter feedback!** 🎉


