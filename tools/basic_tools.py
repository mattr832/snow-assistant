"""Tool definitions for the agentic workflow"""

from typing import Any
from langchain_core.tools import Tool
import logging
import requests
import json
from datetime import datetime
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)

# Import Chainlit for rendering plots in chat
try:
    import chainlit as cl
    CHAINLIT_AVAILABLE = True
except ImportError:
    CHAINLIT_AVAILABLE = False


def search_knowledge(query: str) -> str:
    """Search knowledge base (placeholder for real implementation)"""
    return f"Found information about: {query}"


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


def generate_stevens_pass_weather_plots(grid_data: dict) -> dict:
    """
    [HELPER FUNCTION]
    Generate Plotly visualizations for Stevens Pass weather data.
    Creates two grouped Plotly figures for better readability in chat:
    - Figure 1: Precipitation & Wind (4 plots)
    - Figure 2: Temperature & Humidity (4 plots)
    
    Args:
        grid_data: The forecast grid data from NOAA API
        
    Returns:
        Dictionary with 'figures' (list of Plotly figures), and 'status' message
    """
    try:
        logger.info("Generating weather plots for Stevens Pass...")
        grid_props = grid_data.get("properties", {})
        
        # Create first figure: Precipitation & Wind Analysis (2x2)
        fig1 = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Snowfall Forecast", "Precipitation Forecast",
                "Wind Speed & Gusts", "Wind Direction"
            ),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]],
            vertical_spacing=0.15,
            horizontal_spacing=0.15
        )
        
        # Create second figure: Temperature & Humidity Analysis (2x2)
        fig2 = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Temperature Trends", "Apparent Temperature",
                "Dewpoint & Humidity", "Visibility Forecast"
            ),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]],
            vertical_spacing=0.15,
            horizontal_spacing=0.15
        )
        
        # Helper function to parse time and value from grid data
        def extract_time_value_pairs(param_dict):
            """Extract (datetime, value) tuples from NOAA grid parameter"""
            from datetime import timedelta
            pairs = []
            
            for val in param_dict.get("values", []):
                valid_time = val.get("validTime", "")
                value = val.get("value", None)
                if value is not None and valid_time:
                    # Parse ISO 8601 time format
                    try:
                        # Format: "2025-11-29T15:00:00+00:00/PT2H"
                        time_str = valid_time.split('/')[0]
                        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                        # Convert UTC to Pacific Time (UTC-8, or UTC-7 during DST)
                        # Simply subtract 8 hours for now (will be -7 during daylight saving)
                        dt_pacific = dt - timedelta(hours=8)
                        # Remove timezone info for plotting (keep local time only)
                        dt_naive = dt_pacific.replace(tzinfo=None)
                        pairs.append((dt_naive, value))
                    except Exception as e:
                        logger.warning(f"Could not parse time {valid_time}: {e}")
            return sorted(pairs, key=lambda x: x[0])
        
        # Plot 1: Snowfall Forecast (Figure 1, Row 1, Col 1)
        snow_data = grid_props.get("snowfallAmount", {})
        if snow_data.get("values"):
            # Extract and convert snowfall from mm to inches
            snow_pairs = extract_time_value_pairs(snow_data)
            if snow_pairs:
                times, values_mm = zip(*snow_pairs)
                # Convert from millimeters to inches (1 inch = 25.4 mm)
                values_inches = [v / 25.4 for v in values_mm]
                fig1.add_trace(
                    go.Bar(x=list(times), y=values_inches, name="Snowfall (in)", marker_color="lightblue"),
                    row=1, col=1
                )
                fig1.update_yaxes(title_text="Inches", row=1, col=1)
        
        # Plot 2: Precipitation Forecast (Figure 1, Row 1, Col 2)
        precip_data = grid_props.get("quantitativePrecipitation", {})
        if precip_data.get("values"):
            # Extract and convert precipitation from mm to inches
            precip_pairs = extract_time_value_pairs(precip_data)
            if precip_pairs:
                times, values_mm = zip(*precip_pairs)
                # Convert from millimeters to inches (1 inch = 25.4 mm)
                values_inches = [v / 25.4 for v in values_mm]
                fig1.add_trace(
                    go.Bar(x=list(times), y=values_inches, name="Precipitation (in)", marker_color="steelblue"),
                    row=1, col=2
                )
                fig1.update_yaxes(title_text="Inches", row=1, col=2)
        
        # Plot 3: Wind Speed & Gusts (Figure 1, Row 2, Col 1)
        wind_speed_data = grid_props.get("windSpeed", {})
        wind_gust_data = grid_props.get("windGust", {})
        if wind_speed_data.get("values") or wind_gust_data.get("values"):
            if wind_speed_data.get("values"):
                times, values = zip(*extract_time_value_pairs(wind_speed_data)) if extract_time_value_pairs(wind_speed_data) else ([], [])
                if times:
                    fig1.add_trace(
                        go.Scatter(x=list(times), y=list(values), name="Wind Speed (mph)", mode="lines", line=dict(color="green")),
                        row=2, col=1
                    )
            if wind_gust_data.get("values"):
                times, values = zip(*extract_time_value_pairs(wind_gust_data)) if extract_time_value_pairs(wind_gust_data) else ([], [])
                if times:
                    fig1.add_trace(
                        go.Scatter(x=list(times), y=list(values), name="Wind Gust (mph)", mode="lines", line=dict(color="orange", dash="dash")),
                        row=2, col=1
                    )
            fig1.update_yaxes(title_text="MPH", row=2, col=1)
        
        # Plot 4: Wind Direction (Figure 1, Row 2, Col 2)
        wind_dir_data = grid_props.get("windDirection", {})
        if wind_dir_data.get("values"):
            times, values = zip(*extract_time_value_pairs(wind_dir_data)) if extract_time_value_pairs(wind_dir_data) else ([], [])
            if times:
                fig1.add_trace(
                    go.Scatter(x=list(times), y=list(values), name="Wind Direction (°)", mode="markers", marker=dict(size=6, color="purple")),
                    row=2, col=2
                )
                fig1.update_yaxes(title_text="Degrees", row=2, col=2)
        
        # Plot 5: Temperature - Actual, High, and Low (Figure 2, Row 1, Col 1)
        temp_data = grid_props.get("temperature", {})
        max_temp_data = grid_props.get("maxTemperature", {})
        min_temp_data = grid_props.get("minTemperature", {})
        
        # Helper function to convert Celsius to Fahrenheit
        def celsius_to_fahrenheit(celsius_list):
            return [(c * 9/5) + 32 for c in celsius_list]
        
        # Get actual temperature (hourly)
        temp_pairs = extract_time_value_pairs(temp_data) if temp_data.get("values") else []
        
        # Get max and min temperatures (daily)
        max_pairs = extract_time_value_pairs(max_temp_data) if max_temp_data.get("values") else []
        min_pairs = extract_time_value_pairs(min_temp_data) if min_temp_data.get("values") else []
        
        if temp_pairs:
            times, values = zip(*temp_pairs)
            temp_f = celsius_to_fahrenheit(list(values))
            fig2.add_trace(
                go.Scatter(x=list(times), y=temp_f, name="Temp (°F)", mode="lines", line=dict(color="gray", width=1)),
                row=1, col=1
            )
        
        if max_pairs:
            max_times, max_values = zip(*max_pairs)
            max_f = celsius_to_fahrenheit(list(max_values))
            fig2.add_trace(
                go.Scatter(x=list(max_times), y=max_f, name="High (°F)", mode="lines+markers", line=dict(color="red", width=2), marker=dict(size=5)),
                row=1, col=1
            )
        
        if min_pairs:
            min_times, min_values = zip(*min_pairs)
            min_f = celsius_to_fahrenheit(list(min_values))
            fig2.add_trace(
                go.Scatter(x=list(min_times), y=min_f, name="Low (°F)", mode="lines+markers", line=dict(color="blue", width=2), marker=dict(size=5),
                          fill="tonexty", fillcolor="rgba(100,150,255,0.2)"),
                row=1, col=1
            )
        
        fig2.update_yaxes(title_text="°F", row=1, col=1)
        
        # Plot 6: Apparent Temperature (Figure 2, Row 1, Col 2)
        apparent_temp_data = grid_props.get("apparentTemperature", {})
        if apparent_temp_data.get("values"):
            pairs = extract_time_value_pairs(apparent_temp_data)
            if pairs:
                times, values = zip(*pairs)
                apparent_f = celsius_to_fahrenheit(list(values))
                fig2.add_trace(
                    go.Scatter(x=list(times), y=apparent_f, name="Apparent Temp (°F)", mode="lines", line=dict(color="darkred")),
                    row=1, col=2
                )
                fig2.update_yaxes(title_text="°F", row=1, col=2)
        
        # Plot 7: Dewpoint & Humidity (Figure 2, Row 2, Col 1)
        dew_data = grid_props.get("dewpoint", {})
        humidity_data = grid_props.get("relativeHumidity", {})
        if dew_data.get("values"):
            pairs = extract_time_value_pairs(dew_data)
            if pairs:
                times, values = zip(*pairs)
                dew_f = celsius_to_fahrenheit(list(values))
                fig2.add_trace(
                    go.Scatter(x=list(times), y=dew_f, mode="lines", name="Dewpoint (°F)", line=dict(color="cyan")),
                    row=2, col=1
                )
        if humidity_data.get("values"):
            times, values = zip(*extract_time_value_pairs(humidity_data)) if extract_time_value_pairs(humidity_data) else ([], [])
            if times:
                fig2.add_trace(
                    go.Scatter(x=list(times), y=list(values), name="Humidity (%)", mode="lines", line=dict(color="blue")),
                    row=2, col=1
                )
        fig2.update_yaxes(title_text="°F / %", row=2, col=1)
        
        # Plot 8: Visibility (Figure 2, Row 2, Col 2)
        visibility_data = grid_props.get("visibility", {})
        if visibility_data.get("values"):
            pairs = extract_time_value_pairs(visibility_data)
            if pairs:
                times, values = zip(*pairs)
                # Filter out None values and convert to miles
                valid_pairs = [(t, v / 1609.34 if v and v > 1000 else v) for t, v in zip(times, values) if v is not None]
                if valid_pairs:
                    times, values_miles = zip(*valid_pairs)
                    fig2.add_trace(
                        go.Scatter(x=list(times), y=list(values_miles), name="Visibility (miles)", mode="lines", line=dict(color="brown")),
                        row=2, col=2
                    )
                    fig2.update_yaxes(title_text="Miles", row=2, col=2)
        
        # Update layout for both figures
        fig1.update_layout(
            height=700,
            showlegend=False,
            hovermode="x unified",
            font=dict(size=10),
            margin=dict(l=40, r=40, t=40, b=40)
        )
        
        fig2.update_layout(
            height=700,
            showlegend=False,
            hovermode="x unified",
            font=dict(size=10),
            margin=dict(l=40, r=40, t=40, b=40)
        )
        
        logger.info("✓ Weather plots generated")
        
        return {
            "figure1": fig1,
            "figure2": fig2,
            "status": "✓ Weather plots generated"
        }
        
    except Exception as e:
        logger.error(f"Error generating plots: {e}", exc_info=True)
        return {
            "figure1": None,
            "figure2": None,
            "status": f"⚠️ Could not generate plots: {str(e)}"
        }


