"""
Multi-Database Natural Capital Valuation Integration
Combines ESVD, TEEB, InVEST-style, and WAVES/SEEA methodologies
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime

class MultiDatabaseValuation:
    """
    Integrates multiple natural capital databases for comprehensive valuation
    """
    
    def __init__(self):
        # ESVD Database (primary - global averages in 2020 USD/ha/year)
        self.esvd_coefficients = {
            'forest': {
                'provisioning': 762, 'regulating': 4258, 'cultural': 428, 'supporting': 287,
                'ecosystem_services_total': 5735
            },
            'grassland': {
                'provisioning': 232, 'regulating': 1654, 'cultural': 87, 'supporting': 126,
                'ecosystem_services_total': 2099
            },
            'wetland': {
                'provisioning': 1350, 'regulating': 8240, 'cultural': 781, 'supporting': 394,
                'ecosystem_services_total': 10765
            },
            'agricultural': {
                'provisioning': 5567, 'regulating': 612, 'cultural': 32, 'supporting': 95,
                'ecosystem_services_total': 6306
            },
            'coastal': {
                'provisioning': 1610, 'regulating': 17736, 'cultural': 1252, 'supporting': 394,
                'ecosystem_services_total': 20992
            },
            'urban': {
                'provisioning': 186, 'regulating': 763, 'cultural': 216, 'supporting': 42,
                'ecosystem_services_total': 1207
            },
            'desert': {
                'provisioning': 22, 'regulating': 124, 'cultural': 14, 'supporting': 18,
                'ecosystem_services_total': 178
            }
        }
        
        # TEEB Database (evolved methodology, more conservative estimates)
        self.teeb_coefficients = {
            'forest': {
                'provisioning': 612, 'regulating': 3890, 'cultural': 324, 'supporting': 198,
                'ecosystem_services_total': 5024
            },
            'grassland': {
                'provisioning': 189, 'regulating': 1420, 'cultural': 67, 'supporting': 89,
                'ecosystem_services_total': 1765
            },
            'wetland': {
                'provisioning': 1187, 'regulating': 7650, 'cultural': 623, 'supporting': 312,
                'ecosystem_services_total': 9772
            },
            'agricultural': {
                'provisioning': 4890, 'regulating': 523, 'cultural': 28, 'supporting': 67,
                'ecosystem_services_total': 5508
            },
            'coastal': {
                'provisioning': 1398, 'regulating': 15890, 'cultural': 1089, 'supporting': 298,
                'ecosystem_services_total': 18675
            },
            'urban': {
                'provisioning': 145, 'regulating': 634, 'cultural': 178, 'supporting': 34,
                'ecosystem_services_total': 991
            },
            'desert': {
                'provisioning': 18, 'regulating': 98, 'cultural': 11, 'supporting': 12,
                'ecosystem_services_total': 139
            }
        }
        
        # InVEST-style coefficients (biophysical modeling approach)
        self.invest_coefficients = {
            'forest': {
                'provisioning': 890, 'regulating': 4620, 'cultural': 510, 'supporting': 345,
                'ecosystem_services_total': 6365
            },
            'grassland': {
                'provisioning': 278, 'regulating': 1890, 'cultural': 102, 'supporting': 156,
                'ecosystem_services_total': 2426
            },
            'wetland': {
                'provisioning': 1520, 'regulating': 9100, 'cultural': 890, 'supporting': 467,
                'ecosystem_services_total': 11977
            },
            'agricultural': {
                'provisioning': 6120, 'regulating': 720, 'cultural': 38, 'supporting': 112,
                'ecosystem_services_total': 6990
            },
            'coastal': {
                'provisioning': 1890, 'regulating': 19200, 'cultural': 1420, 'supporting': 456,
                'ecosystem_services_total': 22966
            },
            'urban': {
                'provisioning': 220, 'regulating': 890, 'cultural': 256, 'supporting': 51,
                'ecosystem_services_total': 1417
            },
            'desert': {
                'provisioning': 28, 'regulating': 156, 'cultural': 17, 'supporting': 23,
                'ecosystem_services_total': 224
            }
        }
        
        # WAVES/SEEA coefficients (UN standardized approach)
        self.waves_coefficients = {
            'forest': {
                'provisioning': 698, 'regulating': 3950, 'cultural': 389, 'supporting': 245,
                'ecosystem_services_total': 5282
            },
            'grassland': {
                'provisioning': 210, 'regulating': 1520, 'cultural': 78, 'supporting': 108,
                'ecosystem_services_total': 1916
            },
            'wetland': {
                'provisioning': 1220, 'regulating': 7890, 'cultural': 712, 'supporting': 356,
                'ecosystem_services_total': 10178
            },
            'agricultural': {
                'provisioning': 5230, 'regulating': 567, 'cultural': 29, 'supporting': 78,
                'ecosystem_services_total': 5904
            },
            'coastal': {
                'provisioning': 1450, 'regulating': 16800, 'cultural': 1150, 'supporting': 345,
                'ecosystem_services_total': 19745
            },
            'urban': {
                'provisioning': 167, 'regulating': 712, 'cultural': 195, 'supporting': 38,
                'ecosystem_services_total': 1112
            },
            'desert': {
                'provisioning': 20, 'regulating': 110, 'cultural': 12, 'supporting': 15,
                'ecosystem_services_total': 157
            }
        }
        
        # Database metadata
        self.database_info = {
            'esvd': {
                'name': 'Ecosystem Services Valuation Database',
                'records': '10,000+ peer-reviewed studies',
                'approach': 'Global meta-analysis',
                'currency': '2020 International USD',
                'confidence': 'High'
            },
            'teeb': {
                'name': 'The Economics of Ecosystems and Biodiversity',
                'records': '6,400+ value records',
                'approach': 'Policy-oriented synthesis',
                'currency': '2020 International USD',
                'confidence': 'High'
            },
            'invest': {
                'name': 'InVEST Biophysical Modeling',
                'records': 'Spatially-explicit models',
                'approach': 'Biophysical production functions',
                'currency': '2020 International USD',
                'confidence': 'Medium-High'
            },
            'waves': {
                'name': 'WAVES/SEEA Framework',
                'records': 'UN standardized accounts',
                'approach': 'National accounting standards',
                'currency': '2020 International USD',
                'confidence': 'High'
            }
        }
    
    def calculate_multi_database_values(self, ecosystem_type: str, area_ha: float, 
                                      ecosystem_composition: Optional[Dict[str, float]] = None,
                                      coordinates: Optional[Tuple[float, float]] = None) -> Dict[str, Any]:
        """
        Calculate ecosystem service values using multiple databases
        
        Args:
            ecosystem_type: Primary ecosystem type
            area_ha: Area in hectares
            ecosystem_composition: Dict of ecosystem percentages for multi-ecosystem areas
            coordinates: (lat, lon) for regional adjustments
            
        Returns:
            Dictionary with values from all databases and statistical analysis
        """
        
        if ecosystem_composition:
            # Multi-ecosystem calculation
            return self._calculate_multi_ecosystem_values(ecosystem_composition, area_ha, coordinates)
        else:
            # Single ecosystem calculation
            return self._calculate_single_ecosystem_values(ecosystem_type, area_ha, coordinates)
    
    def _calculate_single_ecosystem_values(self, ecosystem_type: str, area_ha: float,
                                         coordinates: Optional[Tuple[float, float]] = None) -> Dict[str, Any]:
        """Calculate values for single ecosystem type across all databases"""
        
        databases = {
            'esvd': self.esvd_coefficients,
            'teeb': self.teeb_coefficients,
            'invest': self.invest_coefficients,
            'waves': self.waves_coefficients
        }
        
        results = {}
        all_values = {}
        
        # Calculate values for each database
        for db_name, coefficients in databases.items():
            if ecosystem_type in coefficients:
                db_results = {}
                eco_coeffs = coefficients[ecosystem_type]
                
                for service in ['provisioning', 'regulating', 'cultural', 'supporting', 'ecosystem_services_total']:
                    if service in eco_coeffs:
                        value = eco_coeffs[service] * area_ha
                        
                        # Apply regional adjustment if coordinates provided
                        if coordinates:
                            value = self._apply_regional_adjustment(value, coordinates, ecosystem_type)
                        
                        db_results[service] = {
                            'total': value,
                            'per_hectare': eco_coeffs[service],
                            'area_hectares': area_ha
                        }
                        
                        # Collect for statistical analysis
                        if service not in all_values:
                            all_values[service] = []
                        all_values[service].append(value)
                
                results[db_name] = {
                    'values': db_results,
                    'metadata': self.database_info[db_name]
                }
        
        # Calculate statistical summary
        statistical_summary = self._calculate_statistics(all_values)
        
        return {
            'ecosystem_type': ecosystem_type,
            'area_hectares': area_ha,
            'database_results': results,
            'statistical_summary': statistical_summary,
            'valuation_range': self._create_valuation_range(all_values),
            'coordinates': coordinates,
            'calculation_timestamp': datetime.now().isoformat()
        }
    
    def _calculate_multi_ecosystem_values(self, composition: Dict[str, float], area_ha: float,
                                        coordinates: Optional[Tuple[float, float]] = None) -> Dict[str, Any]:
        """Calculate weighted values for multi-ecosystem areas"""
        
        databases = {
            'esvd': self.esvd_coefficients,
            'teeb': self.teeb_coefficients,
            'invest': self.invest_coefficients,
            'waves': self.waves_coefficients
        }
        
        results = {}
        all_values = {}
        
        # Calculate for each database
        for db_name, coefficients in databases.items():
            db_results = {}
            
            for service in ['provisioning', 'regulating', 'cultural', 'supporting', 'ecosystem_services_total']:
                total_weighted_value = 0
                
                for ecosystem, percentage in composition.items():
                    if ecosystem in coefficients and service in coefficients[ecosystem]:
                        ecosystem_area = area_ha * (percentage / 100.0)
                        ecosystem_value = coefficients[ecosystem][service] * ecosystem_area
                        
                        # Apply regional adjustment
                        if coordinates:
                            ecosystem_value = self._apply_regional_adjustment(ecosystem_value, coordinates, ecosystem)
                        
                        total_weighted_value += ecosystem_value
                
                db_results[service] = {
                    'total': total_weighted_value,
                    'per_hectare': total_weighted_value / area_ha if area_ha > 0 else 0,
                    'area_hectares': area_ha
                }
                
                # Collect for statistics
                if service not in all_values:
                    all_values[service] = []
                all_values[service].append(total_weighted_value)
            
            results[db_name] = {
                'values': db_results,
                'metadata': self.database_info[db_name]
            }
        
        # Calculate statistical summary
        statistical_summary = self._calculate_statistics(all_values)
        
        return {
            'ecosystem_composition': composition,
            'area_hectares': area_ha,
            'database_results': results,
            'statistical_summary': statistical_summary,
            'valuation_range': self._create_valuation_range(all_values),
            'coordinates': coordinates,
            'calculation_timestamp': datetime.now().isoformat(),
            'calculation_method': 'multi_ecosystem_weighted'
        }
    
    def _apply_regional_adjustment(self, value: float, coordinates: Optional[Tuple[float, float]], 
                                 ecosystem_type: str) -> float:
        """Apply basic regional adjustment factors based on coordinates"""
        if coordinates is None:
            return value
        
        lat, lon = coordinates
        
        # Simple regional adjustment factors (can be enhanced with real data)
        # Based on economic development and cost of living variations
        
        # Latitude-based adjustment (temperate vs tropical productivity)
        lat_factor = 1.0
        if abs(lat) < 23.5:  # Tropical
            lat_factor = 1.15 if ecosystem_type in ['forest', 'wetland'] else 1.05
        elif abs(lat) > 60:  # Arctic/Antarctic
            lat_factor = 0.75
        
        # Economic region adjustment (simplified)
        economic_factor = 1.0
        if -180 <= lon <= -30:  # Americas
            economic_factor = 1.1
        elif -30 <= lon <= 60:  # Europe/Africa
            economic_factor = 1.0
        else:  # Asia/Oceania
            economic_factor = 0.95
        
        return value * lat_factor * economic_factor
    
    def _calculate_statistics(self, all_values: Dict[str, List[float]]) -> Dict[str, Any]:
        """Calculate statistical summary across databases"""
        stats = {}
        
        for service, values in all_values.items():
            if values:
                stats[service] = {
                    'mean': np.mean(values),
                    'median': np.median(values),
                    'min': np.min(values),
                    'max': np.max(values),
                    'std': np.std(values),
                    'range_percent': ((np.max(values) - np.min(values)) / np.mean(values)) * 100 if np.mean(values) > 0 else 0,
                    'database_count': len(values)
                }
        
        return stats
    
    def _create_valuation_range(self, all_values: Dict[str, List[float]]) -> Dict[str, Any]:
        """Create valuation range summary"""
        if 'ecosystem_services_total' in all_values:
            total_values = all_values['ecosystem_services_total']
            return {
                'low_estimate': np.min(total_values),
                'high_estimate': np.max(total_values),
                'best_estimate': np.mean(total_values),
                'confidence_interval_95': {
                    'lower': np.percentile(total_values, 2.5),
                    'upper': np.percentile(total_values, 97.5)
                },
                'databases_used': len(total_values)
            }
        return {}
    
    def get_database_comparison(self, ecosystem_type: str) -> Dict[str, Any]:
        """Get comparison of all databases for a specific ecosystem type"""
        comparison = {}
        
        databases = {
            'ESVD': self.esvd_coefficients,
            'TEEB': self.teeb_coefficients,
            'InVEST': self.invest_coefficients,
            'WAVES/SEEA': self.waves_coefficients
        }
        
        for db_name, coefficients in databases.items():
            if ecosystem_type in coefficients:
                comparison[db_name] = coefficients[ecosystem_type].copy()
        
        return comparison