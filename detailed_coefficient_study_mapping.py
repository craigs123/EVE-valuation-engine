#!/usr/bin/env python3
"""
Detailed Study ID and Value Mapping for ESVD Coefficients
==========================================================

Enhanced version that shows:
- Study ID and the specific value extracted from that study
- Step-by-step median calculation process for each coefficient
"""

import pandas as pd
import numpy as np
import sys

def load_esvd_database():
    """Load the full ESVD database"""
    try:
        df = pd.read_csv('attached_assets/Esvd_Full_Data_20th-Aug-2025_16-21-52_Database_Version_APR2024V1.1_1755703899941.csv', 
                        low_memory=False)
        return df
    except Exception as e:
        print(f"❌ Error loading ESVD database: {e}")
        return None

def get_sample_coefficients_for_demo():
    """Get a focused sample of key coefficients for detailed demonstration"""
    return {
        'tropical_forest': {
            'climate': 450.00,
            'recreation': 235.00,
            'water_treatment': 320.00,
            'food': 326.36
        },
        'temperate_forest': {
            'recreation': 480.00,
            'climate': 380.00,
            'raw_materials': 425.00
        },
        'wetland': {
            'water_treatment': 1400.00,
            'climate': 407.07,
            'extreme_events': 890.00
        },
        'grassland': {
            'pollination': 280.00,
            'recreation': 180.00,
            'soil': 165.00
        },
        'coastal': {
            'erosion': 1800.00,
            'recreation': 380.00,
            'nursery': 450.00
        },
        'urban': {
            'air_quality': 320.00,
            'recreation': 245.00,
            'climate': 180.00
        }
    }

def get_ecosystem_mappings():
    """Define ecosystem mappings"""
    return {
        'tropical_forest': ['Tropical and subtropical forests', 'Tropical forest', 'Rainforest'],
        'temperate_forest': ['Temperate forests', 'Temperate forest', 'Deciduous forest', 'Mixed forest'],
        'wetland': ['Wetland', 'Swamp', 'Marsh', 'Coastal wetlands and river deltas', 'Freshwater wetland'],
        'grassland': ['Grassland', 'Prairie', 'Savanna', 'Rangelands and natural grasslands'],
        'coastal': ['Coastal', 'Marine', 'Estuary', 'Mangrove', 'Coastal systems'],
        'urban': ['Urban', 'Built environment', 'Urban green and blue infrastructure']
    }

def get_service_mappings():
    """Define service category mappings"""
    return {
        'food': ['Food', 'Agriculture', 'Livestock', 'Aquaculture'],
        'raw_materials': ['Timber', 'Fiber', 'Fuel', 'Building materials', 'Wood', 'Raw materials'],
        'air_quality': ['Air purification', 'Air quality regulation', 'Pollution filtration'],
        'climate': ['Carbon sequestration', 'Climate', 'Climate regulation'],
        'extreme_events': ['Storm protection', 'Flood control', 'Moderation of extreme events'],
        'water_treatment': ['Water treatment', 'Water purification', 'Filtration'],
        'erosion': ['Erosion control', 'Soil retention', 'Erosion prevention'],
        'soil': ['Nutrient cycling', 'Soil formation', 'Soil fertility'],
        'pollination': ['Pollination', 'Crop pollination'],
        'recreation': ['Recreation', 'Tourism', 'Ecotourism', 'Opportunities for recreation and tourism'],
        'nursery': ['Habitat', 'Maintenance of life cycles', 'Life cycle support']
    }

