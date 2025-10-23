"""
AI Service for Talent Intelligence

Provides AI-powered insights about candidates using OpenAI or Anthropic Claude.
Focuses on making technical work understandable for recruiters.
"""

import os
import json
from typing import Optional, Dict, List, Any
from datetime import datetime
import logging

# Try importing AI clients
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


logger = logging.getLogger(__name__)


class AIService:
    """
    Service for AI-powered candidate analysis and insights.
    
    Supports multiple AI providers:
    - OpenAI (GPT-4o-mini, GPT-3.5-turbo)
    - Anthropic Claude (Claude 3.5 Sonnet)
    """
    
    def __init__(
        self,
        provider: str = "openai",
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize AI service.
        
        Args:
            provider: "openai" or "anthropic"
            model: Specific model name (optional, uses defaults)
            api_key: API key (optional, uses env vars)
        """
        self.provider = provider.lower()
        
        # Default models
        self.default_models = {
            "openai": "gpt-4o-mini",  # Good balance of cost/quality
            "anthropic": "claude-3-5-sonnet-20241022"
        }
        
        self.model = model or self.default_models.get(self.provider)
        
        # Initialize client
        if self.provider == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError("OpenAI library not installed. Run: pip install openai")
            
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")
            
            self.client = OpenAI(api_key=api_key)
            
        elif self.provider == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                raise ImportError("Anthropic library not installed. Run: pip install anthropic")
            
            api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")
            
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def _call_openai(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Call OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2000)
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _call_anthropic(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Call Anthropic Claude API."""
        try:
            # Convert messages format (Anthropic doesn't use system in messages array)
            system_message = None
            converted_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    converted_messages.append(msg)
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", 2000),
                temperature=kwargs.get("temperature", 0.7),
                system=system_message or "You are a helpful recruiting assistant.",
                messages=converted_messages
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    def _call_ai(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Route to appropriate AI provider."""
        if self.provider == "openai":
            return self._call_openai(messages, **kwargs)
        elif self.provider == "anthropic":
            return self._call_anthropic(messages, **kwargs)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def generate_profile_summary(
        self,
        candidate_data: Dict[str, Any],
        job_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a recruiter-friendly summary of a candidate's profile.
        
        Args:
            candidate_data: Dictionary with person, employment, github, etc.
            job_context: Optional job description or role context
        
        Returns:
            Dictionary with summary, key_strengths, domains, etc.
        """
        # Build context from candidate data
        context = self._build_candidate_context(candidate_data)
        
        # Build prompt
        system_prompt = """You are an expert technical recruiter who explains engineering talent to non-technical hiring managers.

Your job is to:
1. Summarize a candidate's career and technical work in clear, jargon-free language
2. Highlight their key strengths and domains of expertise
3. Explain what kind of roles they'd be best suited for
4. Make technical work understandable to non-engineers

Be concise, insightful, and focus on what matters for hiring decisions."""

        user_prompt = f"""Analyze this candidate and provide a recruiter-friendly summary:

{context}

{"Job Context: " + job_context if job_context else ""}

Provide a JSON response with:
{{
    "executive_summary": "2-3 sentence overview of who they are professionally",
    "key_strengths": ["strength 1", "strength 2", "strength 3"],
    "technical_domains": ["domain 1", "domain 2"],
    "ideal_roles": ["role 1", "role 2", "role 3"],
    "career_trajectory": "Brief assessment of their career path and level",
    "standout_projects": ["project 1 with brief explanation", "project 2"],
    "recruiter_notes": "2-3 sentences of what makes them interesting or concerns to note"
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = self._call_ai(messages, temperature=0.7)
            
            # Parse JSON response
            # Handle markdown code blocks if present
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            summary = json.loads(response)
            summary["generated_at"] = datetime.now().isoformat()
            summary["model"] = self.model
            
            return summary
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            # Fallback: return raw response
            return {
                "executive_summary": response,
                "generated_at": datetime.now().isoformat(),
                "model": self.model,
                "error": "Failed to parse structured response"
            }
        except Exception as e:
            logger.error(f"Error generating profile summary: {e}")
            raise
    
    def analyze_code_quality(
        self,
        candidate_data: Dict[str, Any],
        job_requirements: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a candidate's code quality and technical work.
        
        Args:
            candidate_data: Dictionary with GitHub contributions and profile
            job_requirements: Optional job requirements to assess fit
        
        Returns:
            Dictionary with code analysis, quality assessment, relevance
        """
        github_context = self._build_github_context(candidate_data)
        
        system_prompt = """You are a senior engineering manager who reviews code and technical contributions.

Your job is to:
1. Assess code quality and engineering practices
2. Explain technical work in terms recruiters understand
3. Identify what kind of engineering work they excel at
4. Note any red flags or concerns

Focus on insights that help hiring decisions, not just technical minutiae."""

        user_prompt = f"""Analyze this engineer's technical work:

{github_context}

{"Job Requirements: " + job_requirements if job_requirements else ""}

Provide a JSON response with:
{{
    "code_quality_assessment": "Overall assessment of their code quality and practices",
    "technical_depth": "Junior/Mid/Senior/Staff - with brief justification",
    "engineering_style": "Description of how they work (e.g., 'full-stack generalist', 'systems specialist')",
    "standout_contributions": ["contribution 1 with impact", "contribution 2"],
    "languages_and_tools": ["primary languages/frameworks they work with"],
    "work_complexity": "Description of complexity level (e.g., 'infrastructure tooling', 'UI components')",
    "collaboration_indicators": "Evidence of teamwork, code review, documentation",
    "relevance_to_role": "How well they match the job requirements (if provided)",
    "concerns": ["any concerns or gaps to note"]
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = self._call_ai(messages, temperature=0.7)
            
            # Parse JSON
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            analysis = json.loads(response)
            analysis["analyzed_at"] = datetime.now().isoformat()
            analysis["model"] = self.model
            
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return {
                "code_quality_assessment": response,
                "analyzed_at": datetime.now().isoformat(),
                "model": self.model,
                "error": "Failed to parse structured response"
            }
        except Exception as e:
            logger.error(f"Error analyzing code quality: {e}")
            raise
    
    def answer_question(
        self,
        candidate_data: Dict[str, Any],
        question: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Answer a specific question about a candidate.
        
        Args:
            candidate_data: Dictionary with candidate information
            question: The recruiter's question
            conversation_history: Previous Q&A for context
        
        Returns:
            Answer string
        """
        context = self._build_candidate_context(candidate_data)
        github_context = self._build_github_context(candidate_data)
        
        system_prompt = """You are a helpful recruiting assistant who answers questions about engineering candidates.

Your job is to:
1. Answer questions accurately based on the candidate's data
2. Explain technical concepts in recruiter-friendly language
3. Provide actionable insights for hiring decisions
4. Admit when you don't have enough information

Be direct, helpful, and focused on what the recruiter needs to know."""

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current question with context
        user_message = f"""Candidate Information:
{context}

GitHub Activity:
{github_context}

Question: {question}

Please answer based on the information provided. If you don't have enough information, say so."""

        messages.append({"role": "user", "content": user_message})
        
        try:
            answer = self._call_ai(messages, temperature=0.7, max_tokens=1000)
            return answer
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            raise
    
    def _build_candidate_context(self, candidate_data: Dict[str, Any]) -> str:
        """Build a text context from candidate data."""
        parts = []
        
        # Person info
        person = candidate_data.get("person", {})
        if person:
            parts.append(f"Name: {person.get('full_name', 'Unknown')}")
            if person.get("headline"):
                parts.append(f"Current Role: {person.get('headline')}")
            if person.get("location"):
                parts.append(f"Location: {person.get('location')}")
            parts.append("")
        
        # Employment history
        employment = candidate_data.get("employment", [])
        if employment:
            parts.append("Employment History:")
            for job in employment[:5]:  # Top 5 most recent
                company = job.get("company_name", "Unknown Company")
                title = job.get("title", "Unknown Role")
                start = job.get("start_date", "")
                end = job.get("end_date", "Present")
                parts.append(f"  - {title} at {company} ({start} to {end})")
            parts.append("")
        
        # Emails (just note if available)
        emails = candidate_data.get("emails", [])
        if emails:
            parts.append(f"Contact: {len(emails)} email(s) available")
            parts.append("")
        
        return "\n".join(parts)
    
    def _build_github_context(self, candidate_data: Dict[str, Any]) -> str:
        """Build GitHub-specific context."""
        parts = []
        
        github = candidate_data.get("github_profile")
        if github:
            parts.append(f"GitHub: @{github.get('github_username', 'unknown')}")
            if github.get("bio"):
                parts.append(f"Bio: {github.get('bio')}")
            parts.append(f"Followers: {github.get('followers', 0)}")
            parts.append(f"Public Repos: {github.get('public_repos', 0)}")
            parts.append("")
        
        contributions = candidate_data.get("github_contributions", [])
        if contributions:
            parts.append("Key Repositories:")
            for contrib in contributions[:10]:  # Top 10
                repo = contrib.get("repo_full_name", "unknown")
                stars = contrib.get("stars", 0)
                lang = contrib.get("language", "Unknown")
                commits = contrib.get("contribution_count", 0)
                desc = contrib.get("description", "")
                
                parts.append(f"  - {repo} ({lang})")
                parts.append(f"    ⭐ {stars} stars | {commits} commits")
                if desc:
                    parts.append(f"    {desc[:100]}")
            parts.append("")
        
        return "\n".join(parts)


# Convenience functions for easy usage
def get_ai_service(provider: str = "openai", model: Optional[str] = None) -> AIService:
    """Get an AI service instance."""
    return AIService(provider=provider, model=model)

