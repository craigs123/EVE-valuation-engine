#!/usr/bin/env python3
"""
Display All Precalculated ESVD Values
Shows comprehensive ecosystem service values from authentic ESVD database
"""

from utils.precomputed_esvd_coefficients import PrecomputedESVDCoefficients

def display_all_esvd_values():
    """Display all precalculated ESVD values"""
    
    print("=" * 80)
    print("🌱 ALL PRECALCULATED ESVD VALUES")
    print("Authentic ESVD Database - APR2024 V1.1 (10,874+ records)")
    print("Values in International $/ha/year (2020 price levels)")
    print("=" * 80)
    
    # Initialize the coefficients calculator
    esvd = PrecomputedESVDCoefficients()
    
    print("\n📊 COMPLETE ESVD COEFFICIENT MATRIX BY ECOSYSTEM TYPE:")
    print("-" * 80)
    
    # Display all ecosystem types and their values
    for ecosystem_type, services in esvd.coefficients.items():
        print(f"\n🌿 {ecosystem_type.replace('_', ' ').upper()} ECOSYSTEM:")
        print("-" * 60)
        
        # Calculate total value
        total_value = sum(services.values())
        print(f"Total Ecosystem Value: ${total_value:,.0f}/ha/year")
        print()
        
        # Display services in organized groups
        service_groups = {
            'Provisioning Services': ['food', 'water', 'timber'],
            'Regulating Services': ['climate', 'water_regulation', 'erosion', 'pollution'],
            'Cultural Services': ['recreation', 'cultural'],
            'Supporting Services': ['habitat']
        }
        
        for group_name, group_services in service_groups.items():
            group_total = 0
            print(f"  {group_name}:")
            for service in group_services:
                if service in services:
                    value = services[service]
                    group_total += value
                    print(f"    • {service.replace('_', ' ').title():.<25} ${value:>8,.2f}/ha/year")
            print(f"    {'GROUP TOTAL':.<25} ${group_total:>8,.0f}/ha/year")
            print()
        
        print(f"  {'ECOSYSTEM TOTAL':.<25} ${total_value:>8,.0f}/ha/year")
        print("=" * 60)
    
    print("\n🌳 FOREST TYPE BREAKDOWN:")
    print("-" * 80)
    
    forest_types = ['tropical_forest', 'temperate_forest', 'boreal_forest', 'mediterranean_forest']
    print("Forest ecosystems are automatically classified by geographic coordinates:")
    print()
    
    for forest_type in forest_types:
        if forest_type in esvd.coefficients:
            services = esvd.coefficients[forest_type]
            total_value = sum(services.values())
            
            climate_zone = forest_type.replace('_forest', '').title()
            print(f"🌲 {climate_zone} Forest:")
            print(f"   Total Value: ${total_value:,.0f}/ha/year")
            
            # Show top 3 services
            top_services = sorted(services.items(), key=lambda x: x[1], reverse=True)[:3]
            print("   Top Services:")
            for service, value in top_services:
                print(f"     • {service.replace('_', ' ').title()}: ${value:,.0f}/ha/year")
            print()
    
    print("\n📈 VALUE COMPARISON BY ECOSYSTEM TYPE:")
    print("-" * 80)
    
    # Calculate and display ecosystem totals
    ecosystem_totals = []
    for ecosystem_type, services in esvd.coefficients.items():
        total_value = sum(services.values())
        ecosystem_totals.append((ecosystem_type, total_value))
    
    # Sort by total value (descending)
    ecosystem_totals.sort(key=lambda x: x[1], reverse=True)
    
    print("Ranked by total ecosystem service value:")
    print()
    
    for rank, (ecosystem_type, total_value) in enumerate(ecosystem_totals, 1):
        ecosystem_name = ecosystem_type.replace('_', ' ').title()
        print(f"{rank:2d}. {ecosystem_name:.<25} ${total_value:>8,.0f}/ha/year")
    
    print("\n🔍 HIGHEST VALUE SERVICES ACROSS ALL ECOSYSTEMS:")
    print("-" * 80)
    
    # Find highest value services
    all_services = []
    for ecosystem_type, services in esvd.coefficients.items():
        for service_type, value in services.items():
            all_services.append((value, ecosystem_type, service_type))
    
    # Sort by value (descending) and show top 10
    all_services.sort(reverse=True)
    
    print("Top 10 highest individual service values:")
    print()
    
    for rank, (value, ecosystem_type, service_type) in enumerate(all_services[:10], 1):
        ecosystem_name = ecosystem_type.replace('_', ' ').title()
        service_name = service_type.replace('_', ' ').title()
        print(f"{rank:2d}. {service_name} ({ecosystem_name}): ${value:,.2f}/ha/year")
    
    print("\n📋 SERVICE CATEGORY DEFINITIONS:")
    print("-" * 80)
    
    descriptions = {
        'Provisioning Services': 'Direct products from ecosystems',
        'Regulating Services': 'Benefits from ecosystem processes',
        'Cultural Services': 'Non-material benefits from ecosystems',
        'Supporting Services': 'Services necessary for other ecosystem services'
    }
    
    for category, description in descriptions.items():
        print(f"• {category}: {description}")
    
    print("\n📊 DATABASE STATISTICS:")
    print("-" * 80)
    
    total_coefficients = sum(len(services) for services in esvd.coefficients.values())
    ecosystem_count = len(esvd.coefficients)
    all_values = [value for services in esvd.coefficients.values() for value in services.values()]
    
    print(f"Total Ecosystem Types: {ecosystem_count}")
    print(f"Total Service Coefficients: {total_coefficients}")
    print(f"Average Coefficient Value: ${sum(all_values)/len(all_values):,.0f}/ha/year")
    print(f"Minimum Coefficient Value: ${min(all_values):,.0f}/ha/year")
    print(f"Maximum Coefficient Value: ${max(all_values):,.0f}/ha/year")
    
    print("\n📖 DATA SOURCE AND METHODOLOGY:")
    print("-" * 80)
    print("• Source: Foundation for Sustainable Development ESVD Database")
    print("• Version: APR2024 V1.1")
    print("• Studies: 10,874+ peer-reviewed research papers")
    print("• Method: Median values from multiple studies per service")
    print("• Currency: International $ (2020 price levels)")
    print("• Regional Adjustments: GDP-based income elasticity method")
    print("• Quality Control: Peer-reviewed studies only")
    print("=" * 80)

if __name__ == "__main__":
    display_all_esvd_values()