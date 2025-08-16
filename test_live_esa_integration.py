"""
Test live ESA WorldCover integration
"""

from utils.openlandmap_integration import OpenLandMapIntegrator
import streamlit as st

def test_live_esa_worldcover():
    """Test ESA WorldCover with authenticated Earth Engine"""
    
    print("Testing Live ESA WorldCover Integration")
    print("=" * 50)
    
    integrator = OpenLandMapIntegrator()
    
    # Test a simple point in Los Angeles
    test_lat, test_lon = 34.0522, -118.2437
    
    print(f"Testing point: Los Angeles ({test_lat}, {test_lon})")
    
    result = integrator.get_land_cover_point(test_lat, test_lon)
    
    if result:
        print(f"Result: {result}")
        if 'WorldCover' in result.get('source', ''):
            print("✅ SUCCESS: Using authentic ESA WorldCover satellite data!")
            return True
        else:
            print("📍 Using fallback detection")
            return False
    else:
        print("❌ No result returned")
        return False

if __name__ == "__main__":
    success = test_live_esa_worldcover()
    if success:
        print("\n✅ ESA WorldCover integration is WORKING with authenticated Earth Engine")
    else:
        print("\n📍 Still using geographic detection - authentication may need completion")