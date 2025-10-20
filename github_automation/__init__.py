"""
GitHub Automation System

Automated discovery, enrichment, and matching of GitHub profiles.

Main components:
- GitHubClient: Rate-limited GitHub API wrapper
- EnrichmentEngine: Core profile enrichment
- ProfileMatcher: Match profiles to people
- QueueManager: Priority queue management
- Scheduler: Orchestration and scheduling
"""

__version__ = "1.0.0"
__author__ = "Talent Intelligence"

from .github_client import GitHubClient
from .enrichment_engine import EnrichmentEngine
from .matcher import ProfileMatcher
from .queue_manager import QueueManager

__all__ = [
    "GitHubClient",
    "EnrichmentEngine",
    "ProfileMatcher",
    "QueueManager",
]

