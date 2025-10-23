"""
Market Intelligence Service

Provides insights about hiring patterns, talent flow, and market trends.
Powered by AI for natural language queries.
"""

from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, timedelta
from psycopg2.extras import RealDictCursor
import logging

from api.services.ai_service import get_ai_service

logger = logging.getLogger(__name__)


class MarketIntelligenceService:
    """
    Service for analyzing market intelligence data.
    
    Provides insights about:
    - Company hiring patterns
    - Talent flow between organizations
    - University pipelines
    - Technology distribution
    - AI-powered natural language queries
    """
    
    def __init__(self, db_connection):
        """Initialize with database connection."""
        self.conn = db_connection
    
    def get_hiring_patterns(
        self,
        company_id: Optional[str] = None,
        company_name: Optional[str] = None,
        time_period_months: int = 24
    ) -> Dict[str, Any]:
        """
        Analyze hiring patterns for a company.
        
        Returns:
        - Hiring volume over time
        - Most common roles hired
        - Growth rate
        - Seasonal patterns
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Get company ID if name provided
            if company_name and not company_id:
                cursor.execute(
                    "SELECT company_id FROM company WHERE company_name ILIKE %s LIMIT 1",
                    (f"%{company_name}%",)
                )
                result = cursor.fetchone()
                if result:
                    company_id = result['company_id']
                else:
                    return {"error": "Company not found"}
            
            if not company_id:
                return {"error": "Company ID or name required"}
            
            # Get company info
            cursor.execute(
                "SELECT company_name FROM company WHERE company_id = %s",
                (company_id,)
            )
            company = cursor.fetchone()
            
            # Hiring volume by month
            cursor.execute(
                """
                SELECT 
                    DATE_TRUNC('month', start_date) as month,
                    COUNT(*) as hires
                FROM employment
                WHERE company_id = %s
                AND start_date >= NOW() - INTERVAL '%s months'
                AND start_date IS NOT NULL
                GROUP BY DATE_TRUNC('month', start_date)
                ORDER BY month
                """,
                (company_id, time_period_months)
            )
            monthly_hires = cursor.fetchall()
            
            # Most common roles
            cursor.execute(
                """
                SELECT 
                    title,
                    COUNT(*) as count
                FROM employment
                WHERE company_id = %s
                AND start_date >= NOW() - INTERVAL '%s months'
                AND title IS NOT NULL
                GROUP BY title
                ORDER BY count DESC
                LIMIT 10
                """,
                (company_id, time_period_months)
            )
            top_roles = cursor.fetchall()
            
            # Total hires in period
            cursor.execute(
                """
                SELECT COUNT(*) as total
                FROM employment
                WHERE company_id = %s
                AND start_date >= NOW() - INTERVAL '%s months'
                """,
                (company_id, time_period_months)
            )
            total_hires = cursor.fetchone()['total']
            
            # Average tenure (for those who left)
            cursor.execute(
                """
                SELECT AVG(DATE_PART('day', end_date::timestamp - start_date::timestamp)) as avg_tenure_days
                FROM employment
                WHERE company_id = %s
                AND end_date IS NOT NULL
                AND start_date IS NOT NULL
                """,
                (company_id,)
            )
            avg_tenure_result = cursor.fetchone()
            avg_tenure = avg_tenure_result['avg_tenure_days'] if avg_tenure_result else None
            
            cursor.close()
            
            return {
                "company_id": str(company_id),
                "company_name": company['company_name'],
                "time_period_months": time_period_months,
                "total_hires": total_hires,
                "avg_tenure_days": float(avg_tenure) if avg_tenure else None,
                "monthly_hires": [
                    {
                        "month": m['month'].isoformat() if m['month'] else None,
                        "hires": m['hires']
                    }
                    for m in monthly_hires
                ],
                "top_roles": [
                    {"title": r['title'], "count": r['count']}
                    for r in top_roles
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting hiring patterns: {e}")
            cursor.close()
            raise
    
    def get_talent_flow(
        self,
        company_id: Optional[str] = None,
        company_name: Optional[str] = None,
        direction: str = "both"  # "inbound", "outbound", or "both"
    ) -> Dict[str, Any]:
        """
        Analyze talent flow to/from a company.
        
        Returns:
        - Top feeder companies (where hires come from)
        - Top destination companies (where people go)
        - Flow volumes
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Get company ID if name provided
            if company_name and not company_id:
                cursor.execute(
                    "SELECT company_id FROM company WHERE company_name ILIKE %s LIMIT 1",
                    (f"%{company_name}%",)
                )
                result = cursor.fetchone()
                if result:
                    company_id = result['company_id']
            
            if not company_id:
                return {"error": "Company ID or name required"}
            
            # Get company info
            cursor.execute(
                "SELECT company_name FROM company WHERE company_id = %s",
                (company_id,)
            )
            company = cursor.fetchone()
            
            result = {
                "company_id": str(company_id),
                "company_name": company['company_name']
            }
            
            # Inbound flow (feeder companies)
            if direction in ["inbound", "both"]:
                cursor.execute(
                    """
                    WITH target_company_joins AS (
                        SELECT person_id, start_date
                        FROM employment
                        WHERE company_id = %s
                        AND start_date IS NOT NULL
                    ),
                    previous_employers AS (
                        SELECT 
                            e.company_id,
                            c.company_name,
                            COUNT(DISTINCT e.person_id) as person_count
                        FROM employment e
                        JOIN company c ON e.company_id = c.company_id
                        JOIN target_company_joins tcj ON e.person_id = tcj.person_id
                        WHERE e.company_id != %s
                        AND e.end_date IS NOT NULL
                        AND e.end_date <= tcj.start_date
                        GROUP BY e.company_id, c.company_name
                        ORDER BY person_count DESC
                        LIMIT 20
                    )
                    SELECT * FROM previous_employers
                    """,
                    (company_id, company_id)
                )
                inbound = cursor.fetchall()
                result["feeder_companies"] = [
                    {
                        "company_id": str(f['company_id']),
                        "company_name": f['company_name'],
                        "person_count": f['person_count']
                    }
                    for f in inbound
                ]
            
            # Outbound flow (destination companies)
            if direction in ["outbound", "both"]:
                cursor.execute(
                    """
                    WITH target_company_departures AS (
                        SELECT person_id, end_date
                        FROM employment
                        WHERE company_id = %s
                        AND end_date IS NOT NULL
                    ),
                    next_employers AS (
                        SELECT 
                            e.company_id,
                            c.company_name,
                            COUNT(DISTINCT e.person_id) as person_count
                        FROM employment e
                        JOIN company c ON e.company_id = c.company_id
                        JOIN target_company_departures tcd ON e.person_id = tcd.person_id
                        WHERE e.company_id != %s
                        AND e.start_date IS NOT NULL
                        AND e.start_date >= tcd.end_date
                        GROUP BY e.company_id, c.company_name
                        ORDER BY person_count DESC
                        LIMIT 20
                    )
                    SELECT * FROM next_employers
                    """,
                    (company_id, company_id)
                )
                outbound = cursor.fetchall()
                result["destination_companies"] = [
                    {
                        "company_id": str(d['company_id']),
                        "company_name": d['company_name'],
                        "person_count": d['person_count']
                    }
                    for d in outbound
                ]
            
            cursor.close()
            return result
            
        except Exception as e:
            logger.error(f"Error getting talent flow: {e}")
            cursor.close()
            raise
    
    def get_university_pipelines(
        self,
        company_id: Optional[str] = None,
        company_name: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Analyze which universities feed talent to a company.
        
        Note: Requires university data in person profiles.
        This is a placeholder for future enhancement.
        """
        # TODO: Implement when university data is added to schema
        return {
            "status": "not_implemented",
            "message": "University pipeline analysis requires university data in person profiles"
        }
    
    def get_technology_distribution(
        self,
        company_id: Optional[str] = None,
        company_name: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Analyze technology/language distribution at a company.
        Based on GitHub activity of employees.
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Get company ID if name provided
            if company_name and not company_id:
                cursor.execute(
                    "SELECT company_id FROM company WHERE company_name ILIKE %s LIMIT 1",
                    (f"%{company_name}%",)
                )
                result = cursor.fetchone()
                if result:
                    company_id = result['company_id']
            
            if not company_id:
                return {"error": "Company ID or name required"}
            
            # Get company info
            cursor.execute(
                "SELECT company_name FROM company WHERE company_id = %s",
                (company_id,)
            )
            company = cursor.fetchone()
            
            # Get languages from GitHub profiles of employees
            cursor.execute(
                """
                WITH company_employees AS (
                    SELECT DISTINCT person_id
                    FROM employment
                    WHERE company_id = %s
                ),
                employee_github AS (
                    SELECT gp.github_profile_id
                    FROM github_profile gp
                    JOIN company_employees ce ON gp.person_id = ce.person_id
                ),
                repo_languages AS (
                    SELECT 
                        gr.language,
                        COUNT(DISTINCT gc.github_profile_id) as developer_count,
                        SUM(gc.contribution_count) as total_contributions,
                        COUNT(DISTINCT gr.repo_id) as repo_count
                    FROM github_contribution gc
                    JOIN employee_github eg ON gc.github_profile_id = eg.github_profile_id
                    JOIN github_repository gr ON gc.repo_id = gr.repo_id
                    WHERE gr.language IS NOT NULL
                    GROUP BY gr.language
                    ORDER BY developer_count DESC, total_contributions DESC
                    LIMIT %s
                )
                SELECT * FROM repo_languages
                """,
                (company_id, limit)
            )
            languages = cursor.fetchall()
            
            cursor.close()
            
            return {
                "company_id": str(company_id),
                "company_name": company['company_name'],
                "languages": [
                    {
                        "language": l['language'],
                        "developer_count": l['developer_count'],
                        "total_contributions": l['total_contributions'],
                        "repo_count": l['repo_count']
                    }
                    for l in languages
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting technology distribution: {e}")
            cursor.close()
            raise
    
    def ask_market_intelligence(
        self,
        question: str,
        company_id: Optional[str] = None,
        company_name: Optional[str] = None,
        provider: str = "openai"
    ) -> Dict[str, Any]:
        """
        Answer natural language questions about market intelligence.
        
        Uses AI to interpret questions and generate insights from data.
        
        Example questions:
        - "What are the hiring trends at Uniswap?"
        - "Where does Coinbase get most of its engineers from?"
        - "What technologies are popular at DeFi companies?"
        - "How does talent flow between Uniswap and Coinbase?"
        """
        try:
            # Gather relevant data
            context_data = {}
            
            if company_id or company_name:
                # Get company-specific data
                hiring_patterns = self.get_hiring_patterns(
                    company_id=company_id,
                    company_name=company_name
                )
                talent_flow = self.get_talent_flow(
                    company_id=company_id,
                    company_name=company_name
                )
                tech_dist = self.get_technology_distribution(
                    company_id=company_id,
                    company_name=company_name
                )
                
                context_data = {
                    "hiring_patterns": hiring_patterns,
                    "talent_flow": talent_flow,
                    "technology_distribution": tech_dist
                }
            
            # Build context for AI
            context = self._build_market_context(context_data)
            
            # Get AI service
            ai_service = get_ai_service(provider=provider)
            
            # Build prompt
            system_prompt = """You are a market intelligence analyst specializing in tech talent and hiring patterns.

Your job is to:
1. Answer questions about hiring trends, talent flow, and market dynamics
2. Provide actionable insights for recruiters and hiring managers
3. Explain data patterns in clear, strategic language
4. Make recommendations based on the data

Focus on insights that help with recruiting strategy and competitive intelligence."""

            user_prompt = f"""Market Intelligence Data:
{context}

Question: {question}

Please provide a clear, strategic answer based on the data. Include:
1. Direct answer to the question
2. Key insights from the data
3. Strategic implications for recruiting
4. Recommendations if applicable"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            answer = ai_service._call_ai(messages, temperature=0.7, max_tokens=1500)
            
            return {
                "question": question,
                "answer": answer,
                "data_sources": list(context_data.keys()),
                "company_name": company_name or (context_data.get("hiring_patterns", {}).get("company_name")),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error answering market intelligence question: {e}")
            raise
    
    def _build_market_context(self, data: Dict[str, Any]) -> str:
        """Build text context from market intelligence data."""
        parts = []
        
        if "hiring_patterns" in data and "error" not in data["hiring_patterns"]:
            hp = data["hiring_patterns"]
            parts.append(f"Company: {hp['company_name']}")
            parts.append(f"Total hires in last {hp['time_period_months']} months: {hp['total_hires']}")
            
            if hp.get('top_roles'):
                parts.append("\nTop roles hired:")
                for role in hp['top_roles'][:5]:
                    parts.append(f"  - {role['title']}: {role['count']} hires")
            
            if hp.get('avg_tenure_days'):
                parts.append(f"\nAverage tenure: {hp['avg_tenure_days']:.0f} days ({hp['avg_tenure_days']/365.25:.1f} years)")
        
        if "talent_flow" in data and "error" not in data["talent_flow"]:
            tf = data["talent_flow"]
            
            if tf.get('feeder_companies'):
                parts.append("\nTop feeder companies (where employees come from):")
                for feeder in tf['feeder_companies'][:10]:
                    parts.append(f"  - {feeder['company_name']}: {feeder['person_count']} people")
            
            if tf.get('destination_companies'):
                parts.append("\nTop destination companies (where employees go):")
                for dest in tf['destination_companies'][:10]:
                    parts.append(f"  - {dest['company_name']}: {dest['person_count']} people")
        
        if "technology_distribution" in data and "error" not in data["technology_distribution"]:
            td = data["technology_distribution"]
            
            if td.get('languages'):
                parts.append("\nTechnology/Language distribution:")
                for lang in td['languages'][:10]:
                    parts.append(f"  - {lang['language']}: {lang['developer_count']} developers, {lang['total_contributions']} contributions")
        
        return "\n".join(parts) if parts else "No market intelligence data available"
    
    def get_overall_statistics(self) -> Dict[str, Any]:
        """
        Get overall dataset statistics and insights.
        
        Returns comprehensive metrics about the entire talent pool.
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Overall counts
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT p.person_id) as total_people,
                    COUNT(DISTINCT CASE WHEN gp.github_profile_id IS NOT NULL THEN p.person_id END) as people_with_github,
                    COUNT(DISTINCT CASE WHEN pe.email_id IS NOT NULL THEN p.person_id END) as people_with_email,
                    COUNT(DISTINCT e.company_id) as total_companies,
                    COUNT(DISTINCT gp.github_profile_id) as total_github_profiles,
                    COUNT(DISTINCT gr.repo_id) as total_repositories
                FROM person p
                LEFT JOIN github_profile gp ON p.person_id = gp.person_id
                LEFT JOIN person_email pe ON p.person_id = pe.person_id
                LEFT JOIN employment e ON p.person_id = e.person_id
                LEFT JOIN github_contribution gc ON gp.github_profile_id = gc.github_profile_id
                LEFT JOIN github_repository gr ON gc.repo_id = gr.repo_id
            """)
            overall = dict(cursor.fetchone())
            
            # Calculate percentages
            total = overall['total_people']
            overall['github_percentage'] = round((overall['people_with_github'] / total * 100), 2) if total > 0 else 0
            overall['email_percentage'] = round((overall['people_with_email'] / total * 100), 2) if total > 0 else 0
            
            return {
                "success": True,
                "data": overall
            }
            
        except Exception as e:
            logger.error(f"Error getting overall statistics: {e}")
            return {"error": str(e)}
        finally:
            cursor.close()
    
    def get_overall_hiring_trends(self, months: int = 24) -> Dict[str, Any]:
        """
        Get hiring trends across all companies in the dataset.
        
        Returns monthly hiring volume for the entire market.
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cutoff_date = datetime.now() - timedelta(days=months * 30)
            
            cursor.execute("""
                SELECT 
                    DATE_TRUNC('month', e.start_date) as month,
                    COUNT(DISTINCT e.person_id) as hires,
                    COUNT(DISTINCT e.company_id) as companies_hiring
                FROM employment e
                WHERE e.start_date >= %s
                    AND e.start_date IS NOT NULL
                GROUP BY DATE_TRUNC('month', e.start_date)
                ORDER BY month
            """, (cutoff_date,))
            
            monthly_data = [dict(row) for row in cursor.fetchall()]
            
            # Calculate total
            total_hires = sum(m['hires'] for m in monthly_data)
            
            return {
                "time_period_months": months,
                "total_hires": total_hires,
                "monthly_hires": monthly_data,
                "average_per_month": round(total_hires / len(monthly_data), 1) if monthly_data else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting overall hiring trends: {e}")
            return {"error": str(e)}
        finally:
            cursor.close()
    
    def get_overall_technology_distribution(self, limit: int = 20) -> Dict[str, Any]:
        """
        Get technology/language distribution across entire dataset.
        
        Returns most popular languages and their adoption.
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute("""
                SELECT 
                    gr.language,
                    COUNT(DISTINCT gc.github_profile_id) as developer_count,
                    COUNT(DISTINCT gr.repo_id) as repo_count,
                    SUM(gc.contribution_count) as total_contributions
                FROM github_repository gr
                JOIN github_contribution gc ON gr.repo_id = gc.repo_id
                WHERE gr.language IS NOT NULL
                    AND gr.language != ''
                GROUP BY gr.language
                ORDER BY developer_count DESC
                LIMIT %s
            """, (limit,))
            
            languages = [dict(row) for row in cursor.fetchall()]
            
            return {
                "languages": languages,
                "total_languages": len(languages)
            }
            
        except Exception as e:
            logger.error(f"Error getting technology distribution: {e}")
            return {"error": str(e)}
        finally:
            cursor.close()
    
    def get_top_companies(self, limit: int = 20) -> Dict[str, Any]:
        """
        Get top companies by current headcount in dataset.
        
        Returns companies ranked by number of people.
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute("""
                SELECT 
                    c.company_id,
                    c.company_name,
                    COUNT(DISTINCT e.person_id) as total_people,
                    COUNT(DISTINCT CASE 
                        WHEN gp.github_profile_id IS NOT NULL THEN e.person_id 
                    END) as people_with_github,
                    COUNT(DISTINCT CASE 
                        WHEN pe.email_id IS NOT NULL THEN e.person_id 
                    END) as people_with_email
                FROM company c
                JOIN employment e ON c.company_id = e.company_id
                LEFT JOIN github_profile gp ON e.person_id = gp.person_id
                LEFT JOIN person_email pe ON e.person_id = pe.person_id
                GROUP BY c.company_id, c.company_name
                ORDER BY total_people DESC
                LIMIT %s
            """, (limit,))
            
            companies = [dict(row) for row in cursor.fetchall()]
            
            return {
                "companies": companies,
                "total_shown": len(companies)
            }
            
        except Exception as e:
            logger.error(f"Error getting top companies: {e}")
            return {"error": str(e)}
        finally:
            cursor.close()
    
    def get_location_distribution(self, limit: int = 15) -> Dict[str, Any]:
        """
        Get geographic distribution of talent.
        
        Returns top locations by talent concentration.
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute("""
                SELECT 
                    location,
                    COUNT(*) as person_count,
                    COUNT(DISTINCT CASE 
                        WHEN gp.github_profile_id IS NOT NULL THEN p.person_id 
                    END) as with_github
                FROM person p
                LEFT JOIN github_profile gp ON p.person_id = gp.person_id
                WHERE location IS NOT NULL 
                    AND location != ''
                GROUP BY location
                ORDER BY person_count DESC
                LIMIT %s
            """, (limit,))
            
            locations = [dict(row) for row in cursor.fetchall()]
            
            return {
                "locations": locations,
                "total_shown": len(locations)
            }
            
        except Exception as e:
            logger.error(f"Error getting location distribution: {e}")
            return {"error": str(e)}
        finally:
            cursor.close()

