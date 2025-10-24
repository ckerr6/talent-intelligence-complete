"""
ABOUTME: Shared utilities for employment record handling across all import scripts
ABOUTME: Provides date parsing, company matching, and employment creation with extensive logging
"""

import re
from typing import Optional, Dict, Tuple
from datetime import date
from dateutil import parser as date_parser


class EmploymentDataExtractor:
    """
    Extracts and normalizes employment data from various sources.
    Handles dates in multiple formats and provides consistent logging.
    """
    
    @staticmethod
    def parse_date_range(date_range_str: str) -> Tuple[Optional[date], Optional[date]]:
        """
        Parse date range from various formats:
        - "Nov 2022 - May 2023" (PhantomBuster)
        - "May 2021 - Present" (current positions)
        - "2018-2021" (year only)
        - "Jan 2020 - " (no end date)
        
        Returns (start_date, end_date)
        Note: end_date will be None for current positions
        """
        if not date_range_str or not date_range_str.strip():
            return None, None
        
        date_range_str = date_range_str.strip()
        
        # Check if current position
        is_current = any(word in date_range_str.lower() 
                        for word in ['present', 'current', 'now'])
        
        # Split by common separators
        separators = [' - ', ' – ', ' to ', ' → ', '-', '–']
        parts = None
        for sep in separators:
            if sep in date_range_str:
                parts = date_range_str.split(sep, 1)
                break
        
        if not parts or len(parts) < 2:
            # Try to parse as single date (assumed start date)
            try:
                parsed = date_parser.parse(date_range_str, fuzzy=True)
                start_date = date(parsed.year, parsed.month, 1)
                return start_date, None  # No end date, treat as current
            except:
                return None, None
        
        start_str = parts[0].strip()
        end_str = parts[1].strip() if len(parts) > 1 else ''
        
        # Parse start date
        start_date = None
        try:
            parsed = date_parser.parse(start_str, fuzzy=True)
            start_date = date(parsed.year, parsed.month, 1)
        except:
            # Try year-only format
            try:
                year = int(re.search(r'\d{4}', start_str).group())
                start_date = date(year, 1, 1)
            except:
                pass
        
        # Parse end date (None for current positions)
        end_date = None
        if not is_current and end_str:
            try:
                parsed = date_parser.parse(end_str, fuzzy=True)
                # Use last day of month
                end_date = date(parsed.year, parsed.month, 28)
            except:
                # Try year-only format
                try:
                    year = int(re.search(r'\d{4}', end_str).group())
                    end_date = date(year, 12, 31)
                except:
                    pass
        
        return start_date, end_date
    
    @staticmethod
    def extract_title_from_text(text: str) -> Optional[str]:
        """
        Extract job title from various text formats:
        - "Senior Engineer at Company" → "Senior Engineer"
        - "CTO | Company Name" → "CTO"
        - "Software Developer (Remote)" → "Software Developer"
        """
        if not text or not text.strip():
            return None
        
        text = text.strip()
        
        # Remove common separators and what follows
        separators = [' at ', ' @ ', ' | ', ' - ', ' – ']
        for sep in separators:
            if sep in text.lower():
                # Case-insensitive search
                idx = text.lower().find(sep.lower())
                text = text[:idx].strip()
                break
        
        # Remove parenthetical info
        text = re.sub(r'\([^)]*\)', '', text).strip()
        
        # Remove trailing punctuation
        text = text.rstrip(',.;:')
        
        return text if text else None
    
    @staticmethod
    def extract_company_from_text(text: str) -> Optional[str]:
        """
        Extract company name from various text formats:
        - "Senior Engineer at Company Name" → "Company Name"
        - "CTO | Startup Inc." → "Startup Inc."
        """
        if not text or not text.strip():
            return None
        
        text = text.strip()
        
        # Look for common separators
        separators = [' at ', ' @ ']
        for sep in separators:
            if sep in text.lower():
                idx = text.lower().find(sep.lower())
                company = text[idx + len(sep):].strip()
                
                # Clean up
                company = re.sub(r'\s*\|\s*.*$', '', company)  # Remove "| 100 followers"
                company = re.sub(r'\([^)]*\)', '', company)    # Remove parenthetical
                company = company.rstrip(',.;:')
                
                return company if company else None
        
        # Look for pipe separator (title | company)
        if ' | ' in text:
            parts = text.split(' | ')
            if len(parts) >= 2:
                company = parts[1].strip()
                company = re.sub(r'\([^)]*\)', '', company)
                company = company.rstrip(',.;:')
                return company if company else None
        
        return None


