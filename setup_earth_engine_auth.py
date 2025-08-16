"""
Earth Engine Authentication Setup Helper
"""

import ee

def setup_earth_engine():
    """Setup Earth Engine authentication"""
    
    print("Setting up Google Earth Engine Authentication")
    print("=" * 50)
    
    try:
        print("Step 1: Attempting to authenticate with Earth Engine...")
        
        # Try notebook authentication mode
        try:
            ee.Authenticate(auth_mode='notebook')
        except Exception:
            # Fallback to standard authentication
            ee.Authenticate()
        
        print("Step 2: Initializing Earth Engine...")
        ee.Initialize()
        
        print("✅ SUCCESS: Earth Engine authentication complete!")
        
        # Test with ESA WorldCover
        print("Step 3: Testing ESA WorldCover access...")
        worldcover = ee.Image('ESA/WorldCover/v200')
        
        # Test point in your selected Oregon area
        test_point = ee.Geometry.Point([-121.07, 42.32])
        sample = worldcover.sample(region=test_point, scale=10, numPixels=1).first()
        lc_value = sample.get('Map').getInfo()
        
        print(f"✅ ESA WorldCover test successful!")
        print(f"   Land cover class detected: {lc_value}")
        print("   Your app will now use authentic 10m satellite data!")
        
        return True
        
    except Exception as e:
        print(f"Authentication step needed: {e}")
        print("\nTo complete setup:")
        print("1. Run: earthengine authenticate")
        print("2. Follow the browser authentication flow")
        print("3. Run this script again to test")
        return False

if __name__ == "__main__":
    setup_earth_engine()