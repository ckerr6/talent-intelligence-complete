#!/usr/bin/env python3
"""
Migration Utilities
Common functions for database migration scripts
"""

import re
from urllib.parse import unquote
from typing import Optional
import hashlib

def normalize_linkedin_url(url: Optional[str]) -> Optional[str]:
    """
    Normalize LinkedIn URL for consistent matching
    
    Examples:
        'https://www.linkedin.com/in/john-smith/' -> 'linkedin.com/in/john-smith'
        'linkedin.com/in/%c3%a1lvaro-g-68840515b' -> 'linkedin.com/in/álvaro-g-68840515b'
    """
    if not url or not str(url).strip():
        return None
    
    url = str(url).lower().strip()
    
    # URL decode
    url = unquote(url)
    
    # Remove protocol
    url = re.sub(r'^https?://', '', url)
    
    # Remove www.
    url = re.sub(r'^www\.', '', url)
    
    # Remove trailing slash
    url = url.rstrip('/')
    
    # Extract just the linkedin.com/in/slug part
    if 'linkedin.com/in/' in url:
        # Remove query parameters and anything after the slug
        match = re.search(r'linkedin\.com/in/([^/?]+)', url)
        if match:
            return f'linkedin.com/in/{match.group(1)}'
    
    return url


def normalize_email(email: Optional[str]) -> Optional[str]:
    """
    Normalize email address for consistent matching
    
    Examples:
        'John.Smith@Company.COM' -> 'john.smith@company.com'
        '  user@example.com  ' -> 'user@example.com'
    """
    if not email or not str(email).strip():
        return None
    
    email = str(email).lower().strip()
    
    # Basic validation
    if '@' not in email or '.' not in email.split('@')[1]:
        return None
    
    return email


def generate_person_id(linkedin_url: Optional[str] = None, 
                      email: Optional[str] = None,
                      full_name: Optional[str] = None) -> str:
    """
    Generate a consistent UUID-like ID for a person based on their identifiers
    Uses SHA256 hash of normalized identifiers
    """
    import uuid
    
    # Normalize inputs
    linkedin = normalize_linkedin_url(linkedin_url) if linkedin_url else None
    email_norm = normalize_email(email) if email else None
    name = full_name.lower().strip() if full_name else None
    
    # Create a deterministic string
    parts = []
    if linkedin:
        parts.append(f"linkedin:{linkedin}")
    if email_norm:
        parts.append(f"email:{email_norm}")
    if name:
        parts.append(f"name:{name}")
    
    if not parts:
        # Fallback to random UUID if no identifiers
        return str(uuid.uuid4())
    
    # Generate UUID from hash
    identifier = "|".join(parts)
    hash_digest = hashlib.sha256(identifier.encode()).hexdigest()
    
    # Convert to UUID format
    return str(uuid.UUID(hash_digest[:32]))


def calculate_match_score(record1: dict, record2: dict) -> float:
    """
    Calculate similarity score between two person records
    Returns 0.0 to 1.0, where 1.0 is perfect match
    """
    score = 0.0
    matches = 0
    total_checks = 0
    
    # LinkedIn URL match (highest weight)
    if record1.get('linkedin_url') and record2.get('linkedin_url'):
        total_checks += 1
        norm1 = normalize_linkedin_url(record1['linkedin_url'])
        norm2 = normalize_linkedin_url(record2['linkedin_url'])
        if norm1 and norm2 and norm1 == norm2:
            score += 0.5
            matches += 1
    
    # Email match (high weight)
    if record1.get('email') and record2.get('email'):
        total_checks += 1
        email1 = normalize_email(record1['email'])
        email2 = normalize_email(record2['email'])
        if email1 and email2 and email1 == email2:
            score += 0.3
            matches += 1
    
    # Name match (medium weight)
    if record1.get('full_name') and record2.get('full_name'):
        total_checks += 1
        name1 = record1['full_name'].lower().strip()
        name2 = record2['full_name'].lower().strip()
        if name1 == name2:
            score += 0.15
            matches += 1
        elif name_similarity(name1, name2) > 0.8:
            score += 0.1
    
    # Company match (low weight)
    if record1.get('company') and record2.get('company'):
        total_checks += 1
        comp1 = record1['company'].lower().strip()
        comp2 = record2['company'].lower().strip()
        if comp1 in comp2 or comp2 in comp1:
            score += 0.05
    
    return score


