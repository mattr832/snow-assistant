#!/usr/bin/env python3
"""Test WSDOT Mountain Pass Conditions tool"""

import logging
from tools.basic_tools import get_wsdot_mountain_pass_conditions

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    print("=" * 80)
    print("Testing WSDOT Mountain Pass Conditions Tool")
    print("=" * 80)
    print()
    
    # Test 1: Stevens Pass (default)
    print("\n" + "=" * 80)
    print("TEST 1: Stevens Pass (default)")
    print("=" * 80)
    try:
        result = get_wsdot_mountain_pass_conditions()
        print(result)
    except Exception as e:
        logger.error(f"Test 1 failed: {e}", exc_info=True)
        print(f"❌ Test 1 failed: {e}")
    
    # Test 2: All passes
    print("\n" + "=" * 80)
    print("TEST 2: All Passes")
    print("=" * 80)
    try:
        result = get_wsdot_mountain_pass_conditions("all")
        print(result)
        print(f"\nResult length: {len(result)} characters")
    except Exception as e:
        logger.error(f"Test 2 failed: {e}", exc_info=True)
        print(f"❌ Test 2 failed: {e}")
    
    print("\n✅ Tests completed!")
    return 0

if __name__ == "__main__":
    exit(main())
