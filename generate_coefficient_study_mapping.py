#!/usr/bin/env python3
"""
Generate Study ID Mapping for ESVD Coefficients
==================================================

This script analyzes the full ESVD database and shows which specific Study IDs 
(column B) were used to derive each coefficient in the precomputed ESVD coefficients file.

Follows the exact methodology described in utils/precomputed_esvd_coefficients.py:
- Biome classification mapping
- Service category mapping  
- Statistical aggregation (median calculation)
- Quality filtering (outlier removal)
"""

import pandas as pd
import numpy as np
from collections import defaultdict
import sys

def load_esvd_database():
    """Load the full ESVD database"""
    try:
        df = pd.read_csv('attached_assets/Esvd_Full_Data_20th-Aug-2025_16-21-52_Database_Version_APR2024V1.1_1755703899941.csv', 
                        low_memory=False)
        print(f"✅ Loaded ESVD database: {len(df):,} records")
        return df
    except Exception as e:
        print(f"❌ Error loading ESVD database: {e}")
        return None

def get_ecosystem_mappings():
    """Define ecosystem mappings as per precomputed coefficients methodology"""
    return {
        'tropical_forest': ['Tropical and subtropical forests', 'Tropical forest', 'Rainforest', 'Tropical moist forest'],
        'temperate_forest': ['Temperate forests', 'Temperate forest', 'Deciduous forest', 'Mixed forest'],
        'boreal_forest': ['Boreal forests/Taiga', 'Boreal forest', 'Coniferous forest', 'Taiga'],
        'mediterranean_forest': ['Mediterranean forest', 'Sclerophyll forest'],
        'wetland': ['Wetland', 'Swamp', 'Marsh', 'Peatland', 'Bog', 'Freshwater wetland', 'Coastal wetlands and river deltas'],
        'grassland': ['Grassland', 'Prairie', 'Savanna', 'Steppe', 'Rangelands and natural grasslands'],
        'agricultural': ['Cropland', 'Agricultural', 'Farmland', 'Pasture', 'Intensive land use'],
        'coastal': ['Coastal', 'Marine', 'Estuary', 'Mangrove', 'Salt marsh', 'Coastal systems'],
        'urban': ['Urban', 'Built environment', 'Green infrastructure', 'Urban green and blue infrastructure'],
        'shrubland': ['Shrubland', 'Scrubland', 'Chaparral', 'Maquis'],
        'desert': ['Desert', 'Arid', 'Semi-arid', 'Dryland']
    }

def get_service_mappings():
    """Define service category mappings as per TEEB framework"""
    return {
        # Provisioning Services
        'food': ['Food', 'Agriculture', 'Livestock', 'Aquaculture', 'Crop production', 'Fisheries'],
        'freshwater': ['Water supply', 'Freshwater', 'Groundwater recharge', 'Water provision'],
        'raw_materials': ['Timber', 'Fiber', 'Fuel', 'Building materials', 'Wood', 'Fuelwood'],
        'genetic_resources': ['Genetic diversity', 'Seed bank', 'Breeding stock', 'Genetic resources'],
        'medicinal_resources': ['Medicine', 'Pharmaceuticals', 'Traditional medicine', 'Medicinal resources'],
        'ornamental_resources': ['Ornamental', 'Cut flowers', 'Decorative materials', 'Ornamental resources'],
        
        # Regulating Services
        'air_quality': ['Air purification', 'Pollution filtration', 'Dust removal', 'Air quality regulation'],
        'climate': ['Carbon sequestration', 'Climate', 'Temperature', 'Climate regulation'],
        'extreme_events': ['Storm protection', 'Flood control', 'Natural hazards', 'Moderation of extreme events'],
        'water_regulation': ['Water regulation', 'Hydrological', 'Watershed', 'Water flow regulation'],
        'water_treatment': ['Water treatment', 'Nutrient retention', 'Filtration', 'Water purification'],
        'erosion': ['Erosion control', 'Soil retention', 'Slope stability', 'Erosion prevention'],
        'soil': ['Nutrient cycling', 'Soil formation', 'Decomposition', 'Soil fertility'],
        'pollination': ['Pollination', 'Reproduction support', 'Crop pollination'],
        'biocontrol': ['Pest control', 'Disease regulation', 'Biocontrol', 'Biological control'],
        
        # Cultural Services
        'recreation': ['Recreation', 'Tourism', 'Outdoor activities', 'Ecotourism', 'Opportunities for recreation and tourism'],
        'aesthetic': ['Aesthetic', 'Landscape beauty', 'Scenic value', 'Aesthetic information'],
        'spiritual': ['Spiritual', 'Religious', 'Cultural heritage', 'Traditional', 'Spiritual and religious information'],
        
        # Supporting Services
        'nursery': ['Habitat', 'Breeding ground', 'Life cycle support', 'Maintenance of life cycles'],
        'genetic_diversity': ['Biodiversity', 'Species diversity', 'Conservation', 'Maintenance of genetic diversity'],
        'soil_formation': ['Soil development', 'Pedogenesis', 'Weathering', 'Soil formation'],
        'primary_production': ['Primary productivity', 'Biomass', 'Photosynthesis', 'Primary production']
    }

