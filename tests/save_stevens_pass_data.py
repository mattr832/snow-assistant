#!/usr/bin/env python3
"""
Script to fetch comprehensive Stevens Pass data and save it to JSON for inspection
"""

import json
import logging
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _create_session_with_retries():
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


def fetch_and_save_stevens_pass_data():
    """Fetch comprehensive Stevens Pass data and save to JSON"""
    try:
        session = _create_session_with_retries()
        timeout = 30
        
        # Stevens Pass - Tye Mill (STS54) coordinates
        latitude = 47.7462
        longitude = -121.0859
        location_name = "Stevens Pass - Tye Mill (STS54)"
        
        logger.info(f"Fetching comprehensive data for {location_name}...")
        
        # Get location/grid info
        logger.info(f"Validating location: {latitude}, {longitude}")
        points_url = f"https://api.weather.gov/points/{latitude},{longitude}"
        points_response = session.get(points_url, timeout=timeout)
        points_response.raise_for_status()
        points_data = points_response.json()
        
        all_data = {
            "metadata": {
                "location": location_name,
                "latitude": latitude,
                "longitude": longitude,
                "timestamp": str(__import__('datetime').datetime.now().isoformat()),
            },
            "points_response": points_data,
            "forecast_response": None,
            "forecast_grid_response": None,
            "alerts_response": None,
        }
        
        props = points_data.get("properties", {})
        forecast_url = props.get("forecast")
        forecast_grid_url = props.get("forecastGridData")
        alerts_url = props.get("alerts")
        
        # Fetch forecast
        if forecast_url:
            logger.info(f"Fetching forecast: {forecast_url}")
            forecast_response = session.get(forecast_url, timeout=timeout)
            forecast_response.raise_for_status()
            all_data["forecast_response"] = forecast_response.json()
        
        # Fetch forecast grid data
        if forecast_grid_url:
            logger.info(f"Fetching forecast grid data: {forecast_grid_url}")
            grid_response = session.get(forecast_grid_url, timeout=timeout)
            grid_response.raise_for_status()
            all_data["forecast_grid_response"] = grid_response.json()
        
        # Fetch alerts
        if alerts_url:
            logger.info(f"Fetching alerts: {alerts_url}")
            alerts_response = session.get(alerts_url, timeout=timeout)
            alerts_response.raise_for_status()
            all_data["alerts_response"] = alerts_response.json()
        
        # Save to JSON file
        output_file = "stevens_pass_data.json"
        logger.info(f"Saving all data to {output_file}")
        with open(output_file, 'w') as f:
            json.dump(all_data, f, indent=2)
        
        logger.info(f"✓ Successfully saved data to {output_file}")
        
        # Print summary
        print(f"\n{'='*70}")
        print(f"Stevens Pass Comprehensive Data Summary")
        print(f"{'='*70}")
        print(f"Location: {all_data['metadata']['location']}")
        print(f"Coordinates: {latitude}°N, {longitude}°W")
        print(f"Timestamp: {all_data['metadata']['timestamp']}")
        print(f"\nData retrieved:")
        if all_data["points_response"]:
            print(f"  ✓ Points data (grid lookup)")
        if all_data["forecast_response"]:
            periods = all_data["forecast_response"].get("properties", {}).get("periods", [])
            print(f"  ✓ Forecast ({len(periods)} periods)")
        if all_data["forecast_grid_response"]:
            grid_props = all_data["forecast_grid_response"].get("properties", {})
            grid_keys = [k for k in grid_props.keys() if isinstance(grid_props.get(k), dict) and "values" in grid_props.get(k, {})]
            print(f"  ✓ Forecast Grid Data ({len(grid_keys)} parameters: {', '.join(grid_keys[:5])}...)")
        if all_data["alerts_response"]:
            alerts = all_data["alerts_response"].get("features", [])
            print(f"  ✓ Alerts ({len(alerts)} active)")
        
        print(f"\nFull data saved to: {output_file}")
        print(f"File size: {len(json.dumps(all_data)) / 1024:.1f} KB")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"Error: {e}")


if __name__ == "__main__":
    fetch_and_save_stevens_pass_data()
