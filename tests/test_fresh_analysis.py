"""
Run a fresh analysis to generate a new prompt file with the fixes applied.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.basic_tools import analyze_snow_forecast_for_stevens_pass

print("=" * 80)
print("Running Fresh Analysis to Generate Updated Prompt")
print("=" * 80)
print()

try:
    result = analyze_snow_forecast_for_stevens_pass()
    
    print()
    print("=" * 80)
    print("Analysis Complete")
    print("=" * 80)
    print()
    print("Check the analysis_prompts/ directory for the newly generated prompt file.")
    print("Then re-run: uv run python tests/test_data_deduplication.py")
    
except Exception as e:
    print(f"❌ Error during analysis: {e}")
    import traceback
    traceback.print_exc()
