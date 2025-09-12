#!/usr/bin/env python3
"""
Debug why the time_series check is failing
"""

from utils.ecosystem_services import EcosystemServicesCalculator

def debug_time_series_issue():
    print("=== Debugging Time Series Issue ===\n")
    
    calculator = EcosystemServicesCalculator()
    
    # Test data that should work
    mock_satellite_data = {
        'time_series': [
            {
                'date': '2024-01-01',
                'red_mean': 0.2,
                'nir_mean': 0.6,
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
    
    print("1. Input Data Check:")
    print(f"   satellite_data type: {type(mock_satellite_data)}")
    print(f"   satellite_data keys: {list(mock_satellite_data.keys())}")
    print(f"   time_series type: {type(mock_satellite_data.get('time_series'))}")
    print(f"   time_series length: {len(mock_satellite_data.get('time_series', []))}")
    print(f"   time_series content: {mock_satellite_data.get('time_series')}")
    
    # Test the exact condition that's failing
    print(f"\n2. Condition Tests:")
    time_series = mock_satellite_data.get('time_series')
    print(f"   satellite_data.get('time_series'): {time_series}")
    print(f"   bool(satellite_data.get('time_series')): {bool(time_series)}")
    print(f"   not satellite_data.get('time_series'): {not time_series}")
    
    if not time_series:
        print("   ❌ CONDITION WOULD FAIL - time_series is falsy")
    else:
        print("   ✅ CONDITION WOULD PASS - time_series is truthy")
    
    print(f"\n3. Method Call Test:")
    try:
        # Call the method and see what happens
        print("   Calling calculate_ecosystem_services_value...")
        
        result = calculator.calculate_ecosystem_services_value(
            satellite_data=mock_satellite_data,
            area_bounds=mock_area_bounds,
            ecosystem_type='agricultural',
            quality_factor=1.0
        )
        
        print(f"   Result type: {type(result)}")
        print(f"   Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        if 'error' in result:
            print(f"   ❌ ERROR RETURNED: {result['error']}")
        else:
            print(f"   ✅ SUCCESS: {len(result.get('services_time_series', []))} time series points")
            
    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n4. Simplified Test - Direct Time Series Check:")
    # Test just the beginning of the method
    try:
        # Simulate what happens at the very start of the method
        if not mock_satellite_data.get('time_series'):
            print("   ❌ Early return - No time series data")
        else:
            time_series = mock_satellite_data['time_series']
            print(f"   ✅ Time series data found: {len(time_series)} points")
            
            # Test area calculation
            area_ha = calculator._calculate_area_hectares(mock_area_bounds)
            print(f"   Area calculation: {area_ha:,.2f} hectares")
            
            # Test area bounds structure
            total_area_ha = calculator._calculate_area_hectares(mock_area_bounds)
            print(f"   Total area: {total_area_ha:,.2f} hectares")
            
    except Exception as e:
        print(f"   ❌ ERROR in simplified test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_time_series_issue()