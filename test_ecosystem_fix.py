#!/usr/bin/env python3
"""Test script to verify ecosystem services fixes"""

from utils.ecosystem_services import detect_ecosystem_type_enhanced, get_ecosystem_service_values
from datetime import datetime

def test_ecosystem_functions():
    test_coords = [[-114.873047,38.822591],[-114.873047,40.780541],[-113.291016,40.780541],[-113.291016,38.822591]]
    
    print('Testing ecosystem detection...')
    ecosystem_result = detect_ecosystem_type_enhanced(test_coords, num_samples=3)
    print(f'Ecosystem detected: {ecosystem_result.get("primary_ecosystem")}')
    print(f'Confidence: {ecosystem_result.get("confidence", 0):.2f}')
    
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
        print('Success: No total_annual_value error!')

if __name__ == "__main__":
    try:
        test_ecosystem_functions()
    except Exception as e:
        print(f'Test error: {e}')
        import traceback
        traceback.print_exc()