async def send_plots_to_chainlit(plot_data: dict) -> None:
    """
    [HELPER FUNCTION]
    Send the generated Plotly plots to Chainlit for rendering in the chat.
    
    Args:
        plot_data: Dictionary returned from generate_stevens_pass_weather_plots()
    """
    if not CHAINLIT_AVAILABLE:
        logger.warning("Chainlit not available, skipping plot rendering in chat")
        return
    
    try:
        logger.info("=== STARTING PLOT SEND TO CHAINLIT ===")
        elements = []
        if plot_data.get("figure1"):
            logger.info("Creating Plotly element for figure1 (Precipitation & Wind)")
            elements.append(cl.Plotly(name="Precipitation & Wind", figure=plot_data["figure1"]))
        if plot_data.get("figure2"):
            logger.info("Creating Plotly element for figure2 (Temperature & Humidity)")
            elements.append(cl.Plotly(name="Temperature & Humidity", figure=plot_data["figure2"]))
        
        if elements:
            logger.info(f"Sending {len(elements)} plot elements to Chainlit...")
            msg = cl.Message(content="📊 **Stevens Pass Weather Forecast Charts**", elements=elements)
            await msg.send()
            logger.info("✓ Plot message sent successfully to Chainlit")
        else:
            logger.warning("No plot elements to send")
    except Exception as e:
        logger.error(f"ERROR sending plots to Chainlit: {e}", exc_info=True)


def send_plots_to_chainlit_sync(plot_data: dict) -> None:
    """
    [HELPER FUNCTION]
    Synchronous wrapper for sending plots to Chainlit.
    Handles asyncio event loop properly for calling from synchronous tool functions.
    
    Args:
        plot_data: Dictionary returned from generate_stevens_pass_weather_plots()
    """
    if not CHAINLIT_AVAILABLE:
        logger.warning("Chainlit not available, skipping plot rendering in chat")
        return
    
    logger.info("=== SEND_PLOTS_TO_CHAINLIT_SYNC CALLED ===")
    
    try:
        import asyncio
        
        # Try to get the current running event loop (we should already be in one from Chainlit)
        try:
            loop = asyncio.get_running_loop()
            logger.info(f"Found running event loop: {loop}")
            # We're in an async context - schedule the coroutine as a task
            # Use ensure_future to create a task that will execute
            future = asyncio.ensure_future(send_plots_to_chainlit(plot_data))
            logger.info(f"✓ Plot message task created: {future}")
        except RuntimeError as e:
            # No running loop - this shouldn't happen in Chainlit context but handle it anyway
            logger.warning(f"No running event loop found: {e}")
            # Try to create and run in a new loop
            try:
                logger.info("Attempting to create new event loop...")
                asyncio.run(send_plots_to_chainlit(plot_data))
                logger.info("✓ Plots sent via new event loop")
            except Exception as e2:
                logger.error(f"Failed to send plots with new loop: {e2}", exc_info=True)
    except Exception as e:
        logger.error(f"Could not send plots to Chainlit: {e}", exc_info=True)


def get_noaa_area_forecast_discussion() -> str:
    """
    [TOOL]
    Retrieve NOAA Area Forecast Discussions (AFD) for both sides of the Cascades.
    Pulls from both OTX (Spokane/east side) and SEW (Seattle/west side) for comprehensive coverage.
    Validates geographic coverage by checking for explicit Cascade/mountain references in the text.
    """
    try:
        session = _create_session_with_retries()
        timeout = 30
        
        afd_results = []
        
        # Get AFD from both WFOs for complete Cascade coverage
        wfo_list = [
            ("OTX", "https://api.weather.gov/products/types/AFD/locations/OTX", "Spokane/East Cascades"),
            ("SEW", "https://api.weather.gov/products/types/AFD/locations/SEW", "Seattle/West Cascades"),
        ]
        
        for wfo_code, afd_url, region_desc in wfo_list:
            logger.info(f"Fetching NOAA Area Forecast Discussion from {wfo_code} ({region_desc}): {afd_url}")
            
            try:
                response = session.get(afd_url, timeout=timeout)
                response.raise_for_status()
                data = response.json()
                
                # Handle @graph structure (JSON-LD format)
                products = data.get("@graph", [])
                if not products:
                    products = data.get("features", [])
                
                if not products:
                    logger.warning(f"No AFD products available for {wfo_code}")
                    continue
                
                logger.info(f"Found {len(products)} products for {wfo_code}")
                
                # Get the first (most recent) product
                first_product = products[0]
                product_url = first_product.get("@id")
                
                if not product_url:
                    logger.warning(f"No @id found in {wfo_code} product")
                    continue
                
                # Fetch the full product with text
                logger.info(f"Fetching full {wfo_code} product from: {product_url}")
                product_response = session.get(product_url, timeout=timeout)
                product_response.raise_for_status()
                product_data = product_response.json()
                
                # Extract information
                product_text = product_data.get("productText", "")
                issued_time = product_data.get("issuanceTime", "Unknown")
                product_code = product_data.get("productCode", "AFD")
                
                if not product_text:
                    logger.warning(f"{wfo_code} AFD text is empty")
                    continue
                
                # Extract and validate Cascade/mountain coverage
                afd_lower = product_text.lower()
                
                # Look for specific phrases that prove Cascade coverage
                cascade_coverage_phrases = [
                    "cascade gap", "pass level", "mountain snow", "cascade foothills",
                    "stevens pass", "snoqualmie pass", "cascade mountain", "alpine",
                    "high elevation", "ridge", "cascade range", "pass conditions"
                ]
                
                found_coverage = []
                for phrase in cascade_coverage_phrases:
                    if phrase in afd_lower:
                        found_coverage.append(phrase)
                
                # Extract the sentences containing Cascade references for display
                cascade_evidence = []
                sentences = product_text.split('.')
                for sentence in sentences:
                    sentence_lower = sentence.lower()
                    if any(phrase in sentence_lower for phrase in cascade_coverage_phrases):
                        cleaned = sentence.strip()
                        if cleaned and len(cleaned) > 20:
                            cascade_evidence.append(cleaned[:150])
                
                # Validate coverage
                if not found_coverage:
                    coverage_status = "⚠️ Coverage not explicitly confirmed"
                else:
                    coverage_status = f"✓ VERIFIED - {', '.join(found_coverage[:2])}"
                
                # Format this WFO's AFD
                wfo_section = f"\n{'='*70}\n"
                wfo_section += f"📋 **NOAA Area Forecast Discussion - {wfo_code}**\n"
                wfo_section += f"Region: {region_desc}\n"
                wfo_section += f"Coverage Status: {coverage_status}\n"
                wfo_section += f"Issued: {issued_time}\n"
                wfo_section += f"Product Code: {product_code}\n\n"
                
                if cascade_evidence:
                    wfo_section += f"**Evidence of Cascade Coverage:**\n"
                    for i, evidence in enumerate(cascade_evidence[:2], 1):
                        wfo_section += f"{i}. \"{evidence}...\"\n"
                    wfo_section += "\n"
                
                wfo_section += f"**Discussion:**\n{product_text[:1500]}"
                if len(product_text) > 1500:
                    wfo_section += "\n...[truncated]"
                
                afd_results.append(wfo_section)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching {wfo_code} AFD: {e}")
                afd_results.append(f"\n❌ Error fetching {wfo_code} AFD: {str(e)}")
        
        if not afd_results:
            return "Error: Could not retrieve any Area Forecast Discussions"
        
        # Combine both AFDs
        combined_afd = f"📋 **NOAA Area Forecast Discussions - CASCADE MOUNTAINS**\n"
        combined_afd += f"Complete Coverage: East Side (OTX) + West Side (SEW)\n"
        combined_afd += "\n".join(afd_results)
        
        logger.info("Successfully retrieved Area Forecast Discussions from both WFOs")
        return combined_afd
        
    except Exception as e:
        logger.error(f"Unexpected error in get_noaa_area_forecast_discussion: {e}")
        return f"Error processing Area Forecast Discussions: {str(e)}"