def name_similarity(name1: str, name2: str) -> float:
    """
    Calculate similarity between two names
    Simple implementation using character overlap
    """
    if not name1 or not name2:
        return 0.0
    
    name1 = set(name1.lower().replace(' ', ''))
    name2 = set(name2.lower().replace(' ', ''))
    
    if not name1 or not name2:
        return 0.0
    
    intersection = len(name1 & name2)
    union = len(name1 | name2)
    
    return intersection / union if union > 0 else 0.0


def log_migration_event(conn, migration_name: str, phase: str, status: str,
                        records_processed: int = 0, records_created: int = 0,
                        records_updated: int = 0, records_skipped: int = 0,
                        error_message: str = None, metadata: dict = None):
    """
    Log a migration event to the migration_log table
    """
    import json
    from datetime import datetime
    
    cursor = conn.cursor()
    
    if status == 'started':
        cursor.execute("""
            INSERT INTO migration_log 
            (migration_name, migration_phase, status, started_at, metadata)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING log_id
        """, (
            migration_name,
            phase,
            status,
            datetime.now(),
            json.dumps(metadata) if metadata else None
        ))
        log_id = cursor.fetchone()[0]
        conn.commit()
        return log_id
    else:
        # Update existing log entry
        cursor.execute("""
            UPDATE migration_log
            SET status = %s,
                records_processed = %s,
                records_created = %s,
                records_updated = %s,
                records_skipped = %s,
                error_message = %s,
                completed_at = %s,
                metadata = %s
            WHERE migration_name = %s
            AND migration_phase = %s
            AND completed_at IS NULL
        """, (
            status,
            records_processed,
            records_created,
            records_updated,
            records_skipped,
            error_message,
            datetime.now(),
            json.dumps(metadata) if metadata else None,
            migration_name,
            phase
        ))
        conn.commit()


def validate_email(email: str) -> bool:
    """Basic email validation"""
    if not email or not isinstance(email, str):
        return False
    
    email = email.strip()
    
    # Basic regex for email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    return bool(re.match(pattern, email))


def infer_email_type(email: str, github_email: str = None) -> str:
    """
    Infer if email is work, personal, or unknown
    """
    if not email:
        return 'unknown'
    
    email_lower = email.lower()
    
    # Common personal email domains
    personal_domains = [
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
        'icloud.com', 'me.com', 'mac.com', 'aol.com', 'protonmail.com',
        'mail.com', 'gmx.com', 'yandex.com', 'qq.com', '163.com'
    ]
    
    # Check if it's a common personal domain
    for domain in personal_domains:
        if email_lower.endswith(f'@{domain}'):
            return 'personal'
    
    # If it matches a GitHub noreply email, mark as unknown
    if 'noreply' in email_lower or 'users.noreply.github.com' in email_lower:
        return 'unknown'
    
    # Otherwise assume it's a work email
    return 'work'


def merge_person_data(existing: dict, new: dict) -> dict:
    """
    Merge two person records, preferring more complete/recent data
    """
    merged = existing.copy()
    
    # For each field, prefer non-null values from new if existing is null
    for key in new:
        if key not in merged or merged[key] is None or merged[key] == '':
            merged[key] = new[key]
        elif new[key] and len(str(new[key])) > len(str(merged[key])):
            # Prefer longer/more complete values
            merged[key] = new[key]
    
    return merged


def batch_processor(items, batch_size=1000):
    """
    Generator that yields batches of items
    """
    batch = []
    for item in items:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    
    if batch:
        yield batch


def print_progress(current: int, total: int, prefix: str = 'Progress'):
    """Print progress bar"""
    if total == 0:
        return
    
    percent = current / total * 100
    bar_length = 50
    filled = int(bar_length * current / total)
    bar = '█' * filled + '░' * (bar_length - filled)
    
    print(f'\r{prefix}: |{bar}| {percent:.1f}% ({current:,}/{total:,})', end='', flush=True)
    
    if current == total:
        print()  # New line when complete

