"""
ABOUTME: Bot detection for filtering out automated GitHub accounts
ABOUTME: Prevents wasting resources on non-human contributors
"""

# Common bot username patterns and known bots
BOT_USERNAMES = {
    'bors',
    'dependabot',
    'dependabot-preview',
    'renovate',
    'greenkeeper',
    'snyk-bot',
    'imgbot',
    'allcontributors',
    'stale',
    'mergify',
    'codecov',
    'coveralls',
    'travis-ci',
    'circleci',
    'appveyor',
    'jenkins-bot',
    'github-actions',
    'netlify',
    'vercel',
    'deepsource-autofix',
    'whitesource-bolt',
    'pyup-bot',
    'pre-commit-ci',
    'codefactor-io',
    'sourcery-ai',
    'sweep-ai',
    'renovate-bot',
    'github-classroom',
    'gitpod-io',
    'web-flow',  # GitHub's web UI bot
}

BOT_PATTERNS = [
    '[bot]',
    '-bot',
    '_bot',
    'bot-',
    'automated',
    'automation',
]

def is_bot(username: str) -> bool:
    """
    Detect if a GitHub username belongs to a bot.
    
    Returns True if username is likely a bot, False otherwise.
    """
    if not username:
        return False
    
    username_lower = username.lower()
    
    # Check exact matches
    if username_lower in BOT_USERNAMES:
        return True
    
    # Check patterns
    for pattern in BOT_PATTERNS:
        if pattern in username_lower:
            return True
    
    return False

def filter_bots(contributors: list) -> list:
    """
    Filter out bots from a list of contributors.
    
    Args:
        contributors: List of contributor dicts with 'login' key
        
    Returns:
        Filtered list without bots
    """
    return [c for c in contributors if not is_bot(c.get('login', ''))]

def get_bot_stats(contributors: list) -> dict:
    """
    Get statistics about bots in a contributor list.
    
    Returns:
        Dict with bot_count, human_count, bot_usernames
    """
    bots = []
    humans = []
    
    for contributor in contributors:
        username = contributor.get('login', '')
        if is_bot(username):
            bots.append(username)
        else:
            humans.append(username)
    
    return {
        'bot_count': len(bots),
        'human_count': len(humans),
        'bot_usernames': bots
    }

