"""
ABOUTME: AI-powered profile analyzer that generates human-readable summaries from GitHub intelligence.
ABOUTME: Uses GPT-4o-mini to create recruiter-friendly profiles from technical data.
"""

import os
import json
from typing import Dict, Any, Optional
import openai


class AIProfileAnalyzer:
    """
    Generates human-readable profile analysis using AI.
    
    Takes raw GitHub intelligence and produces:
    - Executive summary
    - Technical strengths
    - Specialization description
    - Ideal role fit
    - Personalized outreach suggestions
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize AI analyzer.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if self.api_key:
            openai.api_key = self.api_key
        
        self.model = 'gpt-4o-mini'  # Cost-effective model
    
    def analyze_profile(self, intelligence_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate AI analysis of a developer profile.
        
        Args:
            intelligence_data: Complete intelligence from orchestrator
        
        Returns:
            Dictionary with AI-generated summaries
        """
        if not self.api_key:
            return self._generate_template_analysis(intelligence_data)
        
        # Prepare context for AI
        context = self._prepare_context(intelligence_data)
        
        # Generate summary
        summary = self._generate_summary(context)
        
        # Generate specialization
        specialization = self._generate_specialization(context)
        
        # Generate ideal role fit
        ideal_role = self._generate_ideal_role(context)
        
        # Generate outreach tips
        outreach_tips = self._generate_outreach_tips(context)
        
        return {
            'executive_summary': summary,
            'specialization': specialization,
            'ideal_role_fit': ideal_role,
            'outreach_tips': outreach_tips
        }
    
    def _prepare_context(self, intelligence_data: Dict[str, Any]) -> str:
        """
        Prepare context string for AI from intelligence data.
        """
        username = intelligence_data.get('username')
        skill_summary = intelligence_data.get('skill_summary', {})
        seniority = intelligence_data.get('seniority', {})
        network = intelligence_data.get('network', {})
        activity = intelligence_data.get('activity', {})
        reachability = intelligence_data.get('reachability', {})
        
        context = f"""
Developer Profile: @{username}

TECHNICAL SKILLS:
- Primary Specialization: {skill_summary.get('specialization', 'Unknown')}
- Top Languages: {', '.join(skill_summary.get('top_languages', [])[:5])}
- Frameworks: {', '.join(skill_summary.get('top_frameworks', [])[:5])}
- Domains: {', '.join(skill_summary.get('domains', []))}

EXPERIENCE & SENIORITY:
- Level: {seniority.get('seniority_level', 'Unknown')}
- Confidence: {seniority.get('confidence', 0):.0%}
- Score Breakdown: Experience={seniority.get('breakdown', {}).get('experience', 0):.0f}, Output={seniority.get('breakdown', {}).get('output', 0):.0f}, Leadership={seniority.get('breakdown', {}).get('leadership', 0):.0f}, Influence={seniority.get('breakdown', {}).get('influence', 0):.0f}

NETWORK & INFLUENCE:
- Collaborators: {network.get('total_collaborators', 0)}
- Organizations: {len(network.get('organizations', []))}
- Influence Score: {network.get('influence_score', 0)}/100

ACTIVITY PATTERNS:
- Activity Level: {activity.get('activity_level', 'Unknown')}
- Commits/week: {activity.get('commits_per_week', 0)}
- Trend: {activity.get('activity_trend', 'Unknown')}
- Consistency: {activity.get('consistency_score', 0):.0%}
- Days Since Active: {activity.get('days_since_active', 'Unknown')}

REACHABILITY:
- Score: {reachability.get('reachability_score', 0)}/100
- Best Method: {reachability.get('best_contact_method', 'Unknown')}
- Contact Info Available: {len(reachability.get('contact_info', {}))} channels
"""
        
        return context
    
    def _generate_summary(self, context: str) -> str:
        """
        Generate executive summary.
        """
        prompt = f"""Based on this developer's GitHub profile data, write a concise 2-3 sentence executive summary that a recruiter would find useful. Focus on technical expertise, seniority level, and what makes them stand out.

{context}

Executive Summary:"""
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a technical recruiter analyzing developer profiles. Be concise and focus on what makes candidates valuable."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"   ⚠️  OpenAI API error: {e}")
            return "AI analysis unavailable"
    
    def _generate_specialization(self, context: str) -> str:
        """
        Generate specialization description.
        """
        prompt = f"""Based on this developer's profile, describe their technical specialization in one clear sentence. Be specific about what they're an expert in.

{context}

Specialization:"""
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a technical analyst. Describe specializations clearly and specifically."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"   ⚠️  OpenAI API error: {e}")
            return "Specialization analysis unavailable"
    
    def _generate_ideal_role(self, context: str) -> str:
        """
        Generate ideal role fit description.
        """
        prompt = f"""Based on this developer's profile, describe 2-3 ideal roles they would excel in. Be specific about level (e.g., "Senior Engineer", "Staff Engineer") and type of work.

{context}

Ideal Roles:"""
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a technical recruiter matching candidates to roles. Be specific and realistic."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"   ⚠️  OpenAI API error: {e}")
            return "Role fit analysis unavailable"
    
    def _generate_outreach_tips(self, context: str) -> str:
        """
        Generate personalized outreach tips.
        """
        prompt = f"""Based on this developer's profile, provide 2-3 specific tips for reaching out to them effectively. Include what to emphasize and best communication approach.

{context}

Outreach Tips:"""
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a recruiting strategist. Give practical, specific advice for contacting candidates."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"   ⚠️  OpenAI API error: {e}")
            return "Outreach tips unavailable"
    
    def _generate_template_analysis(self, intelligence_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate template-based analysis when AI is not available.
        """
        skill_summary = intelligence_data.get('skill_summary', {})
        seniority = intelligence_data.get('seniority', {})
        activity = intelligence_data.get('activity', {})
        reachability = intelligence_data.get('reachability', {})
        
        specialization = skill_summary.get('specialization', 'Software Developer')
        seniority_level = seniority.get('seniority_level', 'Unknown')
        activity_level = activity.get('activity_level', 'Unknown')
        reachability_level = reachability.get('reachability_level', 'Unknown')
        
        summary = f"{seniority_level} {specialization} with {activity_level.lower()} activity level on GitHub. {reachability_level} reachability score."
        
        return {
            'executive_summary': summary,
            'specialization': specialization,
            'ideal_role_fit': f"{seniority_level} roles in areas matching their {specialization.lower()} expertise",
            'outreach_tips': f"Contact via {reachability.get('best_contact_method', 'GitHub')}. Reference their work in {', '.join(skill_summary.get('domains', ['open source'])[:2])}."
        }


def main():
    """
    Test AI profile analyzer.
    """
    # Sample intelligence data
    sample_intelligence = {
        'username': 'test_dev',
        'skill_summary': {
            'specialization': 'Solidity/Hardhat (DeFi) Developer',
            'top_languages': ['Solidity', 'TypeScript', 'JavaScript'],
            'top_frameworks': ['Hardhat', 'OpenZeppelin', 'Ethers.js'],
            'domains': ['DeFi', 'Smart Contracts']
        },
        'seniority': {
            'seniority_level': 'Senior',
            'confidence': 0.85,
            'breakdown': {
                'experience': 40,
                'output': 25,
                'leadership': 30,
                'influence': 25
            }
        },
        'network': {
            'total_collaborators': 45,
            'organizations': [{'name': 'Uniswap'}, {'name': 'Aave'}],
            'influence_score': 75
        },
        'activity': {
            'activity_level': 'High',
            'commits_per_week': 15,
            'activity_trend': 'Growing',
            'consistency_score': 0.75,
            'days_since_active': 2
        },
        'reachability': {
            'reachability_score': 85,
            'reachability_level': 'Very High',
            'best_contact_method': 'Email',
            'contact_info': {'email': 'test@example.com', 'twitter': '@testdev'}
        }
    }
    
    analyzer = AIProfileAnalyzer()
    result = analyzer.analyze_profile(sample_intelligence)
    
    print("\n🤖 AI Profile Analysis:")
    print(f"\n   Executive Summary:\n   {result['executive_summary']}")
    print(f"\n   Specialization:\n   {result['specialization']}")
    print(f"\n   Ideal Role Fit:\n   {result['ideal_role_fit']}")
    print(f"\n   Outreach Tips:\n   {result['outreach_tips']}")


if __name__ == '__main__':
    main()

