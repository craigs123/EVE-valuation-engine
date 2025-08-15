"""
Test comprehensive ecosystem detection with targeted test locations
"""

from utils.openlandmap_integration import OpenLandMapIntegrator

def test_comprehensive_ecosystem_detection():
    """Test detection across all major ecosystem types with focused locations"""
    
    print("Comprehensive Ecosystem Detection Test")
    print("=" * 60)
    
    # Carefully selected test locations for each ecosystem type
    test_locations = [
        # Urban areas (should be highly accurate)
        {"lat": 34.0522, "lon": -118.2437, "expected": "Urban", "name": "Los Angeles Downtown"},
        {"lat": 33.7376, "lon": -117.7823, "expected": "Urban", "name": "Orange County Center"},
        
        # Forest areas (different types)
        {"lat": 46.7298, "lon": -121.7381, "expected": "Forest", "name": "Mount Rainier Forest"},
        {"lat": 35.6870, "lon": -83.5102, "expected": "Forest", "name": "Great Smoky Mountains"},
        
        # Desert areas
        {"lat": 36.0544, "lon": -115.1462, "expected": "Desert", "name": "Las Vegas Desert"},
        {"lat": 33.6694, "lon": -116.2364, "expected": "Desert", "name": "Joshua Tree Desert"},
        
        # Agricultural areas
        {"lat": 40.4172, "lon": -94.7006, "expected": "Agricultural", "name": "Iowa Corn Belt"},
        {"lat": 39.0458, "lon": -89.1985, "expected": "Agricultural", "name": "Illinois Farmland"},
        
        # Wetland areas (using exact Everglades coordinates)
        {"lat": 25.5, "lon": -80.5, "expected": "Wetland", "name": "Everglades National Park"},
        {"lat": 29.5, "lon": -90.5, "expected": "Wetland", "name": "Louisiana Coastal Wetlands"},
        
        # Coastal areas
        {"lat": 35.2271, "lon": -75.5449, "expected": "Coastal", "name": "Outer Banks NC"},
        {"lat": 37.8044, "lon": -122.2711, "expected": "Coastal", "name": "San Francisco Bay"},
        
        # Grassland/Prairie areas
        {"lat": 38.5, "lon": -99.0, "expected": "Grassland", "name": "Kansas Prairie"},
        {"lat": 43.0, "lon": -101.0, "expected": "Grassland", "name": "South Dakota Grassland"}
    ]
    
    integrator = OpenLandMapIntegrator()
    results_by_type = {}
    total_correct = 0
    
    for location in test_locations:
        print(f"\nTesting: {location['name']}")
        print(f"Coordinates: ({location['lat']}, {location['lon']})")
        print(f"Expected: {location['expected']}")
        
        result = integrator.get_land_cover_point(location['lat'], location['lon'])
        
        if result:
            detected = result['ecosystem_type']
            confidence = result['confidence']
            source = result['source']
            
            print(f"Detected: {detected} ({confidence:.1%} confidence)")
            print(f"Source: {source}")
            
            # Track results by ecosystem type
            expected = location['expected']
            if expected not in results_by_type:
                results_by_type[expected] = {'correct': 0, 'total': 0, 'detected_types': set()}
            
            results_by_type[expected]['total'] += 1
            results_by_type[expected]['detected_types'].add(detected)
            
            if detected == expected:
                print("✅ CORRECT")
                results_by_type[expected]['correct'] += 1
                total_correct += 1
            else:
                print(f"❌ INCORRECT - Expected {expected}")
        else:
            print("❌ NO RESULT")
        
        print("-" * 50)
    
    # Summary analysis
    print(f"\n\nECOSYSTEM DETECTION ANALYSIS")
    print("=" * 60)
    
    all_detected_types = set()
    for expected_type, stats in results_by_type.items():
        accuracy = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
        detected_list = ', '.join(sorted(stats['detected_types']))
        
        print(f"\n{expected_type}:")
        print(f"  Accuracy: {stats['correct']}/{stats['total']} ({accuracy:.0f}%)")
        print(f"  Detected as: {detected_list}")
        
        all_detected_types.update(stats['detected_types'])
    
    overall_accuracy = (total_correct / len(test_locations)) * 100
    print(f"\nOVERALL RESULTS:")
    print(f"  Accuracy: {total_correct}/{len(test_locations)} ({overall_accuracy:.0f}%)")
    print(f"  Types detected: {len(all_detected_types)}")
    print(f"  All types: {', '.join(sorted(all_detected_types))}")
    
    # Assessment
    if overall_accuracy >= 70 and len(all_detected_types) >= 6:
        print("\n✅ ECOSYSTEM DETECTION SYSTEM: GOOD")
        print("   System can detect diverse ecosystem types with acceptable accuracy")
    elif overall_accuracy >= 50:
        print("\n⚠️  ECOSYSTEM DETECTION SYSTEM: MODERATE") 
        print("   System has decent accuracy but may need refinement")
    else:
        print("\n❌ ECOSYSTEM DETECTION SYSTEM: POOR")
        print("   System needs significant improvement for ecosystem diversity")
    
    return results_by_type

if __name__ == "__main__":
    test_comprehensive_ecosystem_detection()