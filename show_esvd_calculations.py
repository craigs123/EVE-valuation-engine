"""
Show how EVE calculates actual ecosystem values using authentic ESVD data
"""

from utils.authentic_esvd_loader import get_esvd_loader
import pandas as pd

def show_calculation_example():
    """Demonstrate actual ESVD calculations for a forest ecosystem"""
    
    print("=" * 70)
    print("EVE CALCULATION EXAMPLE - AUTHENTIC ESVD VALUES")
    print("=" * 70)
    
    # Load ESVD data
    loader = get_esvd_loader()
    
    # Get summary
    summary = loader.get_data_summary()
    print(f"Database Status: {summary['status']}")
    print(f"Total Records: {summary['total_records']:,}")
    print(f"Unique Studies: {summary['unique_studies']:,}")
    print()
    
    # Example: Calculate Forest ecosystem values
    ecosystem_type = "forest"
    area_hectares = 100  # 100 hectare forest
    
    print(f"EXAMPLE: {area_hectares} hectare {ecosystem_type.upper()} ecosystem")
    print("-" * 50)
    
    # Get values for each service category
    service_categories = ['provisioning', 'regulating', 'cultural', 'supporting']
    
    total_value = 0
    breakdown = {}
    
    for service in service_categories:
        values = loader.get_values_for_ecosystem_service(ecosystem_type, service)
        
        if values:
            avg_per_ha = sum(values) / len(values)
            total_for_service = avg_per_ha * area_hectares
            total_value += total_for_service
            breakdown[service] = {
                'per_ha': avg_per_ha,
                'total': total_for_service,
                'records': len(values)
            }
            
            print(f"{service.capitalize()} Services:")
            print(f"  Records found: {len(values)}")
            print(f"  Average value: ${avg_per_ha:,.0f}/ha/year")
            print(f"  Total for {area_hectares}ha: ${total_for_service:,.0f}/year")
            print(f"  Sample values: ${values[0]:.0f}, ${values[1] if len(values)>1 else 0:.0f}, ${values[2] if len(values)>2 else 0:.0f}/ha/year")
            print()
        else:
            print(f"{service.capitalize()} Services: No authentic values found")
            print()
    
    print("=" * 50)
    print(f"TOTAL ECOSYSTEM VALUE: ${total_value:,.0f}/year")
    print(f"PER HECTARE VALUE: ${total_value/area_hectares:,.0f}/ha/year")
    print()
    print("This calculation uses ONLY authentic peer-reviewed values")
    print("from the ESVD database - no estimated coefficients!")
    print("=" * 70)

if __name__ == "__main__":
    show_calculation_example()