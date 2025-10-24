"""
ABOUTME: Master orchestrator for comprehensive job title backfilling
ABOUTME: Runs all backfill strategies and provides detailed progress tracking
"""

import sys
import os
from pathlib import Path
import psycopg2
import psycopg2.extras
from datetime import datetime
import subprocess

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.logging_utils import Logger, Colors


class MasterTitleBackfiller:
    """Orchestrates all job title backfill operations"""
    
    def __init__(self, logger):
        self.logger = logger
        self.db = psycopg2.connect(
            dbname='talent',
            user=os.environ.get('PGUSER', os.environ.get('USER')),
            host=os.environ.get('PGHOST', 'localhost'),
            port=os.environ.get('PGPORT', '5432')
        )
        self.cursor = self.db.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        self.results = {
            'headline_backfill': 0,
            'github_bio': 0,
        }
    
    def get_initial_stats(self):
        """Get baseline statistics before backfilling"""
        self.logger.section("📊 Baseline Statistics")
        
        stats = {}
        
        # Total employment records
        self.cursor.execute("SELECT COUNT(*) as count FROM employment")
        stats['total_employment'] = self.cursor.fetchone()['count']
        
        # Records with titles
        self.cursor.execute("""
            SELECT COUNT(*) as count FROM employment
            WHERE title IS NOT NULL AND title != ''
        """)
        stats['with_titles'] = self.cursor.fetchone()['count']
        
        # Records without titles
        stats['without_titles'] = stats['total_employment'] - stats['with_titles']
        stats['title_coverage_pct'] = (stats['with_titles'] / stats['total_employment'] * 100) if stats['total_employment'] > 0 else 0
        
        # Current positions without titles
        self.cursor.execute("""
            SELECT COUNT(*) as count FROM employment
            WHERE end_date IS NULL
            AND (title IS NULL OR title = '')
        """)
        stats['current_without_titles'] = self.cursor.fetchone()['count']
        
        self.logger.stats({
            "Total Employment Records": f"{stats['total_employment']:,}",
            "Records WITH Titles": f"{stats['with_titles']:,} ({stats['title_coverage_pct']:.1f}%)",
            "Records WITHOUT Titles": f"{stats['without_titles']:,}",
            "Current Positions Missing Titles": f"{stats['current_without_titles']:,}"
        })
        
        return stats
    
    def backfill_from_headlines(self):
        """Run headline backfill script"""
        self.logger.section("1️⃣  Backfilling from Person Headlines")
        self.logger.info("Extracting job titles from person.headline field...")
        
        script_path = Path(__file__).parent / "backfill_job_titles_from_headline.py"
        
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )
            
            if result.returncode == 0:
                # Parse output for statistics
                output_lines = result.stdout.split('\n')
                for line in output_lines:
                    if 'Successfully inserted' in line:
                        self.logger.success(line.strip())
                        # Extract count
                        import re
                        match = re.search(r'(\d+,?\d*) employment', line)
                        if match:
                            count = int(match.group(1).replace(',', ''))
                            self.results['headline_backfill'] = count
                
                self.logger.success("✓ Headline backfill completed")
            else:
                self.logger.error(f"Headline backfill failed with return code {result.returncode}")
                self.logger.error(result.stderr[:500])  # Show first 500 chars of error
                
        except Exception as e:
            self.logger.error(f"Failed to run headline backfill: {str(e)}", e)
    
    
    def backfill_from_github_bio(self):
        """Extract titles from GitHub profile bios"""
        self.logger.section("2️⃣  Extracting Titles from GitHub Bios")
        
        try:
            # Find GitHub profiles with bio data but no current title
            self.cursor.execute("""
                SELECT 
                    gp.person_id,
                    gp.bio,
                    gp.github_company as gh_company
                FROM github_profile gp
                WHERE gp.bio IS NOT NULL
                AND gp.bio != ''
                AND LENGTH(gp.bio) > 10
                AND gp.person_id IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM employment e
                    WHERE e.person_id = gp.person_id
                    AND e.end_date IS NULL
                    AND e.title IS NOT NULL
                    AND e.title != ''
                )
                LIMIT 20000
            """)
            
            candidates = self.cursor.fetchall()
            self.logger.info(f"Found {len(candidates):,} GitHub profiles with bio data")
            
            if len(candidates) == 0:
                self.logger.info("No additional records to backfill from GitHub bios")
                self.results['github_bio'] = 0
                return
            
            # Use the same title extractor from headline backfill
            from scripts.backfill_job_titles_from_headline import HeadlineTitleExtractor
            extractor = HeadlineTitleExtractor(self.logger)
            
            inserted = 0
            from scripts.progress_reporter import ProgressReporter
            progress = ProgressReporter(len(candidates), "Extracting from GitHub Bios")
            
            for candidate in candidates:
                bio = candidate['bio']
                title, company = extractor.extract_title_and_company(bio)
                
                if title:
                    try:
                        # Check if company exists
                        company_id = None
                        if company:
                            self.cursor.execute("""
                                SELECT company_id FROM company
                                WHERE LOWER(company_name) = LOWER(%s)
                                LIMIT 1
                            """, (company,))
                            result = self.cursor.fetchone()
                            if result:
                                company_id = result['company_id']
                        
                        # Insert employment record
                        import uuid
                        self.cursor.execute("""
                            INSERT INTO employment (
                                employment_id, person_id, company_id, title,
                                source_text_ref, source_confidence
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s
                            )
                        """, (
                            str(uuid.uuid4()),
                            candidate['person_id'],
                            company_id,
                            title,
                            f'github_bio: {bio[:50]}',
                            0.6
                        ))
                        
                        inserted += 1
                        progress.update(1, f"{inserted:,} extracted")
                        
                    except Exception as e:
                        progress.update(1)
                else:
                    progress.update(1)
            
            progress.finish()
            self.db.commit()
            
            self.results['github_bio'] = inserted
            self.logger.success(f"✓ Extracted {inserted:,} titles from GitHub bios")
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"GitHub bio backfill failed: {str(e)}", e)
    
    def get_final_stats(self):
        """Get final statistics after backfilling"""
        self.logger.section("📊 Final Statistics")
        
        stats = {}
        
        # Total employment records
        self.cursor.execute("SELECT COUNT(*) as count FROM employment")
        stats['total_employment'] = self.cursor.fetchone()['count']
        
        # Records with titles
        self.cursor.execute("""
            SELECT COUNT(*) as count FROM employment
            WHERE title IS NOT NULL AND title != ''
        """)
        stats['with_titles'] = self.cursor.fetchone()['count']
        
        # Records without titles
        stats['without_titles'] = stats['total_employment'] - stats['with_titles']
        stats['title_coverage_pct'] = (stats['with_titles'] / stats['total_employment'] * 100) if stats['total_employment'] > 0 else 0
        
        # Current positions without titles
        self.cursor.execute("""
            SELECT COUNT(*) as count FROM employment
            WHERE end_date IS NULL
            AND (title IS NULL OR title = '')
        """)
        stats['current_without_titles'] = self.cursor.fetchone()['count']
        
        self.logger.stats({
            "Total Employment Records": f"{stats['total_employment']:,}",
            "Records WITH Titles": f"{stats['with_titles']:,} ({stats['title_coverage_pct']:.1f}%)",
            "Records WITHOUT Titles": f"{stats['without_titles']:,}",
            "Current Positions Missing Titles": f"{stats['current_without_titles']:,}"
        })
        
        return stats
    
    def generate_summary_report(self, initial_stats, final_stats):
        """Generate comprehensive summary report"""
        self.logger.section("📋 COMPREHENSIVE BACKFILL SUMMARY")
        
        # Calculate improvements
        title_improvement = final_stats['with_titles'] - initial_stats['with_titles']
        coverage_improvement = final_stats['title_coverage_pct'] - initial_stats['title_coverage_pct']
        current_improvement = initial_stats['current_without_titles'] - final_stats['current_without_titles']
        
        print(f"\n{Colors.BOLD}{Colors.OKGREEN}RESULTS BY SOURCE:{Colors.ENDC}")
        print(f"  • Headlines: {self.results.get('headline_backfill', 0):,} titles")
        print(f"  • GitHub Bios: {self.results.get('github_bio', 0):,} titles")
        
        total_added = sum(v for v in self.results.values() if v is not None)
        print(f"\n{Colors.BOLD}TOTAL TITLES ADDED: {Colors.OKGREEN}{total_added:,}{Colors.ENDC}")
        
        print(f"\n{Colors.BOLD}{Colors.OKCYAN}IMPROVEMENTS:{Colors.ENDC}")
        print(f"  • Title Coverage: {initial_stats['title_coverage_pct']:.1f}% → {final_stats['title_coverage_pct']:.1f}% ({coverage_improvement:+.1f}%)")
        print(f"  • Current Positions Fixed: {current_improvement:,}")
        print(f"  • Total Records Enriched: {title_improvement:,}")
        
        # Calculate success rate
        if initial_stats['without_titles'] > 0:
            success_rate = (title_improvement / initial_stats['without_titles'] * 100)
            print(f"  • Success Rate: {success_rate:.1f}% of missing titles filled")
        
        self.logger.success("\n✓ Master backfill completed successfully!")
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.db:
            self.db.close()


def run_master_backfill():
    """Execute master backfill orchestration"""
    logger = Logger("master_backfill", verbose=True)
    logger.header("MASTER JOB TITLE BACKFILL ORCHESTRATOR")
    
    backfiller = MasterTitleBackfiller(logger)
    
    try:
        # Get initial statistics
        initial_stats = backfiller.get_initial_stats()
        
        # Run backfill strategies
        logger.section("🚀 Executing Backfill Strategies")
        
        # Strategy 1: Headlines (most reliable)
        backfiller.backfill_from_headlines()
        
        # Strategy 2: GitHub bios
        backfiller.backfill_from_github_bio()
        
        # Get final statistics
        final_stats = backfiller.get_final_stats()
        
        # Generate summary report
        backfiller.generate_summary_report(initial_stats, final_stats)
        
    except Exception as e:
        logger.error(f"Master backfill failed: {str(e)}", e)
        raise
    
    finally:
        backfiller.close()
    
    logger.summary()


if __name__ == "__main__":
    run_master_backfill()

