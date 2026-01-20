#!/usr/bin/env python3
"""
Comprehensive test for ecosystem detection functionality
Tests all 7 ecosystem types with realistic scenarios
"""

import sys
import os
sys.path.append('.')

from utils.satellite_data import SatelliteDataProcessor

def test_ecosystem_detection():
    """Test all ecosystem types with realistic geographic and spectral data"""
    
    processor = SatelliteDataProcessor()
    
    # Test cases for each ecosystem type
    test_cases = [
        {
            'name': 'Amazon Rainforest',
            'bbox': {'min_lat': -3.0, 'max_lat': -2.0, 'min_lon': -60.0, 'max_lon': -59.0},
            'spectral': {'red_mean': 0.05, 'nir_mean': 0.45, 'green_mean': 0.08, 'swir1_mean': 0.15},
            'expected': 'forest'
        },
        {
            'name': 'Great Plains Grassland',
            'bbox': {'min_lat': 39.0, 'max_lat': 40.0, 'min_lon': -101.0, 'max_lon': -100.0},
            'spectral': {'red_mean': 0.15, 'nir_mean': 0.35, 'green_mean': 0.12, 'swir1_mean': 0.25},
            'expected': 'grassland'
        },
        {
            'name': 'Iowa Agricultural Land',
            'bbox': {'min_lat': 42.0, 'max_lat': 43.0, 'min_lon': -93.0, 'max_lon': -92.0},
            'spectral': {'red_mean': 0.15, 'nir_mean': 0.35, 'green_mean': 0.12, 'swir1_mean': 0.30},
            'expected': 'agricultural'
        },
        {
            'name': 'Florida Everglades Wetland',
            'bbox': {'min_lat': 25.5, 'max_lat': 26.5, 'min_lon': -80.5, 'max_lon': -79.5},
            'spectral': {'red_mean': 0.06, 'nir_mean': 0.15, 'green_mean': 0.25, 'swir1_mean': 0.12},
            'expected': 'wetland'
        },
        {
            'name': 'California Coastal Area',
            'bbox': {'min_lat': 36.0, 'max_lat': 37.0, 'min_lon': -122.0, 'max_lon': -121.0},
            'spectral': {'red_mean': 0.10, 'nir_mean': 0.18, 'green_mean': 0.20, 'swir1_mean': 0.14},
            'expected': 'coastal'
        },
        {
            'name': 'New York City Urban',
            'bbox': {'min_lat': 40.7, 'max_lat': 40.8, 'min_lon': -74.1, 'max_lon': -74.0},
            'spectral': {'red_mean': 0.25, 'nir_mean': 0.20, 'green_mean': 0.22, 'swir1_mean': 0.35},
            'expected': 'urban'
        },
        {
            'name': 'Sahara Desert',
            'bbox': {'min_lat': 23.0, 'max_lat': 24.0, 'min_lon': 5.0, 'max_lon': 6.0},
            'spectral': {'red_mean': 0.40, 'nir_mean': 0.42, 'green_mean': 0.38, 'swir1_mean': 0.45},
            'expected': 'desert'
        }
    ]
    
    print("Testing Ecosystem Detection System")
    print("=" * 50)
    
    results = []
    for test_case in test_cases:
        # Create time series with the test spectral data
        time_series = [test_case['spectral']]
        
        # Run detection
        detection_result = processor._detect_ecosystem_type(test_case['bbox'], time_series)
        
        detected_type = detection_result.get('detected_type', 'unknown')
        confidence = detection_result.get('confidence', 0)
        method = detection_result.get('method', 'unknown')
        
        # Check if detection matches expected
        success = detected_type == test_case['expected']
        
        print(f"\nTest: {test_case['name']}")
        print(f"Location: {test_case['bbox']['min_lat']:.1f}°N, {test_case['bbox']['min_lon']:.1f}°E")
        print(f"Expected: {test_case['expected']}")
        print(f"Detected: {detected_type}")
        print(f"Confidence: {confidence:.1%}")
        print(f"Method: {method}")
        print(f"Result: {'✓ PASS' if success else '✗ FAIL'}")
        
        results.append({
            'test_name': test_case['name'],
            'expected': test_case['expected'],
            'detected': detected_type,
            'confidence': confidence,
            'success': success
        })
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {passed/total:.1%}")
    
    # Show failed tests
    failed_tests = [r for r in results if not r['success']]
    if failed_tests:
        print("\nFailed Tests:")
        for test in failed_tests:
            print(f"- {test['test_name']}: Expected {test['expected']}, got {test['detected']}")
    
    # Show ecosystem coverage
    detected_types = set(r['detected'] for r in results)
    expected_types = set(r['expected'] for r in results)
    
    print(f"\nEcosystem Types Detected: {len(detected_types)}")
    print(f"Expected Types: {sorted(expected_types)}")
    print(f"Detected Types: {sorted(detected_types)}")
    
    if detected_types == expected_types:
        print("✓ All ecosystem types successfully detected")
    else:
        missing = expected_types - detected_types
        extra = detected_types - expected_types
        if missing:
            print(f"✗ Missing types: {sorted(missing)}")
        if extra:
            print(f"? Extra types: {sorted(extra)}")
    
    return results

if __name__ == "__main__":
    test_ecosystem_detection()