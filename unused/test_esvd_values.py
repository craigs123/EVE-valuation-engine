"""
Test authentic ESVD ecosystem service values
"""

import sys
sys.path.append('.')

from utils.esvd_integration import calculate_ecosystem_services_value

# Test with Colorado coordinates (39°N, 105°W) - Grassland
print("Testing ESVD ecosystem service values...")
print("Location: Colorado (39°N, 105°W)")
print("Ecosystem: Grassland")
print("Area: 1000 hectares")

results = calculate_ecosystem_services_value(
    ecosystem_type="Grassland",
    area_hectares=1000,
    coordinates=(39.0, -105.0)
)

print("\n=== ESVD Results ===")
print(f"Total Value: ${results['metadata']['total_value']:,.0f}/year")
print(f"Value per Hectare: ${results['metadata']['value_per_hectare']:.0f}/ha/year")
print(f"Regional Factor: {results['metadata']['regional_adjustment']:.2f}")
print(f"Data Source: {results['metadata']['data_source']}")

print("\n=== Service Category Breakdown ===")
categories = ['provisioning', 'regulating', 'cultural', 'supporting']
for category in categories:
    if category in results:
        total = results[category]['total']
        percentage = (total / results['metadata']['total_value'] * 100) if results['metadata']['total_value'] > 0 else 0
        print(f"{category.title()}: ${total:,.0f}/year ({percentage:.0f}%)")

print("\n=== Detailed Service Values ===")
for category in categories:
    if category in results:
        print(f"\n{category.title()} Services:")
        for service, value in results[category].items():
            if service != 'total' and value > 0:
                print(f"  {service.replace('_', ' ').title()}: ${value:,.0f}/year")