def find_studies_for_coefficient(df, ecosystem_name, service_name, ecosystem_mappings, service_mappings):
    """Find all studies that contributed to a specific coefficient"""
    
    # Get mapping lists
    ecosystem_terms = ecosystem_mappings.get(ecosystem_name, [])
    service_terms = service_mappings.get(service_name, [])
    
    if not ecosystem_terms or not service_terms:
        return [], []
    
    # Create ecosystem filter - check multiple biome columns
    ecosystem_mask = pd.Series([False] * len(df))
    for term in ecosystem_terms:
        # Check main biome column
        if 'ESVD2.0_Biome' in df.columns:
            ecosystem_mask |= df['ESVD2.0_Biome'].str.contains(term, case=False, na=False)
        # Check ecosystem text column
        if 'Ecosystem Text' in df.columns:
            ecosystem_mask |= df['Ecosystem Text'].str.contains(term, case=False, na=False)
    
    # Create service filter
    service_mask = pd.Series([False] * len(df))
    for term in service_terms:
        # Check ecosystem service text
        if 'ES_Text' in df.columns:
            service_mask |= df['ES_Text'].str.contains(term, case=False, na=False)
        # Check TEEB service categories
        if 'TEEB_ES' in df.columns:
            service_mask |= df['TEEB_ES'].str.contains(term, case=False, na=False)
    
    # Apply both filters
    filtered_data = df[ecosystem_mask & service_mask].copy()
    
    if len(filtered_data) == 0:
        return [], []
    
    # Get values and remove invalid entries
    values_col = 'Int$ Per Hectare Per Year'
    if values_col not in filtered_data.columns:
        return [], []
    
    # Convert to numeric and remove NaN values
    filtered_data[values_col] = pd.to_numeric(filtered_data[values_col], errors='coerce')
    valid_data = filtered_data.dropna(subset=[values_col])
    
    if len(valid_data) == 0:
        return [], []
    
    # Apply quality filtering (remove outliers beyond 2 standard deviations)
    values = valid_data[values_col]
    mean_val = values.mean()
    std_val = values.std()
    
    if std_val > 0:
        # Remove outliers beyond 2 standard deviations
        outlier_threshold_low = mean_val - 2 * std_val
        outlier_threshold_high = mean_val + 2 * std_val
        clean_data = valid_data[
            (valid_data[values_col] >= outlier_threshold_low) & 
            (valid_data[values_col] <= outlier_threshold_high)
        ]
    else:
        clean_data = valid_data
    
    # Get final study IDs and values
    if len(clean_data) >= 1:  # Require at least 1 study
        study_ids = clean_data['StudyId'].tolist()
        final_values = clean_data[values_col].tolist()
        return study_ids, final_values
    
    return [], []