def _fetch_stevens_pass_detailed_data() -> dict:
    """
    [HELPER FUNCTION]
    Fetches all detailed grid data for Stevens Pass and returns structured data.
    Used internally by comprehensive data function and analysis.
    
    Returns a dict with:
    - grid_data: Raw NOAA grid data
    - forecast_data: Forecast periods
    - alerts_data: Active alerts
    - location_info: Location metadata
    """
    session = _create_session_with_retries()
    timeout = 30
    
    # Stevens Pass - Tye Mill (STS54) coordinates
    latitude = 47.7462
    longitude = -121.0859
    
    points_url = f"https://api.weather.gov/points/{latitude},{longitude}"
    points_response = session.get(points_url, timeout=timeout)
    points_response.raise_for_status()
    points_data = points_response.json()
    
    props = points_data.get("properties", {})
    
    result_data = {
        "grid_data": None,
        "forecast_data": None,
        "alerts_data": None,
        "location_info": {
            "latitude": latitude,
            "longitude": longitude,
            "grid_id": props.get("gridId"),
            "wfo": props.get("cwa"),
            "timezone": props.get("timeZone"),
            "city": props.get("relativeLocation", {}).get("properties", {}).get("city", "Unknown"),
            "state": props.get("relativeLocation", {}).get("properties", {}).get("state", "Unknown"),
        }
    }
    
    forecast_url = props.get("forecast")
    forecast_grid_url = props.get("forecastGridData")
    alerts_url = props.get("alerts")
    
    # Fetch forecast periods
    if forecast_url:
        try:
            forecast_response = session.get(forecast_url, timeout=timeout)
            forecast_response.raise_for_status()
            result_data["forecast_data"] = forecast_response.json()
        except Exception as e:
            logger.warning(f"Could not fetch forecast data: {e}")
    
    # Fetch detailed grid data
    if forecast_grid_url:
        try:
            grid_response = session.get(forecast_grid_url, timeout=timeout)
            grid_response.raise_for_status()
            result_data["grid_data"] = grid_response.json()
        except Exception as e:
            logger.warning(f"Could not fetch grid data: {e}")
    
    # Fetch alerts
    if alerts_url:
        try:
            alerts_response = session.get(alerts_url, timeout=timeout)
            alerts_response.raise_for_status()
            result_data["alerts_data"] = alerts_response.json()
        except Exception as e:
            logger.warning(f"Could not fetch alerts: {e}")
    
    return result_data


def _format_grid_data_for_analysis(grid_data: dict) -> str:
    """
    [HELPER FUNCTION]
    Extracts and formats detailed grid data for LLM analysis.
    Includes snowfall, precipitation, wind, temperature, and other relevant metrics
    with temporal breakdown for better analysis.
    """
    if not grid_data:
        return ""
    
    from datetime import timedelta
    
    grid_props = grid_data.get("properties", {})
    formatted_sections = []
    
    formatted_sections.append("📊 **Detailed NOAA Grid Forecast Data (Temporal Breakdown)**:")
    formatted_sections.append("")
    
    def extract_temporal_values(param_dict, param_name, unit, convert_fn=None):
        """Extract temporal values from grid parameter"""
        values = param_dict.get("values", [])
        if not values:
            return None
        
        temporal_data = []
        for val in values:  # Get all available values (typically 7 days)
            valid_time = val.get("validTime", "")
            value = val.get("value")
            
            if value is not None and valid_time:
                try:
                    # Parse time
                    time_str = valid_time.split('/')[0]
                    dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    dt_pacific = dt - timedelta(hours=8)
                    dt_naive = dt_pacific.replace(tzinfo=None)
                    
                    # Apply conversion if provided
                    if convert_fn:
                        value = convert_fn(value)
                    
                    temporal_data.append((dt_naive, value))
                except Exception as e:
                    continue
        
        return temporal_data
    
    def celsius_to_fahrenheit(c):
        return round((c * 9/5) + 32, 1)
    
    def meters_to_miles(m):
        return round(m / 1609.34, 2)
    
    def mm_to_inches(mm):
        """Convert millimeters to inches (1 inch = 25.4 mm)"""
        return round(mm / 25.4, 2)
    
    # Extract snowfall with timing
    snow_data = grid_props.get("snowfallAmount", {})
    snow_temporal = extract_temporal_values(snow_data, "Snowfall", "in", mm_to_inches)
    if snow_temporal:
        formatted_sections.append("**Snowfall Forecast (inches):**")
        significant_snow = [item for item in snow_temporal if item[1] > 0]
        if significant_snow:
            for dt, amount in significant_snow:  # Show all snowfall events
                formatted_sections.append(f"  • {dt.strftime('%a %m/%d %I%p')}: {amount:.2f}\"")
        else:
            formatted_sections.append("  • No significant snowfall in forecast period")
        formatted_sections.append("")
    
    # Extract precipitation with timing
    precip_data = grid_props.get("quantitativePrecipitation", {})
    precip_temporal = extract_temporal_values(precip_data, "Precipitation", "in", mm_to_inches)
    if precip_temporal:
        formatted_sections.append("**Precipitation Forecast (inches):**")
        significant_precip = [item for item in precip_temporal if item[1] > 0.1]
        if significant_precip:
            for dt, amount in significant_precip:  # Show all significant precipitation
                formatted_sections.append(f"  • {dt.strftime('%a %m/%d %I%p')}: {amount:.2f}\"")
        else:
            formatted_sections.append("  • Minimal precipitation in forecast period")
        formatted_sections.append("")
    
    # Temperature trends
    temp_data = grid_props.get("temperature", {})
    temp_temporal = extract_temporal_values(temp_data, "Temperature", "°F", celsius_to_fahrenheit)
    if temp_temporal:
        formatted_sections.append("**Temperature Trends (°F):**")
        # Show temperature every 6 hours for full 7-day period
        for i in range(0, len(temp_temporal), 6):
            if i < len(temp_temporal):
                dt, temp = temp_temporal[i]
                formatted_sections.append(f"  • {dt.strftime('%a %m/%d %I%p')}: {temp}°F")
        formatted_sections.append("")
    
    # Wind analysis
    wind_speed_data = grid_props.get("windSpeed", {})
    wind_gust_data = grid_props.get("windGust", {})
    wind_dir_data = grid_props.get("windDirection", {})
    
    wind_speed_temporal = extract_temporal_values(wind_speed_data, "Wind Speed", "mph")
    wind_gust_temporal = extract_temporal_values(wind_gust_data, "Wind Gust", "mph")
    wind_dir_temporal = extract_temporal_values(wind_dir_data, "Wind Direction", "°")
    
    if wind_speed_temporal:
        formatted_sections.append("**Wind Conditions:**")
        # Show wind every 12 hours for full period
        for i in range(0, len(wind_speed_temporal), 12):
            if i < len(wind_speed_temporal):
                dt = wind_speed_temporal[i][0]
                speed = wind_speed_temporal[i][1]
                gust = wind_gust_temporal[i][1] if i < len(wind_gust_temporal) else None
                direction = wind_dir_temporal[i][1] if i < len(wind_dir_temporal) else None
                
                wind_str = f"  • {dt.strftime('%a %m/%d %I%p')}: {speed:.1f} mph"
                if gust:
                    wind_str += f", gusts {gust:.1f} mph"
                if direction:
                    wind_str += f" from {int(direction)}°"
                formatted_sections.append(wind_str)
        formatted_sections.append("")
    
    # Visibility
    visibility_data = grid_props.get("visibility", {})
    vis_temporal = extract_temporal_values(visibility_data, "Visibility", "miles", meters_to_miles)
    if vis_temporal:
        formatted_sections.append("**Visibility (miles):**")
        # Only show periods with reduced visibility
        reduced_vis = [item for item in vis_temporal if item[1] < 5]
        if reduced_vis:
            for dt, vis in reduced_vis:  # Show all reduced visibility periods
                formatted_sections.append(f"  • {dt.strftime('%a %m/%d %I%p')}: {vis} mi")
        else:
            formatted_sections.append("  • Good visibility expected (5+ miles)")
        formatted_sections.append("")
    
    return "\n".join(formatted_sections)


