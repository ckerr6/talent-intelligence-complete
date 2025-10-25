#!/usr/bin/env python3
"""
ABOUTME: Extracts technical skills from GitHub repositories and code.
ABOUTME: Detects languages, frameworks, tools, and domain expertise from actual code artifacts.
"""

import re
from typing import Dict, Any, List, Set
import json


class SkillExtractor:
    """
    Extracts technical skills from GitHub profile data.
    
    Analyzes:
    - Programming languages (from repo language stats)
    - Frameworks (from dependency files and repo topics)
    - Tools (from config files and repo structure)
    - Domains (from repo topics, descriptions, and names)
    """
    
    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        # Blockchain/Web3
        'solidity': ['hardhat', 'truffle', 'foundry', '@openzeppelin/contracts', 'ethers', 'web3.js', 'wagmi', 'viem'],
        'rust': ['anchor-lang', 'solana-program', 'near-sdk', 'substrate', 'cosmwasm'],
        
        # Frontend
        'javascript': ['react', 'vue', 'angular', 'next', 'nuxt', 'svelte'],
        'typescript': ['react', 'vue', 'angular', 'next', 'nuxt', 'nest'],
        
        # Backend
        'python': ['django', 'flask', 'fastapi', 'pyramid', 'tornado'],
        'javascript': ['express', 'koa', 'hapi', 'nest'],
        'ruby': ['rails', 'sinatra', 'hanami'],
        'go': ['gin', 'echo', 'fiber', 'chi'],
        
        # Testing
        'any': ['jest', 'mocha', 'chai', 'pytest', 'unittest', 'rspec'],
    }
    
    # Domain detection patterns
    DOMAIN_PATTERNS = {
        'DeFi': ['defi', 'dex', 'amm', 'lending', 'yield', 'swap', 'liquidity', 'staking', 'farming'],
        'NFT': ['nft', 'erc721', 'erc1155', 'opensea', 'collectible', 'art', 'metadata'],
        'Layer 2': ['l2', 'layer2', 'rollup', 'optimism', 'arbitrum', 'zksync', 'polygon', 'scaling'],
        'DAO': ['dao', 'governance', 'voting', 'proposal', 'multisig'],
        'Security': ['security', 'audit', 'fuzzing', 'formal', 'verification', 'slither', 'mythril'],
        'Gaming': ['game', 'gaming', 'unity', 'unreal', 'metaverse', 'p2e'],
        'Infrastructure': ['infrastructure', 'devops', 'kubernetes', 'docker', 'terraform', 'ansible'],
        'AI/ML': ['ml', 'machine-learning', 'ai', 'neural', 'deep-learning', 'pytorch', 'tensorflow'],
        'Data': ['data', 'analytics', 'etl', 'pipeline', 'warehouse', 'spark'],
    }
    
    # Tool detection patterns
    TOOL_PATTERNS = {
        'Docker': ['dockerfile', 'docker-compose', '.dockerignore'],
        'Kubernetes': ['k8s', 'kubernetes', 'deployment.yaml', 'helm'],
        'CI/CD': ['.github/workflows', 'circle.yml', '.travis.yml', 'jenkins', 'gitlab-ci'],
        'Testing': ['jest.config', 'pytest.ini', '.mocharc', 'karma.conf'],
        'Linting': ['eslint', 'prettier', 'black', 'flake8', 'rubocop', 'pylint'],
    }
    
    def __init__(self):
        pass
    
    def extract_skills(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract all skills from profile data.
        
        Args:
            profile_data: Complete profile data from ProfileBuilder
        
        Returns:
            Dictionary with languages, frameworks, tools, and domains
        """
        repos = profile_data.get('repos', [])
        language_stats = profile_data.get('language_stats', {})
        
        return {
            'languages': self._process_languages(language_stats),
            'frameworks': self._detect_frameworks(repos),
            'tools': self._detect_tools(repos),
            'domains': self._detect_domains(repos)
        }
    
    def _process_languages(self, language_stats: Dict[str, int]) -> Dict[str, Any]:
        """
        Process language statistics into structured format.
        
        Args:
            language_stats: Raw language byte counts
        
        Returns:
            Processed language data with proficiency levels
        """
        if not language_stats:
            return {}
        
        total_bytes = sum(language_stats.values())
        
        languages = {}
        for lang, bytes_count in language_stats.items():
            percentage = (bytes_count / total_bytes * 100) if total_bytes > 0 else 0
            
            # Determine proficiency level
            if percentage >= 30:
                proficiency = 'Expert'
            elif percentage >= 15:
                proficiency = 'Advanced'
            elif percentage >= 5:
                proficiency = 'Intermediate'
            else:
                proficiency = 'Beginner'
            
            languages[lang] = {
                'bytes': bytes_count,
                'percentage': round(percentage, 1),
                'proficiency': proficiency
            }
        
        return languages
    
    def _detect_frameworks(self, repos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect frameworks from repository data.
        
        Args:
            repos: List of repository data
        
        Returns:
            List of detected frameworks with evidence
        """
        frameworks = {}
        
        for repo in repos:
            # Skip forks
            if repo.get('fork', False):
                continue
            
            repo_name = repo['name'].lower()
            description = (repo.get('description') or '').lower()
            topics = [t.lower() for t in repo.get('topics', [])]
            
            # Search for framework indicators
            search_text = f"{repo_name} {description} {' '.join(topics)}"
            
            # Check all framework patterns
            for lang, framework_list in self.FRAMEWORK_PATTERNS.items():
                for framework in framework_list:
                    if framework in search_text:
                        if framework not in frameworks:
                            frameworks[framework] = {
                                'name': framework.title(),
                                'repos': [],
                                'count': 0
                            }
                        frameworks[framework]['repos'].append(repo['name'])
                        frameworks[framework]['count'] += 1
        
        # Convert to list and sort by count
        framework_list = list(frameworks.values())
        framework_list.sort(key=lambda x: x['count'], reverse=True)
        
        return framework_list
    
    def _detect_tools(self, repos: List[Dict[str, Any]]) -> List[str]:
        """
        Detect tools from repository structure and configs.
        
        Args:
            repos: List of repository data
        
        Returns:
            List of detected tools
        """
        tools = set()
        
        for repo in repos:
            if repo.get('fork', False):
                continue
            
            repo_name = repo['name'].lower()
            description = (repo.get('description') or '').lower()
            topics = [t.lower() for t in repo.get('topics', [])]
            
            search_text = f"{repo_name} {description} {' '.join(topics)}"
            
            # Check tool patterns
            for tool, patterns in self.TOOL_PATTERNS.items():
                if any(pattern in search_text for pattern in patterns):
                    tools.add(tool)
        
        return sorted(list(tools))
    
    def _detect_domains(self, repos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect domain expertise from repositories.
        
        Args:
            repos: List of repository data
        
        Returns:
            Dictionary of domains with evidence and strength
        """
        domains = {}
        
        for repo in repos:
            if repo.get('fork', False):
                continue
            
            repo_name = repo['name'].lower()
            description = (repo.get('description') or '').lower()
            topics = [t.lower() for t in repo.get('topics', [])]
            
            search_text = f"{repo_name} {description} {' '.join(topics)}"
            
            # Check domain patterns
            for domain, patterns in self.DOMAIN_PATTERNS.items():
                matches = sum(1 for pattern in patterns if pattern in search_text)
                
                if matches > 0:
                    if domain not in domains:
                        domains[domain] = {
                            'name': domain,
                            'repos': [],
                            'match_strength': 0
                        }
                    
                    domains[domain]['repos'].append(repo['name'])
                    domains[domain]['match_strength'] += matches
        
        # Determine expertise level
        for domain_data in domains.values():
            repo_count = len(domain_data['repos'])
            match_strength = domain_data['match_strength']
            
            if repo_count >= 5 or match_strength >= 10:
                domain_data['expertise_level'] = 'Expert'
            elif repo_count >= 3 or match_strength >= 5:
                domain_data['expertise_level'] = 'Advanced'
            elif repo_count >= 2 or match_strength >= 3:
                domain_data['expertise_level'] = 'Intermediate'
            else:
                domain_data['expertise_level'] = 'Familiar'
        
        return domains
    
    def get_primary_specialization(self, skills: Dict[str, Any]) -> str:
        """
        Determine primary technical specialization.
        
        Args:
            skills: Extracted skills data
        
        Returns:
            Description of primary specialization
        """
        languages = skills.get('languages', {})
        domains = skills.get('domains', {})
        frameworks = skills.get('frameworks', [])
        
        # Get top language
        top_lang = None
        if languages:
            top_lang = max(languages.items(), key=lambda x: x[1]['bytes'])[0]
        
        # Get top domain
        top_domain = None
        if domains:
            top_domain = max(domains.items(), key=lambda x: len(x[1]['repos']))[0]
        
        # Get top frameworks
        top_frameworks = [f['name'] for f in frameworks[:3]] if frameworks else []
        
        # Build specialization description
        parts = []
        
        if top_lang:
            parts.append(top_lang)
        
        if top_frameworks:
            parts.append('/'.join(top_frameworks))
        
        if top_domain:
            parts.append(f"({top_domain})")
        
        if parts:
            return ' '.join(parts) + ' Developer'
        else:
            return 'Software Developer'
    
    def get_skill_summary(self, skills: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a summary of skills for quick display.
        
        Args:
            skills: Extracted skills data
        
        Returns:
            Condensed skill summary
        """
        languages = skills.get('languages', {})
        frameworks = skills.get('frameworks', [])
        domains = skills.get('domains', {})
        tools = skills.get('tools', [])
        
        return {
            'primary_language': max(languages.items(), key=lambda x: x[1]['bytes'])[0] if languages else None,
            'language_count': len(languages),
            'top_languages': list(languages.keys())[:5],
            'framework_count': len(frameworks),
            'top_frameworks': [f['name'] for f in frameworks[:5]],
            'domain_count': len(domains),
            'domains': list(domains.keys()),
            'tool_count': len(tools),
            'tools': tools,
            'specialization': self.get_primary_specialization(skills)
        }


def main():
    """
    Test skill extractor with sample data.
    """
    # Sample profile data
    sample_profile = {
        'language_stats': {
            'Solidity': 150000,
            'TypeScript': 80000,
            'JavaScript': 60000,
            'Python': 30000
        },
        'repos': [
            {
                'name': 'defi-protocol',
                'description': 'DeFi lending protocol built with Hardhat and OpenZeppelin',
                'topics': ['defi', 'solidity', 'ethereum', 'hardhat'],
                'fork': False
            },
            {
                'name': 'nft-marketplace',
                'description': 'NFT marketplace frontend with Next.js and ethers.js',
                'topics': ['nft', 'nextjs', 'react', 'web3'],
                'fork': False
            }
        ]
    }
    
    extractor = SkillExtractor()
    skills = extractor.extract_skills(sample_profile)
    
    print("📊 Extracted Skills:")
    print(f"\n   Languages: {list(skills['languages'].keys())}")
    print(f"   Frameworks: {[f['name'] for f in skills['frameworks']]}")
    print(f"   Tools: {skills['tools']}")
    print(f"   Domains: {list(skills['domains'].keys())}")
    
    summary = extractor.get_skill_summary(skills)
    print(f"\n   Specialization: {summary['specialization']}")


if __name__ == '__main__':
    main()

