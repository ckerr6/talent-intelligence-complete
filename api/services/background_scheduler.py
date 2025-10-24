"""
Background Scheduler for AI-First Recruiting

Uses APScheduler to run monitoring jobs at scheduled times.
Runs daily monitoring at 2 AM for AI-powered talent discovery.
"""

import logging
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import Config, get_db_connection

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()


def start_scheduler():
    """
    Initialize and start the background scheduler.
    
    Sets up scheduled jobs:
    - Daily monitoring at 2 AM
    - Preference updates at 3 AM (Phase 2)
    """
    # Check if monitoring is enabled
    monitoring_enabled = os.getenv('AI_MONITORING_ENABLED', 'true').lower() == 'true'
    
    if not monitoring_enabled:
        logger.info("AI monitoring is disabled. Set AI_MONITORING_ENABLED=true to enable.")
        return
    
    try:
        # Add daily monitoring job
        scheduler.add_job(
            run_daily_monitoring_for_all_users,
            CronTrigger(hour=2, minute=0),  # 2 AM daily
            id='daily_monitoring',
            name='Daily AI Monitoring',
            replace_existing=True,
            misfire_grace_time=3600  # Allow 1 hour grace if system was down
        )
        
        # Add manual trigger job for testing (runs immediately if TEST_MODE=true)
        test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
        if test_mode:
            logger.info("TEST_MODE enabled - adding immediate trigger job")
            scheduler.add_job(
                run_daily_monitoring_for_all_users,
                'date',  # Run once immediately
                id='test_monitoring',
                name='Test Monitoring (Immediate)',
                replace_existing=True
            )
        
        # Start scheduler
        scheduler.start()
        logger.info("✅ Background scheduler started successfully")
        logger.info("   - Daily monitoring job: 2:00 AM")
        if test_mode:
            logger.info("   - Test monitoring job: Running immediately")
        
    except Exception as e:
        logger.error(f"❌ Failed to start background scheduler: {e}")
        raise


def stop_scheduler():
    """
    Stop the background scheduler gracefully.
    Called on application shutdown.
    """
    if scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("✅ Background scheduler stopped")


async def run_daily_monitoring_for_all_users():
    """
    Run daily monitoring for all users with auto-monitor enabled searches.
    
    For MVP (single-user), this just monitors the default user.
    In future, this will query all users and monitor each one.
    """
    logger.info("=" * 80)
    logger.info(f"Starting daily monitoring job at {datetime.utcnow().isoformat()}")
    logger.info("=" * 80)
    
    # Import here to avoid circular imports
    from .monitoring_service import MonitoringService
    
    # Get user ID (hardcoded for MVP, will query database in Phase 2)
    user_id = os.getenv('DEFAULT_USER_ID', 'default_user')
    
    conn = None
    try:
        # Get database connection
        conn = get_db_connection(use_pool=True)
        
        # Initialize monitoring service
        monitoring_service = MonitoringService(conn)
        
        # Run monitoring
        results = monitoring_service.run_daily_monitoring(user_id)
        
        # Log summary
        logger.info("-" * 80)
        logger.info("Monitoring Results:")
        logger.info(f"  - New matches: {len(results['new_matches'])}")
        logger.info(f"  - Job changes: {len(results['job_changes'])}")
        logger.info(f"  - GitHub activity: {len(results['github_activity'])}")
        logger.info(f"  - Rising talent: {len(results['rising_talent'])}")
        logger.info(f"  - Notifications created: {results['notifications_created']}")
        
        if results['errors']:
            logger.warning(f"  - Errors: {len(results['errors'])}")
            for error in results['errors']:
                logger.warning(f"    • {error}")
        
        logger.info("-" * 80)
        logger.info("✅ Daily monitoring job completed successfully")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌ Daily monitoring job failed: {e}")
        logger.error("=" * 80)
        raise
    finally:
        # Return connection to pool
        if conn:
            Config.return_connection(conn)


def trigger_monitoring_now():
    """
    Manually trigger monitoring job (for testing/debugging).
    
    Returns:
        Results dict from monitoring
    """
    logger.info("Manually triggering monitoring job...")
    
    from .monitoring_service import MonitoringService
    
    user_id = os.getenv('DEFAULT_USER_ID', 'default_user')
    
    conn = None
    try:
        conn = get_db_connection(use_pool=True)
        monitoring_service = MonitoringService(conn)
        results = monitoring_service.run_daily_monitoring(user_id)
        
        logger.info(f"Manual monitoring complete: {results['notifications_created']} notifications created")
        return results
        
    except Exception as e:
        logger.error(f"Manual monitoring failed: {e}")
        raise
    finally:
        if conn:
            Config.return_connection(conn)


def get_scheduler_status() -> dict:
    """
    Get current scheduler status and job information.
    
    Returns:
        Dict with scheduler status and job details
    """
    if not scheduler.running:
        return {
            'running': False,
            'jobs': []
        }
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
            'trigger': str(job.trigger)
        })
    
    return {
        'running': True,
        'jobs': jobs,
        'timezone': str(scheduler.timezone) if hasattr(scheduler, 'timezone') else 'UTC'
    }


# For testing purposes
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Testing background scheduler...")
    print("\n1. Starting scheduler...")
    start_scheduler()
    
    print("\n2. Scheduler status:")
    status = get_scheduler_status()
    print(f"   Running: {status['running']}")
    print(f"   Jobs: {len(status['jobs'])}")
    for job in status['jobs']:
        print(f"     - {job['name']} (next run: {job['next_run']})")
    
    print("\n3. Manually triggering monitoring job...")
    try:
        results = trigger_monitoring_now()
        print(f"   ✓ Monitoring complete: {results['notifications_created']} notifications")
    except Exception as e:
        print(f"   ✗ Monitoring failed: {e}")
    
    print("\n4. Stopping scheduler...")
    stop_scheduler()
    
    print("\n✅ Test complete!")