def get_comprehensive_stevens_pass_data() -> str:
    """
    [TOOL]
    Retrieve comprehensive NOAA weather data for Stevens Pass including:
    - Detailed forecast
    - Hazards and alerts
    - Raw grid data for detailed analysis
    
    Location: Stevens Pass - Tye Mill (STS54)
    Coordinates: 47.7462°N, 121.0859°W (Elevation: ~5,180 ft)
    """
    try:
        session = _create_session_with_retries()
        timeout = 30
        
        # Stevens Pass - Tye Mill (STS54) coordinates
        latitude = 47.7462
        longitude = -121.0859
        location_name = "Stevens Pass - Tye Mill (STS54)"
        elevation_ft = 5180
        
        logger.info(f"Fetching comprehensive data for {location_name}...")
        
        # Validate location by fetching grid points first
        logger.info(f"Validating location: {latitude}, {longitude}")
        points_url = f"https://api.weather.gov/points/{latitude},{longitude}"
        points_response = session.get(points_url, timeout=timeout)
        points_response.raise_for_status()
        points_data = points_response.json()
        
        props = points_data.get("properties", {})
        
        # Extract location validation info
        grid_id = props.get("gridId")
        wfo = props.get("cwa")  # County Warning Area / Forecast Office
        timezone = props.get("timeZone")
        relative_location = props.get("relativeLocation", {}).get("properties", {})
        
        logger.info(f"✓ Location validated - WFO: {wfo}, Grid: {grid_id}, Timezone: {timezone}")
        
        # Verify this is correct location
        city = relative_location.get("city", "Unknown")
        state = relative_location.get("state", "Unknown")
        distance_description = relative_location.get("description", "")
        
        data_sections = []
        data_sections.append(f"📍 **Location: {location_name}**")
        data_sections.append(f"   Coordinates: {latitude}°N, {longitude}°W")
        data_sections.append(f"   Elevation: {elevation_ft} ft")
        data_sections.append(f"   Nearest City: {city}, {state}")
        data_sections.append(f"   Description: {distance_description}")
        data_sections.append(f"   Forecast Office (WFO): {wfo} (Seattle/Tacoma)")
        data_sections.append(f"   Grid ID: {grid_id}")
        data_sections.append(f"   Timezone: {timezone}\n")
        
        forecast_url = props.get("forecast")
        forecast_grid_url = props.get("forecastGridData")
        alerts_url = props.get("alerts")
        
        # 2. Get forecast
        logger.info("Fetching forecast data")
        grid_data = None
        if forecast_url:
            forecast_response = session.get(forecast_url, timeout=timeout)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()
            
            periods = forecast_data.get("properties", {}).get("periods", [])
            num_periods = len(periods)
            data_sections.append(f"🌡️ **Forecast Periods** ({num_periods} periods available):")
            for i, period in enumerate(periods[:14]):  # Show up to 14 periods (7 days)
                name = period.get("name", "Unknown")
                forecast = period.get("shortForecast", "")
                temp = period.get("temperature", "N/A")
                wind = period.get("windSpeed", "N/A")
                
                # Emphasize snow-related forecasts
                if any(keyword in forecast.lower() for keyword in ["snow", "sleet", "freezing", "blizzard", "flurries"]):
                    forecast = f"**{forecast}**"
                
                data_sections.append(f"  • {name}: {forecast} ({temp}°F, {wind})")
        
        # Helper to format time strings for readability
        def format_forecast_time(valid_time_str):
            """Convert ISO 8601 time format to readable format"""
            try:
                # Format: "2025-11-29T15:00:00+00:00/PT2H"
                time_part = valid_time_str.split('/')[0]
                dt = datetime.fromisoformat(time_part.replace('Z', '+00:00'))
                # Format as: "Sat 11/29 3:00 PM"
                return dt.strftime("%a %m/%d %I:%M %p")
            except Exception:
                return valid_time_str
        
        # 3. Get detailed grid data (precipitation, snow, wind, hazards, etc.)
        logger.info("Fetching detailed grid forecast data")
        if forecast_grid_url:
            try:
                grid_response = session.get(forecast_grid_url, timeout=timeout)
                grid_response.raise_for_status()
                grid_data = grid_response.json()
                
                grid_props = grid_data.get("properties", {})
                
                # Extract snowfall (critical for powder forecasting)
                # Data is retrieved internally but not displayed in chat
                snow = grid_props.get("snowfallAmount", {})
                
                # Extract quantitative precipitation
                # Data is retrieved internally but not displayed in chat
                qpf = grid_props.get("quantitativePrecipitation", {})
                
                # Wind gust (affects snow quality and avalanche risk)
                # Data is retrieved internally but not displayed in chat
                wind_gust = grid_props.get("windGust", {})
                
                # NOTE: All other data is still retrieved but not displayed in chat
                # This includes: wind speed, wind direction, visibility, ceiling height, wind chill,
                # apparent temperature, dew point, humidity, pressure, probability of precipitation,
                # and hazards. This data is still available in grid_data for analysis functions.
                # These details will be shown visually in the Plotly charts.
            
            except Exception as e:
                logger.warning(f"Could not fetch detailed grid data: {e}")
        
        # 4. NOTE: Plot generation moved to app.py for proper async context
        # The grid_data is returned and plots are generated in the Chainlit context
        
        # 5. Get alerts/warnings
        logger.info("Fetching active alerts")
        if alerts_url:
            try:
                alerts_response = session.get(alerts_url, timeout=timeout)
                alerts_response.raise_for_status()
                alerts_data = alerts_response.json()
                
                features = alerts_data.get("features", [])
                if features:
                    data_sections.append("\n⚠️ **Active Alerts/Warnings**:")
                    for alert in features:
                        alert_props = alert.get("properties", {})
                        event = alert_props.get("event", "Alert")
                        headline = alert_props.get("headline", "")
                        severity = alert_props.get("severity", "Unknown")
                        data_sections.append(f"  • [{severity}] {event}: {headline}")
                else:
                    data_sections.append("\n✓ No active alerts")
            except Exception as e:
                logger.warning(f"Could not fetch alerts: {e}")
        
        result = "\n".join(data_sections)
        logger.info("Successfully retrieved comprehensive Stevens Pass data")
        return result
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching comprehensive data: {e}")
        return f"Error fetching Stevens Pass data: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error in get_comprehensive_stevens_pass_data: {e}", exc_info=True)
        return f"Error processing Stevens Pass data: {str(e)}"


def _save_analysis_prompt(prompt: str, filename: str = "stevens_pass_analysis_prompt.txt") -> str:
    """
    [HELPER FUNCTION]
    Saves the formatted analysis prompt to a .txt file for inspection.
    
    Args:
        prompt: The formatted prompt text to save
        filename: The name of the output file (default: stevens_pass_analysis_prompt.txt)
        
    Returns:
        Path to the saved file
    """
    try:
        import os
        from pathlib import Path
        
        # Create output directory if it doesn't exist
        output_dir = Path("analysis_prompts")
        output_dir.mkdir(exist_ok=True)
        
        # Create filepath with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = output_dir / f"{timestamp}_{filename}"
        
        # Write prompt to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        logger.info(f"✓ Analysis prompt saved to: {filepath}")
        return str(filepath)
        
    except Exception as e:
        logger.warning(f"Could not save analysis prompt: {e}")
        return ""


