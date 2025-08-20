#!/usr/bin/env python3
"""
Quality Factor Input Demo
Shows the satellite-based quality factors used to adjust ESVD coefficients
"""

import numpy as np
from utils.precomputed_esvd_coefficients import get_precomputed_coefficients

def demo_quality_adjustments():
    print("🛰️ Ecosystem Quality Factor Demonstration")
    print("="*50)
    
    # Get pre-computed coefficients
    coefficients = get_precomputed_coefficients()
    
    # Demo area and ecosystem
    test_area_ha = 100
    test_ecosystem = 'forest'
    test_coordinates = (40.7128, -74.0060)  # New York coordinates
    
    print(f"\nTest Area: {test_area_ha} hectares of {test_ecosystem}")
    print(f"Location: {test_coordinates}")
    
    # Calculate base values
    base_values = coefficients.calculate_ecosystem_values(
        test_ecosystem, test_area_ha, test_coordinates
    )
    
    print(f"\nBase Values (before quality adjustment):")
    print(f"Climate Regulation: ${base_values['regulating']['climate_regulation']:,.0f}/year")
    print(f"Food Production: ${base_values['provisioning']['food_production']:,.0f}/year")
    print(f"Recreation: ${base_values['cultural']['recreation']:,.0f}/year")
    print(f"Total Annual Value: ${base_values['total_annual_value']:,.0f}/year")
    
    # Demonstrate quality factor effects
    print(f"\n" + "="*50)
    print("Quality Factor Effects on Values:")
    print("-"*30)
    
    quality_scenarios = {
        'Excellent (Pristine)': 1.2,     # 20% bonus
        'Good (Healthy)': 1.0,           # No adjustment  
        'Fair (Degraded)': 0.8,          # 20% reduction
        'Poor (Severely Degraded)': 0.4  # 60% reduction
    }
    
    base_climate = base_values['regulating']['climate_regulation']
    
    for scenario, multiplier in quality_scenarios.items():
        adjusted_climate = base_climate * multiplier
        adjusted_total = base_values['total_annual_value'] * multiplier
        
        print(f"{scenario:25} | Climate: ${adjusted_climate:>8,.0f} | Total: ${adjusted_total:>10,.0f}")
    
    print(f"\n" + "="*50)
    print("Quality Factor Components:")
    print("-"*25)
    print("NDVI (Vegetation Health): 40% weight")
    print("Data Quality: 30% weight") 
    print("Cloud Coverage: 20% weight")
    print("Spectral Health: 10% weight")
    print("\nQuality multiplier range: 0.4x - 1.2x")
    
    print(f"\n" + "="*50)
    print("Performance Benefits:")
    print("-"*20)
    print("✅ Instant coefficient lookup (no database queries)")
    print("✅ Pre-calculated medians from 10,874+ studies")
    print("✅ Maintains authentic research-based values")
    print("✅ Regional adjustments included")
    print("✅ Quality adjustments applied at runtime only")

if __name__ == "__main__":
    demo_quality_adjustments()