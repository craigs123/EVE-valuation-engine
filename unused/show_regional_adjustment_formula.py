#!/usr/bin/env python3
"""
Demonstration of Regional Adjustment Formula with Authentic 2020 World Bank Data
"""

from utils.precomputed_esvd_coefficients import PrecomputedESVDCoefficients

def demonstrate_regional_adjustments():
    """Show how regional adjustment works with authentic 2020 World Bank GDP data"""
    
    print("🌍 ECOSYSTEM VALUATION ENGINE - REGIONAL ADJUSTMENT FORMULA")
    print("=" * 70)
    print()
    
    # Initialize with default elasticity
    esvd = PrecomputedESVDCoefficients(income_elasticity=0.6)
    
    print("📊 AUTHENTIC 2020 WORLD BANK GDP DATA:")
    print("Source: World Bank World Development Indicators Database")
    print("GDP per capita (current US$), regional averages")
    print()
    
    regions = [
        ("North America", (37.7749, -122.4194)),  # San Francisco
        ("Europe", (52.5200, 13.4050)),            # Berlin  
        ("Asia-Pacific Dev", (-33.8688, 151.2093)),  # Sydney
        ("Asia Emerging", (39.9042, 116.4074)),    # Beijing
        ("Latin America", (-23.5505, -46.6333)),   # São Paulo
        ("Africa", (-1.2921, 36.8219))             # Nairobi
    ]
    
    print("REGION                GDP/CAPITA    ADJUSTMENT   EXAMPLE")
    print("-" * 65)
    
    base_value = 1000  # $1000/ha ecosystem service value
    
    for region_name, coordinates in regions:
        regional_gdp = esvd.get_regional_gdp(coordinates)
        adjustment = esvd.get_regional_factor(coordinates)
        adjusted_value = base_value * adjustment
        
        print(f"{region_name:<17} ${regional_gdp:>8,.0f}      {adjustment:.2f}x     ${adjusted_value:>6.0f}/ha")
    
    print()
    print("📐 REGIONAL ADJUSTMENT FORMULA:")
    print("Adjustment Factor = 1 + (Income Elasticity × (Regional GDP / Global GDP - 1))")
    print()
    print("WHERE:")
    print(f"• Global GDP Average (2020): ${esvd.regional_gdp_data['global_average']:,}")
    print(f"• Income Elasticity: {esvd.income_elasticity} (user-configurable)")
    print("• Bounds: 0.4x to 2.5x (prevents extreme adjustments)")
    print()
    
    print("🔬 SCIENTIFIC BASIS:")
    print("• Income Elasticity of Willingness to Pay method")
    print("• Literature suggests 0.5-0.6 elasticity for environmental services")
    print("• Accounts for regional purchasing power differences")
    print("• Maintains global research authenticity from ESVD database")
    print()
    
    # Demonstrate formula calculation
    na_coordinates = (37.7749, -122.4194)
    regional_gdp = esvd.get_regional_gdp(na_coordinates)
    global_gdp = esvd.regional_gdp_data['global_average']
    elasticity = esvd.income_elasticity
    
    print("💡 FORMULA EXAMPLE (North America):")
    print(f"Regional GDP: ${regional_gdp:,}")
    print(f"Global GDP: ${global_gdp:,}")
    print(f"GDP Ratio: {regional_gdp/global_gdp:.2f}")
    print(f"Income Elasticity: {elasticity}")
    print(f"Calculation: 1 + ({elasticity} × ({regional_gdp/global_gdp:.2f} - 1))")
    print(f"            = 1 + ({elasticity} × {regional_gdp/global_gdp - 1:.2f})")
    print(f"            = 1 + {elasticity * (regional_gdp/global_gdp - 1):.2f}")
    print(f"            = {1 + elasticity * (regional_gdp/global_gdp - 1):.2f}")
    
    bounded_result = max(0.4, min(2.5, 1 + elasticity * (regional_gdp/global_gdp - 1)))
    print(f"Bounded Result: {bounded_result:.2f}x")
    print()
    
    print("✅ DATA INTEGRITY ASSURANCE:")
    print("• GDP data sourced from World Bank official statistics")
    print("• 2020 vintage aligns with ESVD Int$ baseline year")
    print("• Regional boundaries follow World Bank classifications")
    print("• Methodology documented in peer-reviewed literature")

if __name__ == "__main__":
    demonstrate_regional_adjustments()