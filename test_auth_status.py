"""
Quick test to check if Earth Engine authentication is working
"""

import ee

def check_auth_status():
    """Check Earth Engine authentication status"""
    
    print("Checking Earth Engine Authentication Status")
    print("=" * 45)
    
    try:
        # Try to initialize without authentication first
        ee.Initialize()
        
        print("✅ Earth Engine is authenticated and ready!")
        
        # Test ESA WorldCover access
        print("Testing ESA WorldCover access...")
        worldcover = ee.Image('ESA/WorldCover/v200')
        
        # Test with a sample point
        test_point = ee.Geometry.Point([-121.07, 42.32])  # Oregon area
        sample = worldcover.sample(region=test_point, scale=10, numPixels=1).first()
        lc_value = sample.get('Map').getInfo()
        
        print(f"✅ ESA WorldCover working! Land cover class: {lc_value}")
        print("🌱 Your Ecosystem Valuation Engine is now using authentic satellite data!")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication needed: {e}")
        print("\nTo complete authentication:")
        print("1. Run: earthengine authenticate --auth_mode=notebook")
        print("2. Follow the browser authentication steps")
        print("3. Run this test again")
        
        return False

if __name__ == "__main__":
    check_auth_status()