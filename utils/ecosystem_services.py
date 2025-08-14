"""
Ecosystem Services Valuation Module
Calculates monetary values for provisioning, regulating, cultural and supporting ecosystem services
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Tuple
import math

class EcosystemServicesCalculator:
    """
    Calculates ecosystem services values across four main categories
    """
    
    def __init__(self):
        # Economic valuation coefficients (USD per hectare per year)
        self.service_values = {
            'provisioning': {
                'food_production': {
                    'forest': 32,
                    'grassland': 54,
                    'wetland': 25,
                    'agricultural': 92,
                    'coastal': 38
                },
                'fresh_water': {
                    'forest': 28,
                    'grassland': 3,
                    'wetland': 15,
                    'agricultural': 2,
                    'coastal': 7
                },
                'timber_fiber': {
                    'forest': 721,
                    'grassland': 2,
                    'wetland': 162,
                    'agricultural': 8,
                    'coastal': 12
                },
                'genetic_resources': {
                    'forest': 79,
                    'grassland': 13,
                    'wetland': 49,
                    'agricultural': 6,
                    'coastal': 33
                }
            },
            'regulating': {
                'climate_regulation': {
                    'forest': 969,
                    'grassland': 127,
                    'wetland': 1654,
                    'agricultural': 39,
                    'coastal': 381
                },
                'water_regulation': {
                    'forest': 1380,
                    'grassland': 87,
                    'wetland': 15567,
                    'agricultural': 18,
                    'coastal': 2143
                },
                'erosion_control': {
                    'forest': 1056,
                    'grassland': 129,
                    'wetland': 8498,
                    'agricultural': 24,
                    'coastal': 2729
                },
                'pollution_control': {
                    'forest': 88,
                    'grassland': 87,
                    'wetland': 6696,
                    'agricultural': 9,
                    'coastal': 51
                },
                'disease_control': {
                    'forest': 60,
                    'grassland': 3,
                    'wetland': 25,
                    'agricultural': 1,
                    'coastal': 8
                }
            },
            'cultural': {
                'recreation': {
                    'forest': 112,
                    'grassland': 23,
                    'wetland': 658,
                    'agricultural': 3,
                    'coastal': 2016
                },
                'aesthetic_value': {
                    'forest': 2,
                    'grassland': 1,
                    'wetland': 3,
                    'agricultural': 1,
                    'coastal': 12
                },
                'spiritual_value': {
                    'forest': 3,
                    'grassland': 1,
                    'wetland': 15,
                    'agricultural': 1,
                    'coastal': 8
                },
                'educational_value': {
                    'forest': 258,
                    'grassland': 1,
                    'wetland': 20,
                    'agricultural': 1,
                    'coastal': 35
                }
            },
            'supporting': {
                'soil_formation': {
                    'forest': 13,
                    'grassland': 2,
                    'wetland': 3,
                    'agricultural': 1,
                    'coastal': 1
                },
                'nutrient_cycling': {
                    'forest': 114,
                    'grassland': 4,
                    'wetland': 19,
                    'agricultural': 2,
                    'coastal': 7
                },
                'primary_production': {
                    'forest': 161,
                    'grassland': 28,
                    'wetland': 89,
                    'agricultural': 12,
                    'coastal': 112
                },
                'habitat_provision': {
                    'forest': 302,
                    'grassland': 23,
                    'wetland': 1619,
                    'agricultural': 3,
                    'coastal': 405
                }
            }
        }
        
        # Quality multipliers based on ecosystem health
        self.quality_multipliers = {
            'excellent': 1.2,
            'good': 1.0,
            'fair': 0.8,
            'poor': 0.6,
            'degraded': 0.4
        }
    
    def calculate_ecosystem_services_value(self, satellite_data: Dict, area_bounds: Dict, 
                                         ecosystem_type: str = 'forest') -> Dict[str, Any]:
        """
        Calculate total ecosystem services value and track changes over time
        
        Args:
            satellite_data: Satellite data dictionary
            area_bounds: Area boundary information
            ecosystem_type: Type of ecosystem (forest, grassland, wetland, agricultural, coastal)
            
        Returns:
            Dictionary containing ecosystem services valuation results
        """
        try:
            if not satellite_data.get('time_series'):
                return {'error': 'No time series data available for ecosystem services calculation'}
            
            time_series = satellite_data['time_series']
            area_ha = self._calculate_area_hectares(area_bounds)
            
            # Calculate services values for each time point
            services_time_series = []
            total_values = []
            
            for data_point in time_series:
                # Determine ecosystem health quality from satellite indicators
                quality = self._assess_ecosystem_quality(data_point)
                quality_multiplier = self.quality_multipliers[quality]
                
                # Calculate values for each service category
                provisioning_value = self._calculate_provisioning_services(
                    ecosystem_type, area_ha, quality_multiplier, data_point
                )
                
                regulating_value = self._calculate_regulating_services(
                    ecosystem_type, area_ha, quality_multiplier, data_point
                )
                
                cultural_value = self._calculate_cultural_services(
                    ecosystem_type, area_ha, quality_multiplier, data_point
                )
                
                supporting_value = self._calculate_supporting_services(
                    ecosystem_type, area_ha, quality_multiplier, data_point
                )
                
                total_value = (provisioning_value['total'] + regulating_value['total'] + 
                              cultural_value['total'] + supporting_value['total'])
                
                total_values.append(total_value)
                
                services_time_series.append({
                    'date': data_point['date'],
                    'total_value': total_value,
                    'provisioning': provisioning_value,
                    'regulating': regulating_value,
                    'cultural': cultural_value,
                    'supporting': supporting_value,
                    'ecosystem_quality': quality,
                    'area_hectares': area_ha
                })
            
            # Calculate statistics
            current_value = total_values[-1] if total_values else 0
            previous_value = total_values[-2] if len(total_values) > 1 else current_value
            mean_value = np.mean(total_values) if total_values else 0
            trend = np.polyfit(range(len(total_values)), total_values, 1)[0] if len(total_values) > 1 else 0
            
            # Calculate annual change
            annual_change = trend * 365 if trend != 0 else 0
            
            # Calculate service category contributions
            latest_services = services_time_series[-1] if services_time_series else {}
            
            return {
                'current_value': float(current_value),
                'previous_value': float(previous_value),
                'mean_value': float(mean_value),
                'trend_slope': float(trend),
                'annual_change_usd': float(annual_change),
                'value_per_hectare': float(current_value / area_ha) if area_ha > 0 else 0,
                'ecosystem_type': ecosystem_type,
                'area_hectares': float(area_ha),
                'time_series': services_time_series,
                'service_breakdown': {
                    'provisioning_percent': float(latest_services.get('provisioning', {}).get('total', 0) / current_value * 100) if current_value > 0 else 0,
                    'regulating_percent': float(latest_services.get('regulating', {}).get('total', 0) / current_value * 100) if current_value > 0 else 0,
                    'cultural_percent': float(latest_services.get('cultural', {}).get('total', 0) / current_value * 100) if current_value > 0 else 0,
                    'supporting_percent': float(latest_services.get('supporting', {}).get('total', 0) / current_value * 100) if current_value > 0 else 0
                },
                'valuation_summary': self._generate_valuation_summary(current_value, trend, ecosystem_type)
            }
            
        except Exception as e:
            return {'error': f'Error calculating ecosystem services value: {str(e)}'}
    
    def _calculate_provisioning_services(self, ecosystem_type: str, area_ha: float, 
                                       quality_multiplier: float, data_point: Dict) -> Dict[str, float]:
        """Calculate provisioning services values"""
        services = self.service_values['provisioning']
        
        # Adjust values based on vegetation health (NDVI)
        red = data_point.get('red_mean', 0)
        nir = data_point.get('nir_mean', 0)
        ndvi = (nir - red) / (nir + red) if (nir + red) != 0 else 0
        vegetation_factor = max(0.5, min(1.5, ndvi * 2))  # Scale NDVI to vegetation productivity
        
        values = {}
        for service, type_values in services.items():
            base_value = type_values.get(ecosystem_type, 0)
            adjusted_value = base_value * area_ha * quality_multiplier * vegetation_factor
            values[service] = float(adjusted_value)
        
        values['total'] = sum(values.values())
        return values
    
    def _calculate_regulating_services(self, ecosystem_type: str, area_ha: float, 
                                     quality_multiplier: float, data_point: Dict) -> Dict[str, float]:
        """Calculate regulating services values"""
        services = self.service_values['regulating']
        
        # Adjust values based on vegetation cover and health
        red = data_point.get('red_mean', 0)
        nir = data_point.get('nir_mean', 0)
        ndvi = (nir - red) / (nir + red) if (nir + red) != 0 else 0
        regulation_factor = max(0.6, min(1.4, (ndvi + 0.5) * 1.2))
        
        values = {}
        for service, type_values in services.items():
            base_value = type_values.get(ecosystem_type, 0)
            adjusted_value = base_value * area_ha * quality_multiplier * regulation_factor
            values[service] = float(adjusted_value)
        
        values['total'] = sum(values.values())
        return values
    
    def _calculate_cultural_services(self, ecosystem_type: str, area_ha: float, 
                                   quality_multiplier: float, data_point: Dict) -> Dict[str, float]:
        """Calculate cultural services values"""
        services = self.service_values['cultural']
        
        # Cultural services are less dependent on vegetation but affected by overall quality
        aesthetic_factor = quality_multiplier  # Direct relationship with ecosystem quality
        
        values = {}
        for service, type_values in services.items():
            base_value = type_values.get(ecosystem_type, 0)
            adjusted_value = base_value * area_ha * aesthetic_factor
            values[service] = float(adjusted_value)
        
        values['total'] = sum(values.values())
        return values
    
    def _calculate_supporting_services(self, ecosystem_type: str, area_ha: float, 
                                     quality_multiplier: float, data_point: Dict) -> Dict[str, float]:
        """Calculate supporting services values"""
        services = self.service_values['supporting']
        
        # Supporting services are fundamental and relatively stable
        stability_factor = max(0.8, quality_multiplier)  # More stable than other services
        
        values = {}
        for service, type_values in services.items():
            base_value = type_values.get(ecosystem_type, 0)
            adjusted_value = base_value * area_ha * stability_factor
            values[service] = float(adjusted_value)
        
        values['total'] = sum(values.values())
        return values
    
    def _assess_ecosystem_quality(self, data_point: Dict) -> str:
        """Assess ecosystem quality based on satellite indicators"""
        red = data_point.get('red_mean', 0)
        nir = data_point.get('nir_mean', 0)
        cloud_coverage = data_point.get('cloud_coverage', 0)
        data_quality = data_point.get('data_quality', 'unknown')
        
        # Calculate NDVI
        ndvi = (nir - red) / (nir + red) if (nir + red) != 0 else 0
        
        # Quality assessment based on multiple factors
        quality_score = 0
        
        # NDVI contribution (40% weight)
        if ndvi > 0.7:
            quality_score += 40
        elif ndvi > 0.5:
            quality_score += 30
        elif ndvi > 0.3:
            quality_score += 20
        elif ndvi > 0.1:
            quality_score += 10
        
        # Data quality contribution (30% weight)
        if data_quality == 'good':
            quality_score += 30
        elif data_quality == 'fair':
            quality_score += 20
        else:
            quality_score += 10
        
        # Cloud coverage contribution (20% weight)
        if cloud_coverage < 10:
            quality_score += 20
        elif cloud_coverage < 20:
            quality_score += 15
        elif cloud_coverage < 30:
            quality_score += 10
        else:
            quality_score += 5
        
        # Spectral health contribution (10% weight)
        if nir > 0.3:  # Healthy vegetation
            quality_score += 10
        elif nir > 0.2:
            quality_score += 7
        else:
            quality_score += 3
        
        # Convert score to quality category
        if quality_score >= 85:
            return 'excellent'
        elif quality_score >= 70:
            return 'good'
        elif quality_score >= 55:
            return 'fair'
        elif quality_score >= 40:
            return 'poor'
        else:
            return 'degraded'
    
    def _calculate_area_hectares(self, area_bounds: Dict) -> float:
        """Calculate area in hectares from coordinates"""
        if not area_bounds or 'coordinates' not in area_bounds:
            return 100.0  # Default area
        
        coords = area_bounds['coordinates']
        if len(coords) < 3:
            return 100.0
        
        # Simple area calculation using shoelace formula
        lats = [coord[1] for coord in coords]
        lons = [coord[0] for coord in coords]
        
        # Convert to approximate area in km²
        area_km2 = abs(sum((lons[i] * lats[i+1] - lons[i+1] * lats[i]) 
                          for i in range(-1, len(lons)-1))) * 111.32 * 111.32 / 2
        
        # Convert to hectares
        area_ha = area_km2 * 100
        
        return max(1.0, area_ha)  # Minimum 1 hectare
    
    def _generate_valuation_summary(self, current_value: float, trend: float, ecosystem_type: str) -> str:
        """Generate a summary of the ecosystem valuation"""
        trend_direction = "increasing" if trend > 100 else "decreasing" if trend < -100 else "stable"
        
        value_category = "very high" if current_value > 50000 else \
                        "high" if current_value > 20000 else \
                        "moderate" if current_value > 10000 else \
                        "low" if current_value > 5000 else "very low"
        
        return f"This {ecosystem_type} ecosystem provides {value_category} economic value " \
               f"(${current_value:,.0f}/year) with {trend_direction} trend " \
               f"(${trend*365:+,.0f}/year change rate)."

    def calculate_service_category_trends(self, services_data: Dict) -> Dict[str, Any]:
        """Calculate trends for each ecosystem service category"""
        if 'time_series' not in services_data:
            return {}
        
        time_series = services_data['time_series']
        categories = ['provisioning', 'regulating', 'cultural', 'supporting']
        
        trends = {}
        for category in categories:
            values = []
            for point in time_series:
                if category in point and 'total' in point[category]:
                    values.append(point[category]['total'])
            
            if len(values) > 1:
                trend = np.polyfit(range(len(values)), values, 1)[0]
                current = values[-1] if values else 0
                previous = values[-2] if len(values) > 1 else current
                
                trends[category] = {
                    'current_value': float(current),
                    'trend_slope': float(trend),
                    'annual_change': float(trend * 365),
                    'change_percent': float((current - previous) / previous * 100) if previous != 0 else 0
                }
        
        return trends