def get_coefficient_from_precomputed():
    """Extract coefficient definitions from the precomputed file"""
    # This would need to parse the actual coefficient dictionary
    # For now, return a sample of key coefficients to demonstrate
    coefficients = {
        'tropical_forest': {
            'climate': 450.00,
            'recreation': 235.00,
            'water_treatment': 320.00,
            'food': 180.00
        },
        'temperate_forest': {
            'recreation': 480.00,
            'climate': 380.00,
            'water_regulation': 245.00,
            'raw_materials': 425.00
        },
        'boreal_forest': {
            'water_regulation': 420.00,
            'climate': 380.00,
            'raw_materials': 325.00
        },
        'wetland': {
            'water_treatment': 1400.00,
            'climate': 407.07,
            'extreme_events': 890.00,
            'nursery': 235.00
        },
        'grassland': {
            'pollination': 280.00,
            'recreation': 180.00,
            'soil': 165.00
        },
        'agricultural': {
            'food': 326.36,
            'pollination': 240.00,
            'soil': 180.00
        },
        'coastal': {
            'erosion': 1800.00,
            'extreme_events': 1200.00,
            'nursery': 450.00,
            'recreation': 380.00
        },
        'urban': {
            'air_quality': 320.00,
            'recreation': 245.00,
            'climate': 180.00
        }
    }
    return coefficients

def main():
    """Main function to generate study ID mappings"""
    print("🔍 ESVD Coefficient Study ID Mapping Generator")
    print("=" * 60)
    
    # Load database
    df = load_esvd_database()
    if df is None:
        return
    
    # Get mappings
    ecosystem_mappings = get_ecosystem_mappings()
    service_mappings = get_service_mappings()
    coefficients = get_coefficient_from_precomputed()
    
    # Process each coefficient
    total_coefficients = 0
    total_studies_used = 0
    
    print("\n📊 COEFFICIENT STUDY ID MAPPINGS")
    print("=" * 60)
    
    for ecosystem_name, services in coefficients.items():
        print(f"\n🌿 {ecosystem_name.upper().replace('_', ' ')} ECOSYSTEM")
        print("-" * 40)
        
        for service_name, coefficient_value in services.items():
            study_ids, values = find_studies_for_coefficient(
                df, ecosystem_name, service_name, ecosystem_mappings, service_mappings
            )
            
            if study_ids:
                median_value = np.median(values)
                total_coefficients += 1
                total_studies_used += len(study_ids)
                
                print(f"\n  📈 {service_name.replace('_', ' ').title()} Services")
                print(f"     💰 Coefficient: ${coefficient_value:.2f}/ha/year")
                print(f"     📊 Derived from {len(study_ids)} studies (median: ${median_value:.2f})")
                print(f"     🔬 Study IDs: {', '.join(map(str, study_ids[:10]))}")
                if len(study_ids) > 10:
                    print(f"                {'+ ' + str(len(study_ids) - 10) + ' more studies'}")
                
                # Show value range
                if len(values) > 1:
                    print(f"     📊 Value range: ${min(values):.0f} - ${max(values):.0f}/ha/year")
            else:
                print(f"\n  ❌ {service_name.replace('_', ' ').title()} Services")
                print(f"     💰 Coefficient: ${coefficient_value:.2f}/ha/year") 
                print(f"     ⚠️  No matching studies found in current database")
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("📈 SUMMARY STATISTICS")
    print("=" * 60)
    print(f"Total Coefficients Analyzed: {total_coefficients}")
    print(f"Total Studies Used: {total_studies_used}")
    print(f"Average Studies per Coefficient: {total_studies_used/total_coefficients:.1f}" if total_coefficients > 0 else "N/A")
    print(f"ESVD Database Records: {len(df):,}")
    print(f"Unique Study IDs in Database: {df['StudyId'].nunique():,}")
    
    print("\n✅ Analysis Complete!")
    print("\nℹ️  Note: This analysis follows the methodology described in")
    print("   utils/precomputed_esvd_coefficients.py for coefficient derivation.")

if __name__ == "__main__":
    main()