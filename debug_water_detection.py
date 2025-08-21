#!/usr/bin/env python3
"""
Debug script to test water detection logic
"""
import numpy as np
from utils.satellite_data import SatelliteDataProcessor

def test_water_detection():
    """Test water detection with various scenarios"""
    processor = SatelliteDataProcessor()
    
    # Test cases for water detection
    test_cases = [
        {
            'name': 'Clear open water',
            'red_mean': 0.05,
            'nir_mean': 0.02,
            'green_mean': 0.04,
            'swir1_mean': 0.01,
            'expected': 'water/wetland'
        },
        {
            'name': 'Lake water',
            'red_mean': 0.08,
            'nir_mean': 0.03,
            'green_mean': 0.06,
            'swir1_mean': 0.02,
            'expected': 'water/wetland'
        },
        {
            'name': 'Coastal water',
            'red_mean': 0.12,
            'nir_mean': 0.05,
            'green_mean': 0.10,
            'swir1_mean': 0.03,
            'expected': 'water/wetland'
        },
        {
            'name': 'Forest',
            'red_mean': 0.15,
            'nir_mean': 0.45,
            'green_mean': 0.12,
            'swir1_mean': 0.25,
            'expected': 'forest'
        }
    ]
    
    print("=== Water Detection Debug Test ===\n")
    
    for test_case in test_cases:
        print(f"Testing: {test_case['name']}")
        
        # Calculate indices
        red = test_case['red_mean']
        nir = test_case['nir_mean'] 
        green = test_case['green_mean']
        swir1 = test_case['swir1_mean']
        
        # Calculate NDVI and NDWI
        ndvi = (nir - red) / (nir + red) if (nir + red) > 0 else 0
        ndwi = (green - nir) / (green + nir) if (green + nir) > 0 else 0
        
        print(f"  Red: {red:.3f}, NIR: {nir:.3f}, Green: {green:.3f}, SWIR1: {swir1:.3f}")
        print(f"  NDVI: {ndvi:.3f}, NDWI: {ndwi:.3f}")
        
        # Test water detection criteria
        is_clear_water = ndwi > 0.4 and ndvi < 0.1
        is_likely_water = ndwi > 0.3 and ndvi < 0.2
        
        print(f"  Clear water (NDWI > 0.4 & NDVI < 0.1): {is_clear_water}")
        print(f"  Likely water (NDWI > 0.3 & NDVI < 0.2): {is_likely_water}")
        
        # Run actual detection
        bbox = {
            'min_lat': 35.0, 'max_lat': 35.1,
            'min_lon': -120.0, 'max_lon': -119.9
        }
        
        time_series_data = [{
            'date': '2024-08-21',
            'red_mean': red,
            'nir_mean': nir,
            'green_mean': green,
            'swir1_mean': swir1
        }]
        
        try:
            detection = processor._detect_ecosystem_type(bbox, time_series_data)
            detected_type = detection['detected_type']
            is_open_water = detection.get('is_open_water', False)
            water_confidence = detection.get('water_confidence', 0)
            
            print(f"  Detected type: {detected_type}")
            print(f"  Is open water: {is_open_water}")
            print(f"  Water confidence: {water_confidence:.3f}")
            print(f"  Expected: {test_case['expected']}")
            
            # Check if detection matches expectation
            if 'water' in test_case['expected'].lower() or 'wetland' in test_case['expected'].lower():
                if detected_type == 'wetland' or is_open_water:
                    print("  ✅ PASS - Correctly detected water/wetland")
                else:
                    print("  ❌ FAIL - Should detect water/wetland")
            else:
                if detected_type != 'wetland' and not is_open_water:
                    print("  ✅ PASS - Correctly detected non-water")
                else:
                    print("  ❌ FAIL - Should not detect water")
            
        except Exception as e:
            print(f"  ERROR: {e}")
        
        print("-" * 50)

if __name__ == "__main__":
    test_water_detection()