#!/usr/bin/env python3
"""
Demonstration of Country-Specific Regional Adjustment with Authentic 2020 World Bank GDP Data
"""

from utils.precomputed_esvd_coefficients import PrecomputedESVDCoefficients, get_country_from_coordinates

def demonstrate_country_specific_adjustments():
    """Show how country-specific adjustment works with authentic 2020 World Bank GDP data"""
    
    print("🌍 ECOSYSTEM VALUATION ENGINE - COUNTRY-SPECIFIC ADJUSTMENTS")
    print("=" * 75)
    print()
    
    # Initialize with default elasticity
    esvd = PrecomputedESVDCoefficients(income_elasticity=0.6)
    
    print("📊 AUTHENTIC 2020 WORLD BANK GDP DATA (Country-Specific):")
    print("Source: World Bank World Development Indicators Database")
    print("GDP per capita (current US$), individual country values")
    print()
    
    locations = [
        ("San Francisco, USA", (37.7749, -122.4194)),
        ("Toronto, Canada", (43.6532, -79.3832)),
        ("Mexico City, Mexico", (19.4326, -99.1332)),
        ("Berlin, Germany", (52.5200, 13.4050)),
        ("Paris, France", (48.8566, 2.3522)),
        ("London, UK", (51.5074, -0.1278)),
        ("Madrid, Spain", (40.4168, -3.7038)),
        ("Tokyo, Japan", (35.6762, 139.6503)),
        ("Sydney, Australia", (-33.8688, 151.2093)),
        ("Seoul, S. Korea", (37.5665, 126.9780)),
        ("Beijing, China", (39.9042, 116.4074)),
        ("Mumbai, India", (19.0760, 72.8777)),
        ("Bangkok, Thailand", (13.7563, 100.5018)),
        ("São Paulo, Brazil", (-23.5505, -46.6333)),
        ("Buenos Aires, Argentina", (-34.6118, -58.3960)),
        ("Nairobi, Kenya", (-1.2921, 36.8219)),
        ("Lagos, Nigeria", (6.5244, 3.3792)),
        ("Cape Town, S. Africa", (-33.9249, 18.4241))
    ]
    
    print("LOCATION                COUNTRY           GDP/CAPITA    ADJUSTMENT   EXAMPLE")
    print("-" * 75)
    
    base_value = 1000  # $1000/ha ecosystem service value
    
    for location_name, coordinates in locations:
        country_code = get_country_from_coordinates(coordinates[0], coordinates[1])
        country_gdp = esvd.get_country_gdp(coordinates)
        adjustment = esvd.get_regional_factor(coordinates)
        adjusted_value = base_value * adjustment
        
        # Format country code for display
        country_display = country_code.replace('_', ' ').title()
        
        print(f"{location_name:<20} {country_display:<15} ${country_gdp:>8,.0f}      {adjustment:.2f}x     ${adjusted_value:>6.0f}/ha")
    
    print()
    print("📐 COUNTRY-SPECIFIC ADJUSTMENT FORMULA:")
    print("Adjustment Factor = 1 + (Income Elasticity × (Country GDP / Global GDP - 1))")
    print()
    print("WHERE:")
    print(f"• Global GDP Average (2020): ${esvd.global_gdp_average:,}")
    print(f"• Income Elasticity: {esvd.income_elasticity} (user-configurable)")
    print("• Bounds: 0.4x to 2.5x (prevents extreme adjustments)")
    print()
    
    print("🔬 IMPROVEMENTS OVER REGIONAL AVERAGES:")
    print("• USA ($63,593) vs North America average ($63,543)")
    print("• Germany ($46,259) vs Europe average ($38,420)")
    print("• China ($10,500) vs Asia Emerging average ($7,348)")
    print("• Kenya ($1,838) vs Africa average ($1,739)")
    print()
    
    print("✅ DATA ACCURACY BENEFITS:")
    print("• Country-specific precision instead of broad regional estimates")
    print("• Authentic World Bank GDP data for each nation")
    print("• Geographic boundary mapping to countries")
    print("• Maintains scientific rigor with real economic data")
    print()
    
    # Show some calculation examples
    print("💡 CALCULATION EXAMPLES:")
    print()
    
    # USA example
    usa_coords = (37.7749, -122.4194)
    usa_gdp = esvd.get_country_gdp(usa_coords)
    usa_ratio = usa_gdp / esvd.global_gdp_average
    usa_calc = 1 + (esvd.income_elasticity * (usa_ratio - 1))
    usa_bounded = max(0.4, min(2.5, usa_calc))
    
    print("🇺🇸 USA (San Francisco):")
    print(f"GDP: ${usa_gdp:,} | Ratio: {usa_ratio:.2f} | Raw: {usa_calc:.2f} | Final: {usa_bounded:.2f}x")
    
    # Kenya example
    kenya_coords = (-1.2921, 36.8219)
    kenya_gdp = esvd.get_country_gdp(kenya_coords)
    kenya_ratio = kenya_gdp / esvd.global_gdp_average
    kenya_calc = 1 + (esvd.income_elasticity * (kenya_ratio - 1))
    kenya_bounded = max(0.4, min(2.5, kenya_calc))
    
    print("🇰🇪 Kenya (Nairobi):")
    print(f"GDP: ${kenya_gdp:,} | Ratio: {kenya_ratio:.2f} | Raw: {kenya_calc:.2f} | Final: {kenya_bounded:.2f}x")

if __name__ == "__main__":
    demonstrate_country_specific_adjustments()