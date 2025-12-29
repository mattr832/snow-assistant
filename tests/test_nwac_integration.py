"""
Test that NWAC avalanche forecast is properly integrated into comprehensive weather and snow analysis.
Also tests performance optimizations for parallel data fetching.
"""

import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.basic_tools import get_comprehensive_stevens_pass_data, analyze_snow_forecast_for_stevens_pass

print("Testing NWAC Integration with Stevens Pass Tools")
print("=" * 80)
print()

# Test 1: Comprehensive Weather Data
print("TEST 1: Comprehensive Weather Data includes NWAC")
print("-" * 80)
try:
    result = get_comprehensive_stevens_pass_data()
    
    # Check for NWAC content
    has_nwac = "NWAC AVALANCHE FORECAST" in result
    has_safety_gear = "Avalanche beacon" in result
    has_danger_levels = "Danger Levels:" in result
    has_nwac_link = "nwac.us/avalanche-forecast" in result
    
    print(f"✓ Function executed successfully")
    print(f"  Result length: {len(result)} characters")
    print(f"  Contains NWAC header: {'✅' if has_nwac else '❌'}")
    print(f"  Contains safety gear info: {'✅' if has_safety_gear else '❌'}")
    print(f"  Contains danger levels: {'✅' if has_danger_levels else '❌'}")
    print(f"  Contains NWAC link: {'✅' if has_nwac_link else '❌'}")
    
    if all([has_nwac, has_safety_gear, has_danger_levels, has_nwac_link]):
        print("\n✅ TEST 1 PASSED - NWAC content properly integrated")
    else:
        print("\n⚠️  TEST 1 INCOMPLETE - Some NWAC content missing")
    
except Exception as e:
    print(f"❌ TEST 1 FAILED: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print()

# Test 2: Snow Analysis includes NWAC
print("TEST 2: Snow Analysis includes NWAC (with performance benchmark)")
print("-" * 80)
print("Note: This test makes real API calls and LLM analysis - may take 30-60 seconds")
print()

try:
    print("Analyzing snow forecast with NWAC integration...")
    start_time = time.time()
    result = analyze_snow_forecast_for_stevens_pass()
    elapsed_time = time.time() - start_time
    
    # The analysis should reference avalanche conditions
    has_avalanche_mention = any(keyword in result.lower() for keyword in [
        'avalanche', 'nwac', 'backcountry safety', 'beacon', 'avalanche conditions'
    ])
    has_nwac_link = "nwac.us" in result.lower()
    
    print(f"✓ Function executed successfully")
    print(f"  Execution time: {elapsed_time:.2f} seconds")
    print(f"  Result length: {len(result)} characters")
    print(f"  Mentions avalanche/safety: {'✅' if has_avalanche_mention else '❌'}")
    print(f"  Contains NWAC link: {'✅' if has_nwac_link else '❌'}")
    
    # Performance assessment
    if elapsed_time < 45:
        print(f"  Performance: 🚀 Excellent (< 45s)")
    elif elapsed_time < 60:
        print(f"  Performance: ✅ Good (< 60s)")
    else:
        print(f"  Performance: ⚠️  Slow (> 60s) - may need optimization")
    
    if has_avalanche_mention or has_nwac_link:
        print("\n✅ TEST 2 PASSED - NWAC content included in analysis")
    else:
        print("\n⚠️  TEST 2 WARNING - NWAC content may not be prominent in analysis")
    
except Exception as e:
    print(f"❌ TEST 2 FAILED: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("Integration testing complete!")