def get_powder_poobah_latest_forecast() -> str:
    """
    [HELPER FUNCTION]
    Dynamically fetch the latest Powder Poobah snow forecast and extract key sections.
    Parses the website to find the most recent powder alert post and extracts:
    - Short Term Forecast
    - Highlights
    - Extended Outlook
    """
    try:
        import re
        from bs4 import BeautifulSoup
        
        logger.info("Fetching latest Powder Poobah forecast from https://www.powderpoobah.com/")
        
        session = _create_session_with_retries()
        timeout = 30
        
        # Fetch the main page to find the latest powder alert post
        logger.info("Fetching Powder Poobah main page to find latest post...")
        home_response = session.get("https://www.powderpoobah.com/", timeout=timeout)
        home_response.raise_for_status()
        
        # Parse HTML to find the latest powder alert link
        soup = BeautifulSoup(home_response.content, 'html.parser')
        
        # Find all powder alert post links - they're in the "Powder Alerts" section
        post_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if '/post/' in href and 'powderpoobah.com' in href:
                # Filter for actual powder alert posts (not about/sponsors/etc)
                if any(x in href.lower() for x in ['powder', 'snow', 'forecast', 'coming']):
                    post_links.append(href)
                elif '/post/' in href and len(href.split('/')) > 3:  # Real post links have more path depth
                    post_links.append(href)
        
        if not post_links:
            logger.warning("Could not find any Powder Poobah posts")
            return ""
        
        # Get the first/most recent post
        latest_post_url = post_links[0]
        if not latest_post_url.startswith('http'):
            latest_post_url = f"https://www.powderpoobah.com{latest_post_url}"
        
        logger.info(f"Fetching latest post: {latest_post_url}")
        post_response = session.get(latest_post_url, timeout=timeout)
        post_response.raise_for_status()
        
        post_soup = BeautifulSoup(post_response.content, 'html.parser')
        
        # Extract post date/title BEFORE cleaning - try multiple selectors
        title_elem = post_soup.find('h1')
        if not title_elem:
            title_elem = post_soup.find('h2', class_=re.compile('title|heading', re.I))
        post_title = title_elem.get_text(strip=True) if title_elem else "Latest Forecast"
        
        # Now clean the HTML - remove scripts, styles, and other noise
        for element in post_soup(['script', 'style', 'nav', 'footer', 'header', 'iframe']):
            element.decompose()
        
        # Look for common content containers
        content = None
        for selector in ['main', 'article', '[class*="content"]', '[class*="post"]']:
            try:
                if selector.startswith('['):
                    content = post_soup.select_one(selector)
                else:
                    content = post_soup.find(selector)
                if content:
                    break
            except:
                continue
        
        if not content:
            content = post_soup.body
        
        # Get text with better formatting - use separator to help with parsing
        post_text = content.get_text(separator='\n', strip=True) if content else ""
        
        # Clean up excessive newlines and whitespace
        post_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', post_text)
        post_text = re.sub(r'[ \t]+', ' ', post_text)
        
        # Extract key sections using regex patterns - be more flexible
        short_term_section = ""
        highlights_section = ""
        extended_outlook_section = ""
        
        # Look for "Short Term Forecast" section
        # Match everything until we hit another major section or lots of uppercase text
        short_term_match = re.search(
            r'short\s+term\s+forecast\s*[\n:]\s*(.*?)(?=\n\s*(?:highlights?|extended\s+outlook|slopes?|map\s+\d+|elevation|the\s+perfect\s+gift)\s*[\n:]|$)',
            post_text,
            re.IGNORECASE | re.DOTALL
        )
        if short_term_match:
            short_term_text = short_term_match.group(1).strip()
            # Split into sentences/paragraphs and clean
            sentences = re.split(r'(?<=[.!?])\s+', short_term_text)
            clean_sentences = []
            for sent in sentences[:15]:  # Take first 15 sentences
                sent = sent.strip()
                if len(sent) > 10 and not any(x in sent.lower() for x in ['map', 'image', 'email', 'subscribe', 'click here', 'shop our']):
                    clean_sentences.append(sent)
            short_term_section = ' '.join(clean_sentences)
        
        # Look for "HIGHLIGHTS" section - stop BEFORE Extended Outlook
        highlights_match = re.search(
            r'highlights?\s*[\n:]\s*(.*?)(?=\n\s*(?:extended\s+outlook|slopes?\s*[-–]\s*elevation|map\s+\d+|the\s+perfect\s+gift)\s*[\n:]|$)',
            post_text,
            re.IGNORECASE | re.DOTALL
        )
        if highlights_match:
            highlights_text = highlights_match.group(1).strip()
            # Look for bullet points or numbered items
            lines = highlights_text.split('\n')
            clean_lines = []
            for line in lines[:15]:  # Reduced to avoid pulling in Extended Outlook
                line = line.strip()
                # Stop if we hit Extended Outlook section marker
                if re.match(r'extended\s+outlook', line, re.IGNORECASE):
                    break
                # Skip lines that look like they're from other sections
                if len(line) > 5 and not any(x in line.lower() for x in ['map', 'image', 'email', 'subscribe', 'click here', 'shop our', 'michael fagin', 'meteorologist', 'forward this', 'when will the ski']):
                    clean_lines.append(line)
            highlights_section = '\n'.join(clean_lines)
        
        # Look for "Extended Outlook" section - skip past the header line itself
        extended_match = re.search(
            r'extended\s+outlook\s*[-–]?\s*[\w\s,]*\n+(.*?)(?=\n\s*(?:michael\s+fagin|meteorologist|forward\s+this|p\.s\.|event\s+alert|slope\s+stories?|riddle|daily\s+dose|recent\s+posts|the\s+perfect\s+gift)\s*[\n:]|$)',
            post_text,
            re.IGNORECASE | re.DOTALL
        )
        if extended_match:
            extended_text = extended_match.group(1).strip()
            # Skip if it starts with HIGHLIGHTS (means we caught the wrong section)
            if extended_text.upper().startswith('HIGHLIGHTS'):
                extended_text = ''
            else:
                # Split into sentences/paragraphs
                sentences = re.split(r'(?<=[.!?])\s+', extended_text)
                clean_sentences = []
                for sent in sentences[:20]:  # Take first 20 sentences
                    sent = sent.strip()
                    # Stop if we hit HIGHLIGHTS or other sections
                    if sent.upper().startswith('HIGHLIGHTS'):
                        break
                    if len(sent) > 10 and not any(x in sent.lower() for x in ['map', 'image', 'email', 'subscribe', 'click here', 'shop our', 'sponsor shoutouts', 'meet larry']):
                        clean_sentences.append(sent)
                extended_text = ' '.join(clean_sentences)
            extended_outlook_section = extended_text
        
        # Build the formatted context
        poobah_context = f"""
{'='*70}
EXPERT CONTEXT: Powder Poobah Professional Snow Forecast
{'='*70}

Post: {post_title}
Source: {latest_post_url}
"""
        
        # Add sections if found, otherwise include raw content
        sections_found = False
        
        if short_term_section:
            poobah_context += f"\nSHORT TERM FORECAST:\n{short_term_section}\n"
            sections_found = True
        
        if highlights_section:
            poobah_context += f"\nHIGHLIGHTS:\n{highlights_section}\n"
            sections_found = True
        
        if extended_outlook_section:
            poobah_context += f"\nEXTENDED OUTLOOK:\n{extended_outlook_section}\n"
            sections_found = True
        
        # If no sections found, include first 2000 chars of raw content as fallback
        if not sections_found and post_text:
            # Clean up the text - remove newsletter/sponsor sections
            clean_text = post_text
            for remove_phrase in ['FORWARD THIS', 'Subscribe', 'RIDDLE', 'DAILY DOSE', 'Recent Posts', 'THE PERFECT GIFT', 'Michael Fagin', 'Meteorologist']:
                if remove_phrase in clean_text:
                    clean_text = clean_text.split(remove_phrase)[0]
            
            if len(clean_text) > 200:
                poobah_context += f"\nFORECAST CONTENT:\n{clean_text[:2000].strip()}\n"
                if len(clean_text) > 2000:
                    poobah_context += "\n[Content truncated for brevity]\n"
        
        poobah_context += f"\n{'='*70}\n"
        
        logger.info(f"✓ Successfully retrieved and parsed Powder Poobah latest forecast")
        return poobah_context
        
    except ImportError:
        logger.warning("BeautifulSoup not available - install with: pip install beautifulsoup4")
        return ""
    except Exception as e:
        logger.warning(f"Could not fetch/parse Powder Poobah forecast: {e}")
        return ""


