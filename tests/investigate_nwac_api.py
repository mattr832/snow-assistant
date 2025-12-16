"""
Investigate NWAC API endpoints for avalanche forecast data.
"""

import requests
import json
from bs4 import BeautifulSoup

# Known NWAC zone for Stevens Pass
STEVENS_PASS_ZONE = "stevens-pass"

# Try common API patterns
possible_endpoints = [
    f"https://nwac.us/api/v1/avalanche-forecast/{STEVENS_PASS_ZONE}",
    f"https://nwac.us/api/avalanche-forecast/{STEVENS_PASS_ZONE}",
    f"https://nwac.us/api/v2/forecast/{STEVENS_PASS_ZONE}",
    f"https://api.nwac.us/v1/forecast/{STEVENS_PASS_ZONE}",
    f"https://api.nwac.us/forecast/{STEVENS_PASS_ZONE}",
    "https://nwac.us/wp-json/nwac/v1/forecast",
    f"https://nwac.us/wp-json/nwac/v1/forecast/{STEVENS_PASS_ZONE}",
    f"https://nwac.us/wp-json/wp/v2/avalanche_forecast",
]

print("Testing NWAC API endpoints...\n")
print("=" * 80)

for endpoint in possible_endpoints:
    try:
        print(f"\nTrying: {endpoint}")
        response = requests.get(endpoint, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            # Try to parse as JSON
            try:
                data = response.json()
                print(f"✅ SUCCESS - JSON Response!")
                print(f"Keys: {list(data.keys()) if isinstance(data, dict) else 'Array with ' + str(len(data)) + ' items'}")
                
                # Save successful response
                with open('nwac_api_response.json', 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"Saved to nwac_api_response.json")
                
                # Print first 500 chars
                print(f"\nFirst 500 chars of response:")
                print(json.dumps(data, indent=2)[:500])
                break
            except:
                # Not JSON, maybe HTML
                if 'json' in response.headers.get('Content-Type', ''):
                    print(f"Content-Type says JSON but failed to parse")
                else:
                    print(f"Content-Type: {response.headers.get('Content-Type')}")
                    print(f"Response length: {len(response.text)} chars")
        
        elif response.status_code == 404:
            print("❌ Not Found")
        elif response.status_code == 403:
            print("❌ Forbidden (may require API key)")
        else:
            print(f"❌ Status {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("⏱️ Timeout")
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error")
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "=" * 80)
print("\nAlternative: Scraping the forecast page HTML")
print("=" * 80)

# Try scraping the forecast page
try:
    url = f"https://nwac.us/avalanche-forecast/#{STEVENS_PASS_ZONE}"
    print(f"\nFetching: {url}")
    response = requests.get(url, timeout=10, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    if response.status_code == 200:
        print(f"✅ Page loaded successfully")
        print(f"Page size: {len(response.text)} chars")
        
        # Look for JSON data embedded in the page
        if 'window.NWAC' in response.text or 'forecast' in response.text.lower():
            print("Found potential forecast data in page")
            
            # Save HTML for analysis
            with open('nwac_forecast_page.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("Saved HTML to nwac_forecast_page.html")
            
            # Try to find JSON in script tags
            soup = BeautifulSoup(response.text, 'html.parser')
            scripts = soup.find_all('script')
            print(f"\nFound {len(scripts)} script tags")
            
            for i, script in enumerate(scripts):
                if script.string and ('forecast' in script.string.lower() or 'nwac' in script.string.lower()):
                    print(f"\nScript {i} contains forecast/nwac keywords")
                    print(f"First 300 chars: {script.string[:300]}")
                    
except Exception as e:
    print(f"Error scraping: {e}")

print("\n" + "=" * 80)
print("Investigation complete.")
