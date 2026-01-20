#!/usr/bin/env python3
"""
Test script to verify the agricultural food service calculation fix
"""

from utils.ecosystem_services import EcosystemServicesCalculator
from utils.precomputed_esvd_coefficients import get_precomputed_coefficients

def test_agricultural_calculation():
    print("=== Testing Agricultural Food Service Fix ===\n")
    
    # Test 1: Check service categorization
    calculator = EcosystemServicesCalculator()
    print("1. Service Categorization Test:")
    print(f"   'food' in provisioning services: {'food' in calculator.service_categories['provisioning']}")
    print(f"   'climate' in regulating services: {'climate' in calculator.service_categories['regulating']}")
    print()
    
    # Test 2: Check ESVD coefficients
    precomputed = get_precomputed_coefficients()
    print("2. ESVD Coefficients Test:")
    
    # Test agricultural coefficients directly
    result = precomputed.calculate_ecosystem_values('agricultural', 1000.0, None, 0.15)
    print(f"   Total Value: ${result.get('total_value', 0):,.2f}")
    print(f"   Food Service Coefficient: ${result.get('provisioning', {}).get('food', 0):,.2f}")
    print()
    
    # Test 3: Check individual coefficient lookup
    food_coeff = precomputed.get_coefficient('agricultural', 'food')
    print(f"3. Direct coefficient lookup: agricultural food = {food_coeff}")
    print()
    
    # Test 4: Mock ecosystem services calculation
    print("4. Mock Ecosystem Services Calculation Test:")
    
    # Create mock satellite data similar to what the app would use
    mock_satellite_data = {
        'time_series': [
            {
                'date': '2024-01-01',
                'red_mean': 0.2,   # Agricultural areas typically have moderate reflectance
                'nir_mean': 0.6,   # Good vegetation in agricultural areas
                'cloud_coverage': 5,
                'data_quality': 0.95
            }
        ],
        'ecosystem_detection': {
            'detected_type': 'agricultural',
            'confidence': 0.90,
            'is_open_water': False,
            'water_confidence': 0.0
        }
    }
    
    mock_area_bounds = {
        'min_lat': 40.0, 'max_lat': 40.1,
        'min_lon': -74.1, 'max_lon': -74.0
    }
    
    # Calculate NDVI for reference
    red = mock_satellite_data['time_series'][0]['red_mean']
    nir = mock_satellite_data['time_series'][0]['nir_mean']
    ndvi = (nir - red) / (nir + red) if (nir + red) != 0 else 0
    vegetation_factor = max(0.5, min(1.5, ndvi * 2))
    
    print(f"   Mock NDVI: {ndvi:.3f}")
    print(f"   Vegetation Factor: {vegetation_factor:.3f}")
    print(f"   Expected Food Value (before vegetation factor): {food_coeff * 1000:.2f}")
    print(f"   Expected Food Value (after vegetation factor): {food_coeff * 1000 * vegetation_factor:.2f}")
    
    try:
        # Test the full calculation
        result = calculator.calculate_ecosystem_services_value(
            satellite_data=mock_satellite_data,
            area_bounds=mock_area_bounds,
            ecosystem_type='agricultural',
            quality_factor=1.0,
            ecosystem_intactness={'Agricultural': 100.0}
        )
        
        if 'error' in result:
            print(f"   ERROR: {result['error']}")
        else:
            current_value = result.get('current_value', 0)
            provisioning = result.get('services_time_series', [{}])[-1].get('provisioning', {})
            food_value = provisioning.get('food', 0)
            
            print(f"   Total Current Value: ${current_value:,.2f}")
            print(f"   Food Service Value: ${food_value:,.2f}")
            
            # Check if the fix worked
            expected_range_min = food_coeff * 1000 * 0.4  # Minimum possible with vegetation factor
            expected_range_max = food_coeff * 1000 * 1.5  # Maximum possible with vegetation factor
            
            if expected_range_min <= food_value <= expected_range_max:
                print(f"   ✅ FIXED! Food value is within expected range (${expected_range_min:,.0f} - ${expected_range_max:,.0f})")
            else:
                print(f"   ❌ Still broken. Expected range: ${expected_range_min:,.0f} - ${expected_range_max:,.0f}")
    
    except Exception as e:
        print(f"   ERROR in calculation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agricultural_calculation()