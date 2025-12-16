#!/usr/bin/env python3
"""Test script to verify AFD geographic coverage"""

import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

session = requests.Session()
retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount('https://', adapter)

# Fetch SEW AFD products
afd_url = 'https://api.weather.gov/products/types/AFD/locations/SEW'
print(f"Fetching AFD from: {afd_url}\n")

response = session.get(afd_url, timeout=30)
data = response.json()

# Get first product to see what it covers
products = data.get('@graph', [])
print(f"Found {len(products)} AFD products\n")

if products:
    first = products[0]
    product_url = first.get('@id')
    issued_time = first.get('issuanceTime')
    print(f'Product Issued: {issued_time}')
    print(f'Product URL: {product_url}\n')
    
    # Fetch full product
    product_response = session.get(product_url, timeout=30)
    product_data = product_response.json()
    
    afd_text = product_data.get('productText', '')
    
    # Print first 3000 chars to see what areas are covered
    print('AFD Content (first 3000 chars):')
    print('='*70)
    print(afd_text[:3000])
    print("\n" + "="*70)
    
    # Check what geographic areas are mentioned in the SYNOPSIS
    print("\n✓ Looking for geographic coverage mentions...")
    
    # Find SYNOPSIS section
    if '.SYNOPSIS' in afd_text:
        synopsis_start = afd_text.find('.SYNOPSIS')
        synopsis_end = afd_text.find('\n.', synopsis_start + 1)
        if synopsis_end == -1:
            synopsis_end = len(afd_text)
        
        synopsis = afd_text[synopsis_start:synopsis_end]
        print("\n**SYNOPSIS SECTION:**")
        print(synopsis[:800])
        
        # Check for Cascade/mountain mentions
        cascade_keywords = ["cascade", "mountain", "pass", "stevens", "snoqualmie", "snoqualme", 
                           "alpine", "terrain", "elevation", "divide"]
        
        mentions = [kw for kw in cascade_keywords if kw.lower() in synopsis.lower()]
        if mentions:
            print(f"\n✓ Cascade Keywords Found in SYNOPSIS: {mentions}")
        else:
            print(f"\n⚠️ No Cascade keywords in SYNOPSIS section")
    
    # Look for explicit area descriptions in the full text
    print("\n" + "="*70)
    print("Looking for explicit geographic coverage...")
    
    lines = afd_text.split('\n')[:20]  # First 20 lines
    print("\nFirst 20 lines of AFD:")
    for i, line in enumerate(lines, 1):
        print(f"{i}: {line}")
