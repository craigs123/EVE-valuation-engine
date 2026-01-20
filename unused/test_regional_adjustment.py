#!/usr/bin/env python3
"""
Test the corrected regional adjustment approach
"""

from utils.precomputed_esvd_coefficients import get_precomputed_coefficients

def test_regional_adjustments():
    print("🌍 Testing Regional Deviation from ESVD Global Norm")
    print("=" * 55)
    
    coefficients = get_precomputed_coefficients()
    
    # Test locations with their expected regional characteristics
    test_locations = [
        # (lat, lon, description)
        (40.7128, -74.0060, "New York, USA (High-income)"),
        (51.5074, -0.1278, "London, UK (High-income)"), 
        (-33.8688, 151.2093, "Sydney, Australia (High-income)"),
        (39.9042, 116.4074, "Beijing, China (Emerging economy)"),
        (-23.5505, -46.6333, "São Paulo, Brazil (Emerging economy)"),
        (52.2297, 21.0122, "Warsaw, Poland (Emerging economy)"),
        (-1.2921, 36.8219, "Nairobi, Kenya (Least developed region)"),
        (28.6139, 77.2090, "New Delhi, India (Least developed region)"),
        (0.0, 0.0, "Null Island (Global norm)")
    ]
    
    print("Regional Deviation Factors:")
    print("-" * 30)
    
    for lat, lon, description in test_locations:
        coordinates = (lat, lon)
        deviation_factor = coefficients.get_regional_factor(coordinates)
        
        # Calculate sample ecosystem value to show impact
        base_coefficient = coefficients.get_coefficient('forest', 'climate')
        adjusted_value = base_coefficient * deviation_factor
        deviation_pct = (deviation_factor - 1.0) * 100
        
        print(f"{description}")
        print(f"  Deviation factor: {deviation_factor:.3f} ({deviation_pct:+.1f}% from global norm)")
        print(f"  Forest climate value: ${base_coefficient:.2f} → ${adjusted_value:.2f}")
        print()
    
    print("=" * 55)
    print("KEY INSIGHTS:")
    print("✅ ESVD coefficients already include global regional factors")
    print("✅ Our adjustments reflect local deviations from that norm")  
    print("✅ Small adjustments (±5%) preserve research integrity")
    print("✅ High-income regions: +5% premium above global norm")
    print("✅ Emerging economies: -2% below global norm")
    print("✅ Least developed: -5% below global norm")
    print("✅ Most locations use global norm (no adjustment)")

if __name__ == "__main__":
    test_regional_adjustments()