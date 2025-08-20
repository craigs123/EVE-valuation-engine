"""
Authentic ESVD Data Integration
For implementing real ESVD database values when CSV data is available
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import os

class AuthenticESVDIntegration:
    """
    Integration with authentic ESVD data from downloaded CSV files
    Requires manual download from www.esvd.net
    """
    
    def __init__(self, esvd_csv_path: Optional[str] = None):
        self.esvd_data = None
        self.is_authentic_data_loaded = False
        
        if esvd_csv_path and os.path.exists(esvd_csv_path):
            self.load_authentic_esvd_data(esvd_csv_path)
    
    def load_authentic_esvd_data(self, csv_path: str) -> bool:
        """
        Load authentic ESVD data from downloaded CSV file
        
        Args:
            csv_path: Path to downloaded ESVD CSV file from www.esvd.net
            
        Returns:
            bool: True if data loaded successfully
        """
        try:
            # Load the ESVD CSV data
            self.esvd_data = pd.read_csv(csv_path)
            
            # Verify it's authentic ESVD data by checking expected columns
            expected_columns = [
                'Biome', 'Ecosystem service', 'Value estimate',
                'Country', 'Continent', 'Year of publication'
            ]
            
            if all(col in self.esvd_data.columns for col in expected_columns):
                self.is_authentic_data_loaded = True
                print(f"✅ Authentic ESVD data loaded: {len(self.esvd_data)} records")
                return True
            else:
                print("❌ CSV file doesn't match ESVD format")
                return False
                
        except Exception as e:
            print(f"❌ Error loading ESVD data: {e}")
            return False
    
    def get_authentic_values(self, ecosystem_type: str, service_category: str, 
                           region: str = None) -> Dict[str, Any]:
        """
        Get authentic ESVD values for specific ecosystem and service
        
        Args:
            ecosystem_type: Type of ecosystem (e.g., 'Tropical forests')
            service_category: Service category (e.g., 'Climate regulation')
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
        
        # Filter data based on criteria
        filtered_data = self.esvd_data[
            (self.esvd_data['Biome'].str.contains(ecosystem_type, case=False, na=False)) &
            (self.esvd_data['Ecosystem service'].str.contains(service_category, case=False, na=False))
        ]
        
        if region:
            filtered_data = filtered_data[
                filtered_data['Continent'].str.contains(region, case=False, na=False)
            ]
        
        # Extract numerical values
        values = filtered_data['Value estimate'].dropna()
        
        if len(values) > 0:
            return {
                'values': values.tolist(),
                'mean': float(values.mean()),
                'median': float(values.median()),
                'std': float(values.std()),
                'count': len(values),
                'source': 'Authentic ESVD database',
                'authentic': True,
                'studies': filtered_data['Year of publication'].unique().tolist()
            }
        else:
            return {
                'values': [],
                'mean': 0,
                'median': 0,
                'count': 0,
                'source': 'No matching ESVD records found',
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

def create_esvd_download_instructions() -> str:
    """
    Provide instructions for downloading authentic ESVD data
    
    Returns:
        str: Step-by-step instructions
    """
    return """
    To use authentic ESVD data in the Ecosystem Valuation Engine:
    
    1. Visit: https://www.esvd.net/
    2. Create a free account (registration required)
    3. Download the complete ESVD dataset as CSV
    4. Place the CSV file in the project directory
    5. Update the app to use authentic_esvd_integration.py
    
    Benefits of authentic ESVD data:
    - Real peer-reviewed values from 1,300+ studies
    - Geographic specificity for your analysis region
    - Confidence intervals and uncertainty measures
    - Study metadata and publication details
    - Quality indicators for each value record
    
    Note: The current app uses estimated coefficients for demonstration.
    Authentic ESVD integration requires the manual CSV download step.
    """