#!/usr/bin/env python3
"""
Test the adapted regional adjustment method using GDP and income elasticity
"""

from utils.precomputed_esvd_coefficients import get_precomputed_coefficients

def test_adapted_method():
    print("🔄 Testing Adapted Regional Method (GDP + Income Elasticity)")
    print("=" * 65)
    
    coefficients = get_precomputed_coefficients()
    
    # Test locations
    test_locations = [
        # (lat, lon, description, expected_region)
        (40.7128, -74.0060, "New York, USA", "North America"),
        (51.5074, -0.1278, "London, UK", "Europe"), 
        (-33.8688, 151.2093, "Sydney, Australia", "Asia-Pacific Developed"),
        (39.9042, 116.4074, "Beijing, China", "Emerging Asia"),
        (-23.5505, -46.6333, "São Paulo, Brazil", "Latin America"),
        (-1.2921, 36.8219, "Nairobi, Kenya", "Africa"),
        (0.0, 0.0, "Global Average", "Global")
    ]
    
    print("REGIONAL GDP AND ADJUSTMENT FACTORS:")
    print("-" * 40)
    
    base_coefficient = coefficients.get_coefficient('forest', 'climate')
    
    for lat, lon, description, region in test_locations:
        coordinates = (lat, lon)
        
        # Get regional data
        regional_gdp = coefficients.get_regional_gdp(coordinates)
        regional_factor = coefficients.get_regional_factor(coordinates)
        adjusted_value = base_coefficient * regional_factor
        
        print(f"{description} ({region}):")
        print(f"  GDP per capita: ${regional_gdp:,}")
        print(f"  Regional factor: {regional_factor:.3f}")
        print(f"  Forest climate: ${base_coefficient:.2f} → ${adjusted_value:.2f}")
        print()
    
    print("=" * 65)
    print("METHOD COMPARISON:")
    print("-" * 17)
    print("✅ ADAPTED METHOD:")
    print("   - Uses GDP per capita by region (previous working method)")
    print("   - Applies income elasticity of 0.25 (literature-based)")
    print("   - Treats ESVD coefficients as global baseline")
    print("   - Formula: (Regional_GDP / Global_GDP) ^ 0.25")
    print("   - Bounded between 0.5x and 2.0x for safety")
    print()
    print("📊 INCOME ELASTICITY IMPACT:")
    print(f"   - North America (${coefficients.regional_gdp_data['north_america']:,}): {coefficients.get_regional_factor((45, -100)):.3f}x")
    print(f"   - Europe (${coefficients.regional_gdp_data['europe']:,}): {coefficients.get_regional_factor((50, 10)):.3f}x") 
    print(f"   - Africa (${coefficients.regional_gdp_data['africa']:,}): {coefficients.get_regional_factor((0, 20)):.3f}x")
    print(f"   - Global baseline (${coefficients.regional_gdp_data['global_average']:,}): 1.000x")

if __name__ == "__main__":
    test_adapted_method()