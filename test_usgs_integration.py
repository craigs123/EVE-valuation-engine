"""
Test USGS Earth Explorer Integration
Verifies authentic satellite data access for ecosystem quality assessment
"""

import sys
import os
sys.path.append('.')

from utils.usgs_integration import usgs_integrator
from utils.satellite_data import SatelliteDataProcessor
from datetime import datetime, timedelta

def test_usgs_integration():
    """Test USGS Earth Explorer integration"""
    
    print("=" * 80)
    print("USGS EARTH EXPLORER INTEGRATION TEST")
    print("=" * 80)
    print()
    
    print("🔧 TESTING CONNECTION:")
    print("-" * 50)
    
    # Test connection
    test_result = usgs_integrator.test_connection()
    
    print(f"USGS Libraries Available: {'✅' if test_result['usgs_available'] else '❌'}")
    print(f"Credentials Provided: {'✅' if test_result['credentials_provided'] else '❌'}")
    print(f"Authentication Success: {'✅' if test_result['authentication_success'] else '❌'}")
    print(f"API Access: {'✅' if test_result['api_access'] else '❌'}")
    print(f"Test Search: {'✅' if test_result['test_search'] else '❌'}")
    
    if test_result.get('error'):
        print(f"Error: {test_result['error']}")
    
    if test_result.get('search_error'):
        print(f"Search Error: {test_result['search_error']}")
    
    if test_result.get('sample_scenes_found'):
        print(f"Sample Scenes Found: {test_result['sample_scenes_found']}")
    
    print()
    
    print("📊 TESTING SATELLITE DATA RETRIEVAL:")
    print("-" * 50)
    
    # Test area (NYC region)
    demo_area = {
        'coordinates': [
            [-74.0, 40.7],
            [-74.0, 40.8], 
            [-73.9, 40.8],
            [-73.9, 40.7],
            [-74.0, 40.7]
        ]
    }
    
    # Test satellite data processor with authentic data
    processor = SatelliteDataProcessor()
    start_date = datetime.now() - timedelta(days=90)  # Last 3 months
    end_date = datetime.now()
    
    print(f"Test Area: NYC region")
    print(f"Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print()
    
    # Get satellite data (will try USGS first, then fallback)
    satellite_data = processor.get_time_series_data(demo_area, start_date, end_date)
    
    print("📈 SATELLITE DATA RESULTS:")
    print("-" * 50)
    
    metadata = satellite_data.get('metadata', {})
    print(f"Data Source: {metadata.get('data_source', 'Unknown')}")
    print(f"Authentic Data: {'✅' if metadata.get('authentic_data') else '❌ (Using simulation)'}")
    
    if metadata.get('fallback_reason'):
        print(f"Fallback Reason: {metadata['fallback_reason']}")
    
    time_series = satellite_data.get('time_series', [])
    print(f"Time Points: {len(time_series)}")
    
    if time_series:
        latest = time_series[-1]
        print()
        print("🛰️ LATEST DATA POINT:")
        print(f"Date: {latest['date']}")
        print(f"Red Band: {latest['red_mean']:.4f}")
        print(f"NIR Band: {latest['nir_mean']:.4f}")
        print(f"Cloud Coverage: {latest['cloud_coverage']:.1f}%")
        print(f"Data Quality: {latest['data_quality']}")
        
        if latest.get('authentic_source'):
            print(f"Scene ID: {latest.get('scene_id', 'N/A')}")
            print(f"Satellite: {latest.get('satellite', 'N/A')}")
            print(f"Collection: {latest.get('collection', 'N/A')}")
        
        # Calculate NDVI
        red = latest['red_mean']
        nir = latest['nir_mean']
        ndvi = (nir - red) / (nir + red) if (nir + red) != 0 else 0
        
        print(f"Calculated NDVI: {ndvi:.4f}")
        
        # Quality assessment
        quality_score = 0
        if ndvi > 0.7:
            quality_score += 40
        elif ndvi > 0.5:
            quality_score += 30
        elif ndvi > 0.3:
            quality_score += 20
        elif ndvi > 0.1:
            quality_score += 10
        
        if latest['data_quality'] == 'good':
            quality_score += 30
        elif latest['data_quality'] == 'fair':
            quality_score += 20
        else:
            quality_score += 10
        
        if latest['cloud_coverage'] < 10:
            quality_score += 20
        elif latest['cloud_coverage'] < 20:
            quality_score += 15
        elif latest['cloud_coverage'] < 30:
            quality_score += 10
        else:
            quality_score += 5
        
        if nir > 0.3:
            quality_score += 10
        elif nir > 0.2:
            quality_score += 7
        else:
            quality_score += 3
        
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
        
        print(f"Quality Score: {quality_score}/100")
        print(f"Quality Category: {quality_category.upper()}")
        print(f"Quality Multiplier: {multiplier}x")
    
    print()
    print("💡 NEXT STEPS:")
    print("-" * 50)
    
    if test_result['authentication_success']:
        print("✅ USGS authentication successful!")
        print("✅ Ready to use authentic Landsat imagery")
        print("✅ Quality factors from real satellite data")
    else:
        print("⚠️  USGS authentication not complete")
        print("📝 Check USGS_USERNAME and USGS_PASSWORD environment variables")
        print("🌐 Create account at: https://earthexplorer.usgs.gov/register")
        print("📊 Currently using enhanced simulation for quality factors")
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    test_usgs_integration()