class EmploymentRecordManager:
    """
    Manages employment record creation and updates with proper date handling.
    Integrates with Logger for extensive logging.
    """
    
    def __init__(self, cursor, logger=None):
        """
        Args:
            cursor: Database cursor
            logger: Logger instance for extensive logging (optional)
        """
        self.cursor = cursor
        self.logger = logger
    
    def log(self, level: str, message: str):
        """Log message if logger is available"""
        if self.logger:
            if level == 'info':
                self.logger.info(message)
            elif level == 'success':
                self.logger.success(message)
            elif level == 'warning':
                self.logger.warning(message)
            elif level == 'error':
                self.logger.error(message)
    
    def add_employment_record(
        self, 
        person_id: str, 
        company_id: str,
        title: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        location: Optional[str] = None,
        source_text_ref: Optional[str] = None,
        source_confidence: float = 0.7,
        date_precision: str = 'month_year',
        check_duplicates: bool = True
    ) -> bool:
        """
        Add employment record with full date support.
        
        Args:
            person_id: UUID of person
            company_id: UUID of company
            title: Job title (optional but recommended)
            start_date: Start date (optional)
            end_date: End date (None for current positions)
            location: Job location (optional)
            source_text_ref: Reference to source data
            source_confidence: Confidence score (0.0-1.0)
            date_precision: 'exact', 'month_year', 'year_only', or 'unknown'
            check_duplicates: Whether to check for existing similar records
            
        Returns:
            bool: True if record was added, False if duplicate or error
        """
        try:
            if check_duplicates:
                # Check if similar employment already exists
                # Consider it a duplicate if same person + company + similar dates
                self.cursor.execute("""
                    SELECT employment_id
                    FROM employment
                    WHERE person_id = %s::uuid
                    AND company_id = %s::uuid
                    AND (
                        (start_date = %s OR (start_date IS NULL AND %s IS NULL))
                        OR (end_date = %s OR (end_date IS NULL AND %s IS NULL))
                    )
                    LIMIT 1
                """, (person_id, company_id, start_date, start_date, end_date, end_date))
                
                if self.cursor.fetchone():
                    self.log('info', f"Skipping duplicate employment: {title} at company {company_id[:8]}...")
                    return False
            
            # Insert employment record
            self.cursor.execute("""
                INSERT INTO employment (
                    employment_id, 
                    person_id, 
                    company_id, 
                    title,
                    start_date, 
                    end_date, 
                    location,
                    source_text_ref,
                    source_confidence,
                    date_precision
                )
                VALUES (
                    gen_random_uuid(), 
                    %s::uuid, 
                    %s::uuid, 
                    %s,
                    %s, 
                    %s, 
                    %s,
                    %s,
                    %s,
                    %s
                )
                RETURNING employment_id
            """, (
                person_id, 
                company_id, 
                title,
                start_date, 
                end_date, 
                location,
                source_text_ref,
                source_confidence,
                date_precision
            ))
            
            result = self.cursor.fetchone()
            if result:
                employment_id = result['employment_id']
                date_info = ''
                if start_date:
                    date_info = f" ({start_date.strftime('%Y-%m')}"
                    if end_date:
                        date_info += f" to {end_date.strftime('%Y-%m')})"
                    else:
                        date_info += " to Present)"
                
                self.log('success', f"✓ Added employment: {title or 'No title'}{date_info}")
                return True
            
            return False
            
        except Exception as e:
            self.log('error', f"Error adding employment: {str(e)}")
            return False
    
    def find_or_create_company(self, company_name: str, company_cache: dict = None) -> Optional[str]:
        """
        Find existing company or create new one.
        
        Args:
            company_name: Name of company
            company_cache: Optional dict for caching {lowercase_name: company_id}
            
        Returns:
            str: company_id (UUID) or None if invalid
        """
        if not company_name or not company_name.strip():
            return None
        
        company_name = company_name.strip()
        company_lower = company_name.lower()
        
        # Check cache first
        if company_cache and company_lower in company_cache:
            return company_cache[company_lower]
        
        # Search database
        try:
            self.cursor.execute("""
                SELECT company_id
                FROM company
                WHERE LOWER(TRIM(company_name)) = LOWER(TRIM(%s))
                LIMIT 1
            """, (company_name,))
            
            result = self.cursor.fetchone()
            if result:
                company_id = result['company_id']
                if company_cache is not None:
                    company_cache[company_lower] = company_id
                return company_id
            
            # Create new company
            self.cursor.execute("""
                INSERT INTO company (company_id, company_name)
                VALUES (gen_random_uuid(), %s)
                RETURNING company_id
            """, (company_name,))
            
            result = self.cursor.fetchone()
            if result:
                company_id = result['company_id']
                if company_cache is not None:
                    company_cache[company_lower] = company_id
                self.log('success', f"✓ Created new company: {company_name}")
                return company_id
                
        except Exception as e:
            self.log('error', f"Error finding/creating company '{company_name}': {str(e)}")
            return None
        
        return None

