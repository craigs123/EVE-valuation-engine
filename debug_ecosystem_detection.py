"""
Debug ecosystem detection to trace the flow
"""

from utils.openlandmap_integration import OpenLandMapIntegrator

def debug_detection_flow():
    """Debug the ecosystem detection flow for specific coordinates"""
    
    integrator = OpenLandMapIntegrator()
    
    # Test Los Angeles coordinates
    lat, lon = 34.0522, -118.2437
    print(f"Debugging detection for Los Angeles: ({lat}, {lon})")
    print("=" * 60)
    
    # Test each detection method individually
    print("1. Testing urban detection:")
    urban_result = integrator._detect_urban_areas(lat, lon)
    print(f"   Result: {urban_result}")
    
    print("\n2. Testing wetland detection:")
    wetland_result = integrator._detect_wetland_areas(lat, lon)
    print(f"   Result: {wetland_result}")
    
    print("\n3. Testing coastal detection:")
    coastal_result = integrator._detect_coastal_areas(lat, lon)
    print(f"   Result: {coastal_result}")
    
    print("\n4. Testing US ecosystem detection:")
    us_result = integrator._enhanced_us_ecosystem_detection(lat, lon)
    print(f"   Result: {us_result}")
    
    print("\n5. Testing global ecosystem detection:")
    global_result = integrator._detect_global_ecosystems(lat, lon)
    print(f"   Result: {global_result}")
    
    print("\n6. Full detection result:")
    full_result = integrator.get_land_cover_point(lat, lon)
    print(f"   Result: {full_result}")
    
    print("\nDetection priority should be:")
    print("   1. Urban (should detect Los Angeles)")
    print("   2. Wetland (not applicable)")
    print("   3. Coastal (not applicable)")
    print("   4. US-specific (Desert - competing with urban)")
    print("   5. Global (not reached)")

if __name__ == "__main__":
    debug_detection_flow()