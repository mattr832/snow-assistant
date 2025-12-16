#!/usr/bin/env python3
"""
Test script for get_powder_poobah_latest_forecast function
"""

import sys
import logging
from pathlib import Path

# Add the tools directory to path so we can import basic_tools
tools_dir = Path(__file__).parent / "tools"
sys.path.insert(0, str(tools_dir))

from basic_tools import get_powder_poobah_latest_forecast

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("=" * 70)
    print("Testing get_powder_poobah_latest_forecast()")
    print("=" * 70)
    print()
    
    try:
        result = get_powder_poobah_latest_forecast()
        
        if result:
            print("✓ Successfully retrieved Powder Poobah forecast!")
            print()
            print(result)
        else:
            print("⚠️ Function returned empty result")
            print("This might mean:")
            print("  - BeautifulSoup4 is not installed (run: pip install beautifulsoup4)")
            print("  - The website structure changed")
            print("  - Network connection issue")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