def analyze_snow_forecast_for_stevens_pass() -> str:
    """
    [TOOL]
    Retrieve and analyze comprehensive NOAA data to highlight snow, blizzards, and large forecast 
    snow amounts in Cascade mountains, particularly Stevens Pass. Integrates multiple data sources
    including raw grid data for detailed analysis, plus professional forecaster insights from Powder Poobah.
    
    Optimized to minimize duplicate API calls and parallelize independent data fetching.
    """
    try:
        import re
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        session = _create_session_with_retries()
        timeout = 30
        
        # Collect all available data
        logger.info("=" * 70)
        logger.info("Stevens Pass Comprehensive Analysis - Data Collection")
        logger.info("=" * 70)
        
        data_parts = []
        
        # Part 1: Fetch detailed Stevens Pass data using helper (eliminates duplicate API calls)
        logger.info("[1/3] Fetching NOAA data (grid, forecast, alerts)...")
        detailed_data = _fetch_stevens_pass_detailed_data()
        grid_data_for_plots = detailed_data.get("grid_data")
        
        # Format the comprehensive data from detailed fetch
        comprehensive_data = get_comprehensive_stevens_pass_data()
        data_parts.append(comprehensive_data)
        
        # Format grid data for LLM analysis
        if grid_data_for_plots:
            try:
                grid_summary = _format_grid_data_for_analysis(grid_data_for_plots)
                if grid_summary:
                    data_parts.append(f"\n\n{grid_summary}")
            except Exception as e:
                logger.warning(f"Grid data formatting failed: {e}")
        
        # Part 2: Fetch independent data sources in parallel for efficiency
        logger.info("[2/3] Fetching additional sources (Powder Poobah, NWAC, WSDOT, AFDs)...")
        
        def fetch_powder_poobah():
            """Fetch Powder Poobah forecast"""
            try:
                result = get_powder_poobah_latest_forecast()
                return ("poobah", result)
            except Exception as e:
                logger.debug(f"Powder Poobah fetch failed: {e}")
                return ("poobah", "")
        
        def fetch_nwac():
            """Fetch NWAC avalanche forecast"""
            try:
                result = get_nwac_avalanche_forecast("stevens-pass")
                return ("nwac", result)
            except Exception as e:
                logger.debug(f"NWAC fetch failed: {e}")
                return ("nwac", "")
        
        def fetch_wsdot():
            """Fetch WSDOT pass conditions"""
            try:
                result = get_wsdot_mountain_pass_conditions("stevens")
                return ("wsdot", result)
            except Exception as e:
                logger.debug(f"WSDOT fetch failed: {e}")
                return ("wsdot", "")
        
        def fetch_afd(wfo_code, afd_url, region_desc):
            """Fetch a single AFD"""
            try:
                afd_response = session.get(afd_url, timeout=timeout)
                afd_response.raise_for_status()
                afd_data = afd_response.json()
                
                products = afd_data.get("@graph", [])
                if products:
                    first_product = products[0]
                    product_url = first_product.get("@id")
                    
                    if product_url:
                        product_response = session.get(product_url, timeout=timeout)
                        product_response.raise_for_status()
                        product_data = product_response.json()
                        
                        afd_full_text = product_data.get("productText", "")
                        issued_time = product_data.get("issuanceTime", "Unknown")
                        
                        if afd_full_text:
                            return ("afd", f"\n\n{'='*70}\nFull AFD Discussion - {wfo_code} ({region_desc})\nIssued: {issued_time}\n{'='*70}\n{afd_full_text}")
                
                return ("afd", "")
            except Exception as e:
                logger.debug(f"{wfo_code} AFD fetch failed: {e}")
                return ("afd", "")
        
        # Execute all fetches in parallel
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = []
            
            # Submit all independent fetch tasks
            futures.append(executor.submit(fetch_powder_poobah))
            futures.append(executor.submit(fetch_nwac))
            futures.append(executor.submit(fetch_wsdot))
            futures.append(executor.submit(fetch_afd, "OTX", "https://api.weather.gov/products/types/AFD/locations/OTX", "Spokane/East Cascades"))
            futures.append(executor.submit(fetch_afd, "SEW", "https://api.weather.gov/products/types/AFD/locations/SEW", "Seattle/West Cascades"))
            
            # Collect results as they complete
            results = {}
            afd_results = []
            for future in as_completed(futures):
                try:
                    data_type, content = future.result()
                    if data_type == "afd":
                        if content:
                            afd_results.append(content)
                    else:
                        results[data_type] = content
                except Exception as e:
                    logger.warning(f"Parallel fetch error: {e}")
        
        # Log fetch summary
        fetch_status = []
        if results.get("poobah"): fetch_status.append("Powder Poobah")
        if results.get("nwac"): fetch_status.append("NWAC")
        if results.get("wsdot"): fetch_status.append("WSDOT")
        if afd_results: fetch_status.append(f"{len(afd_results)} AFDs")
        
        logger.info(f"    ✓ Retrieved: {', '.join(fetch_status) if fetch_status else 'None'}")
        
        # Append results in logical order
        # Add Powder Poobah first (professional context)
        poobah_content = results.get("poobah", "")
        if poobah_content and len(poobah_content.strip()) > 200:  # Ensure we have actual content
            data_parts.append(poobah_content)
        
        # Add NWAC avalanche forecast
        nwac_content = results.get("nwac", "")
        if nwac_content:
            data_parts.append(f"\n\n{nwac_content}")
        
        # Add both AFDs
        for afd_content in afd_results:
            data_parts.append(afd_content)
        
        # Add WSDOT pass conditions
        wsdot_content = results.get("wsdot", "")
        if wsdot_content:
            data_parts.append(f"\n\n{wsdot_content}")
        
        combined_data = "\n".join(data_parts)
        
        if not combined_data or len(combined_data) < 100:
            return "⚠️ Could not retrieve enough data for analysis. Please try again."
        
        # Import the LLM to analyze all the data
        from models.local_llm import UnifiedLLM
        llm = UnifiedLLM()
        
        logger.info("[3/3] Analyzing data with LLM...")
        
        # Create comprehensive analysis prompt focused on winter sports opportunities
        # Now includes detailed grid data extraction directives AND professional forecaster insights
        analysis_prompt = f"""You are a winter sports weather analyst for Stevens Pass. Analyze the provided data with STRICT accuracy - only report what is explicitly stated in the data below. Do not assume, speculate, or fabricate any information.

## CRITICAL RULES
- Use exact numbers from data (e.g., "4.2 inches" not "around 4")
- Cite which source each insight comes from
- State "Data not available" if unclear or missing
- Powder day = 9+ inches in 24 hours only

## DATA SOURCES AVAILABLE
1. **NOAA Grid Data**: Hourly snowfall amounts, temperatures, wind, visibility
2. **NOAA AFD** (OTX/SEW): Professional meteorologist analysis & model discussions  
3. **Powder Poobah**: Expert PNW snow forecaster insights
4. **NWAC**: Avalanche danger ratings & backcountry safety
5. **WSDOT** (PRIMARY for travel): Real-time WA state road conditions, pass status, restrictions, closures, delays, advisories
6. **Weather Alerts**: Active warnings/watches/advisories

## YOUR TASK
Synthesize the data into a comprehensive forecast covering:

**1. SNOWFALL** - Extract all events with exact amounts/timing from NOAA grid; identify 9+ inch periods; compare with Powder Poobah & AFD

**2. SNOW QUALITY** - Temperature during snowfall (cold=powder, warm=heavy); wind speeds; expert assessments from Poobah/AFD

**3. TIMING** - Next 48hrs: hour-by-hour breakdown; Days 3-7: daily summary; weekday vs weekend opportunities

**4. CONDITIONS** - Wind/visibility/temps from grid data; mountain impacts; expert commentary

**5. ACCESS (CRITICAL)** - WSDOT is PRIMARY source for travel info. REQUIRED: Report exact WSDOT data: pass open/closed status, eastbound/westbound restrictions, chain requirements, current temp/weather/road surface, travel advisories. ⚠️ EMPHASIZE any closures, delays, or restricted access prominently. Make clear verdict: Can riders reach the mountain?

**6. SAFETY** - Active alerts; NWAC avalanche info; backcountry hazards (NOTE: NWAC doesn't apply to ski areas); AFD warnings

**7. RECONCILIATION** - Compare Powder Poobah vs NOAA vs AFD; where sources agree/differ; confidence levels

**8. BOTTOM LINE** - Near-term (48hr) actionable recommendations including road access; extended (3-7 day) outlook; best windows

## OUTPUT FORMAT
**SNOWFALL FORECAST** - Exact amounts, timing, classification

**SNOW QUALITY & CONDITIONS** - Temps, wind, visibility during snow events

**NEAR-TERM (48 Hours)** - Hour-by-hour/period-by-period breakdown

**EXTENDED (Days 3-7)** - Daily conditions summary

**TRAVEL CONSIDERATIONS** - Lead with WSDOT real-time data: pass status, restrictions (both directions), chain requirements, road surface, advisories. ⚠️ HIGHLIGHT any closures/delays/restricted access at top of section. Final verdict: Is the mountain accessible?

**SAFETY & HAZARDS** - Avalanche info, alerts, warnings

**EXPERT RECONCILIATION** - How sources align/differ

**BOTTOM LINE**  
• Next 48hrs: [specific recommendations + road access reality]  
• Days 3-7: [multi-day outlook]

Tone: Professional, data-driven, enthusiastic but honest | Audience: Experienced riders | Max 1300 words

════════════════════════════════════════════════════════════════════════════════
OFFICIAL DATA
════════════════════════════════════════════════════════════════════════════════

{combined_data}"""

        # Save the prompt for inspection before sending to LLM
        prompt_filepath = _save_analysis_prompt(analysis_prompt)
        
        analysis_chunks = []
        for chunk in llm.generate_stream(analysis_prompt):
            analysis_chunks.append(chunk)
        
        analysis = "".join(analysis_chunks)
        
        # NOTE: Plot generation moved to app.py for proper async context
        # Signal that plots should be generated by including metadata
        
        # Build metadata for validation/testing
        data_sources_fetched = {
            "noaa_grid": grid_data_for_plots is not None,
            "powder_poobah": bool(results.get("poobah")),
            "nwac": bool(results.get("nwac")),
            "wsdot": bool(results.get("wsdot")),
            "afd_count": len(afd_results),
        }
        
        # Log fetch summary for testing
        logger.info(f"Data fetch summary: NOAA={'✓' if data_sources_fetched['noaa_grid'] else '✗'}, "
                   f"Poobah={'✓' if data_sources_fetched['powder_poobah'] else '✗'}, "
                   f"NWAC={'✓' if data_sources_fetched['nwac'] else '✗'}, "
                   f"WSDOT={'✓' if data_sources_fetched['wsdot'] else '✗'}, "
                   f"AFDs={data_sources_fetched['afd_count']}")
        
        logger.info("=" * 70)
        logger.info("Analysis Complete")
        logger.info("=" * 70)
        
        result = f"❄️ **Comprehensive Stevens Pass Snow & Weather Analysis**\n\n"
        result += f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*\n"
        result += f"*Data Source: NOAA Weather API (Forecast Grid Data) + Area Forecast Discussion*\n\n"
        result += "="*70 + "\n\n"
        result += analysis
        
        return result
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data for analysis: {e}")
        return f"Error fetching Stevens Pass data: {str(e)}"
    except Exception as e:
        logger.error(f"Error analyzing Stevens Pass data: {e}", exc_info=True)
        return f"Error analyzing Stevens Pass data: {str(e)}"


