"""
Test the NWAC API v1 endpoint found in the page source.
"""

import requests
import json

# Base API URL from page source
BASE_API_URL = "https://nwac.us/api/v1/"

# Possible endpoints based on common REST patterns
endpoints_to_test = [
    "forecast/stevens-pass",
    "forecasts/stevens-pass",
    "avalanche-forecast/stevens-pass",
    "zones/stevens-pass/forecast",
    "zones/stevens-pass",
    "forecast",
    "forecasts",
    "zones",
]

print("Testing NWAC API v1 endpoints...")
print("=" * 80)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
}

for endpoint in endpoints_to_test:
    url = BASE_API_URL + endpoint
    try:
        print(f"\n🔍 Trying: {url}")
        response = requests.get(url, timeout=10, headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ SUCCESS - JSON Response!")
                
                # Display structure
                if isinstance(data, dict):
                    print(f"   Type: Dictionary")
                    print(f"   Keys: {list(data.keys())[:10]}")
                elif isinstance(data, list):
                    print(f"   Type: Array with {len(data)} items")
                    if len(data) > 0:
                        print(f"   First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'N/A'}")
                
                # Save the response
                filename = f"nwac_api_{endpoint.replace('/', '_')}.json"
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"   💾 Saved to {filename}")
                
                # Show preview
                preview = json.dumps(data, indent=2)[:800]
                print(f"\n   Preview (first 800 chars):")
                print("   " + "-" * 76)
                for line in preview.split('\n'):
                    print(f"   {line}")
                print("   " + "-" * 76)
                
                # If this is the forecast endpoint, we're done!
                if 'danger' in preview.lower() or 'avalanche' in preview.lower():
                    print(f"\n   🎯 This looks like the forecast data we need!")
                    break
                    
            except json.JSONDecodeError:
                print(f"   ⚠️ Response not JSON")
                print(f"   Content-Type: {response.headers.get('Content-Type')}")
                
        elif response.status_code == 404:
            print("   ❌ Not Found")
        elif response.status_code == 403:
            print("   ❌ Forbidden")
        else:
            print(f"   ❌ Status {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("   ⏱️ Timeout")
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection Error")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 80)
print("Testing complete!")