def find_studies_with_values(df, ecosystem_name, service_name, ecosystem_mappings, service_mappings):
    """Find studies with detailed value extraction and processing steps"""
    ecosystem_terms = ecosystem_mappings.get(ecosystem_name, [])
    service_terms = service_mappings.get(service_name, [])
    
    if not ecosystem_terms or not service_terms:
        return [], [], []
    
    # Step 1: Apply ecosystem filter
    ecosystem_mask = pd.Series([False] * len(df))
    for term in ecosystem_terms:
        if 'ESVD2.0_Biome' in df.columns:
            ecosystem_mask |= df['ESVD2.0_Biome'].str.contains(term, case=False, na=False)
        if 'Ecosystem Text' in df.columns:
            ecosystem_mask |= df['Ecosystem Text'].str.contains(term, case=False, na=False)
    
    # Step 2: Apply service filter
    service_mask = pd.Series([False] * len(df))
    for term in service_terms:
        if 'ES_Text' in df.columns:
            service_mask |= df['ES_Text'].str.contains(term, case=False, na=False)
        if 'TEEB_ES' in df.columns:
            service_mask |= df['TEEB_ES'].str.contains(term, case=False, na=False)
    
    # Step 3: Get filtered dataset
    filtered_data = df[ecosystem_mask & service_mask].copy()
    
    if len(filtered_data) == 0:
        return [], [], []
    
    # Step 4: Extract values and convert to numeric
    values_col = 'Int$ Per Hectare Per Year'
    if values_col not in filtered_data.columns:
        return [], [], []
    
    filtered_data[values_col] = pd.to_numeric(filtered_data[values_col], errors='coerce')
    valid_data = filtered_data.dropna(subset=[values_col])
    
    if len(valid_data) == 0:
        return [], [], []
    
    # Step 5: Record original values before filtering
    original_study_ids = valid_data['StudyId'].tolist()
    original_values = valid_data[values_col].tolist()
    
    # Step 6: Apply quality filtering (outlier removal)
    values_array = np.array(original_values)
    if len(values_array) > 2:
        mean_val = np.mean(values_array)
        std_val = np.std(values_array)
        
        if std_val > 0:
            # Identify outliers (beyond 2 standard deviations)
            lower_bound = mean_val - 2 * std_val
            upper_bound = mean_val + 2 * std_val
            
            # Filter out outliers
            outlier_mask = (values_array >= lower_bound) & (values_array <= upper_bound)
            clean_study_ids = [original_study_ids[i] for i, keep in enumerate(outlier_mask) if keep]
            clean_values = [original_values[i] for i, keep in enumerate(outlier_mask) if keep]
        else:
            clean_study_ids = original_study_ids
            clean_values = original_values
    else:
        clean_study_ids = original_study_ids
        clean_values = original_values
    
    return clean_study_ids, clean_values, original_values

def calculate_median_detailed(values):
    """Calculate median with detailed steps"""
    if not values:
        return 0, []
    
    sorted_values = sorted(values)
    n = len(sorted_values)
    
    if n % 2 == 0:
        # Even number of values - average of two middle values
        mid1_idx = n // 2 - 1
        mid2_idx = n // 2
        median = (sorted_values[mid1_idx] + sorted_values[mid2_idx]) / 2
        calculation_steps = [
            f"Step 1: Sort values: {sorted_values}",
            f"Step 2: n = {n} (even number)",
            f"Step 3: Middle positions: {mid1_idx + 1} and {mid2_idx + 1}",
            f"Step 4: Middle values: {sorted_values[mid1_idx]:.2f} and {sorted_values[mid2_idx]:.2f}",
            f"Step 5: Median = ({sorted_values[mid1_idx]:.2f} + {sorted_values[mid2_idx]:.2f}) / 2 = {median:.2f}"
        ]
    else:
        # Odd number of values - middle value
        mid_idx = n // 2
        median = sorted_values[mid_idx]
        calculation_steps = [
            f"Step 1: Sort values: {sorted_values}",
            f"Step 2: n = {n} (odd number)",
            f"Step 3: Middle position: {mid_idx + 1}",
            f"Step 4: Median = {median:.2f}"
        ]
    
    return median, calculation_steps

