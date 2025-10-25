"""
ABOUTME: AI-powered specialization detector for deep analysis of technical focus areas.
ABOUTME: Analyzes repos, commits, and patterns to identify specific expertise (e.g., "Security-focused DeFi engineer").
"""

import os
from typing import Dict, Any, Optional, List
import openai


class AISpecializationDetector:
    """
    Detects deep technical specialization using AI analysis.
    
    Goes beyond simple skill extraction to identify:
    - Specific technical focus (e.g., "Smart contract security")
    - Domain depth (DeFi ⭐⭐⭐ expert vs NFT ⭐ familiar)
    - Career trajectory (specialist vs generalist)
    - Unique combination of skills
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize specialization detector.
        
        Args:
            api_key: OpenAI API key
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if self.api_key:
            openai.api_key = self.api_key
        
        self.model = 'gpt-4o-mini'
    
    def detect_specialization(self, intelligence_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect deep specialization from intelligence data.
        
        Args:
            intelligence_data: Complete intelligence from orchestrator
        
        Returns:
            Dictionary with specialization analysis
        """
        if not self.api_key:
            return self._template_specialization(intelligence_data)
        
        # Prepare context
        context = self._prepare_context(intelligence_data)
        
        # Detect primary focus
        primary_focus = self._detect_primary_focus(context)
        
        # Assess domain depth
        domain_depth = self._assess_domain_depth(context)
        
        # Identify unique combo
        unique_combo = self._identify_unique_combination(context)
        
        return {
            'primary_focus': primary_focus,
            'domain_depth': domain_depth,
            'unique_combination': unique_combo,
            'specialization_type': self._classify_specialization_type(intelligence_data)
        }
    
    def _prepare_context(self, intelligence_data: Dict[str, Any]) -> str:
        """
        Prepare context for AI analysis.
        """
        skills = intelligence_data.get('skill_summary', {})
        repos = intelligence_data.get('profile_data', {}).get('repos', [])
        
        # Get top projects by stars
        top_projects = sorted(
            [r for r in repos if not r.get('fork', False)],
            key=lambda r: r.get('stargazers_count', 0),
            reverse=True
        )[:5]
        
        context = f"""
Developer Technical Profile:

PRIMARY SKILLS:
{skills.get('specialization', 'Unknown')}

TOP LANGUAGES:
{', '.join(skills.get('top_languages', [])[:5])}

FRAMEWORKS & TOOLS:
{', '.join(skills.get('top_frameworks', [])[:5])}

DOMAINS:
{', '.join(skills.get('domains', []))}

TOP PROJECTS:
"""
        
        for proj in top_projects:
            context += f"- {proj['name']}: {proj.get('description', 'No description')} ({proj.get('stargazers_count', 0)} stars)\n"
        
        return context
    
    def _detect_primary_focus(self, context: str) -> str:
        """
        Detect primary technical focus.
        """
        prompt = f"""Based on this developer's profile, identify their PRIMARY technical focus in one specific phrase (e.g., "Smart contract security", "DeFi protocol development", "Frontend architecture").

{context}

Primary Focus:"""
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a technical analyst. Be specific and precise about specializations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=50
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"   ⚠️  OpenAI API error: {e}")
            return "Technical specialization analysis unavailable"
    
    def _assess_domain_depth(self, context: str) -> List[Dict[str, Any]]:
        """
        Assess depth in each domain (★ to ★★★★★).
        """
        prompt = f"""Based on this profile, rate their expertise level in relevant domains using stars (★ to ★★★★★).

{context}

For each domain they work in, provide:
- Domain name
- Star rating (1-5)
- Brief evidence

Format as: "DeFi: ★★★★ - Multiple protocol contributions"

Domain Expertise:"""
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a technical evaluator. Rate expertise based on actual work shown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=200
            )
            
            # Parse response into structured format
            text = response.choices[0].message.content.strip()
            domains = []
            
            for line in text.split('\n'):
                if ':' in line and '★' in line:
                    parts = line.split(':')
                    domain = parts[0].strip().replace('-', '').strip()
                    stars = line.count('★')
                    evidence = parts[1].split('-')[1].strip() if '-' in parts[1] else ''
                    
                    domains.append({
                        'domain': domain,
                        'stars': stars,
                        'evidence': evidence
                    })
            
            return domains
        except Exception as e:
            print(f"   ⚠️  OpenAI API error: {e}")
            return []
    
    def _identify_unique_combination(self, context: str) -> str:
        """
        Identify unique skill combination.
        """
        prompt = f"""What makes this developer's skill combination unique or valuable? Identify their "superpower" - the intersection of skills that sets them apart.

{context}

Unique Combination:"""
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a talent analyst. Identify what makes candidates uniquely valuable."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"   ⚠️  OpenAI API error: {e}")
            return "Unique skill combination analysis unavailable"
    
    def _classify_specialization_type(self, intelligence_data: Dict[str, Any]) -> str:
        """
        Classify as specialist, generalist, or T-shaped.
        """
        skills = intelligence_data.get('skill_summary', {})
        
        lang_count = skills.get('language_count', 0)
        domain_count = skills.get('domain_count', 0)
        
        # Heuristic classification
        if lang_count <= 2 and domain_count <= 2:
            return "Deep Specialist"
        elif lang_count >= 5 and domain_count >= 3:
            return "Broad Generalist"
        elif lang_count <= 3 and domain_count >= 2:
            return "T-Shaped (Deep + Broad)"
        else:
            return "Balanced Specialist"
    
    def _template_specialization(self, intelligence_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Template-based specialization when AI unavailable.
        """
        skills = intelligence_data.get('skill_summary', {})
        
        return {
            'primary_focus': skills.get('specialization', 'Software Development'),
            'domain_depth': [
                {'domain': d, 'stars': 3, 'evidence': 'Active contributor'}
                for d in skills.get('domains', [])[:3]
            ],
            'unique_combination': f"Combines {', '.join(skills.get('top_languages', [])[:2])} expertise",
            'specialization_type': self._classify_specialization_type(intelligence_data)
        }


def main():
    """
    Test specialization detector.
    """
    sample_intelligence = {
        'skill_summary': {
            'specialization': 'Solidity/Hardhat (DeFi) Developer',
            'top_languages': ['Solidity', 'TypeScript', 'JavaScript'],
            'top_frameworks': ['Hardhat', 'OpenZeppelin', 'Foundry'],
            'domains': ['DeFi', 'Smart Contracts', 'Security'],
            'language_count': 3,
            'domain_count': 3
        },
        'profile_data': {
            'repos': [
                {
                    'name': 'defi-protocol',
                    'description': 'Advanced DeFi lending protocol with flash loans',
                    'stargazers_count': 500,
                    'fork': False
                }
            ]
        }
    }
    
    detector = AISpecializationDetector()
    result = detector.detect_specialization(sample_intelligence)
    
    print("\n🎯 Specialization Detection:")
    print(f"\n   Primary Focus: {result['primary_focus']}")
    print(f"   Type: {result['specialization_type']}")
    print(f"\n   Domain Depth:")
    for domain in result['domain_depth']:
        stars = '★' * domain['stars']
        print(f"      {domain['domain']}: {stars} - {domain['evidence']}")
    print(f"\n   Unique Combination: {result['unique_combination']}")


if __name__ == '__main__':
    main()

