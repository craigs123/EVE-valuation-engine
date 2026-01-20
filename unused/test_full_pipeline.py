#!/usr/bin/env python3
"""
Test the full EcosystemServicesCalculator pipeline to find the $305,000 bug
"""

from utils.ecosystem_services import EcosystemServicesCalculator
from utils.precomputed_esvd_coefficients import get_precomputed_coefficients

def test_full_pipeline():
    print("=== Testing Full EcosystemServicesCalculator Pipeline ===\n")
    
    # Create calculator and mock data similar to what the app would use
    calculator = EcosystemServicesCalculator()
    
    # Mock satellite data that would come from the app for agricultural area
    mock_satellite_data = {
        'time_series': [
            {
                'date': '2024-01-01',
                'red_mean': 0.2,    # Agricultural areas - moderate reflectance
                'nir_mean': 0.6,    # Good vegetation
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
    
    # Mock area bounds that would represent ~1000 hectares
    mock_area_bounds = {
        'min_lat': 40.0, 'max_lat': 40.1,   # ~11 km tall
        'min_lon': -74.1, 'max_lon': -74.0  # ~11 km wide ≈ 121 km² ≈ 12,100 ha
    }
    
    print("1. Input Data:")
    print(f"   Ecosystem type: {mock_satellite_data['ecosystem_detection']['detected_type']}")
    red = mock_satellite_data['time_series'][0]['red_mean']
    nir = mock_satellite_data['time_series'][0]['nir_mean']
    ndvi = (nir - red) / (nir + red) if (nir + red) != 0 else 0
    vegetation_factor = max(0.5, min(1.5, ndvi * 2))
    print(f"   NDVI: {ndvi:.3f}")
    print(f"   Vegetation factor: {vegetation_factor:.3f}")
    print()
    
    # Test area calculation
    print("2. Area Calculation:")
    area_ha = calculator._calculate_area_hectares(mock_area_bounds)
    print(f"   Calculated area: {area_ha:,.2f} hectares")
    print()
    
    # Test ESVD call independently
    print("3. Independent ESVD Test:")
    precomputed = get_precomputed_coefficients()
    esvd_results = precomputed.calculate_ecosystem_values('agricultural', area_ha, None, 0.15)
    esvd_food_value = esvd_results.get('provisioning', {}).get('services', {}).get('food', 0)
    print(f"   ESVD food value: ${esvd_food_value:,.2f}")
    print(f"   ESVD total value: ${esvd_results.get('total_value', 0):,.2f}")
    print()
    
    # Test the full pipeline
    print("4. Full EcosystemServicesCalculator Pipeline:")
    try:
        # Test with Agricultural ecosystem intactness (like the app would have)
        ecosystem_intactness = {'Agricultural': 100.0}
        
        result = calculator.calculate_ecosystem_services_value(
            satellite_data=mock_satellite_data,
            area_bounds=mock_area_bounds,
            ecosystem_type='agricultural',
            quality_factor=1.0,
            ecosystem_intactness=ecosystem_intactness,
            urban_green_blue_multiplier=0.15
        )
        
        if 'error' in result:
            print(f"   ERROR: {result['error']}")
        else:
            current_value = result.get('current_value', 0)
            services_time_series = result.get('services_time_series', [])
            
            print(f"   Total Current Value: ${current_value:,.2f}")
            print(f"   Number of time series points: {len(services_time_series)}")
            
            if services_time_series:
                latest_point = services_time_series[-1]
                provisioning = latest_point.get('provisioning', {})
                food_value = provisioning.get('food', 0)
                total_provisioning = provisioning.get('total', 0)
                
                print(f"   Latest food service value: ${food_value:,.2f}")
                print(f"   Latest total provisioning: ${total_provisioning:,.2f}")
                print(f"   Area used in calculation: {latest_point.get('area_hectares', 0):,.2f} ha")
                
                # Diagnostic: Check what multipliers were applied
                # Compare the ESVD base value vs final value to see what happened
                print(f"\n   Diagnostic:")
                print(f"   ESVD base food value: ${esvd_food_value:,.2f}")
                print(f"   Final food value: ${food_value:,.2f}")
                if esvd_food_value > 0:
                    ratio = food_value / esvd_food_value
                    print(f"   Ratio (final/base): {ratio:.6f}")
                    print(f"   Expected with vegetation factor: {ratio / vegetation_factor:.6f}")
                
                # Check all provisioning services
                print(f"\n   All provisioning services:")
                for service, value in provisioning.items():
                    if service != 'total' and value > 0:
                        print(f"     {service}: ${value:,.2f}")
                
    except Exception as e:
        print(f"   ERROR in calculation: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n5. Test _apply_esvd_values directly:")
    try:
        # Test the specific method that applies NDVI adjustments
        esvd_provisioning = esvd_results.get('provisioning', {}).get('services', {})
        data_point = mock_satellite_data['time_series'][0]
        quality_multiplier = 1.0  # 100% intactness
        
        adjusted_values = calculator._apply_esvd_values(esvd_provisioning, quality_multiplier, data_point)
        print(f"   Adjusted food value: ${adjusted_values.get('food', 0):,.2f}")
        print(f"   Adjusted total: ${adjusted_values.get('total', 0):,.2f}")
        
        # Check if food is properly categorized as provisioning
        print(f"   Food in provisioning category: {'food' in calculator.service_categories['provisioning']}")
        
    except Exception as e:
        print(f"   ERROR in _apply_esvd_values test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_pipeline()