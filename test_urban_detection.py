"""
Test script to verify Urban ecosystem detection from OpenLandMap
"""

from utils.openlandmap_integration import OpenLandMapIntegrator, detect_ecosystem_type
import json

def test_urban_areas():
    """Test urban ecosystem detection for known urban areas"""
    
    # Test locations known to be urban areas
    urban_test_locations = [
        # Los Angeles downtown
        {"lat": 34.0522, "lon": -118.2437, "name": "Los Angeles Downtown"},
        # Manhattan, NYC
        {"lat": 40.7589, "lon": -73.9851, "name": "Manhattan NYC"},
        # San Francisco downtown
        {"lat": 37.7749, "lon": -122.4194, "name": "San Francisco"},
        # Orange County urban area (from user's selection)
        {"lat": 33.7376, "lon": -117.7823, "name": "Orange County Urban"}
    ]
    
    integrator = OpenLandMapIntegrator()
    
    print("Testing Urban Ecosystem Detection")
    print("=" * 50)
    
    for location in urban_test_locations:
        print(f"\nTesting: {location['name']}")
        print(f"Coordinates: ({location['lat']}, {location['lon']})")
        
        # Test single point detection
        result = integrator.get_land_cover_point(location['lat'], location['lon'])
        
        if result:
            print(f"Ecosystem Type: {result['ecosystem_type']}")
            print(f"Confidence: {result['confidence']:.2%}")
            print(f"Source: {result['source']}")
            print(f"Land Cover Class: {result.get('landcover_class', 'N/A')}")
            
            if result['ecosystem_type'] == 'Urban':
                print("✅ CORRECT: Urban ecosystem detected")
            else:
                print(f"❌ INCORRECT: Expected 'Urban', got '{result['ecosystem_type']}'")
        else:
            print("❌ ERROR: No result returned")
        
        print("-" * 30)

def test_area_ecosystem_detection():
    """Test area-based ecosystem detection for urban areas"""
    
    print("\n\nTesting Area-based Urban Detection")
    print("=" * 50)
    
    # Orange County urban area coordinates (from user's recent selection)
    urban_area_coords = [
        [-117.981491, 33.731764],
        [-117.981491, 33.73833],
        [-117.973251, 33.73833], 
        [-117.973251, 33.731764],
        [-117.981491, 33.731764]
    ]
    
    try:
        ecosystem_info = detect_ecosystem_type(
            coordinates=urban_area_coords,
            sampling_frequency=2.0  # Higher frequency for small urban area
        )
        
        print(f"Primary Ecosystem: {ecosystem_info['primary_ecosystem']}")
        print(f"Confidence: {ecosystem_info['confidence']:.2%}")
        print(f"Coverage: {ecosystem_info['coverage_percentage']:.1f}%")
        print(f"Total Samples: {ecosystem_info['total_samples']}")
        print(f"Successful Queries: {ecosystem_info['successful_queries']}")
        
        if 'ecosystem_distribution' in ecosystem_info:
            print("\nEcosystem Distribution:")
            for eco_type, data in ecosystem_info['ecosystem_distribution'].items():
                percentage = (data['count'] / ecosystem_info['successful_queries']) * 100
                print(f"  • {eco_type}: {percentage:.1f}% ({data['count']} samples)")
        
        if ecosystem_info['primary_ecosystem'] == 'Urban':
            print("\n✅ SUCCESS: Urban ecosystem correctly detected for area")
        else:
            print(f"\n❌ ISSUE: Expected 'Urban', got '{ecosystem_info['primary_ecosystem']}'")
            
    except Exception as e:
        print(f"❌ ERROR in area detection: {e}")

def check_landcover_mappings():
    """Check the land cover class mappings for urban detection"""
    
    print("\n\nChecking Land Cover Mappings for Urban")
    print("=" * 50)
    
    integrator = OpenLandMapIntegrator()
    
    print("Urban-mapped classes in landcover_to_ecosystem:")
    urban_classes = []
    for class_id, ecosystem in integrator.landcover_to_ecosystem.items():
        if ecosystem == "Urban":
            urban_classes.append(class_id)
            print(f"  Class {class_id}: {ecosystem}")
    
    print(f"\nTotal urban classes defined: {len(urban_classes)}")
    print(f"Urban classes: {urban_classes}")
    
    if len(urban_classes) == 0:
        print("❌ WARNING: No land cover classes mapped to 'Urban' ecosystem!")
    else:
        print("✅ Urban classes are properly mapped")

if __name__ == "__main__":
    # Run all tests
    check_landcover_mappings()
    test_urban_areas() 
    test_area_ecosystem_detection()