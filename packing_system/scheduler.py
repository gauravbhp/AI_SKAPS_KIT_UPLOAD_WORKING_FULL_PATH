"""
Background scheduler for periodic file monitoring and processing
"""
import logging
import os
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler = None


def check_and_process_txt_files():
    """
    Check if txt files exist in source directory and process them.
    This runs periodically in the background.
    """
    try:
        from .views import SOURCE_DIR, move_txt_files
        
        source_path = Path(SOURCE_DIR)
        
        # Check if source directory exists
        if not source_path.exists():
            logger.warning(f"[FILE_MONITOR] Source directory does not exist: {SOURCE_DIR}")
            return
        
        # Look for .txt files
        txt_files = list(source_path.glob('*.txt'))
        
        if txt_files:
            logger.info(f"[FILE_MONITOR] Found {len(txt_files)} .txt files in source directory")
            logger.info(f"[FILE_MONITOR] Processing files: {[f.name for f in txt_files]}")
            
            # Call the move function
            success = move_txt_files()
            
            if success:
                logger.info(f"[FILE_MONITOR] ✅ Successfully processed files")
            else:
                logger.warning(f"[FILE_MONITOR] ⚠️ File processing completed with issues")
        else:
            logger.debug(f"[FILE_MONITOR] No .txt files found in source directory")
            
    except Exception as e:
        logger.error(f"[FILE_MONITOR ERROR] Error in check_and_process_txt_files: {str(e)}")
        import traceback
        traceback.print_exc()


def start_file_monitor():
    """
    Start the background scheduler for monitoring txt files
    Runs every 5 minutes by default
    """
    global _scheduler
    
    try:
        # Check if scheduler is already running
        if _scheduler and _scheduler.running:
            logger.info("[SCHEDULER] File monitor scheduler already running")
            return
        
        # Create new scheduler
        _scheduler = BackgroundScheduler()
        
        # Add the job to check for files every 5 minutes
        _scheduler.add_job(
            check_and_process_txt_files,
            'interval',
            minutes=1,
            id='txt_file_monitor',
            name='Monitor and process txt files',
            replace_existing=True
        )
        
        # Start the scheduler
        _scheduler.start()
        logger.info("[SCHEDULER] ✅ File monitor scheduler started (checks every 5 minutes)")
        
    except Exception as e:
        logger.error(f"[SCHEDULER ERROR] Failed to start scheduler: {str(e)}")
        import traceback
        traceback.print_exc()


def stop_file_monitor():
    """
    Stop the background scheduler
    """
    global _scheduler
    
    try:
        if _scheduler and _scheduler.running:
            _scheduler.shutdown()
            logger.info("[SCHEDULER] File monitor scheduler stopped")
    except Exception as e:
        logger.error(f"[SCHEDULER ERROR] Error stopping scheduler: {str(e)}")


def get_scheduler_status():
    """
    Get the current status of the scheduler
    """
    global _scheduler
    
    if _scheduler is None:
        return {
            'running': False,
            'message': 'Scheduler not initialized'
        }
    
    return {
        'running': _scheduler.running,
        'jobs': len(_scheduler.get_jobs()),
        'jobs_list': [
            {
                'id': job.id,
                'name': job.name,
                'next_run_time': str(job.next_run_time) if job.next_run_time else 'Not scheduled'
            }
            for job in _scheduler.get_jobs()
        ]
    }
