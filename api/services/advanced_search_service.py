# ABOUTME: Advanced search service for multi-criteria candidate filtering
# ABOUTME: Implements complex queries with match reason generation and extensive logging

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import psycopg2.extras
from api.models.advanced_search import (
    AdvancedSearchRequest,
    SearchResultPerson,
    SearchResultWithMatch,
    MatchExplanation
)

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Console handler with formatting
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class AdvancedSearchService:
    """Service for executing advanced multi-criteria candidate searches"""
    
    def __init__(self):
        self.logger = logger
    
    def execute_search(
        self,
        conn,
        request: AdvancedSearchRequest,
        offset: int = 0,
        limit: int = 50
    ) -> Tuple[List[SearchResultWithMatch], int, Dict[str, Any]]:
        """
        Execute advanced search with multiple criteria
        
        Returns: (results, total_count, filters_applied)
        """
        start_time = time.time()
        
        self.logger.info("="*80)
        self.logger.info("ADVANCED SEARCH STARTED")
        self.logger.info(f"Filters: {request.model_dump(exclude_none=True)}")
        self.logger.info(f"Pagination: offset={offset}, limit={limit}")
        
        try:
            # Build query components
            where_clauses = []
            params = []
            joins = {}  # Use dict to avoid duplicate joins and control order
            filters_applied = {}
            
            # Track which filters are active
            active_filters = request.model_dump(exclude_none=True)
            
            # Technology filter
            if request.technologies:
                tech_clause, tech_params = self._build_technology_filter(request.technologies)
                where_clauses.append(tech_clause)
                params.extend(tech_params)
                # Mark that we need these joins (will be added later in proper order)
                joins['github_profile'] = True
                joins['github_contribution'] = True
                joins['github_repository'] = True
                filters_applied['technologies'] = request.technologies
                self.logger.info(f"✓ Technology filter applied: {request.technologies}")
            
            # Company filter
            if request.companies:
                company_clause, company_params = self._build_company_filter(request.companies)
                where_clauses.append(company_clause)
                params.extend(company_params)
                joins['employment'] = True
                joins['company'] = True
                filters_applied['companies'] = request.companies
                self.logger.info(f"✓ Company filter applied: {request.companies}")
            
            # Title filter
            if request.titles:
                title_clause, title_params = self._build_title_filter(request.titles)
                where_clauses.append(title_clause)
                params.extend(title_params)
                joins['employment'] = True
                filters_applied['titles'] = request.titles
                self.logger.info(f"✓ Title filter applied: {request.titles}")
            
            # Keyword filter
            if request.keywords:
                keyword_clause, keyword_params = self._build_keyword_filter(request.keywords)
                where_clauses.append(keyword_clause)
                params.extend(keyword_params)
                filters_applied['keywords'] = request.keywords
                self.logger.info(f"✓ Keyword filter applied: {request.keywords}")
            
            # Location filter
            if request.location:
                where_clauses.append("LOWER(p.location) LIKE LOWER(%s)")
                params.append(f"%{request.location}%")
                filters_applied['location'] = request.location
                self.logger.info(f"✓ Location filter applied: {request.location}")
            
            # Email filter
            if request.has_email is not None:
                if request.has_email:
                    where_clauses.append("EXISTS (SELECT 1 FROM person_email WHERE person_id = p.person_id)")
                else:
                    where_clauses.append("NOT EXISTS (SELECT 1 FROM person_email WHERE person_id = p.person_id)")
                filters_applied['has_email'] = request.has_email
                self.logger.info(f"✓ Email filter applied: has_email={request.has_email}")
            
            # GitHub filter
            if request.has_github is not None:
                if request.has_github:
                    where_clauses.append("EXISTS (SELECT 1 FROM github_profile WHERE person_id = p.person_id)")
                else:
                    where_clauses.append("NOT EXISTS (SELECT 1 FROM github_profile WHERE person_id = p.person_id)")
                filters_applied['has_github'] = request.has_github
                self.logger.info(f"✓ GitHub filter applied: has_github={request.has_github}")
            
            # Build final query with joins in proper order
            joins_list = []
            if joins.get('github_profile'):
                joins_list.append("LEFT JOIN github_profile gp ON p.person_id = gp.person_id")
            if joins.get('github_contribution'):
                joins_list.append("LEFT JOIN github_contribution gc ON gp.github_profile_id = gc.github_profile_id")
            if joins.get('github_repository'):
                joins_list.append("LEFT JOIN github_repository gr ON gc.repo_id = gr.repo_id")
            if joins.get('employment'):
                joins_list.append("LEFT JOIN employment e ON p.person_id = e.person_id")
            if joins.get('company'):
                joins_list.append("LEFT JOIN company c ON e.company_id = c.company_id")
            
            joins_sql = "\n".join(joins_list)
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            # Count total results
            count_query = f"""
                SELECT COUNT(DISTINCT p.person_id) as total
                FROM person p
                {joins_sql}
                WHERE {where_sql}
            """
            
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()['total']
            
            self.logger.info(f"Total matching candidates: {total_count:,}")
            
            if total_count == 0:
                self.logger.warning("No results found for search criteria")
                return [], 0, filters_applied
            
            # Get paginated results
            results_query = f"""
                SELECT DISTINCT
                    p.person_id::text,
                    p.full_name,
                    p.linkedin_url,
                    p.location,
                    p.headline,
                    EXISTS (SELECT 1 FROM person_email WHERE person_id = p.person_id) as has_email,
                    EXISTS (SELECT 1 FROM github_profile WHERE person_id = p.person_id) as has_github
                FROM person p
                {joins_sql}
                WHERE {where_sql}
                ORDER BY p.full_name
                LIMIT %s OFFSET %s
            """
            
            params.extend([limit, offset])
            cursor.execute(results_query, params)
            rows = cursor.fetchall()
            
            self.logger.info(f"Retrieved {len(rows)} results for page (offset={offset}, limit={limit})")
            
            # Enrich results with match explanations
            results = []
            for i, row in enumerate(rows, 1):
                person_dict = dict(row)
                person_id = person_dict['person_id']
                
                # Get additional details
                enriched_person = self._enrich_person_data(conn, person_id, person_dict)
                
                # Generate match explanation
                match_explanation = self._generate_match_reasons(
                    conn, person_id, request, enriched_person
                )
                
                result = SearchResultWithMatch(
                    person=enriched_person,
                    match_explanation=match_explanation
                )
                results.append(result)
                
                if i % 10 == 0:
                    self.logger.info(f"  Processed {i}/{len(rows)} results...")
            
            elapsed = time.time() - start_time
            self.logger.info(f"✓ Search completed in {elapsed:.2f}s")
            self.logger.info("="*80)
            
            return results, total_count, filters_applied
            
        except Exception as e:
            self.logger.error(f"✗ Search error: {str(e)}", exc_info=True)
            raise
    
    def _build_technology_filter(self, technologies: List[str]) -> Tuple[str, List]:
        """Build filter for GitHub contribution languages"""
        placeholders = ','.join(['%s'] * len(technologies))
        clause = f"""
            EXISTS (
                SELECT 1
                FROM github_profile gp2
                JOIN github_contribution gc2 ON gp2.github_profile_id = gc2.github_profile_id
                JOIN github_repository gr2 ON gc2.repo_id = gr2.repo_id
                WHERE gp2.person_id = p.person_id
                AND LOWER(gr2.language) IN ({placeholders})
            )
        """
        params = [tech.lower() for tech in technologies]
        return clause, params
    
    def _build_company_filter(self, companies: List[str]) -> Tuple[str, List]:
        """Build filter for employment history OR repository ownership"""
        placeholders = ','.join(['%s'] * len(companies))
        
        # Match either worked at company OR contributed to company's repos
        clause = f"""
            (
                EXISTS (
                    SELECT 1
                    FROM employment e2
                    JOIN company c2 ON e2.company_id = c2.company_id
                    WHERE e2.person_id = p.person_id
                    AND LOWER(c2.company_name) IN ({placeholders})
                )
                OR
                EXISTS (
                    SELECT 1
                    FROM github_profile gp3
                    JOIN github_contribution gc3 ON gp3.github_profile_id = gc3.github_profile_id
                    JOIN github_repository gr3 ON gc3.repo_id = gr3.repo_id
                    JOIN company c3 ON gr3.company_id = c3.company_id
                    WHERE gp3.person_id = p.person_id
                    AND LOWER(c3.company_name) IN ({placeholders})
                )
            )
        """
        params = [comp.lower() for comp in companies] * 2  # Used twice in query
        return clause, params
    
    def _build_title_filter(self, titles: List[str]) -> Tuple[str, List]:
        """Build filter for job title patterns using fuzzy matching"""
        # Use regex OR pattern for multiple titles
        title_conditions = []
        params = []
        
        for title in titles:
            title_conditions.append("e.title ~* %s")
            params.append(title)  # PostgreSQL ~* is case-insensitive regex
        
        clause = f"""
            EXISTS (
                SELECT 1
                FROM employment e3
                WHERE e3.person_id = p.person_id
                AND ({' OR '.join(title_conditions)})
            )
        """
        return clause, params
    
    def _build_keyword_filter(self, keywords: List[str]) -> Tuple[str, List]:
        """Build filter for keywords across multiple fields"""
        keyword_conditions = []
        params = []
        
        for keyword in keywords:
            keyword_pattern = f"%{keyword}%"
            keyword_conditions.append("""
                (
                    LOWER(p.headline) LIKE LOWER(%s)
                    OR LOWER(p.description) LIKE LOWER(%s)
                )
            """)
            params.extend([keyword_pattern, keyword_pattern])
        
        clause = f"({' OR '.join(keyword_conditions)})"
        return clause, params
    
    def _enrich_person_data(
        self, conn, person_id: str, base_data: Dict
    ) -> SearchResultPerson:
        """Enrich person data with current employment and GitHub stats"""
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get current employment
        cursor.execute("""
            SELECT c.company_name, e.title
            FROM employment e
            JOIN company c ON e.company_id = c.company_id
            WHERE e.person_id = %s::uuid
            AND e.end_date IS NULL
            ORDER BY e.start_date DESC NULLS LAST
            LIMIT 1
        """, (person_id,))
        current_job = cursor.fetchone()
        
        # Get GitHub stats
        cursor.execute("""
            SELECT
                gp.github_username,
                COALESCE(SUM(gr.stars), 0) as total_stars,
                COUNT(DISTINCT gc.repo_id) as repo_count
            FROM github_profile gp
            LEFT JOIN github_contribution gc ON gp.github_profile_id = gc.github_profile_id
            LEFT JOIN github_repository gr ON gc.repo_id = gr.repo_id
            WHERE gp.person_id = %s::uuid
            GROUP BY gp.github_username
        """, (person_id,))
        github_stats = cursor.fetchone()
        
        # Calculate years of experience (rough estimate from employment history)
        cursor.execute("""
            SELECT MIN(start_date) as first_job
            FROM employment
            WHERE person_id = %s::uuid
            AND start_date IS NOT NULL
        """, (person_id,))
        first_job = cursor.fetchone()
        
        years_experience = None
        if first_job and first_job['first_job']:
            years_experience = (datetime.now().date() - first_job['first_job']).days // 365
        
        return SearchResultPerson(
            person_id=base_data['person_id'],
            full_name=base_data['full_name'],
            linkedin_url=base_data['linkedin_url'],
            location=base_data.get('location'),
            headline=base_data.get('headline'),
            has_email=base_data.get('has_email', False),
            has_github=base_data.get('has_github', False),
            current_company=current_job['company_name'] if current_job else None,
            current_title=current_job['title'] if current_job else None,
            years_experience=years_experience,
            total_github_stars=int(github_stats['total_stars']) if github_stats else None,
            github_username=github_stats['github_username'] if github_stats else None
        )
    
    def _generate_match_reasons(
        self,
        conn,
        person_id: str,
        request: AdvancedSearchRequest,
        person: SearchResultPerson
    ) -> MatchExplanation:
        """Generate explanation of why this person matched the search"""
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        matched_technologies = []
        matched_companies = []
        matched_titles = []
        matched_keywords = []
        
        # Check technologies
        if request.technologies:
            cursor.execute("""
                SELECT DISTINCT gr.language
                FROM github_profile gp
                JOIN github_contribution gc ON gp.github_profile_id = gc.github_profile_id
                JOIN github_repository gr ON gc.repo_id = gr.repo_id
                WHERE gp.person_id = %s::uuid
                AND LOWER(gr.language) = ANY(%s)
            """, (person_id, [t.lower() for t in request.technologies]))
            matched_technologies = [row['language'] for row in cursor.fetchall()]
        
        # Check companies
        if request.companies:
            cursor.execute("""
                SELECT DISTINCT c.company_name
                FROM employment e
                JOIN company c ON e.company_id = c.company_id
                WHERE e.person_id = %s::uuid
                AND LOWER(c.company_name) = ANY(%s)
            """, (person_id, [comp.lower() for comp in request.companies]))
            matched_companies = [row['company_name'] for row in cursor.fetchall()]
        
        # Check titles
        if request.titles:
            cursor.execute("""
                SELECT DISTINCT e.title
                FROM employment e
                WHERE e.person_id = %s::uuid
                AND e.title IS NOT NULL
            """, (person_id,))
            all_titles = [row['title'] for row in cursor.fetchall()]
            
            for search_title in request.titles:
                for actual_title in all_titles:
                    if search_title.lower() in actual_title.lower():
                        matched_titles.append(actual_title)
                        break
        
        # Check keywords
        if request.keywords:
            headline = person.headline or ""
            for keyword in request.keywords:
                if keyword.lower() in headline.lower():
                    matched_keywords.append(keyword)
        
        # Calculate relevance score
        relevance_score = self._score_relevance(
            request, matched_technologies, matched_companies, 
            matched_titles, matched_keywords
        )
        
        # Generate match summary
        summary_parts = []
        if matched_technologies:
            summary_parts.append(f"Technologies: {', '.join(matched_technologies)}")
        if matched_companies:
            summary_parts.append(f"Companies: {', '.join(matched_companies)}")
        if matched_titles:
            summary_parts.append(f"Titles: {', '.join(matched_titles[:2])}")  # Limit to 2
        if matched_keywords:
            summary_parts.append(f"Keywords: {', '.join(matched_keywords)}")
        
        match_summary = " | ".join(summary_parts) if summary_parts else "General match"
        
        return MatchExplanation(
            matched_technologies=matched_technologies,
            matched_companies=matched_companies,
            matched_titles=matched_titles,
            matched_keywords=matched_keywords,
            relevance_score=relevance_score,
            match_summary=match_summary
        )
    
    def _score_relevance(
        self,
        request: AdvancedSearchRequest,
        matched_techs: List[str],
        matched_companies: List[str],
        matched_titles: List[str],
        matched_keywords: List[str]
    ) -> float:
        """Calculate relevance score 0-100 based on match quality"""
        score = 0.0
        max_score = 0.0
        
        # Technology matches (40 points)
        if request.technologies:
            max_score += 40
            match_ratio = len(matched_techs) / len(request.technologies)
            score += match_ratio * 40
        
        # Company matches (30 points)
        if request.companies:
            max_score += 30
            match_ratio = len(matched_companies) / len(request.companies)
            score += match_ratio * 30
        
        # Title matches (20 points)
        if request.titles:
            max_score += 20
            if matched_titles:
                score += 20  # Binary: either matched or didn't
        
        # Keyword matches (10 points)
        if request.keywords:
            max_score += 10
            match_ratio = len(matched_keywords) / len(request.keywords)
            score += match_ratio * 10
        
        # Normalize to 0-100
        if max_score == 0:
            return 50.0  # Default score if no specific criteria
        
        return round((score / max_score) * 100, 1)

