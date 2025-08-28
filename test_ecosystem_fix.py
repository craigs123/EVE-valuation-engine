#!/usr/bin/env python3
"""Test script to verify ecosystem services fixes"""

from utils.ecosystem_services import detect_ecosystem_type_enhanced, get_ecosystem_service_values
from datetime import datetime

def test_ecosystem_functions():
    # Test areas for single ecosystem validation (all exactly 1000 hectares)
    test_areas = {
        'Test area (Agricultural)': [[-99.037, 40.014], [-99.037, 40.042], [-99.000, 40.042], [-99.000, 40.014], [-99.037, 40.014]],
        'Test area (Grassland)': [[-110.500, 45.000], [-110.500, 45.028], [-110.463, 45.028], [-110.463, 45.000], [-110.500, 45.000]],
        'Test area (Boreal Forest)': [[-105.000, 55.000], [-105.000, 55.028], [-104.963, 55.028], [-104.963, 55.000], [-105.000, 55.000]],
        'Test area (Desert)': [[-112.500, 33.500], [-112.500, 33.528], [-112.463, 33.528], [-112.463, 33.500], [-112.500, 33.500]]
    }
    
    for area_name, test_coords in test_areas.items():
        print(f'\n{"="*60}')
        print(f'Testing {area_name}')
        print(f'{"="*60}')
        
        print('Testing ecosystem detection...')
        ecosystem_result = detect_ecosystem_type_enhanced(test_coords, num_samples=3)
        print(f'Ecosystem detected: {ecosystem_result.get("primary_ecosystem")}')
        print(f'Confidence: {ecosystem_result.get("confidence", 0):.2f}')
        
        # Check if multiple ecosystems detected
        if 'ecosystem_distribution' in ecosystem_result:
            distribution = ecosystem_result['ecosystem_distribution']
            if len(distribution) > 1:
                print(f'⚠️  Mixed ecosystem detected ({len(distribution)} types):')
                for eco_type, data in distribution.items():
                    print(f'   - {eco_type}: {data["count"]} sample points')
            else:
                print('✅ Single ecosystem confirmed')
        
        print('\nTesting ecosystem service values...')
        service_result = get_ecosystem_service_values(
            ecosystem_result['primary_ecosystem'], 
            test_coords,
            datetime(2024, 1, 1),
            datetime(2024, 6, 1),
            num_samples=2
        )
        
        if 'error' in service_result:
            print(f'Service calculation error: {service_result["error"]}')
        else:
            print(f'Current value: ${service_result.get("current_value", 0):,.0f}')
            print('✅ Success: No total_annual_value error!')
    
    print(f'\n{"="*60}')
    print('All test areas completed!')

if __name__ == "__main__":
    try:
        test_ecosystem_functions()
    except Exception as e:
        print(f'Test error: {e}')
        import traceback
        traceback.print_exc()