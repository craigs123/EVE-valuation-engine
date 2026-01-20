"""
EVE - Ecosystem Valuation Engine ESVD Integration Demonstration
Shows exactly how authentic ESVD values are used by ecosystem type and service
"""

import pandas as pd
import numpy as np

def demonstrate_esvd_usage():
    """Show how EVE uses authentic ESVD values by ecosystem and service"""
    
    # Load authentic ESVD database
    data = pd.read_csv('attached_assets/Esvd_Full_Data_20th-Aug-2025_16-21-52_Database_Version_APR2024V1.1_1755703899941.csv', low_memory=False)
    
    print("=" * 80)
    print("EVE - ECOSYSTEM VALUATION ENGINE")
    print("AUTHENTIC ESVD INTEGRATION DEMONSTRATION")
    print("=" * 80)
    print(f"Database: ESVD APR2024 V1.1")
    print(f"Total Records: {len(data):,}")
    print(f"Unique Studies: {data['StudyId'].nunique():,}")
    print(f"Value Column: 'Int$ Per Hectare Per Year' (2020 price levels)")
    print()
    
    # Define ecosystem mappings used by EVE
    ecosystem_mappings = {
        'Forest': ['Tropical and subtropical forests', 'Temperate forest and woodland'],
        'Wetland': ['Inland wetlands', 'Coastal systems'],
        'Grassland': ['Rangelands and natural grasslands'],
        'Agricultural': ['Intensive land use'],
        'Coastal': ['Marine', 'Coastal systems'],
        'Urban': ['Urban green and blue infrastructure']
    }
    
    # Define service mappings used by EVE
    service_mappings = {
        'Provisioning': ['food', 'timber', 'water', 'provision', 'fisheries', 'raw materials'],
        'Regulating': ['climate', 'carbon', 'regulation', 'air quality', 'pollution', 'sequestration'],
        'Cultural': ['recreation', 'aesthetic', 'cultural', 'tourism', 'landscape'],
        'Supporting': ['habitat', 'biodiversity', 'soil', 'nutrient', 'primary production']
    }
    
    print("🌍 HOW EVE MAPS ECOSYSTEM TYPES TO AUTHENTIC ESVD VALUES:")
    print("-" * 60)
    
    for eve_ecosystem, esvd_biomes in ecosystem_mappings.items():
        print(f"\n{eve_ecosystem.upper()} ECOSYSTEM:")
        
        # Get all records for this ecosystem type
        ecosystem_mask = data['ESVD2.0_Biome'].isin(esvd_biomes)
        ecosystem_data = data[ecosystem_mask]
        
        print(f"  ESVD Biomes: {', '.join(esvd_biomes)}")
        print(f"  Total Records: {len(ecosystem_data):,}")
        
        if len(ecosystem_data) > 0:
            avg_value = ecosystem_data['Int$ Per Hectare Per Year'].mean()
            median_value = ecosystem_data['Int$ Per Hectare Per Year'].median()
            min_value = ecosystem_data['Int$ Per Hectare Per Year'].min()
            max_value = ecosystem_data['Int$ Per Hectare Per Year'].max()
            
            print(f"  Average Value: ${avg_value:,.0f}/ha/year")
            print(f"  Median Value: ${median_value:,.0f}/ha/year")
            print(f"  Range: ${min_value:,.0f} - ${max_value:,.0f}/ha/year")
            
            # Show service breakdown for this ecosystem
            print(f"  Service Breakdown:")
            for service_category, service_terms in service_mappings.items():
                service_pattern = '|'.join(service_terms)
                service_mask = ecosystem_data['ES_Text'].str.contains(service_pattern, case=False, na=False)
                service_data = ecosystem_data[service_mask]
                
                if len(service_data) > 0:
                    service_avg = service_data['Int$ Per Hectare Per Year'].mean()
                    print(f"    {service_category}: ${service_avg:,.0f}/ha/year ({len(service_data)} records)")
    
    print("\n" + "=" * 80)
    print("📊 SAMPLE AUTHENTIC ESVD RECORDS USED BY EVE:")
    print("-" * 60)
    
    # Show specific examples from different ecosystems
    examples = [
        ('Forest', 'Carbon sequestration', 'Regulating'),
        ('Wetland', 'Recreation', 'Cultural'),
        ('Agricultural', 'Pollination', 'Regulating'),
        ('Urban', 'Air quality', 'Regulating')
    ]
    
    for ecosystem, service_example, category in examples:
        esvd_biomes = ecosystem_mappings.get(ecosystem, [])
        if esvd_biomes:
            ecosystem_mask = data['ESVD2.0_Biome'].isin(esvd_biomes)
            service_mask = data['ES_Text'].str.contains(service_example, case=False, na=False)
            example_data = data[ecosystem_mask & service_mask].head(3)
            
            if len(example_data) > 0:
                print(f"\n{ecosystem} - {service_example} ({category} Services):")
                for _, row in example_data.iterrows():
                    value = row['Int$ Per Hectare Per Year']
                    study_id = row['StudyId']
                    country = row.get('Countries', 'Unknown')
                    year = row.get('Year_Pub', 'Unknown')
                    print(f"  ${value:,.0f}/ha/year | Study {study_id} | {country} | {year}")
    
    print("\n" + "=" * 80)
    print("🔬 EVE METHODOLOGY - AUTHENTIC DATA INTEGRATION:")
    print("-" * 60)
    print("1. User selects area → EVE detects ecosystem type")
    print("2. EVE maps detected type to ESVD biome categories")
    print("3. EVE retrieves authentic values for that ecosystem")
    print("4. EVE filters by service categories (Provisioning, Regulating, Cultural, Supporting)")
    print("5. EVE calculates weighted averages based on peer-reviewed studies")
    print("6. EVE applies regional adjustments using ESVD income elasticity factors")
    print("7. EVE applies quality multipliers based on ecosystem health from satellite data")
    print("8. Final value = AUTHENTIC ESVD BASE × REGIONAL ADJUSTMENT × QUALITY FACTOR")
    print()
    print("All values standardized to International $/ha/year (2020 price levels)")
    print("Source: Foundation for Sustainable Development ESVD Database")
    print("=" * 80)

if __name__ == "__main__":
    demonstrate_esvd_usage()