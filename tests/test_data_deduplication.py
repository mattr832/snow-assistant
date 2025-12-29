"""
Test to verify data sources are not duplicated in the analysis prompt.
Also checks that Powder Poobah content is properly extracted.
"""

import sys
from pathlib import Path
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.basic_tools import get_powder_poobah_latest_forecast

print("=" * 80)
print("Data Deduplication & Content Validation Test")
print("=" * 80)
print()

# Test 1: Check Powder Poobah extraction
print("TEST 1: Powder Poobah Content Extraction")
print("-" * 80)

try:
    poobah_content = get_powder_poobah_latest_forecast()
    
    if not poobah_content:
        print("❌ FAILED: No content returned")
    else:
        # Check structure
        has_header = "EXPERT CONTEXT: Powder Poobah" in poobah_content
        has_post_title = "Post:" in poobah_content
        has_source = "Source:" in poobah_content
        
        # Check for content sections
        has_short_term = "SHORT TERM FORECAST:" in poobah_content
        has_highlights = "HIGHLIGHTS:" in poobah_content
        has_extended = "EXTENDED OUTLOOK:" in poobah_content
        has_fallback_content = "FORECAST CONTENT:" in poobah_content
        
        has_any_content = has_short_term or has_highlights or has_extended or has_fallback_content
        
        print(f"✓ Content retrieved: {len(poobah_content)} characters")
        print(f"  Header present: {'✅' if has_header else '❌'}")
        print(f"  Post title present: {'✅' if has_post_title else '❌'}")
        print(f"  Source URL present: {'✅' if has_source else '❌'}")
        print()
        print(f"  Structured sections found:")
        print(f"    - Short Term Forecast: {'✅' if has_short_term else '❌'}")
        print(f"    - Highlights: {'✅' if has_highlights else '❌'}")
        print(f"    - Extended Outlook: {'✅' if has_extended else '❌'}")
        print(f"    - Fallback Content: {'✅' if has_fallback_content else '❌'}")
        print()
        
        if has_any_content:
            # Show sample
            if has_fallback_content:
                content_start = poobah_content.find("FORECAST CONTENT:") + len("FORECAST CONTENT:")
                sample = poobah_content[content_start:content_start+200].strip()
            elif has_short_term:
                content_start = poobah_content.find("SHORT TERM FORECAST:") + len("SHORT TERM FORECAST:")
                sample = poobah_content[content_start:content_start+200].strip()
            else:
                sample = "N/A"
            
            print(f"  Content sample (first 200 chars):")
            print(f"  {sample}")
            print()
            print("✅ TEST 1 PASSED: Powder Poobah has content")
        else:
            print("❌ TEST 1 FAILED: No forecast content found")
            print()
            print("Debug - Full output:")
            print(poobah_content)
            
except Exception as e:
    print(f"❌ TEST 1 FAILED: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print()

# Test 2: Check for duplication in saved prompt (if available)
print("TEST 2: Check Latest Saved Prompt for Duplication")
print("-" * 80)

try:
    # Find most recent prompt file
    prompt_dir = Path("analysis_prompts")
    if prompt_dir.exists():
        prompt_files = sorted(prompt_dir.glob("*.txt"), reverse=True)
        if prompt_files:
            latest_prompt = prompt_files[0]
            print(f"Analyzing: {latest_prompt.name}")
            
            with open(latest_prompt, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count NWAC sections
            nwac_count = content.count("NWAC AVALANCHE FORECAST - STEVENS PASS")
            print(f"  NWAC sections found: {nwac_count}")
            
            if nwac_count > 1:
                print(f"  ❌ DUPLICATE NWAC SECTIONS FOUND ({nwac_count} occurrences)")
            else:
                print(f"  ✅ NWAC not duplicated")
            
            # Check Powder Poobah content length
            poobah_start = content.find("EXPERT CONTEXT: Powder Poobah")
            if poobah_start >= 0:
                poobah_end = content.find("=" * 70, poobah_start + 100)
                if poobah_end > poobah_start:
                    poobah_section = content[poobah_start:poobah_end]
                    
                    # Check if it's just empty headers
                    lines = [l.strip() for l in poobah_section.split('\n') if l.strip()]
                    content_lines = [l for l in lines if not l.startswith('=') and 'Post:' not in l and 'Source:' not in l and 'EXPERT CONTEXT' not in l]
                    
                    print(f"  Powder Poobah section length: {len(poobah_section)} chars")
                    print(f"  Powder Poobah content lines: {len(content_lines)}")
                    
                    if len(content_lines) > 0:
                        print(f"  ✅ Powder Poobah has content")
                    else:
                        print(f"  ⚠️  Powder Poobah section is mostly empty")
            else:
                print(f"  ⚠️  Powder Poobah section not found")
            
            print()
            if nwac_count == 1:
                print("✅ TEST 2 PASSED: No duplication detected")
            else:
                print("❌ TEST 2 FAILED: Duplication found")
        else:
            print("⚠️  No prompt files found in analysis_prompts/")
    else:
        print("⚠️  analysis_prompts/ directory not found")
        
except Exception as e:
    print(f"❌ TEST 2 FAILED: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("Tests Complete")
print("=" * 80)
