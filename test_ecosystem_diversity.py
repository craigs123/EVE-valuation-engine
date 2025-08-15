"""
Test ecosystem detection diversity across different coordinate types
"""

from utils.openlandmap_integration import OpenLandMapIntegrator, detect_ecosystem_type
import json

def test_ecosystem_diversity():
    """Test detection of different ecosystem types"""
    
    print("Testing Ecosystem Detection Diversity")
    print("=" * 60)
    
    # Test locations for different ecosystem types
    test_locations = [
        # Urban areas
        {"lat": 34.0522, "lon": -118.2437, "expected": "Urban", "name": "Los Angeles (Urban)"},
        {"lat": 33.7376, "lon": -117.7823, "expected": "Urban", "name": "Orange County (Urban)"},
        
        # Agricultural areas
        {"lat": 40.0, "lon": -95.0, "expected": "Agricultural", "name": "Nebraska Farmland"},
        {"lat": 39.5, "lon": -90.0, "expected": "Agricultural", "name": "Illinois Agricultural"},
        
        # Forest areas
        {"lat": 47.0, "lon": -120.0, "expected": "Forest", "name": "Washington State Forest"},
        {"lat": 36.0, "lon": -82.0, "expected": "Forest", "name": "Appalachian Forest"},
        {"lat": 30.0, "lon": -85.0, "expected": "Forest", "name": "Southeast Forest"},
        
        # Desert areas
        {"lat": 35.0, "lon": -115.0, "expected": "Desert", "name": "Mojave Desert"},
        {"lat": 32.0, "lon": -110.0, "expected": "Desert", "name": "Sonoran Desert"},
        
        # Grassland areas
        {"lat": 40.0, "lon": -100.0, "expected": "Grassland", "name": "Great Plains"},
        {"lat": 42.0, "lon": -98.0, "expected": "Grassland", "name": "Nebraska Grassland"},
        
        # Wetland areas
        {"lat": 28.0, "lon": -90.0, "expected": "Wetland", "name": "Gulf Coast Wetland"},
        {"lat": 25.5, "lon": -80.5, "expected": "Wetland", "name": "Everglades"},
        
        # Coastal areas
        {"lat": 35.0, "lon": -75.0, "expected": "Coastal", "name": "Outer Banks"},
        {"lat": 41.0, "lon": -71.0, "expected": "Coastal", "name": "Rhode Island Coast"}
    ]
    
    integrator = OpenLandMapIntegrator()
    results_summary = {}
    
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
            
            # Track results
            if detected not in results_summary:
                results_summary[detected] = {'correct': 0, 'total': 0}
            results_summary[detected]['total'] += 1
            
            if detected == location['expected']:
                print("✅ CORRECT")
                results_summary[detected]['correct'] += 1
            else:
                print(f"❌ INCORRECT - Expected {location['expected']}")
        else:
            print("❌ NO RESULT")
        
        print("-" * 40)
    
    # Summary
    print(f"\nDetection Summary")
    print("=" * 30)
    
    total_tests = len(test_locations)
    correct_detections = 0
    ecosystem_types_detected = set()
    
    for ecosystem, stats in results_summary.items():
        accuracy = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
        print(f"{ecosystem}: {stats['correct']}/{stats['total']} correct ({accuracy:.0f}%)")
        correct_detections += stats['correct']
        ecosystem_types_detected.add(ecosystem)
    
    overall_accuracy = (correct_detections / total_tests) * 100
    print(f"\nOverall Accuracy: {correct_detections}/{total_tests} ({overall_accuracy:.0f}%)")
    print(f"Ecosystem Types Detected: {len(ecosystem_types_detected)}")
    print(f"Types: {', '.join(sorted(ecosystem_types_detected))}")
    
    if len(ecosystem_types_detected) >= 5:
        print("✅ Good ecosystem diversity detected")
    else:
        print("❌ Limited ecosystem diversity - system may be falling back to defaults")
    
    return results_summary

if __name__ == "__main__":
    test_ecosystem_diversity()