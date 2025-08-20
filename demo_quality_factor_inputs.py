"""
Demo: Quality Factor Input Sources in EVE
Shows exactly where red_mean, nir_mean, cloud_coverage, and data_quality come from
"""

import sys
import os
sys.path.append('.')

from datetime import datetime, timedelta
from utils.satellite_data import SatelliteDataProcessor

def demo_quality_factor_input_sources():
    """Demonstrate where EVE gets quality factor inputs"""
    
    print("=" * 80)
    print("EVE QUALITY FACTOR INPUT SOURCES DEMO")
    print("=" * 80)
    print()
    
    print("🛰️ SATELLITE DATA SOURCE:")
    print("-" * 50)
    print("Current Status: SOPHISTICATED SIMULATION")
    print("File: utils/satellite_data.py")
    print("Method: SatelliteDataProcessor.get_time_series_data()")
    print()
    
    # Initialize satellite processor
    processor = SatelliteDataProcessor()
    
    # Demo area (example coordinates)
    demo_area = {
        'coordinates': [
            [-74.0, 40.7],   # NYC area
            [-74.0, 40.8],
            [-73.9, 40.8],
            [-73.9, 40.7],
            [-74.0, 40.7]
        ]
    }
    
    # Get satellite data
    start_date = datetime.now() - timedelta(days=365)
    end_date = datetime.now()
    
    print("📊 GETTING SATELLITE DATA FOR DEMO AREA:")
    print(f"Area: NYC region ({demo_area['coordinates'][0]} to {demo_area['coordinates'][2]})")
    print(f"Time Range: {start_date.strftime('%Y-%m')} to {end_date.strftime('%Y-%m')}")
    print()
    
    satellite_data = processor.get_time_series_data(demo_area, start_date, end_date)
    
    print("📈 QUALITY FACTOR INPUTS EXTRACTED:")
    print("-" * 50)
    
    if satellite_data.get('time_series'):
        # Show the most recent data point
        latest_data = satellite_data['time_series'][-1]
        
        print("📅 Latest Time Point:")
        print(f"Date: {latest_data['date']}")
        print()
        
        print("🔴 RED BAND (red_mean):")
        print(f"Value: {latest_data['red_mean']:.4f}")
        print(f"Source: Simulated red band reflectance")
        print(f"Range: {latest_data['red_mean'] - latest_data['red_std']:.4f} - {latest_data['red_mean'] + latest_data['red_std']:.4f}")
        print(f"Used for: NDVI calculation, vegetation health")
        print()
        
        print("🟢 NIR BAND (nir_mean):")
        print(f"Value: {latest_data['nir_mean']:.4f}")
        print(f"Source: Simulated near-infrared reflectance")
        print(f"Range: {latest_data['nir_mean'] - latest_data['nir_std']:.4f} - {latest_data['nir_mean'] + latest_data['nir_std']:.4f}")
        print(f"Used for: NDVI calculation, vegetation biomass")
        print()
        
        print("☁️ CLOUD COVERAGE (cloud_coverage):")
        print(f"Value: {latest_data['cloud_coverage']:.1f}%")
        print(f"Source: Simulated weather conditions")
        print(f"Range: 0-50% (varies by location/season)")
        print(f"Used for: Data quality assessment")
        print()
        
        print("📊 DATA QUALITY (data_quality):")
        print(f"Value: {latest_data['data_quality']}")
        print(f"Source: Simulated sensor conditions")
        print(f"Options: 'good', 'fair', 'poor'")
        print(f"Used for: Quality scoring weight")
        print()
        
        # Calculate NDVI from the data
        red = latest_data['red_mean']
        nir = latest_data['nir_mean']
        ndvi = (nir - red) / (nir + red) if (nir + red) != 0 else 0
        
        print("🧮 QUALITY FACTOR CALCULATION:")
        print("-" * 50)
        print(f"NDVI = (NIR - Red) / (NIR + Red)")
        print(f"NDVI = ({nir:.4f} - {red:.4f}) / ({nir:.4f} + {red:.4f})")
        print(f"NDVI = {ndvi:.4f}")
        print()
        
        # Quality scoring simulation
        quality_score = 0
        
        # NDVI contribution (40% weight)
        if ndvi > 0.7:
            ndvi_points = 40
            ndvi_category = "Excellent"
        elif ndvi > 0.5:
            ndvi_points = 30
            ndvi_category = "Good"
        elif ndvi > 0.3:
            ndvi_points = 20
            ndvi_category = "Fair"
        elif ndvi > 0.1:
            ndvi_points = 10
            ndvi_category = "Poor"
        else:
            ndvi_points = 0
            ndvi_category = "Very Poor"
        quality_score += ndvi_points
        
        # Data quality contribution (30% weight)
        if latest_data['data_quality'] == 'good':
            quality_points = 30
            quality_desc = "High quality"
        elif latest_data['data_quality'] == 'fair':
            quality_points = 20
            quality_desc = "Medium quality"
        else:
            quality_points = 10
            quality_desc = "Low quality"
        quality_score += quality_points
        
        # Cloud coverage contribution (20% weight)
        cloud = latest_data['cloud_coverage']
        if cloud < 10:
            cloud_points = 20
            cloud_desc = "Clear skies"
        elif cloud < 20:
            cloud_points = 15
            cloud_desc = "Mostly clear"
        elif cloud < 30:
            cloud_points = 10
            cloud_desc = "Partly cloudy"
        else:
            cloud_points = 5
            cloud_desc = "Cloudy"
        quality_score += cloud_points
        
        # Spectral health contribution (10% weight)
        if nir > 0.3:
            spectral_points = 10
            spectral_desc = "Healthy vegetation"
        elif nir > 0.2:
            spectral_points = 7
            spectral_desc = "Moderate vegetation"
        else:
            spectral_points = 3
            spectral_desc = "Sparse vegetation"
        quality_score += spectral_points
        
        print("📋 QUALITY SCORING BREAKDOWN:")
        print(f"NDVI Health: {ndvi_points}/40 points ({ndvi_category})")
        print(f"Data Quality: {quality_points}/30 points ({quality_desc})")
        print(f"Cloud Coverage: {cloud_points}/20 points ({cloud_desc})")
        print(f"Spectral Health: {spectral_points}/10 points ({spectral_desc})")
        print(f"Total Score: {quality_score}/100 points")
        print()
        
        # Determine quality category and multiplier
        if quality_score >= 85:
            quality_category = 'excellent'
            multiplier = 1.2
        elif quality_score >= 70:
            quality_category = 'good'
            multiplier = 1.0
        elif quality_score >= 55:
            quality_category = 'fair'
            multiplier = 0.8
        elif quality_score >= 40:
            quality_category = 'poor'
            multiplier = 0.6
        else:
            quality_category = 'degraded'
            multiplier = 0.4
            
        print("🏆 FINAL QUALITY ASSESSMENT:")
        print(f"Quality Category: {quality_category.upper()}")
        print(f"Quality Multiplier: {multiplier}x")
        print()
        
        print("💰 IMPACT ON ESVD VALUES:")
        print("-" * 50)
        base_value = 1417  # Example: Forest cultural services $/ha/year
        final_value = base_value * multiplier
        print(f"ESVD Base Value: ${base_value:,}/ha/year")
        print(f"Quality Adjusted: ${final_value:,.0f}/ha/year")
        print(f"Quality Impact: {((multiplier - 1) * 100):+.0f}% from baseline")
        print()
        
    print("🔧 DATA SOURCE CONFIGURATION:")
    print("-" * 50)
    print("Current Setup: Realistic simulation based on:")
    print("• Geographic location → Ecosystem type → Spectral characteristics")
    print("• Seasonal variations → Natural vegetation cycles")
    print("• Random noise → Natural variability")
    print("• Weather patterns → Cloud coverage simulation")
    print()
    print("For Real Satellite Data:")
    print("• Option 1: Google Earth Engine (Sentinel-2/Landsat)")
    print("• Option 2: Planet Labs API (high resolution)")
    print("• Option 3: USGS Earth Explorer API")
    print("• Status: Available with proper authentication")
    print()
    print("=" * 80)

if __name__ == "__main__":
    demo_quality_factor_input_sources()