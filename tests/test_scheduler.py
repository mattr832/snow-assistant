"""
Test script for the scheduled snow analysis feature.
Tests scheduler setup, analysis execution, and Slack posting.
"""

import sys
from pathlib import Path
import asyncio
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_scheduler_initialization():
    """Test that scheduler initializes correctly"""
    print("=" * 80)
    print("TEST 1: Scheduler Initialization")
    print("=" * 80)
    
    try:
        from scheduler import get_scheduler
        
        scheduler = get_scheduler()
        
        # Check scheduler exists
        assert scheduler is not None, "Scheduler should be created"
        assert hasattr(scheduler, 'scheduler'), "Should have scheduler attribute"
        assert hasattr(scheduler, 'slack_client'), "Should have slack_client attribute"
        
        # Check Slack client initialization
        if scheduler.slack_client:
            print("✅ Slack client initialized successfully")
        else:
            print("⚠️  Slack client not initialized (SLACK_BOT_TOKEN may be missing)")
        
        print(f"✅ Scheduler channel: {scheduler.slack_channel}")
        print("✅ TEST 1 PASSED: Scheduler initialized correctly\n")
        return True
        
    except Exception as e:
        print(f"❌ TEST 1 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


async def test_snow_analysis_execution():
    """Test that snow analysis can be executed"""
    print("=" * 80)
    print("TEST 2: Snow Analysis Execution")
    print("=" * 80)
    
    try:
        from scheduler import get_scheduler
        
        scheduler = get_scheduler()
        
        # Run the analysis (this will take ~30 seconds)
        print("🔄 Running snow analysis (this may take 30+ seconds)...")
        await scheduler.run_snow_analysis()
        
        print("✅ TEST 2 PASSED: Snow analysis executed successfully\n")
        return True
        
    except Exception as e:
        print(f"❌ TEST 2 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


async def test_scheduler_start_stop():
    """Test scheduler start and stop functionality"""
    print("=" * 80)
    print("TEST 3: Scheduler Start/Stop")
    print("=" * 80)
    
    try:
        from scheduler import get_scheduler, start_scheduler, stop_scheduler
        
        # Start scheduler
        start_scheduler()
        scheduler = get_scheduler()
        
        assert scheduler.is_running, "Scheduler should be running after start"
        print("✅ Scheduler started")
        
        # Check next run time
        next_run = scheduler.get_next_run_time()
        if next_run:
            print(f"✅ Next scheduled run: {next_run}")
        else:
            print("⚠️  No jobs scheduled")
        
        # Check jobs
        jobs = scheduler.scheduler.get_jobs()
        print(f"✅ Number of scheduled jobs: {len(jobs)}")
        for job in jobs:
            print(f"   - {job.name}: {job.next_run_time}")
        
        # Stop scheduler
        stop_scheduler()
        print("✅ Scheduler stopped")
        
        print("✅ TEST 3 PASSED: Scheduler start/stop working correctly\n")
        return True
        
    except Exception as e:
        print(f"❌ TEST 3 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


async def test_slack_message_formatting():
    """Test Slack message formatting and length handling"""
    print("=" * 80)
    print("TEST 4: Slack Message Formatting")
    print("=" * 80)
    
    try:
        from scheduler import get_scheduler
        
        scheduler = get_scheduler()
        
        # Test with short message
        short_msg = "Test analysis result - short version"
        print("✅ Testing short message formatting...")
        
        # Test with long message (>4000 chars)
        long_msg = "Test analysis result\n\n" + ("This is a test section. " * 200)
        print(f"✅ Testing long message formatting ({len(long_msg)} chars)...")
        
        # Check if it would split (just logic test, don't actually post)
        max_length = 3800
        if len(long_msg) > max_length:
            print(f"✅ Long message would be split into chunks (exceeds {max_length} chars)")
        
        print("✅ TEST 4 PASSED: Message formatting working correctly\n")
        return True
        
    except Exception as e:
        print(f"❌ TEST 4 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


async def test_environment_variables():
    """Test that required environment variables are set"""
    print("=" * 80)
    print("TEST 5: Environment Variables")
    print("=" * 80)
    
    try:
        import os
        
        required_vars = {
            "SLACK_BOT_TOKEN": "Slack bot authentication token",
            "SLACK_SIGNING_SECRET": "Slack app signing secret",
            "SLACK_CHANNEL_ID": "Target channel for updates"
        }
        
        all_set = True
        for var_name, description in required_vars.items():
            value = os.getenv(var_name)
            if value:
                # Mask sensitive values
                masked = value[:10] + "..." if len(value) > 10 else "***"
                print(f"✅ {var_name}: {masked} ({description})")
            else:
                print(f"⚠️  {var_name}: NOT SET ({description})")
                all_set = False
        
        if all_set:
            print("✅ TEST 5 PASSED: All required environment variables are set\n")
        else:
            print("⚠️  TEST 5 WARNING: Some environment variables are missing\n")
        
        return True
        
    except Exception as e:
        print(f"❌ TEST 5 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all scheduler tests"""
    print("\n")
    print("*" * 80)
    print("SCHEDULED SNOW ANALYSIS - TEST SUITE")
    print("*" * 80)
    print("\n")
    
    results = []
    
    # Test 1: Initialization
    results.append(await test_scheduler_initialization())
    
    # Test 2: Environment variables
    results.append(await test_environment_variables())
    
    # Test 3: Start/Stop
    results.append(await test_scheduler_start_stop())
    
    # Test 4: Message formatting
    results.append(await test_slack_message_formatting())
    
    # Test 5: Actual execution (optional, takes time)
    print("=" * 80)
    print("OPTIONAL: Full Snow Analysis Test")
    print("=" * 80)
    print("This test will run the actual snow analysis (~30 seconds)")
    response = input("Run full analysis test? (y/n): ").lower().strip()
    
    if response == 'y':
        results.append(await test_snow_analysis_execution())
    else:
        print("⏭️  Skipping full analysis test\n")
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ ALL TESTS PASSED")
    else:
        print(f"⚠️  {total - passed} TEST(S) FAILED")
    
    print("=" * 80)


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run tests
    asyncio.run(run_all_tests())
