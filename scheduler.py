"""Background scheduler for automated snow analysis updates"""

import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os

logger = logging.getLogger(__name__)


class SnowAnalysisScheduler:
    """Scheduler for automated Stevens Pass snow analysis"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.slack_client = None
        self.slack_channel = os.getenv("SLACK_CHANNEL_ID", "#snow-forecasts")
        self.is_running = False
        
        # Initialize Slack client if token is available
        slack_token = os.getenv("SLACK_BOT_TOKEN")
        if slack_token:
            self.slack_client = WebClient(token=slack_token)
            logger.info("✓ Slack client initialized for scheduled updates")
        else:
            logger.warning("⚠️ SLACK_BOT_TOKEN not found - scheduled Slack updates disabled")
    
    async def run_snow_analysis(self):
        """Execute snow analysis and post to Slack"""
        try:
            logger.info("=" * 70)
            logger.info("SCHEDULED SNOW ANALYSIS - Starting")
            logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 70)
            
            # Import here to avoid circular dependency
            from tools.basic_tools import analyze_snow_forecast_for_stevens_pass
            
            # Run the analysis
            analysis_result = analyze_snow_forecast_for_stevens_pass()
            
            if not analysis_result or "Error" in analysis_result:
                logger.error(f"Analysis failed: {analysis_result}")
                return
            
            # Post to Slack if client is available
            if self.slack_client:
                await self.post_to_slack(analysis_result)
            else:
                logger.info("Slack client not available - analysis complete but not posted")
            
            logger.info("✓ Scheduled snow analysis completed successfully")
            
        except Exception as e:
            logger.error(f"Error in scheduled snow analysis: {e}", exc_info=True)
    
    async def post_to_slack(self, analysis: str):
        """Post analysis results to Slack channel"""
        try:
            # Format the message with header
            timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
            message = f"🔔 *Automated Snow Analysis Update*\n_{timestamp}_\n\n{analysis}"
            
            # Slack has 4000 char limit per message, split if needed
            max_length = 3800  # Leave room for header
            
            if len(message) > max_length:
                # Split into multiple messages
                chunks = []
                current_chunk = f"🔔 *Automated Snow Analysis Update (Part 1)*\n_{timestamp}_\n\n"
                
                # Split by sections to avoid breaking mid-section
                sections = analysis.split("\n\n")
                part_num = 1
                
                for section in sections:
                    if len(current_chunk) + len(section) + 2 > max_length:
                        chunks.append(current_chunk)
                        part_num += 1
                        current_chunk = f"*...continued (Part {part_num})*\n\n{section}\n\n"
                    else:
                        current_chunk += section + "\n\n"
                
                if current_chunk:
                    chunks.append(current_chunk)
                
                # Post each chunk
                for i, chunk in enumerate(chunks):
                    response = self.slack_client.chat_postMessage(
                        channel=self.slack_channel,
                        text=chunk,
                        unfurl_links=False,
                        unfurl_media=False
                    )
                    logger.info(f"✓ Posted message chunk {i+1}/{len(chunks)} to Slack channel {self.slack_channel}")
                    
                    # Small delay between chunks to maintain order
                    if i < len(chunks) - 1:
                        await asyncio.sleep(0.5)
            else:
                # Single message
                response = self.slack_client.chat_postMessage(
                    channel=self.slack_channel,
                    text=message,
                    unfurl_links=False,
                    unfurl_media=False
                )
                logger.info(f"✓ Posted message to Slack channel {self.slack_channel}")
            
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            logger.error(f"Details: {e}")
        except Exception as e:
            logger.error(f"Error posting to Slack: {e}", exc_info=True)
    
    def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler already running")
            return
        
        # Schedule job to run every 6 hours
        # Runs at: 12am, 6am, 12pm, 6pm daily
        self.scheduler.add_job(
            self.run_snow_analysis,
            trigger=CronTrigger(hour="0,6,12,18", minute=0),
            id="snow_analysis_6hr",
            name="Stevens Pass Snow Analysis (Every 6 hours)",
            replace_existing=True
        )
        
        # Optional: Run immediately on startup (comment out if not desired)
        # self.scheduler.add_job(
        #     self.run_snow_analysis,
        #     trigger="date",
        #     id="snow_analysis_startup",
        #     name="Stevens Pass Snow Analysis (Startup)",
        # )
        
        self.scheduler.start()
        self.is_running = True
        
        logger.info("=" * 70)
        logger.info("🕐 SCHEDULER STARTED")
        logger.info("=" * 70)
        logger.info("Snow analysis will run every 6 hours (12am, 6am, 12pm, 6pm)")
        logger.info(f"Results will post to Slack channel: {self.slack_channel}")
        logger.info(f"Next run: {self.scheduler.get_jobs()[0].next_run_time}")
        logger.info("=" * 70)
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Scheduler stopped")
    
    def get_next_run_time(self):
        """Get the next scheduled run time"""
        jobs = self.scheduler.get_jobs()
        if jobs:
            return jobs[0].next_run_time
        return None


# Global scheduler instance
_scheduler = None


def get_scheduler() -> SnowAnalysisScheduler:
    """Get or create the global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = SnowAnalysisScheduler()
    return _scheduler


def start_scheduler():
    """Start the global scheduler"""
    scheduler = get_scheduler()
    scheduler.start()


def stop_scheduler():
    """Stop the global scheduler"""
    global _scheduler
    if _scheduler:
        _scheduler.stop()
        _scheduler = None
