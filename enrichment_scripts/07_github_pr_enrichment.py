"""
GitHub PR Enrichment Script

Fetches PR merge status, lines of code, and quality metrics using GitHub GraphQL API
Based on expert sourcer feedback for identifying high-quality contributors

Usage:
    python3 enrichment_scripts/07_github_pr_enrichment.py --batch-size 50

Features:
- Fetches merged PR counts (CRITICAL signal)
- Collects lines added/deleted (code volume)
- Tracks PR merge dates (recency)
- Calculates contribution quality scores
- Respects GitHub API rate limits (5000/hour)
"""

import os
import sys
import argparse
import requests
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# GitHub API configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    logger.error("❌ GITHUB_TOKEN environment variable not set!")
    logger.error("   Get a token from: https://github.com/settings/tokens")
    logger.error("   Required scopes: repo, read:user")
    sys.exit(1)

GRAPHQL_URL = "https://api.github.com/graphql"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

# GraphQL Query to fetch PR data
GRAPHQL_QUERY = """
query($username: String!, $first: Int!) {
  user(login: $username) {
    contributionsCollection {
      pullRequestContributions(first: $first) {
        totalCount
        nodes {
          pullRequest {
            repository {
              nameWithOwner
              isFork
            }
            merged
            mergedAt
            additions
            deletions
            changedFiles
            state
            createdAt
          }
        }
      }
    }
    sponsorshipsAsMaintainer {
      totalCount
    }
    repositories(first: 100, privacy: PUBLIC, ownerAffiliations: OWNER) {
      nodes {
        stargazerCount
      }
    }
  }
  rateLimit {
    remaining
    resetAt
  }
}
"""


def fetch_github_pr_data(username: str) -> Optional[Dict]:
    """
    Fetch PR data for a GitHub user using GraphQL API
    
    Returns:
        Dict with PR stats, lines changed, and other metrics
        None if user not found or API error
    """
    variables = {
        "username": username,
        "first": 100  # Get up to 100 PRs
    }
    
    try:
        response = requests.post(
            GRAPHQL_URL,
            json={"query": GRAPHQL_QUERY, "variables": variables},
            headers=HEADERS,
            timeout=30
        )
        
        if response.status_code != 200:
            logger.error(f"GitHub API error for {username}: {response.status_code}")
            return None
        
        data = response.json()
        
        if "errors" in data:
            logger.error(f"GraphQL errors for {username}: {data['errors']}")
            return None
        
        if "data" not in data or "user" not in data["data"] or not data["data"]["user"]:
            logger.warning(f"User {username} not found on GitHub")
            return None
        
        return parse_pr_data(data["data"])
        
    except Exception as e:
        logger.error(f"Error fetching data for {username}: {e}")
        return None


def parse_pr_data(data: Dict) -> Dict:
    """Parse GraphQL response into structured PR data"""
    user = data["user"]
    pr_contributions = user["contributionsCollection"]["pullRequestContributions"]
    
    # Initialize counters
    stats = {
        "total_prs": pr_contributions["totalCount"],
        "merged_prs": 0,
        "open_prs": 0,
        "closed_unmerged": 0,
        "total_lines_added": 0,
        "total_lines_deleted": 0,
        "total_files_changed": 0,
        "repos": {},  # Per-repository stats
        "last_merged_date": None,
        "is_pro": False  # Simplified: check if has sponsors or many stars
    }
    
    # Process each PR
    for node in pr_contributions["nodes"]:
        pr = node["pullRequest"]
        repo_name = pr["repository"]["nameWithOwner"]
        is_fork = pr["repository"]["isFork"]
        
        # Initialize repo stats
        if repo_name not in stats["repos"]:
            stats["repos"][repo_name] = {
                "pr_count": 0,
                "merged_count": 0,
                "open_count": 0,
                "closed_unmerged": 0,
                "lines_added": 0,
                "lines_deleted": 0,
                "files_changed": 0,
                "is_fork": is_fork
            }
        
        repo_stats = stats["repos"][repo_name]
        repo_stats["pr_count"] += 1
        
        # Count PR states
        if pr["merged"]:
            stats["merged_prs"] += 1
            repo_stats["merged_count"] += 1
            
            # Track last merged date
            if pr["mergedAt"]:
                merged_date = datetime.fromisoformat(pr["mergedAt"].replace('Z', '+00:00'))
                if not stats["last_merged_date"] or merged_date > stats["last_merged_date"]:
                    stats["last_merged_date"] = merged_date
        elif pr["state"] == "OPEN":
            stats["open_prs"] += 1
            repo_stats["open_count"] += 1
        else:
            stats["closed_unmerged"] += 1
            repo_stats["closed_unmerged"] += 1
        
        # Accumulate lines changed
        additions = pr["additions"] or 0
        deletions = pr["deletions"] or 0
        files = pr["changedFiles"] or 0
        
        stats["total_lines_added"] += additions
        stats["total_lines_deleted"] += deletions
        stats["total_files_changed"] += files
        
        repo_stats["lines_added"] += additions
        repo_stats["lines_deleted"] += deletions
        repo_stats["files_changed"] += files
    
    # Check for Pro account indicators
    has_sponsors = user["sponsorshipsAsMaintainer"]["totalCount"] > 0
    total_stars = sum(repo["stargazerCount"] for repo in user["repositories"]["nodes"])
    stats["is_pro"] = has_sponsors or total_stars > 100
    stats["total_stars_earned"] = total_stars
    
    # Log rate limit
    rate_limit = data.get("rateLimit", {})
    remaining = rate_limit.get("remaining", "unknown")
    logger.debug(f"Rate limit remaining: {remaining}")
    
    return stats


