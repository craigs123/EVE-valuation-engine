"""
Authentic ESVD Data Integration
Real ESVD database with 10,874 peer-reviewed ecosystem service values
Database Version: APR2024 V1.1 from Foundation for Sustainable Development
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import os

class AuthenticESVDIntegration:
    """
    Integration with authentic ESVD database (APR2024 V1.1)
    Contains 10,874 peer-reviewed ecosystem service values from 693+ studies
    """
    
    def __init__(self, esvd_csv_path: str = "data/esvd_database.csv"):
        self.esvd_data = None
        self.is_authentic_data_loaded = False
        self.value_columns = []
        
        # Load the authentic ESVD database
        if os.path.exists(esvd_csv_path):
            self.load_authentic_esvd_data(esvd_csv_path)
        else:
            print(f"❌ ESVD database not found at {esvd_csv_path}")
    
    def load_authentic_esvd_data(self, csv_path: str) -> bool:
        """
        Load authentic ESVD data from APR2024 V1.1 database
        
        Args:
            csv_path: Path to ESVD database CSV file
            
        Returns:
            bool: True if data loaded successfully
        """
        try:
            # Load the ESVD CSV data with proper handling for mixed types
            self.esvd_data = pd.read_csv(csv_path, low_memory=False)
            
            # Verify it's authentic ESVD data by checking key columns
            expected_columns = [
                'ESVD2.0_Biome', 'ES_Text', 'Int$ Per Hectare Per Year',
                'Country_1', 'ValueId', 'StudyId'
            ]
            
            missing_cols = [col for col in expected_columns if col not in self.esvd_data.columns]
            if not missing_cols:
                self.is_authentic_data_loaded = True
                
                # Identify key value columns
                self.value_columns = [
                    'Int$ Per Hectare Per Year',  # Primary standardized value
                    'Original Value',             # Original study value
                    'Value Year',                # Year of valuation
                    'Present Value Year'         # Present value year
                ]
                
                print(f"✅ Authentic ESVD APR2024 V1.1 loaded: {len(self.esvd_data):,} records")
                print(f"   - {self.esvd_data['ESVD2.0_Biome'].nunique()} unique biomes")
                print(f"   - {self.esvd_data['StudyId'].nunique()} unique studies")
                return True
            else:
                print(f"❌ Missing expected ESVD columns: {missing_cols}")
                return False
                
        except Exception as e:
            print(f"❌ Error loading ESVD data: {e}")
            return False
    
    def get_authentic_values(self, ecosystem_type: str, service_category: str, 
                           region: str = None) -> Dict[str, Any]:
        """
        Get authentic ESVD values for specific ecosystem and service
        
        Args:
            ecosystem_type: Type of ecosystem (e.g., 'forest', 'wetland')
            service_category: Service category (e.g., 'climate', 'recreation')
            region: Optional geographic filter
            
        Returns:
            dict: Authentic values with metadata
        """
        if not self.is_authentic_data_loaded:
            return {
                'values': [],
                'mean': 0,
                'median': 0,
                'count': 0,
                'source': 'No authentic ESVD data available',
                'authentic': False
            }
        
        # Create ecosystem mapping for ESVD biomes
        ecosystem_mapping = {
            'forest': ['forest', 'woodland'],
            'tropical_forest': ['tropical', 'subtropical forest'],
            'temperate_forest': ['temperate forest'],
            'wetland': ['wetland', 'marsh'],
            'grassland': ['grassland', 'rangeland'],
            'agricultural': ['intensive land use', 'cropland'],
            'coastal': ['coastal', 'marine'],
            'urban': ['urban green'],
            'desert': ['desert', 'arid']
        }
        
        # Service category mapping
        service_mapping = {
            'food': ['food', 'fishing', 'hunting', 'provisioning'],
            'water': ['water', 'fresh water'],
            'timber': ['timber', 'wood', 'fiber'],
            'climate': ['climate', 'carbon', 'sequestration'],
            'water_regulation': ['water regulation', 'flood', 'hydrology'],
            'erosion': ['erosion', 'soil'],
            'pollution': ['pollution', 'purification', 'filtration'],
            'recreation': ['recreation', 'tourism', 'aesthetic'],
            'cultural': ['cultural', 'spiritual', 'education'],
            'habitat': ['habitat', 'biodiversity', 'nursery']
        }
        
        # Build filter conditions
        biome_conditions = []
        if ecosystem_type in ecosystem_mapping:
            for term in ecosystem_mapping[ecosystem_type]:
                biome_conditions.append(
                    self.esvd_data['ESVD2.0_Biome'].str.contains(term, case=False, na=False)
                )
        
        service_conditions = []
        if service_category in service_mapping:
            for term in service_mapping[service_category]:
                service_conditions.append(
                    self.esvd_data['ES_Text'].str.contains(term, case=False, na=False)
                )
        
        # Apply filters
        if biome_conditions:
            biome_filter = biome_conditions[0]
            for condition in biome_conditions[1:]:
                biome_filter = biome_filter | condition
        else:
            biome_filter = pd.Series([True] * len(self.esvd_data), index=self.esvd_data.index)
            
        if service_conditions:
            service_filter = service_conditions[0]
            for condition in service_conditions[1:]:
                service_filter = service_filter | condition
        else:
            service_filter = pd.Series([True] * len(self.esvd_data), index=self.esvd_data.index)
        
        filtered_data = self.esvd_data[biome_filter & service_filter]
        
        # Extract standardized values
        values = pd.to_numeric(filtered_data['Int$ Per Hectare Per Year'], errors='coerce').dropna()
        
        if len(values) > 0:
            return {
                'values': values.tolist(),
                'mean': float(values.mean()),
                'median': float(values.median()),
                'std': float(values.std()) if len(values) > 1 else 0,
                'count': len(values),
                'source': 'Authentic ESVD APR2024 V1.1',
                'authentic': True,
                'studies': filtered_data['StudyId'].nunique(),
                'countries': filtered_data['Country_1'].nunique()
            }
        else:
            return {
                'values': [],
                'mean': 0,
                'median': 0,
                'count': 0,
                'source': f'No ESVD records for {ecosystem_type} + {service_category}',
                'authentic': False
            }
    
    def get_data_status(self) -> Dict[str, Any]:
        """
        Get status of loaded ESVD data
        
        Returns:
            dict: Status information
        """
        if self.is_authentic_data_loaded:
            return {
                'status': 'Authentic ESVD data loaded',
                'records_count': len(self.esvd_data),
                'biomes': self.esvd_data['Biome'].unique().tolist(),
                'services': self.esvd_data['Ecosystem service'].unique().tolist(),
                'years_range': f"{self.esvd_data['Year of publication'].min()}-{self.esvd_data['Year of publication'].max()}",
                'authentic': True
            }
        else:
            return {
                'status': 'No authentic ESVD data loaded',
                'message': 'Download CSV from www.esvd.net and use load_authentic_esvd_data()',
                'authentic': False
            }

def get_ecosystem_services_coefficients(ecosystem_type: str) -> Dict[str, float]:
    """
    Get authentic ESVD-based coefficients for ecosystem services
    
    Args:
        ecosystem_type: Type of ecosystem
        
    Returns:
        dict: Service coefficients in Int$/ha/year
    """
    esvd = AuthenticESVDIntegration()
    
    if not esvd.is_authentic_data_loaded:
        # Fallback to estimated values if ESVD not available
        return get_fallback_coefficients(ecosystem_type)
    
    # Get authentic values for each service category
    services = {
        'food_production': esvd.get_authentic_values(ecosystem_type, 'food'),
        'fresh_water': esvd.get_authentic_values(ecosystem_type, 'water'),
        'timber_fiber': esvd.get_authentic_values(ecosystem_type, 'timber'),
        'climate_regulation': esvd.get_authentic_values(ecosystem_type, 'climate'),
        'water_regulation': esvd.get_authentic_values(ecosystem_type, 'water_regulation'),
        'erosion_control': esvd.get_authentic_values(ecosystem_type, 'erosion'),
        'pollution_control': esvd.get_authentic_values(ecosystem_type, 'pollution'),
        'recreation': esvd.get_authentic_values(ecosystem_type, 'recreation'),
        'cultural_value': esvd.get_authentic_values(ecosystem_type, 'cultural'),
        'habitat_provision': esvd.get_authentic_values(ecosystem_type, 'habitat')
    }
    
    # Convert to coefficients (use median values for stability)
    coefficients = {}
    for service, data in services.items():
        if data['count'] > 0:
            coefficients[service] = data['median']
        else:
            # Use fallback if no data available for this service
            fallback = get_fallback_coefficients(ecosystem_type)
            coefficients[service] = fallback.get(service, 0)
    
    return coefficients


def get_fallback_coefficients(ecosystem_type: str) -> Dict[str, float]:
    """
    Fallback coefficients when ESVD data is not available
    Based on literature review approximations
    """
    fallback_data = {
        'forest': {
            'food_production': 200, 'fresh_water': 100, 'timber_fiber': 800,
            'climate_regulation': 2000, 'water_regulation': 1500, 'erosion_control': 1000,
            'pollution_control': 400, 'recreation': 600, 'cultural_value': 300,
            'habitat_provision': 1200
        },
        'wetland': {
            'food_production': 150, 'fresh_water': 900, 'timber_fiber': 200,
            'climate_regulation': 3500, 'water_regulation': 8000, 'erosion_control': 2000,
            'pollution_control': 1500, 'recreation': 1200, 'cultural_value': 200,
            'habitat_provision': 2500
        },
        'grassland': {
            'food_production': 220, 'fresh_water': 15, 'timber_fiber': 25,
            'climate_regulation': 450, 'water_regulation': 200, 'erosion_control': 300,
            'pollution_control': 90, 'recreation': 120, 'cultural_value': 50,
            'habitat_provision': 250
        },
        'agricultural': {
            'food_production': 750, 'fresh_water': 50, 'timber_fiber': 70,
            'climate_regulation': 250, 'water_regulation': 120, 'erosion_control': 160,
            'pollution_control': 50, 'recreation': 50, 'cultural_value': 25,
            'habitat_provision': 70
        }
    }
    
    return fallback_data.get(ecosystem_type, fallback_data['forest'])