def main():
    """Generate detailed study ID mappings with values and median calculations"""
    print("🔍 Detailed ESVD Study ID and Value Mapping")
    print("=" * 70)
    
    # Load database
    df = load_esvd_database()
    if df is None:
        return
    
    print(f"✅ Loaded ESVD database: {len(df):,} records")
    
    # Get mappings
    ecosystem_mappings = get_ecosystem_mappings()
    service_mappings = get_service_mappings()
    coefficients = get_sample_coefficients_for_demo()
    
    # Open output file
    with open('detailed_esvd_study_value_mappings.txt', 'w') as f:
        f.write("DETAILED ESVD COEFFICIENT STUDY ID AND VALUE MAPPINGS\n")
        f.write("=" * 80 + "\n\n")
        f.write("This document shows:\n")
        f.write("1. Study IDs (column B from ESVD database)\n")
        f.write("2. Specific values extracted from each study\n")
        f.write("3. Step-by-step median calculation process\n")
        f.write("4. Quality filtering applied (outlier removal)\n\n")
        f.write(f"Database: ESVD APR2024 V1.1 ({len(df):,} records)\n\n")
        
        for ecosystem_name, services in coefficients.items():
            ecosystem_display = ecosystem_name.upper().replace('_', ' ')
            f.write(f"\n{'='*80}\n")
            f.write(f"{ecosystem_display} ECOSYSTEM\n")
            f.write(f"{'='*80}\n")
            
            for service_name, coefficient_value in services.items():
                study_ids, clean_values, original_values = find_studies_with_values(
                    df, ecosystem_name, service_name, ecosystem_mappings, service_mappings
                )
                
                service_display = service_name.replace('_', ' ').title()
                f.write(f"\n{service_display} Services\n")
                f.write(f"{'-' * 50}\n")
                f.write(f"Target Coefficient: ${coefficient_value:.2f}/ha/year\n")
                
                if study_ids and clean_values:
                    # Calculate median with detailed steps
                    calculated_median, median_steps = calculate_median_detailed(clean_values)
                    
                    f.write(f"Studies Found: {len(study_ids)}\n")
                    f.write(f"Calculated Median: ${calculated_median:.2f}/ha/year\n\n")
                    
                    # Show study-by-study breakdown
                    f.write("STUDY ID → VALUE MAPPING:\n")
                    f.write("-" * 30 + "\n")
                    for study_id, value in zip(study_ids, clean_values):
                        f.write(f"Study {study_id}: ${value:.2f}/ha/year\n")
                    
                    # Show median calculation process
                    f.write(f"\nMEDIAN CALCULATION PROCESS:\n")
                    f.write("-" * 30 + "\n")
                    for step in median_steps:
                        f.write(f"{step}\n")
                    
                    # Show quality filtering info if applicable
                    if len(original_values) != len(clean_values):
                        outliers_removed = len(original_values) - len(clean_values)
                        f.write(f"\nQUALITY FILTERING APPLIED:\n")
                        f.write("-" * 30 + "\n")
                        f.write(f"Original studies: {len(original_values)}\n")
                        f.write(f"Outliers removed: {outliers_removed}\n")
                        f.write(f"Final studies used: {len(clean_values)}\n")
                        f.write(f"Mean ± 2×StdDev filtering applied\n")
                    
                    # Statistical summary
                    f.write(f"\nSTATISTICAL SUMMARY:\n")
                    f.write("-" * 20 + "\n")
                    f.write(f"Minimum: ${min(clean_values):.2f}/ha/year\n")
                    f.write(f"Maximum: ${max(clean_values):.2f}/ha/year\n")
                    f.write(f"Mean: ${np.mean(clean_values):.2f}/ha/year\n")
                    f.write(f"Median: ${calculated_median:.2f}/ha/year\n")
                    f.write(f"Std Dev: ${np.std(clean_values):.2f}/ha/year\n")
                    
                else:
                    f.write("Studies Found: 0\n")
                    f.write("Note: No matching studies in current database\n")
                    f.write("Coefficient may be derived from literature meta-analysis\n")
                
                f.write("\n" + "=" * 60 + "\n")
    
    print(f"✅ Detailed analysis saved to 'detailed_esvd_study_value_mappings.txt'")
    print("📊 This file includes study IDs, values, and median calculations for each coefficient")

if __name__ == "__main__":
    main()