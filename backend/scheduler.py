"""
Automated scheduler for model retraining.
"""

import schedule
import time
import logging
from datetime import datetime
from pathlib import Path
from retrain_pipeline import RetrainingPipeline


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('scheduler')


def check_and_retrain():
    """
    Check if retraining is needed and execute if ready.
    """
    logger.info("="*70)
    logger.info("SCHEDULED RETRAINING CHECK")
    logger.info("="*70)
    
    try:
        pipeline = RetrainingPipeline()
        
        # Check if ready
        if not pipeline.is_ready():
            logger.info("Not ready for retraining (need 100 files: 50 real + 50 fake)")
            logger.info("Skipping retraining until more data collected")
            return
        
        logger.info("✓ Ready for retraining - starting pipeline...")
        
        # Run retraining
        success = pipeline.run_retraining()
        
        if success:
            logger.info("✓ Retraining completed successfully")
        else:
            logger.warning("⚠ Retraining rejected or failed")
            
    except Exception as e:
        logger.error(f" Scheduler error: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    logger.info("="*70 + "\n")


def run_scheduler():
    """
    Main scheduler loop.
    """
    logger.info(" Retraining Scheduler Started")
    logger.info(f"Schedule: Daily at 3:00 AM")
    logger.info(f"Logs: scheduler.log")
    logger.info("")
    
    # Schedule daily at 3:00 AM
    schedule.every().day.at("03:00").do(check_and_retrain)
    
    logger.info("✓ Scheduler running... (press Ctrl+C to stop)")
    
    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("\nScheduler stopped by user")


if __name__ == "__main__":
    run_scheduler()