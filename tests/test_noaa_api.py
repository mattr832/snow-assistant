#!/usr/bin/env python3
"""Test script to inspect NOAA API responses"""

import requests
import json
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


def create_session_with_retries():
    """Create a requests session with retry logic and longer timeout"""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def test_afd_endpoints():
    """Test various NOAA AFD endpoints"""
    session = create_session_with_retries()
    timeout = 30
    
    endpoints = [
        "https://api.weather.gov/products/types/AFD/locations/SEW",
    ]
    
    for url in endpoints:
        print(f"\n{'='*80}")
        print(f"Testing endpoint: {url}")
        print('='*80)
        
        try:
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            
            print(f"Status Code: {response.status_code}")
            
            # Handle @graph structure
            if "@graph" in data:
                graph = data["@graph"]
                print(f"Found {len(graph)} items in @graph")
                
                if graph:
                    first_item = graph[0]
                    print(f"\nFirst item in @graph:")
                    print(f"  - id: {first_item.get('id')}")
                    print(f"  - productCode: {first_item.get('productCode')}")
                    print(f"  - issuanceTime: {first_item.get('issuanceTime')}")
                    print(f"  - @id: {first_item.get('@id')}")
                    print(f"  - Keys available: {list(first_item.keys())}")
                    
                    # Try to fetch the full product
                    product_id = first_item.get('id')
                    product_api_url = first_item.get('@id')
                    
                    print(f"\nTrying to fetch full product details...")
                    
                    # Try using the @id URL
                    if product_api_url:
                        try:
                            print(f"  Fetching from @id: {product_api_url}")
                            product_response = session.get(product_api_url, timeout=timeout)
                            product_response.raise_for_status()
                            product_data = product_response.json()
                            
                            print(f"  Response keys: {list(product_data.keys())}")
                            
                            if "productText" in product_data:
                                product_text = product_data["productText"]
                                print(f"  ✓ Found productText! Length: {len(product_text)} chars")
                                print(f"  First 500 chars:\n{product_text[:500]}")
                            else:
                                print(f"  ✗ productText not in response")
                                print(f"  Available keys: {list(product_data.keys())}")
                        except Exception as e:
                            print(f"  Error fetching from @id: {e}")
                    
                    # Try constructing URL from product_id
                    if product_id:
                        try:
                            constructed_url = f"https://api.weather.gov/products/{product_id}"
                            print(f"\n  Trying constructed URL: {constructed_url}")
                            product_response = session.get(constructed_url, timeout=timeout)
                            product_response.raise_for_status()
                            product_data = product_response.json()
                            
                            print(f"  Response keys: {list(product_data.keys())}")
                            
                            if "productText" in product_data:
                                product_text = product_data["productText"]
                                print(f"  ✓ Found productText! Length: {len(product_text)} chars")
                                print(f"  First 500 chars:\n{product_text[:500]}")
                            else:
                                print(f"  ✗ productText not in response")
                        except Exception as e:
                            print(f"  Error with constructed URL: {e}")
        
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")


def test_stevens_pass_weather():
    """Test Stevens Pass weather endpoint"""
    session = create_session_with_retries()
    timeout = 30
    
    print(f"\n{'='*80}")
    print("Testing Stevens Pass Weather Endpoint")
    print('='*80)
    
    latitude = 47.7462
    longitude = -121.0859
    
    # Get grid points
    points_url = f"https://api.weather.gov/points/{latitude},{longitude}"
    print(f"\nFetching grid points from: {points_url}")
    
    try:
        response = session.get(points_url, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Grid location found")
        
        props = data.get("properties", {})
        print(f"  - Grid ID: {props.get('gridId')}")
        print(f"  - Forecast URL: {props.get('forecast')}")
        print(f"  - Forecast Grid URL: {props.get('forecastGridData')}")
        
        # Test forecast endpoint
        forecast_url = props.get('forecast')
        if forecast_url:
            print(f"\nFetching forecast from: {forecast_url}")
            forecast_response = session.get(forecast_url, timeout=timeout)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()
            
            periods = forecast_data.get("properties", {}).get("periods", [])
            print(f"  - Number of forecast periods: {len(periods)}")
            
            if periods:
                first_period = periods[0]
                print(f"\n  First period:")
                print(f"    - Name: {first_period.get('name')}")
                print(f"    - Forecast: {first_period.get('shortForecast')}")
                print(f"    - Temperature: {first_period.get('temperature')}°F")
                print(f"    - Wind: {first_period.get('windSpeed')} from {first_period.get('windDirection')}")
    
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("NOAA API Response Inspector")
    print("="*80)
    
    test_afd_endpoints()
    test_stevens_pass_weather()
    
    print(f"\n{'='*80}")
    print("Test complete!")