def get_nwac_avalanche_forecast(zone: str = "stevens-pass") -> str:
    """
    Get the current avalanche forecast from Northwest Avalanche Center (NWAC).
    
    Uses LLM to extract and summarize key sections from the NWAC forecast page:
    - The Bottom Line (summary and immediate concerns)
    - Forecast Discussion (detailed analysis)
    - Danger ratings and metadata
    
    Args:
        zone: NWAC forecast zone (default: "stevens-pass")
              Other zones: mt-baker, snoqualmie-pass, washington-pass, etc.
    
    Returns:
        Formatted string with avalanche forecast summary and safety information
    """
    try:
        from bs4 import BeautifulSoup
        
        zone_names = {
            "stevens-pass": "Stevens Pass",
            "mt-baker": "Mt. Baker",
            "snoqualmie-pass": "Snoqualmie Pass", 
            "washington-pass": "Washington Pass",
            "mt-rainier": "Mt. Rainier",
            "white-pass": "White Pass",
            "olympics": "Olympics",
        }
        
        zone_display = zone_names.get(zone, zone.replace("-", " ").title())
        url = f"https://nwac.us/avalanche-forecast/#{zone}"
        
        logger.info(f"Fetching NWAC avalanche forecast page for {zone_display}")
        
        # Fetch the page HTML
        session = _create_session_with_retries()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        response = session.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse HTML and extract text content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove scripts, styles, and navigation
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'iframe']):
            element.decompose()
        
        # Get the main text content
        page_text = soup.get_text(separator='\n', strip=True)
        
        # Clean up excessive whitespace
        import re
        page_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', page_text)
        page_text = re.sub(r'[ \t]+', ' ', page_text)
        
        logger.info(f"Extracted {len(page_text)} characters from NWAC page, sending to LLM for analysis")
        
        # Use LLM to extract and summarize the key sections
        from models.local_llm import UnifiedLLM
        llm = UnifiedLLM()
        
        extraction_prompt = f"""You are analyzing an avalanche forecast page from the Northwest Avalanche Center (NWAC).

Your task is to extract and summarize the following sections from the page text below:

1. **METADATA** (if present):
   - Zone name
   - Issue date/time
   - Expiration date/time
   - Forecaster name

2. **DANGER RATINGS** (if present):
   - Upper elevations danger level
   - Middle elevations danger level
   - Lower elevations danger level

3. **THE BOTTOM LINE** (CRITICAL - Extract this section):
   - This is the forecaster's key summary and immediate concerns
   - Usually 1-2 paragraphs explaining the main hazard and advice
   - Extract the COMPLETE text of this section

4. **FORECAST DISCUSSION** (CRITICAL - Extract this section):
   - The detailed analysis and reasoning
   - Multiple paragraphs explaining snowpack conditions, weather impacts, and hazard assessment
   - Extract the COMPLETE text of this section

IMPORTANT RULES:
- If a section is not found, write "Section not found in page content"
- Extract the ACTUAL TEXT from the page, do not make up content
- Preserve the original wording from the forecast
- If the page shows "No Rating" for danger levels, report that
- Focus on extracting "The Bottom Line" and "Forecast Discussion" completely

Format your response EXACTLY as follows:

ZONE: [zone name]
ISSUED: [issue time]
EXPIRES: [expiration time]
FORECASTER: [name]

DANGER RATINGS:
Upper: [level]
Middle: [level]
Lower: [level]

THE BOTTOM LINE:
[Complete extracted text]

FORECAST DISCUSSION:
[Complete extracted text]

---
PAGE TEXT TO ANALYZE:
{page_text[:8000]}
"""

        logger.info("Sending extraction request to LLM")
        extracted_content = llm.generate(extraction_prompt)
        
        logger.info("LLM extraction complete, formatting final output")
        logger.info("LLM extraction complete, formatting final output")
        
        # Build the formatted result with extracted content and safety information
        result = []
        result.append("=" * 80)
        result.append(f"NWAC AVALANCHE FORECAST - {zone_display.upper()}")
        result.append("=" * 80)
        result.append("")
        result.append(extracted_content)
        result.append("")
        result.append("-" * 80)
        result.append("AVALANCHE SAFETY REMINDERS")
        result.append("-" * 80)
        result.append("")
        result.append("Essential Safety Gear (Backcountry):")
        result.append("  ✓ Avalanche beacon (check batteries before each trip)")
        result.append("  ✓ Probe (240cm+ recommended)")
        result.append("  ✓ Shovel (metal blade)")
        result.append("  ✓ Communication device")
        result.append("  ✓ First aid kit")
        result.append("")
        result.append("Danger Level Reference:")
        result.append("  1 - Low: Generally safe avalanche conditions")
        result.append("  2 - Moderate: Heightened avalanche conditions on specific terrain")
        result.append("  3 - Considerable: Dangerous avalanche conditions, careful evaluation required")
        result.append("  4 - High: Very dangerous conditions, travel not recommended")
        result.append("  5 - Extreme: Avoid all avalanche terrain")
        result.append("")
        result.append("Red Flags (Turn Around!):")
        result.append("  🚩 Recent avalanches")
        result.append("  🚩 Whumpfing (collapsing) sounds")
        result.append("  🚩 Shooting cracks")
        result.append("  🚩 Heavy, rapid snowfall (>1 inch/hour)")
        result.append("  🚩 Rain on snow or significant warming")
        result.append("  🚩 Strong winds loading slopes")
        result.append("")
        result.append("=" * 80)
        result.append("DISCLAIMER")
        result.append("=" * 80)
        result.append("")
        result.append("This backcountry avalanche information does NOT apply to ski areas")
        result.append("where avalanche control work is performed. Always check the current")
        result.append(f"forecast at {url} before heading into the backcountry.")
        result.append("")
        result.append("Support NWAC's life-saving work: https://nwac.us/membership/")
        result.append("")
        result.append("=" * 80)
        
        logger.info(f"Successfully extracted and formatted NWAC avalanche forecast for {zone_display}")
        return "\n".join(result)
        
    except ImportError as e:
        error_msg = f"Required library not available: {e}\nPlease ensure beautifulsoup4 is installed."
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        logger.error(f"Error fetching/analyzing NWAC avalanche forecast: {e}", exc_info=True)
        # Fallback to providing link with safety info
        zone_display = zone_names.get(zone, zone.replace("-", " ").title())
        url = f"https://nwac.us/avalanche-forecast/#{zone}"
        return f"""⚠️  Could not extract forecast content automatically.

Please visit the current avalanche forecast directly:
🔗 {url}

Error: {str(e)}

IMPORTANT: Always check the current avalanche forecast before entering backcountry terrain.
The Northwest Avalanche Center provides daily forecasts with danger ratings, avalanche 
problems, and travel advice at nwac.us."""