def calculate_quality_score(contrib: Dict) -> float:
    """
    Calculate contribution quality score (0-100)
    
    Based on:
    - Merged PRs to official repos (highest weight)
    - Code volume (substantial changes)
    - Repository popularity (stars)
    - Recency of contributions
    - Fork penalty (if no upstream merge)
    """
    score = 0.0
    
    # Base: Official repo vs fork
    if not contrib.get("is_fork", False):
        score += 20
    
    # CRITICAL: Merged PRs
    merged_count = contrib.get("merged_pr_count", 0)
    if merged_count > 0:
        score += min(merged_count * 5, 30)  # Max 30 points (6+ PRs)
    
    # Code volume
    lines_added = contrib.get("lines_added", 0)
    if lines_added > 1000:
        score += 15
    elif lines_added > 100:
        score += 10
    elif lines_added > 10:
        score += 5
    
    # Repository popularity
    stars = contrib.get("stars", 0)
    if stars > 1000:
        score += 15
    elif stars > 100:
        score += 10
    elif stars > 50:
        score += 5
    
    # Recency (if we have last merged date)
    if contrib.get("last_merged_pr_date"):
        try:
            # Make now() timezone-aware to match GitHub's datetime
            from datetime import timezone
            now_utc = datetime.now(timezone.utc)
            last_merged = contrib["last_merged_pr_date"]
            
            # Ensure last_merged is timezone-aware
            if last_merged.tzinfo is None:
                last_merged = last_merged.replace(tzinfo=timezone.utc)
            
            days_ago = (now_utc - last_merged).days
            if days_ago < 90:  # Last 3 months
                score += 10
            elif days_ago < 180:  # Last 6 months
                score += 5
        except Exception as e:
            logger.debug(f"Could not calculate recency: {e}")
    
    # Penalty: Fork with no confirmed upstream merge
    if contrib.get("is_fork", False) and merged_count == 0:
        score -= 10
    
    return max(0, min(score, 100))  # Clamp to 0-100


