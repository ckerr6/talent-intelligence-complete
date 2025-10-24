# ABOUTME: Job Description parser service using OpenAI
# ABOUTME: Extracts structured requirements from unstructured JD text

import logging
import time
import json
import os
from typing import Dict, Any
from openai import OpenAI
from api.models.advanced_search import (
    ParsedJobDescription,
    AdvancedSearchRequest
)

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class JobDescriptionParser:
    """Parse job descriptions and extract structured requirements using AI"""
    
    def __init__(self):
        self.logger = logger
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            self.logger.warning("OPENAI_API_KEY not set - JD parsing will not work")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
            self.logger.info("OpenAI client initialized for JD parsing")
    
    def parse_job_description(self, jd_text: str) -> ParsedJobDescription:
        """
        Parse job description text and extract structured requirements
        
        Args:
            jd_text: Full job description text
            
        Returns:
            ParsedJobDescription with extracted fields
        """
        start_time = time.time()
        
        self.logger.info("="*80)
        self.logger.info("JOB DESCRIPTION PARSING STARTED")
        self.logger.info(f"JD text length: {len(jd_text)} characters")
        
        if not self.client:
            self.logger.error("OpenAI client not initialized - cannot parse JD")
            return ParsedJobDescription(
                original_jd=jd_text,
                extraction_confidence=0.0
            )
        
        try:
            # Build prompt for GPT-4
            prompt = self._build_parsing_prompt(jd_text)
            
            self.logger.info("Calling OpenAI API (GPT-4)...")
            api_start = time.time()
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using mini for cost efficiency
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert technical recruiter who extracts structured data from job descriptions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3,  # Low temperature for more consistent extraction
                max_tokens=1500
            )
            
            api_elapsed = time.time() - api_start
            self.logger.info(f"✓ OpenAI API call completed in {api_elapsed:.2f}s")
            
            # Log token usage
            usage = response.usage
            self.logger.info(f"Token usage: {usage.prompt_tokens} prompt + {usage.completion_tokens} completion = {usage.total_tokens} total")
            
            # Parse response
            content = response.choices[0].message.content
            parsed_data = json.loads(content)
            
            self.logger.info("Extracted fields:")
            self.logger.info(f"  Technologies: {parsed_data.get('technologies', [])}")
            self.logger.info(f"  Companies: {parsed_data.get('companies', [])}")
            self.logger.info(f"  Job Level: {parsed_data.get('job_level')}")
            self.logger.info(f"  Domain Expertise: {parsed_data.get('domain_expertise', [])}")
            self.logger.info(f"  Min Experience: {parsed_data.get('min_experience_years')}")
            self.logger.info(f"  Location: {parsed_data.get('location')}")
            self.logger.info(f"  Keywords: {parsed_data.get('keywords', [])}")
            
            # Create ParsedJobDescription
            parsed_jd = ParsedJobDescription(
                technologies=parsed_data.get('technologies', []),
                companies=parsed_data.get('companies', []),
                job_level=parsed_data.get('job_level'),
                domain_expertise=parsed_data.get('domain_expertise', []),
                min_experience_years=parsed_data.get('min_experience_years'),
                location=parsed_data.get('location'),
                keywords=parsed_data.get('keywords', []),
                original_jd=jd_text,
                extraction_confidence=parsed_data.get('confidence', 0.8)
            )
            
            elapsed = time.time() - start_time
            self.logger.info(f"✓ JD parsing completed in {elapsed:.2f}s")
            self.logger.info("="*80)
            
            return parsed_jd
            
        except Exception as e:
            self.logger.error(f"✗ JD parsing error: {str(e)}", exc_info=True)
            # Return empty parsed JD on error
            return ParsedJobDescription(
                original_jd=jd_text,
                extraction_confidence=0.0
            )
    
    def _build_parsing_prompt(self, jd_text: str) -> str:
        """Build the prompt for GPT-4 to parse the JD"""
        return f"""Parse this job description and extract the following information as JSON:

1. **technologies**: List of programming languages, frameworks, and technologies mentioned
   - Examples: ["Rust", "Solidity", "TypeScript", "React", "PostgreSQL"]
   - Include both required and preferred technologies

2. **companies**: List of companies mentioned as preferred backgrounds
   - Examples: ["Jump Trading", "Wintermute", "Paradigm", "Uniswap"]
   - Look for phrases like "experience at", "worked at", "background from"

3. **job_level**: Seniority level of the role
   - One of: "Junior", "Mid", "Senior", "Staff", "Principal", "Lead", null
   - Infer from job title and requirements

4. **domain_expertise**: List of domain/industry keywords
   - Examples: ["DeFi", "trading systems", "smart contracts", "protocols", "infrastructure"]
   - Include industry-specific terms

5. **min_experience_years**: Minimum years of experience required
   - Integer or null if not specified
   - Look for "X+ years" or "X years of experience"

6. **location**: Location requirements
   - String or null if remote/not specified
   - Examples: "San Francisco", "New York", "Remote", "Remote US"

7. **keywords**: Additional important keywords and skills
   - Examples: ["protocol development", "system design", "smart contract security"]
   - Include soft skills and specific technical skills not in technologies

8. **confidence**: Your confidence in the extraction (0.0 to 1.0)
   - Consider clarity of the JD and specificity of requirements

Return ONLY valid JSON with these exact keys. If any field is not found, use empty list [] for arrays or null for scalars.

Job Description:
{jd_text}
"""
    
    def convert_to_search_request(self, parsed_jd: ParsedJobDescription) -> AdvancedSearchRequest:
        """
        Convert parsed JD to AdvancedSearchRequest
        
        Args:
            parsed_jd: Parsed job description
            
        Returns:
            AdvancedSearchRequest ready for search execution
        """
        self.logger.info("Converting parsed JD to search request...")
        
        # Combine domain expertise and keywords
        all_keywords = list(set(parsed_jd.domain_expertise + parsed_jd.keywords))
        
        # Build title patterns from job level
        titles = []
        if parsed_jd.job_level:
            level = parsed_jd.job_level.lower()
            if level in ['senior', 'staff', 'principal', 'lead']:
                titles.append(f"{parsed_jd.job_level}.*Engineer")
                titles.append(f"{parsed_jd.job_level}.*Developer")
            else:
                titles.append("Engineer")
                titles.append("Developer")
        
        search_request = AdvancedSearchRequest(
            technologies=parsed_jd.technologies if parsed_jd.technologies else None,
            companies=parsed_jd.companies if parsed_jd.companies else None,
            titles=titles if titles else None,
            keywords=all_keywords if all_keywords else None,
            location=parsed_jd.location,
            min_experience_years=parsed_jd.min_experience_years,
            has_email=True,  # Usually want contact info
            has_github=True if parsed_jd.technologies else None  # Want GitHub if tech role
        )
        
        self.logger.info(f"✓ Search request created with {len([f for f in [search_request.technologies, search_request.companies, search_request.titles, search_request.keywords] if f])} active filters")
        
        return search_request

