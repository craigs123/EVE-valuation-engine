#!/usr/bin/env python3
"""
Debug the specific ESVD calculation issue
"""

from utils.precomputed_esvd_coefficients import get_precomputed_coefficients

def debug_esvd_calculation():
    print("=== Debugging ESVD Calculation ===\n")
    
    precomputed = get_precomputed_coefficients()
    
    # Test 1: Check the service_categories structure
    print("1. Service Categories Structure:")
    print("   Provisioning services:", precomputed.service_categories.get('provisioning', {}))
    print()
    
    # Test 2: Check agricultural coefficients directly
    print("2. Agricultural Coefficients:")
    agri_coeffs = precomputed.get_ecosystem_coefficients('agricultural')
    for service, coeff in agri_coeffs.items():
        print(f"   {service}: {coeff}")
    print()
    
    # Test 3: Test individual coefficient lookup
    print("3. Individual Coefficient Lookups:")
    food_coeff = precomputed.get_coefficient('agricultural', 'food')
    print(f"   get_coefficient('agricultural', 'food'): {food_coeff}")
    
    # Test with the ESVD service name mapping
    provisioning_services = precomputed.service_categories.get('provisioning', {})
    for service_name, esvd_key in provisioning_services.items():
        coeff = precomputed.get_coefficient('agricultural', esvd_key)
        print(f"   get_coefficient('agricultural', '{esvd_key}'): {coeff} (service: {service_name})")
    print()
    
    # Test 4: Step-by-step calculation
    print("4. Step-by-step Manual Calculation:")
    ecosystem_type = 'agricultural'
    area_hectares = 1000.0
    coordinates = None
    
    regional_factor = precomputed.get_regional_factor(coordinates)
    print(f"   Regional factor: {regional_factor}")
    
    # Check the actual calculation loop
    results = {}
    total_value = 0
    
    for category, services in precomputed.service_categories.items():
        print(f"\n   Processing category: {category}")
        category_total = 0
        category_services = {}
        
        for service, esvd_service in services.items():
            coefficient = precomputed.get_coefficient(ecosystem_type, esvd_service, coordinates)
            value = coefficient * area_hectares * regional_factor
            
            print(f"     {service} -> {esvd_service}: coeff={coefficient}, value=${value:,.2f}")
            
            category_services[service] = value
            category_total += value
        
        results[category] = {
            'services': category_services,
            'total': category_total
        }
        total_value += category_total
        print(f"   Category total: ${category_total:,.2f}")
    
    print(f"\n   Final total value: ${total_value:,.2f}")
    
    # Test 5: Compare with the actual method
    print("\n5. Actual Method Result:")
    actual_result = precomputed.calculate_ecosystem_values('agricultural', 1000.0, None, 0.15)
    print(f"   Total Value: ${actual_result.get('total_value', 0):,.2f}")
    
    provisioning = actual_result.get('provisioning', {})
    print(f"   Provisioning structure: {type(provisioning)}")
    print(f"   Provisioning keys: {list(provisioning.keys()) if isinstance(provisioning, dict) else 'Not a dict'}")
    
    if isinstance(provisioning, dict):
        if 'services' in provisioning:
            food_value = provisioning['services'].get('food', 0)
            print(f"   Food value (from services): ${food_value:,.2f}")
        else:
            food_value = provisioning.get('food', 0)
            print(f"   Food value (direct): ${food_value:,.2f}")

if __name__ == "__main__":
    debug_esvd_calculation()