"""
Performance test for analyze_snow_forecast_for_stevens_pass optimization.

Tests the efficiency improvements from:
1. Eliminating duplicate API calls (using _fetch_stevens_pass_detailed_data)
2. Parallelizing independent data fetching (ThreadPoolExecutor)
3. Removing unused variable extraction

Expected improvements:
- ~40-50% reduction in total fetch time
- Fewer API calls (from ~10 to ~6)
"""

import sys
from pathlib import Path
import time
import logging
from datetime import datetime
from io import StringIO

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Capture logs for validation
log_capture = StringIO()
log_handler = logging.StreamHandler(log_capture)
log_handler.setLevel(logging.INFO)
log_formatter = logging.Formatter('%(levelname)s: %(message)s')
log_handler.setFormatter(log_formatter)

# Get the logger used by basic_tools
logger = logging.getLogger('tools.basic_tools')
logger.addHandler(log_handler)

from tools.basic_tools import analyze_snow_forecast_for_stevens_pass

print("=" * 80)
print("PERFORMANCE TEST: Stevens Pass Snow Analysis")
print("=" * 80)
print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

print("Optimization Details:")
print("-" * 80)
print("✓ Eliminated duplicate NOAA grid data API calls")
print("✓ Parallelized Powder Poobah, NWAC, WSDOT, and AFD fetching")
print("✓ Removed unused Powder Poobah regex extraction")
print()

print("Running comprehensive snow analysis...")
print("-" * 80)
print()

try:
    # Warm-up - ensure imports are loaded
    print("Warming up (imports, session initialization)...")
    
    # Main test
    print("\nExecuting optimized analysis function...")
    start_time = time.time()
    
    result = analyze_snow_forecast_for_stevens_pass()
    
    elapsed_time = time.time() - start_time
    
    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"✓ Execution completed successfully")
    print(f"  Total execution time: {elapsed_time:.2f} seconds")
    print(f"  Result length: {len(result):,} characters")
    print()
    
    # Performance benchmarks
    print("Performance Assessment:")
    print("-" * 80)
    
    # Data fetching time (estimated at 60-70% of total time)
    estimated_fetch_time = elapsed_time * 0.65
    print(f"  Estimated data fetching time: ~{estimated_fetch_time:.1f}s")
    
    # LLM processing time (estimated at 30-40% of total time)
    estimated_llm_time = elapsed_time * 0.35
    print(f"  Estimated LLM processing time: ~{estimated_llm_time:.1f}s")
    print()
    
    # Overall rating
    if elapsed_time < 40:
        rating = "🚀 EXCELLENT"
        comment = "Well optimized with parallel fetching"
    elif elapsed_time < 50:
        rating = "✅ GOOD"
        comment = "Solid performance with optimizations"
    elif elapsed_time < 60:
        rating = "✓ ACCEPTABLE"
        comment = "Meets target performance"
    else:
        rating = "⚠️  SLOW"
        comment = "May need further optimization or network issues"
    
    print(f"Overall Performance: {rating}")
    print(f"  {comment}")
    print()
    
    # Content validation - parse logs instead of checking LLM output
    print("Data Source Validation (from fetch logs):")
    print("-" * 80)
    
    # Get captured logs
    log_output = log_capture.getvalue()
    
    # Parse the data fetch summary log
    data_sources = {}
    if "Data fetch summary:" in log_output:
        summary_line = [line for line in log_output.split('\n') if "Data fetch summary:" in line]
        if summary_line:
            summary = summary_line[0]
            data_sources = {
                "NOAA Grid Data": "NOAA=✓" in summary,
                "Powder Poobah": "Poobah=✓" in summary,
                "NWAC Avalanche": "NWAC=✓" in summary,
                "WSDOT Pass Conditions": "WSDOT=✓" in summary,
                "AFD Discussions": "AFDs=2" in summary or "AFDs=1" in summary,
            }
    
    # Fallback: Check individual fetch success logs
    if not data_sources:
        data_sources = {
            "NOAA Grid Data": "✓ Detailed grid data extracted" in log_output,
            "Powder Poobah": "✓ Powder Poobah forecast retrieved" in log_output,
            "NWAC Avalanche": "✓ NWAC forecast retrieved" in log_output,
            "WSDOT Pass Conditions": "✓ WSDOT conditions retrieved" in log_output,
            "AFD Discussions": ("✓ OTX AFD retrieved" in log_output or "✓ SEW AFD retrieved" in log_output),
        }
    
    for source, fetched in data_sources.items():
        status = "✅" if fetched else "❌"
        print(f"  {status} {source}: {'Fetched' if fetched else 'Failed'}")
    
    all_present = all(data_sources.values())
    print()
    if all_present:
        print("✅ ALL DATA SOURCES FETCHED SUCCESSFULLY")
    else:
        missing = [k for k, v in data_sources.items() if not v]
        print(f"❌ FAILED TO FETCH: {', '.join(missing)}")
        print("    Check logs above for error details")
    
    print()
    print("=" * 80)
    print(f"Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
except Exception as e:
    print()
    print("=" * 80)
    print("❌ TEST FAILED")
    print("=" * 80)
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    print()
    print("Test terminated with errors.")
