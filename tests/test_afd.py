#!/usr/bin/env python3
"""Test NOAA Area Forecast Discussion (AFD) tool"""

import logging
from tools.basic_tools import get_noaa_area_forecast_discussion

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    print("=" * 80)
    print("Testing NOAA Area Forecast Discussion Tool")
    print("=" * 80)
    print()
    
    try:
        logger.info("Calling get_noaa_area_forecast_discussion()...")
        result = get_noaa_area_forecast_discussion()
        
        print("\n" + "=" * 80)
        print("RESULT:")
        print("=" * 80)
        print(result)
        print("\n" + "=" * 80)
        print(f"Result length: {len(result)} characters")
        print("=" * 80)
        
        # Check for key indicators
        print("\nValidation Checks:")
        print(f"  ✓ Contains OTX section: {'OTX' in result}")
        print(f"  ✓ Contains SEW section: {'SEW' in result}")
        print(f"  ✓ Contains cascade coverage: {'VERIFIED' in result or 'cascade' in result.lower()}")
        print(f"  ✓ Contains discussion text: {len(result) > 500}")
        
        # Check for errors
        if "Error" in result or "❌" in result:
            print("\n⚠️  WARNING: Result contains errors!")
        else:
            print("\n✅ Test completed successfully!")
            
    except Exception as e:
        logger.error(f"Test failed with exception: {e}", exc_info=True)
        print(f"\n❌ Test failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
