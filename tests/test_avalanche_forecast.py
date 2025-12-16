"""
Test the NWAC avalanche forecast scraper.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.basic_tools import get_nwac_avalanche_forecast

print("Testing NWAC Avalanche Forecast Scraper")
print("=" * 80)
print()

try:
    forecast = get_nwac_avalanche_forecast("stevens-pass")
    print(forecast)
    print()
    print("=" * 80)
    print("✅ Test completed successfully!")
    print(f"Forecast length: {len(forecast)} characters")
    
    # Check for key elements
    checks = {
        "Has danger ratings": "DANGER" in forecast.upper(),
        "Has bottom line": "BOTTOM LINE" in forecast.upper(),
        "Has forecast discussion": "DISCUSSION" in forecast.upper(),
        "Has weather summary": "WEATHER" in forecast.upper(),
        "Has source URL": "nwac.us" in forecast.lower(),
    }
    
    print()
    print("Content validation:")
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")
    
except Exception as e:
    print(f"❌ Test failed with error: {e}")
    import traceback
    traceback.print_exc()
