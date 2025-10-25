"""
ABOUTME: Comprehensive logging utilities for GitHub data ingestion
ABOUTME: Provides detailed, real-time visibility into all discovery and enrichment operations
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
import json

class DetailedLogger:
    """
    Enhanced logger with detailed formatting and multiple outputs.
    Shows exactly what data is being discovered and stored.
    """
    
    def __init__(self, name: str, log_dir: str = "logs/detailed"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Console handler with color and detail
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # Detailed file handler
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        detailed_file = self.log_dir / f"{name}_{timestamp}_detailed.log"
        file_handler = logging.FileHandler(detailed_file)
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)
        
        # JSON structured log for analysis
        self.json_log = self.log_dir / f"{name}_{timestamp}_structured.jsonl"
        
        self.logger.info(f"="*80)
        self.logger.info(f"🚀 {name.upper()} - DETAILED LOGGING STARTED")
        self.logger.info(f"="*80)
        self.logger.info(f"📝 Detailed logs: {detailed_file}")
        self.logger.info(f"📊 Structured logs: {self.json_log}")
    
    def log_repo_scan_start(self, owner: str, name: str, tags: list = None):
        """Log when starting to scan a repository"""
        self.logger.info(f"")
        self.logger.info(f"{'='*80}")
        self.logger.info(f"📦 SCANNING REPOSITORY: {owner}/{name}")
        if tags:
            self.logger.info(f"   Tags: {', '.join(tags)}")
        self.logger.debug(f"   Full URL: https://github.com/{owner}/{name}")
        
        self._write_json_log({
            'event': 'repo_scan_start',
            'repo_owner': owner,
            'repo_name': name,
            'tags': tags,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_repo_scan_complete(self, owner: str, name: str, contributor_count: int):
        """Log when repository scan completes"""
        self.logger.info(f"✅ COMPLETED: {owner}/{name}")
        self.logger.info(f"   Contributors found: {contributor_count}")
        
        self._write_json_log({
            'event': 'repo_scan_complete',
            'repo_owner': owner,
            'repo_name': name,
            'contributor_count': contributor_count,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_contributor_discovered(self, username: str, contributions: int, repo: str):
        """Log each contributor as they're discovered"""
        self.logger.info(f"   👤 Discovered: @{username} ({contributions} contributions in {repo})")
        self.logger.debug(f"      Profile: https://github.com/{username}")
        
        self._write_json_log({
            'event': 'contributor_discovered',
            'username': username,
            'contributions': contributions,
            'repo': repo,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_profile_saved(self, username: str, profile_id: str, is_new: bool):
        """Log when a profile is saved to database"""
        status = "NEW PROFILE CREATED" if is_new else "EXISTING PROFILE UPDATED"
        self.logger.info(f"   💾 {status}: @{username}")
        self.logger.debug(f"      Profile ID: {profile_id}")
        
        self._write_json_log({
            'event': 'profile_saved',
            'username': username,
            'profile_id': str(profile_id),
            'is_new': is_new,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_enrichment_start(self, username: str, contribution_count: int = None):
        """Log when enrichment starts for a developer"""
        self.logger.info(f"")
        self.logger.info(f"{'='*80}")
        self.logger.info(f"🔍 ENRICHING DEVELOPER: @{username}")
        if contribution_count:
            self.logger.info(f"   Total Contributions: {contribution_count:,}")
        
        self._write_json_log({
            'event': 'enrichment_start',
            'username': username,
            'contribution_count': contribution_count,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_profile_data_fetched(self, username: str, data_summary: dict):
        """Log detailed profile data as it's fetched"""
        self.logger.info(f"   📊 Profile Data Retrieved:")
        self.logger.info(f"      Name: {data_summary.get('name', 'N/A')}")
        self.logger.info(f"      Bio: {data_summary.get('bio', 'N/A')}")
        self.logger.info(f"      Followers: {data_summary.get('followers', 0):,}")
        self.logger.info(f"      Public Repos: {data_summary.get('public_repos', 0)}")
        self.logger.info(f"      Account Created: {data_summary.get('created_at', 'N/A')}")
        
        if 'email' in data_summary and data_summary['email']:
            self.logger.info(f"      📧 Email: {data_summary['email']}")
        
        if 'company' in data_summary and data_summary['company']:
            self.logger.info(f"      🏢 Company: {data_summary['company']}")
        
        if 'location' in data_summary and data_summary['location']:
            self.logger.info(f"      📍 Location: {data_summary['location']}")
        
        self._write_json_log({
            'event': 'profile_data_fetched',
            'username': username,
            'data': data_summary,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_repositories_analyzed(self, username: str, repo_count: int, top_languages: dict):
        """Log repository analysis results"""
        self.logger.info(f"   📦 Repositories Analyzed: {repo_count}")
        self.logger.info(f"   🔤 Top Languages:")
        for lang, percentage in sorted(top_languages.items(), key=lambda x: x[1], reverse=True)[:5]:
            self.logger.info(f"      • {lang}: {percentage:.1f}%")
        
        self._write_json_log({
            'event': 'repositories_analyzed',
            'username': username,
            'repo_count': repo_count,
            'languages': top_languages,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_skills_extracted(self, username: str, skills: dict):
        """Log extracted skills"""
        self.logger.info(f"   🎯 Skills Extracted:")
        
        if skills.get('languages'):
            langs = list(skills['languages'].keys())[:5]
            self.logger.info(f"      Languages: {', '.join(langs)}")
        
        if skills.get('frameworks'):
            frameworks = skills['frameworks'][:5]
            # Handle both list of strings and list of dicts
            framework_names = [f if isinstance(f, str) else f.get('name', str(f)) for f in frameworks]
            self.logger.info(f"      Frameworks: {', '.join(framework_names)}")
        
        if skills.get('domains'):
            domains = skills['domains'][:3]
            # Handle both list of strings and list of dicts
            domain_names = [d if isinstance(d, str) else d.get('name', str(d)) for d in domains]
            self.logger.info(f"      Domains: {', '.join(domain_names)}")
        
        self._write_json_log({
            'event': 'skills_extracted',
            'username': username,
            'skills': skills,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_seniority_assessed(self, username: str, level: str, confidence: float, reasoning: dict):
        """Log seniority assessment"""
        self.logger.info(f"   📊 Seniority Assessment:")
        self.logger.info(f"      Level: {level}")
        self.logger.info(f"      Confidence: {confidence*100:.1f}%")
        
        if reasoning:
            self.logger.debug(f"      Reasoning:")
            for key, value in reasoning.items():
                self.logger.debug(f"        {key}: {value}")
        
        self._write_json_log({
            'event': 'seniority_assessed',
            'username': username,
            'level': level,
            'confidence': confidence,
            'reasoning': reasoning,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_network_analyzed(self, username: str, collaborators: int, organizations: list, influence_score: int):
        """Log network analysis"""
        self.logger.info(f"   🌐 Network Analysis:")
        self.logger.info(f"      Collaborators: {collaborators}")
        self.logger.info(f"      Organizations: {len(organizations)}")
        if organizations:
            self.logger.info(f"         {', '.join(organizations[:5])}")
        self.logger.info(f"      Influence Score: {influence_score}/100")
        
        self._write_json_log({
            'event': 'network_analyzed',
            'username': username,
            'collaborators': collaborators,
            'organizations': organizations,
            'influence_score': influence_score,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_enrichment_complete(self, username: str, profile_id: str, summary: dict):
        """Log when enrichment is complete and stored"""
        self.logger.info(f"   ✅ ENRICHMENT COMPLETE: @{username}")
        self.logger.info(f"      Stored in database: {profile_id}")
        self.logger.info(f"      Seniority: {summary.get('seniority', 'N/A')}")
        self.logger.info(f"      Influence: {summary.get('influence', 0)}/100")
        self.logger.info(f"      Reachability: {summary.get('reachability', 0)}/100")
        self.logger.info(f"{'='*80}")
        
        self._write_json_log({
            'event': 'enrichment_complete',
            'username': username,
            'profile_id': str(profile_id),
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_batch_progress(self, batch_num: int, processed: int, total: int, 
                          contributors_found: int, profiles_saved: int):
        """Log batch processing progress"""
        percentage = (processed / total * 100) if total > 0 else 0
        self.logger.info(f"")
        self.logger.info(f"{'='*80}")
        self.logger.info(f"📈 BATCH {batch_num} PROGRESS:")
        self.logger.info(f"   Repos Processed: {processed:,} / {total:,} ({percentage:.2f}%)")
        self.logger.info(f"   Contributors Found: {contributors_found:,}")
        self.logger.info(f"   Profiles Saved: {profiles_saved:,}")
        self.logger.info(f"{'='*80}")
        
        self._write_json_log({
            'event': 'batch_progress',
            'batch_num': batch_num,
            'processed': processed,
            'total': total,
            'percentage': percentage,
            'contributors_found': contributors_found,
            'profiles_saved': profiles_saved,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_rate_limit_status(self, remaining: int, limit: int, reset_time: str):
        """Log GitHub API rate limit status"""
        self.logger.warning(f"⚠️  API RATE LIMIT STATUS:")
        self.logger.warning(f"   Remaining: {remaining} / {limit}")
        self.logger.warning(f"   Resets at: {reset_time}")
        
        self._write_json_log({
            'event': 'rate_limit_status',
            'remaining': remaining,
            'limit': limit,
            'reset_time': reset_time,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_error(self, context: str, error: Exception, username: str = None, repo: str = None):
        """Log errors with full context"""
        self.logger.error(f"❌ ERROR in {context}:")
        if username:
            self.logger.error(f"   Username: @{username}")
        if repo:
            self.logger.error(f"   Repository: {repo}")
        self.logger.error(f"   Error: {str(error)}")
        self.logger.debug(f"   Error Type: {type(error).__name__}")
        
        self._write_json_log({
            'event': 'error',
            'context': context,
            'error': str(error),
            'error_type': type(error).__name__,
            'username': username,
            'repo': repo,
            'timestamp': datetime.now().isoformat()
        })
    
    def _write_json_log(self, data: dict):
        """Write structured JSON log for analysis"""
        try:
            with open(self.json_log, 'a') as f:
                f.write(json.dumps(data) + '\n')
        except Exception as e:
            self.logger.debug(f"Failed to write JSON log: {e}")
    
    def info(self, message: str):
        """Standard info log"""
        self.logger.info(message)
    
    def debug(self, message: str):
        """Standard debug log"""
        self.logger.debug(message)
    
    def warning(self, message: str):
        """Standard warning log"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Standard error log"""
        self.logger.error(message)

