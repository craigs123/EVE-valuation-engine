"""
Test OpenLandMap integration with real coordinates
"""

import sys
sys.path.append('.')

from utils.openlandmap_integration import detect_ecosystem_type

# Test coordinates from the user's recent selection
test_coordinates = [
    [-120.146484, 41.771312],
    [-120.146484, 42.488302], 
    [-118.476563, 42.488302],
    [-118.476563, 41.771312],
    [-120.146484, 41.771312]
]

print("Testing OpenLandMap ecosystem detection...")
print(f"Coordinates: {test_coordinates}")

result = detect_ecosystem_type(test_coordinates)

print("\nResults:")
print(f"Primary Ecosystem: {result['primary_ecosystem']}")
print(f"Confidence: {result['confidence']:.0%}")
print(f"Coverage: {result['coverage_percentage']:.0f}%")
print(f"Successful Queries: {result['successful_queries']}/{result['total_samples']}")
print(f"Source: {result['source']}")

if 'ecosystem_distribution' in result:
    print("\nEcosystem Distribution:")
    for ecosystem, data in result['ecosystem_distribution'].items():
        print(f"  {ecosystem}: {data['count']} samples, avg confidence: {data['confidence']/data['count']:.0%}")