def get_wsdot_mountain_pass_conditions(pass_name: str = "stevens") -> str:
    """
    [TOOL]
    Get current road conditions, restrictions, and weather for Washington State mountain passes.
    Retrieves real-time data from WSDOT including closures, travel advisories, temperature,
    and road conditions.
    
    Args:
        pass_name: Pass to check (default: "stevens"). Options: "stevens", "snoqualmie", "white", "all"
        
    Returns:
        Formatted string with pass conditions, restrictions, temperature, and advisories
    """
    try:
        import os
        access_code = os.getenv("WSDOT_ACCESS_CODE")
        if not access_code:
            return "Error: WSDOT_ACCESS_CODE not found in environment variables"
        
        api_url = f"http://www.wsdot.wa.gov/Traffic/api/MountainPassConditions/MountainPassConditionsREST.svc/GetMountainPassConditionsAsJson?AccessCode={access_code}"
        
        logger.info(f"Fetching WSDOT mountain pass conditions for: {pass_name}")
        
        session = _create_session_with_retries()
        response = session.get(api_url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Map pass names to WSDOT IDs
        pass_mapping = {
            "stevens": "Stevens Pass US 2",
            "snoqualmie": "Snoqualmie Pass I-90",
            "white": "White Pass US 12",
            "chinook": "Chinook Pass SR 410",
            "blewett": "Blewett Pass US 97",
        }
        
        # Filter passes based on request
        passes_to_show = []
        if pass_name.lower() == "all":
            passes_to_show = data
        else:
            target_name = pass_mapping.get(pass_name.lower())
            if target_name:
                passes_to_show = [p for p in data if target_name.lower() in p.get("MountainPassName", "").lower()]
            else:
                # Fallback: search by partial name match
                passes_to_show = [p for p in data if pass_name.lower() in p.get("MountainPassName", "").lower()]
        
        if not passes_to_show:
            return f"No pass conditions found for '{pass_name}'. Try: stevens, snoqualmie, white, or 'all'"
        
        # Format the results
        result_lines = []
        result_lines.append("🚗 **WSDOT Mountain Pass Conditions**")
        result_lines.append("=" * 70)
        result_lines.append("")
        
        for pass_data in passes_to_show:
            pass_full_name = pass_data.get("MountainPassName", "Unknown Pass")
            elevation = pass_data.get("ElevationInFeet", "N/A")
            temp = pass_data.get("TemperatureInFahrenheit")
            weather = pass_data.get("WeatherCondition", "N/A")
            road_condition = pass_data.get("RoadCondition", "No information available")
            travel_advisory = pass_data.get("TravelAdvisoryActive", False)
            
            # Parse date updated
            date_updated = pass_data.get("DateUpdated", "")
            if date_updated:
                # WSDOT format: /Date(1765784463873-0800)/
                import re
                match = re.search(r'/Date\((\d+)', date_updated)
                if match:
                    timestamp_ms = int(match.group(1))
                    from datetime import datetime
                    dt = datetime.fromtimestamp(timestamp_ms / 1000)
                    date_updated = dt.strftime("%Y-%m-%d %I:%M %p")
            
            result_lines.append(f"📍 **{pass_full_name}**")
            result_lines.append(f"   Elevation: {elevation:,} ft")
            if temp is not None:
                result_lines.append(f"   Temperature: {temp}°F")
            result_lines.append(f"   Weather: {weather}")
            result_lines.append(f"   Last Updated: {date_updated}")
            result_lines.append("")
            
            # Restrictions
            restriction_one = pass_data.get("RestrictionOne", {})
            restriction_two = pass_data.get("RestrictionTwo", {})
            
            if restriction_one or restriction_two:
                result_lines.append("   **Restrictions:**")
                if restriction_one and restriction_one.get("RestrictionText"):
                    direction = restriction_one.get("TravelDirection", "")
                    text = restriction_one.get("RestrictionText", "")
                    result_lines.append(f"   • {direction}: {text}")
                if restriction_two and restriction_two.get("RestrictionText"):
                    direction = restriction_two.get("TravelDirection", "")
                    text = restriction_two.get("RestrictionText", "")
                    result_lines.append(f"   • {direction}: {text}")
                result_lines.append("")
            
            # Road conditions
            result_lines.append(f"   **Road Conditions:**")
            result_lines.append(f"   {road_condition}")
            result_lines.append("")
            
            # Travel advisory
            if travel_advisory:
                result_lines.append("   ⚠️ **TRAVEL ADVISORY ACTIVE**")
                result_lines.append("")
            
            result_lines.append("-" * 70)
            result_lines.append("")
        
        result_lines.append("🔗 **More Information:**")
        result_lines.append("   WSDOT Mountain Pass Report: https://wsdot.wa.gov/travel/real-time/mountainpasses")
        result_lines.append("   Mountain Pass Cameras: https://wsdot.wa.gov/travel/real-time/mountainpasses")
        result_lines.append("")
        result_lines.append("=" * 70)
        
        logger.info(f"Successfully retrieved WSDOT conditions for {len(passes_to_show)} pass(es)")
        return "\n".join(result_lines)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching WSDOT pass conditions: {e}")
        return f"Error fetching WSDOT mountain pass conditions: {str(e)}\nPlease try again or visit https://wsdot.wa.gov/travel/real-time/mountainpasses"
    except Exception as e:
        logger.error(f"Unexpected error in get_wsdot_mountain_pass_conditions: {e}", exc_info=True)
        return f"Error processing WSDOT pass conditions: {str(e)}"


# ============================================================================
# TOOL DEFINITIONS - Functions callable by the agent
# ============================================================================

# Define tools for LangGraph
tools = [
    Tool(
        name="search",
        func=search_knowledge,
        description="Search knowledge base for general information. REQUIRES parameter: 'query' (string) - the search query. Example: {'query': 'powder skiing'}",
    ),

    Tool(
        name="nwac_avalanche_forecast",
        func=get_nwac_avalanche_forecast,
        description="Get current avalanche forecast from Northwest Avalanche Center (NWAC). Returns: danger ratings (upper/middle/lower elevations), Bottom Line summary, detailed forecast discussion, weather conditions, and backcountry safety information. OPTIONAL parameter: 'zone' (default: 'stevens-pass'). Available zones: 'stevens-pass', 'mt-baker', 'snoqualmie-pass', 'washington-pass', 'mt-rainier', 'white-pass', 'olympics'. Use {} for Stevens Pass default or {'zone': 'mt-baker'} for other areas.",
    ),

    Tool(
        name="noaa_area_forecast_discussion",
        func=get_noaa_area_forecast_discussion,
        description="Get professional meteorologist analysis from NOAA Area Forecast Discussions (AFD) covering both sides of Cascades. Returns: synoptic pattern analysis, model discussions, forecaster confidence levels, system timing, and technical weather insights from OTX (Spokane/East Cascades) and SEW (Seattle/West Cascades) offices. Useful for understanding weather patterns, forecast uncertainty, and detailed meteorological reasoning. NO parameters needed - use empty input {}.",
    ),
    Tool(
        name="powder_poobah_forecast",
        func=get_powder_poobah_latest_forecast,
        description="Get the latest Powder Poobah professional snow forecast for Pacific Northwest mountains including short-term forecast, highlights, and extended outlook. Expert analysis from a trusted Pacific Northwest snow forecaster. NO parameters needed - use empty input {}.",
    ),
    Tool(
        name="stevens_pass_comprehensive_weather",
        func=get_comprehensive_stevens_pass_data,
        description="Get comprehensive NOAA weather data for Stevens Pass (Tye Mill, 5180ft elevation). Returns: 14-period text forecast, hourly grid data with snowfall amounts/timing, temperature trends, wind speed/gusts, precipitation, visibility, humidity, and active weather alerts. Best for general weather overview without detailed analysis. NO parameters needed - use empty input {}.",
    ),
    Tool(
        name="stevens_pass_snow_analysis",
        func=analyze_snow_forecast_for_stevens_pass,
        description="PREMIUM comprehensive analysis tool combining ALL sources: NOAA grid data, AFD meteorologist discussions, Powder Poobah expert forecast, NWAC avalanche info, and WSDOT road conditions. Returns: AI-synthesized analysis covering snowfall amounts/timing, snow quality assessment, powder day identification (9+ inches), timing windows, mountain conditions, road access, hazards, and winter sports bottom line. Use this when user asks for complete analysis or snow forecast assessment. Takes ~30 seconds. NO parameters needed - use empty input {}.",
    ),
    Tool(
        name="wsdot_pass_conditions",
        func=get_wsdot_mountain_pass_conditions,
        description="Get REAL-TIME road conditions from Washington State DOT for mountain passes. Returns: pass open/closed status, eastbound/westbound restrictions (chains required, traction tires, etc.), current temperature/weather at pass elevation, road surface conditions, travel advisories, closures, delays, and expected changes. CRITICAL for determining if mountain is accessible. Use this when user asks about road conditions, driving, pass status, or 'can I get there'. OPTIONAL parameter: 'pass_name' (default: 'stevens'). Options: 'stevens', 'snoqualmie', 'white', 'chinook', 'blewett', 'all'. Example: {} for Stevens Pass or {'pass_name': 'snoqualmie'} for Snoqualmie Pass.",
    ),
    Tool(
        name="stevens_pass_weather_plots",
        func=generate_stevens_pass_weather_plots,
        description="Generate interactive weather charts for Stevens Pass (internal use - not directly callable by user). Used automatically when weather data is retrieved.",
    ),
]


# ============================================================================
# HELPER FUNCTION UTILITY
# ============================================================================

def get_tool_by_name(name: str) -> Tool | None:
    """Get a tool by name"""
    for tool in tools:
        if tool.name == name:
            return tool
    return None