def enrich_github_profiles(batch_size: int = 50, rate_limit_delay: float = 0.8):
    """
    Enrich GitHub profiles with PR data
    
    Args:
        batch_size: Number of profiles to process
        rate_limit_delay: Seconds between requests (default keeps us under 5000/hour)
    """
    conn = Config.get_pooled_connection()
    cursor = conn.cursor()
    
    try:
        # Get profiles without PR enrichment
        cursor.execute("""
            SELECT 
                gp.github_profile_id, 
                gp.github_username, 
                p.full_name
            FROM github_profile gp
            JOIN person p ON gp.person_id = p.person_id
            WHERE gp.enriched_at IS NULL
            ORDER BY gp.created_at DESC
            LIMIT %s
        """, (batch_size,))
        
        profiles = cursor.fetchall()
        
        if not profiles:
            logger.info("✅ No profiles need enrichment!")
            return
        
        logger.info(f"📊 Processing {len(profiles)} GitHub profiles...")
        logger.info(f"⏱️  Rate limit delay: {rate_limit_delay}s between requests")
        logger.info(f"⏰ Estimated time: {len(profiles) * rate_limit_delay / 60:.1f} minutes")
        
        success_count = 0
        error_count = 0
        
        for i, (profile_id, username, full_name) in enumerate(profiles, 1):
            logger.info(f"\n[{i}/{len(profiles)}] Processing: {full_name} (@{username})")
            
            try:
                # Fetch PR data from GitHub
                pr_data = fetch_github_pr_data(username)
                
                if not pr_data:
                    error_count += 1
                    logger.warning(f"  ⚠️  No data returned for {username}")
                    continue
                
                # Update github_profile table
                cursor.execute("""
                    UPDATE github_profile
                    SET 
                        total_merged_prs = %s,
                        is_pro_account = %s,
                        total_lines_contributed = %s,
                        total_stars_earned = %s,
                        enriched_at = NOW()
                    WHERE github_profile_id = %s
                """, (
                    pr_data["merged_prs"],
                    pr_data["is_pro"],
                    pr_data["total_lines_added"],
                    pr_data["total_stars_earned"],
                    profile_id
                ))
                
                logger.info(f"  ✓ Profile: {pr_data['merged_prs']} merged PRs, {pr_data['total_lines_added']:,} lines")
                
                # Update contribution data per repository
                for repo_name, repo_data in pr_data["repos"].items():
                    # Get repository from our database
                    cursor.execute("""
                        SELECT repo_id, stars, is_fork
                        FROM github_repository
                        WHERE full_name = %s
                    """, (repo_name,))
                    
                    repo_row = cursor.fetchone()
                    if not repo_row:
                        logger.debug(f"    Repository not in database: {repo_name}")
                        continue
                    
                    repo_id, stars, is_fork_db = repo_row
                    
                    # Calculate quality score
                    contrib_data = {
                        "merged_pr_count": repo_data["merged_count"],
                        "lines_added": repo_data["lines_added"],
                        "stars": stars,
                        "is_fork": repo_data["is_fork"] or is_fork_db,
                        "last_merged_pr_date": pr_data["last_merged_date"]
                    }
                    quality_score = calculate_quality_score(contrib_data)
                    
                    # Update github_contribution
                    cursor.execute("""
                        UPDATE github_contribution
                        SET 
                            pr_count = %s,
                            merged_pr_count = %s,
                            open_pr_count = %s,
                            closed_unmerged_pr_count = %s,
                            lines_added = %s,
                            lines_deleted = %s,
                            files_changed = %s,
                            last_merged_pr_date = %s,
                            contribution_quality_score = %s
                        WHERE github_profile_id = %s 
                        AND repo_id = %s
                    """, (
                        repo_data["pr_count"],
                        repo_data["merged_count"],
                        repo_data["open_count"],
                        repo_data["closed_unmerged"],
                        repo_data["lines_added"],
                        repo_data["lines_deleted"],
                        repo_data["files_changed"],
                        pr_data["last_merged_date"],
                        quality_score,
                        profile_id,
                        repo_id
                    ))
                    
                    logger.debug(f"    • {repo_name}: {repo_data['merged_count']} merged, score={quality_score:.1f}")
                
                conn.commit()
                success_count += 1
                logger.info(f"  ✅ Successfully enriched {username}")
                
                # Rate limiting
                time.sleep(rate_limit_delay)
                
            except Exception as e:
                logger.error(f"  ❌ Error processing {username}: {e}")
                conn.rollback()
                error_count += 1
                continue
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ Enrichment complete!")
        logger.info(f"   Success: {success_count}/{len(profiles)}")
        logger.info(f"   Errors: {error_count}/{len(profiles)}")
        logger.info(f"{'='*60}")
        
    finally:
        cursor.close()
        Config.return_connection(conn)


def main():
    parser = argparse.ArgumentParser(description="GitHub PR Enrichment Script")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of profiles to process (default: 50)"
    )
    parser.add_argument(
        "--rate-limit-delay",
        type=float,
        default=0.8,
        help="Seconds between API requests (default: 0.8 = 4500/hour)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode: only process 5 profiles"
    )
    
    args = parser.parse_args()
    
    if args.test:
        logger.info("🧪 TEST MODE: Processing 5 profiles only")
        args.batch_size = 5
    
    logger.info("="*60)
    logger.info("🚀 GitHub PR Enrichment Script")
    logger.info("="*60)
    logger.info("This script fetches PR merge status and code metrics")
    logger.info("from GitHub API to identify high-quality contributors")
    logger.info("="*60)
    
    enrich_github_profiles(
        batch_size=args.batch_size,
        rate_limit_delay=args.rate_limit_delay
    )


if __name__ == "__main__":
    main()

