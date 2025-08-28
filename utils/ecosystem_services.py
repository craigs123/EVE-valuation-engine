"""
Ecosystem Services Valuation Module
Calculates monetary values for provisioning, regulating, cultural and supporting ecosystem services
Now integrated with ESVD (Ecosystem Services Valuation Database) for authentic coefficients
Uses OpenLandMap STAC API for reliable global ecosystem detection
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
import math
from .precomputed_esvd_coefficients import get_precomputed_coefficients
from .openlandmap_stac_api import openlandmap_stac

class EcosystemServicesCalculator:
    """
    Calculates ecosystem services values across four main categories
    """
    
    def __init__(self):
        # Initialize pre-computed ESVD coefficients for optimal performance
        self.precomputed_esvd = get_precomputed_coefficients()
        
        # Performance cache for repeated calculations
        self._calculation_cache = {}
        
        # Quality multipliers based on ecosystem health
        self.quality_multipliers = {
            'excellent': 1.2,
            'good': 1.0,
            'fair': 0.8,
            'poor': 0.6,
            'degraded': 0.4
        }
    
    def calculate_ecosystem_services_value(self, satellite_data: Dict, area_bounds: Dict, 
                                         ecosystem_type: str = "forest") -> Dict[str, Any]:
        """
        Calculate total ecosystem services value using ESVD coefficients and track changes over time
        
        Args:
            satellite_data: Satellite data dictionary
            area_bounds: Area boundary information
            ecosystem_type: Type of ecosystem (forest, grassland, wetland, agricultural, coastal)
            
        Returns:
            Dictionary containing ecosystem services valuation results with ESVD data
        """
        try:
            if not satellite_data.get('time_series'):
                return {'error': 'No time series data available for ecosystem services calculation'}
            
            time_series = satellite_data['time_series']
            area_ha = self._calculate_area_hectares(area_bounds)
            
            # Calculate water exclusion for single ecosystem analysis
            total_area_ha = self._calculate_area_hectares(area_bounds)
            ecosystem_detection = satellite_data.get('ecosystem_detection', {})
            
            # Check if this is open water area that should be excluded
            is_open_water = ecosystem_detection.get('is_open_water', False)
            water_confidence = ecosystem_detection.get('water_confidence', 0)
            
            if is_open_water:
                # Mostly water - minimal land area for calculation
                water_area_ha = total_area_ha * max(0.8, water_confidence)  # Use water confidence
                land_area_ha = total_area_ha - water_area_ha
                effective_area_ha = land_area_ha
            else:
                water_area_ha = 0
                land_area_ha = total_area_ha
                effective_area_ha = total_area_ha
            
            # Use automatic ecosystem type detection if not provided
            if ecosystem_type is None:
                # Check for multi-ecosystem detection first
                multi_detection = satellite_data.get('multi_ecosystem_detection', {})
                if multi_detection.get('diversity_index', 1) > 1:
                    # Multiple ecosystems detected - use multi-ecosystem calculation
                    return self._calculate_multi_ecosystem_values(satellite_data, area_bounds, multi_detection)
                else:
                    # Single ecosystem - use primary detected type
                    ecosystem_type = ecosystem_detection.get('detected_type', 'forest')
                    detection_confidence = ecosystem_detection.get('confidence', 0.5)
            else:
                detection_confidence = 1.0
            
            # Get coordinates for regional adjustment
            coordinates = self._extract_coordinates(area_bounds)
            
            # Calculate values using pre-computed authentic ESVD coefficients (use effective land area)
            esvd_results = self.precomputed_esvd.calculate_ecosystem_values(
                ecosystem_type, effective_area_ha, coordinates if coordinates else None
            )
            
            # No fallback needed - pre-computed coefficients always available
            
            # Calculate services values for each time point using ESVD as baseline
            services_time_series = []
            total_values = []
            
            for data_point in time_series:
                # Determine ecosystem health quality from satellite indicators
                quality = self._assess_ecosystem_quality(data_point)
                quality_multiplier = self.quality_multipliers[quality]
                
                # Apply ESVD values with quality adjustments
                provisioning_value = self._apply_esvd_values(
                    esvd_results.get('provisioning', {}), quality_multiplier, data_point
                )
                
                regulating_value = self._apply_esvd_values(
                    esvd_results.get('regulating', {}), quality_multiplier, data_point
                )
                
                cultural_value = self._apply_esvd_values(
                    esvd_results.get('cultural', {}), quality_multiplier, data_point
                )
                
                supporting_value = self._apply_esvd_values(
                    esvd_results.get('supporting', {}), quality_multiplier, data_point
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
                    'area_hectares': effective_area_ha,
                    'esvd_metadata': esvd_results.get('metadata', {})
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
            
            # Get ESVD metadata
            esvd_metadata = esvd_results.get('metadata', {})
            
            return {
                'current_value': float(current_value),
                'total_annual_value': float(current_value),  # Add both keys for compatibility
                'previous_value': float(previous_value),
                'mean_value': float(mean_value),
                'trend_slope': float(trend),
                'annual_change_usd': float(annual_change),
                'value_per_hectare': float(current_value / effective_area_ha) if effective_area_ha > 0 else 0,
                'ecosystem_type': ecosystem_type,
                'detected_ecosystem_type': ecosystem_type,
                'area_hectares': float(effective_area_ha),  # Land area used for calculations
                'total_area_hectares': float(total_area_ha),  # Total selected area
                'water_area_hectares': float(water_area_ha),  # Excluded water area
                'is_open_water_area': is_open_water,  # Flag indicating if area is mostly water
                'ecosystem_detection': ecosystem_detection,
                'detection_confidence': detection_confidence,
                'time_series': services_time_series,
                'service_breakdown': {
                    'provisioning_percent': float(latest_services.get('provisioning', {}).get('total', 0) / current_value * 100) if current_value > 0 else 0,
                    'regulating_percent': float(latest_services.get('regulating', {}).get('total', 0) / current_value * 100) if current_value > 0 else 0,
                    'cultural_percent': float(latest_services.get('cultural', {}).get('total', 0) / current_value * 100) if current_value > 0 else 0,
                    'supporting_percent': float(latest_services.get('supporting', {}).get('total', 0) / current_value * 100) if current_value > 0 else 0
                },
                'esvd_results': esvd_results,  # Use the raw ESVD results which have service breakdown
                'valuation_summary': self._generate_valuation_summary(current_value, trend, ecosystem_type),
                'data_source': 'ESVD (Ecosystem Services Valuation Database)',
                'esvd_metadata': esvd_metadata,
                'regional_adjustment': esvd_metadata.get('regional_adjustment', 1.0),
                'database_version': esvd_metadata.get('database_version', 'ESVD APR2024V1.1')
            }
            
        except Exception as e:
            return {'error': f'Error calculating ESVD ecosystem services value: {str(e)}'}
    

    
    def _calculate_multi_ecosystem_values(self, satellite_data: Dict, area_bounds: Dict, 
                                        multi_detection: Dict) -> Dict[str, Any]:
        """
        Calculate ecosystem services values for areas with multiple ecosystem types
        
        Args:
            satellite_data: Satellite data dictionary
            area_bounds: Area boundary information
            multi_detection: Multi-ecosystem detection results
            
        Returns:
            Dictionary containing multi-ecosystem valuation results
        """
        try:
            time_series = satellite_data['time_series']
            total_area_ha = self._calculate_area_hectares(area_bounds)
            coordinates = self._extract_coordinates(area_bounds)
            
            # Calculate water exclusion based on detection results
            water_percentage = multi_detection.get('water_percentage', 0)
            water_area_ha = total_area_ha * (water_percentage / 100.0)
            land_area_ha = total_area_ha - water_area_ha
            
            ecosystem_composition = multi_detection.get('ecosystem_composition', {})
            primary_ecosystem = multi_detection.get('primary_ecosystem', 'forest')
            
            # Calculate values for each ecosystem type
            ecosystem_results = {}
            total_combined_value = 0
            combined_time_series = []
            
            # Initialize time series structure
            for data_point in time_series:
                combined_time_series.append({
                    'date': data_point['date'],
                    'total_value': 0,
                    'ecosystem_breakdown': {},
                    'area_breakdown': {}
                })
            
            # Calculate values for each ecosystem type
            for ecosystem_type, percentage in ecosystem_composition.items():
                if percentage < 1.0:  # Skip ecosystems with less than 1% coverage
                    continue
                
                # Calculate area for this ecosystem type (based on land area only)
                ecosystem_area_ha = land_area_ha * (percentage / 100.0)
                
                # Get ESVD values for this ecosystem type
                esvd_results = self.precomputed_esvd.calculate_ecosystem_values(
                    ecosystem_type, ecosystem_area_ha, coordinates
                )
                
                if 'error' in esvd_results:
                    continue
                
                # Calculate time series for this ecosystem
                ecosystem_time_series = []
                ecosystem_values = []
                
                for i, data_point in enumerate(time_series):
                    quality = self._assess_ecosystem_quality(data_point)
                    quality_multiplier = self.quality_multipliers[quality]
                    
                    # Apply ESVD values with quality adjustments
                    provisioning_value = self._apply_esvd_values(
                        esvd_results.get('provisioning', {}), quality_multiplier, data_point
                    )
                    regulating_value = self._apply_esvd_values(
                        esvd_results.get('regulating', {}), quality_multiplier, data_point
                    )
                    cultural_value = self._apply_esvd_values(
                        esvd_results.get('cultural', {}), quality_multiplier, data_point
                    )
                    supporting_value = self._apply_esvd_values(
                        esvd_results.get('supporting', {}), quality_multiplier, data_point
                    )
                    
                    ecosystem_total = (provisioning_value['total'] + regulating_value['total'] + 
                                     cultural_value['total'] + supporting_value['total'])
                    
                    ecosystem_values.append(ecosystem_total)
                    
                    # Add to combined time series
                    combined_time_series[i]['total_value'] += ecosystem_total
                    combined_time_series[i]['ecosystem_breakdown'][ecosystem_type] = ecosystem_total
                    combined_time_series[i]['area_breakdown'][ecosystem_type] = ecosystem_area_ha
                
                # Store ecosystem-specific results
                current_value = ecosystem_values[-1] if ecosystem_values else 0
                previous_value = ecosystem_values[-2] if len(ecosystem_values) > 1 else current_value
                trend = np.polyfit(range(len(ecosystem_values)), ecosystem_values, 1)[0] if len(ecosystem_values) > 1 else 0
                
                ecosystem_results[ecosystem_type] = {
                    'area_hectares': ecosystem_area_ha,
                    'area_percentage': percentage,
                    'current_value': float(current_value),
                    'previous_value': float(previous_value),
                    'value_per_hectare': float(current_value / ecosystem_area_ha) if ecosystem_area_ha > 0 else 0,
                    'trend_slope': float(trend),
                    'annual_change_usd': float(trend * 365) if trend != 0 else 0,
                    'esvd_metadata': esvd_results.get('metadata', {}),
                    'time_series': ecosystem_values
                }
                
                total_combined_value += current_value
            
            # Calculate combined statistics
            combined_values = [point['total_value'] for point in combined_time_series]
            current_total = combined_values[-1] if combined_values else 0
            previous_total = combined_values[-2] if len(combined_values) > 1 else current_total
            combined_trend = np.polyfit(range(len(combined_values)), combined_values, 1)[0] if len(combined_values) > 1 else 0
            
            # Calculate ecosystem diversity metrics
            diversity_metrics = {
                'shannon_diversity': self._calculate_shannon_diversity(ecosystem_composition),
                'simpson_diversity': self._calculate_simpson_diversity(ecosystem_composition),
                'dominant_ecosystem': primary_ecosystem,
                'ecosystem_count': len(ecosystem_composition),
                'homogeneity_index': multi_detection.get('homogeneity', 0)
            }
            
            # Calculate combined services for multi-ecosystem areas
            combined_services = {
                'provisioning': {'total': 0, 'services': {}},
                'regulating': {'total': 0, 'services': {}}, 
                'cultural': {'total': 0, 'services': {}},
                'supporting': {'total': 0, 'services': {}}
            }
            
            # Aggregate services from all ecosystems
            if combined_time_series:
                latest_data = combined_time_series[-1]
                for ecosystem_type in ecosystem_composition.keys():
                    if ecosystem_type in ecosystem_results:
                        # Get the latest ESVD results for this ecosystem
                        ecosystem_area_ha = land_area_ha * (ecosystem_composition[ecosystem_type] / 100.0)
                        coordinates = self._extract_coordinates(area_bounds)
                        
                        esvd_results = self.precomputed_esvd.calculate_ecosystem_values(
                            ecosystem_type, ecosystem_area_ha, coordinates
                        )
                        
                        if 'error' not in esvd_results:
                            for category in ['provisioning', 'regulating', 'cultural', 'supporting']:
                                if category in esvd_results:
                                    combined_services[category]['total'] += esvd_results[category].get('total', 0)
                                    # Aggregate individual services
                                    if 'services' in esvd_results[category]:
                                        for service, value in esvd_results[category]['services'].items():
                                            if service in combined_services[category]['services']:
                                                combined_services[category]['services'][service] += value
                                            else:
                                                combined_services[category]['services'][service] = value

            return {
                'current_value': float(current_total),
                'total_annual_value': float(current_total),  # Add both keys for compatibility
                'previous_value': float(previous_total),
                'value_change': float(current_total - previous_total),
                'annual_change_usd': float(combined_trend * 365) if combined_trend != 0 else 0,
                'value_per_hectare': float(current_total / land_area_ha) if land_area_ha > 0 else 0,
                'area_hectares': float(land_area_ha),  # Land area used for calculations
                'total_area_hectares': float(total_area_ha),  # Total selected area
                'water_area_hectares': float(water_area_ha),  # Excluded water area
                'water_percentage': float(water_percentage),  # Percentage of area that is water
                'ecosystem_type': 'multi_ecosystem',
                'primary_ecosystem': primary_ecosystem,
                'ecosystem_composition': ecosystem_composition,
                'ecosystem_results': ecosystem_results,
                'diversity_metrics': diversity_metrics,
                'multi_ecosystem_detection': multi_detection,
                'time_series': combined_time_series,
                'esvd_results': combined_services,  # Add combined services breakdown
                'valuation_summary': self._generate_multi_ecosystem_summary(ecosystem_composition, current_total, combined_trend),
                'data_source': 'ESVD (Ecosystem Services Valuation Database) - Multi-ecosystem Analysis',
                'calculation_method': 'spatial_composition_weighted_land_only'
            }
            
        except Exception as e:
            return {'error': f'Error calculating multi-ecosystem values: {str(e)}'}
    
    def _calculate_shannon_diversity(self, composition: Dict[str, float]) -> float:
        """Calculate Shannon diversity index for ecosystem composition"""
        import math
        total = sum(composition.values())
        if total == 0:
            return 0
        
        diversity = 0
        for percentage in composition.values():
            if percentage > 0:
                proportion = percentage / total
                diversity -= proportion * math.log(proportion)
        
        return diversity
    
    def _calculate_simpson_diversity(self, composition: Dict[str, float]) -> float:
        """Calculate Simpson diversity index for ecosystem composition"""
        total = sum(composition.values())
        if total == 0:
            return 0
        
        simpson = 0
        for percentage in composition.values():
            if percentage > 0:
                proportion = percentage / total
                simpson += proportion ** 2
        
        return 1 - simpson
    
    def _generate_multi_ecosystem_summary(self, composition: Dict[str, float], 
                                        total_value: float, trend: float) -> str:
        """Generate a summary for multi-ecosystem valuation"""
        dominant = max(composition.items(), key=lambda x: x[1])
        ecosystem_count = len(composition)
        
        trend_text = "increasing" if trend > 0 else "decreasing" if trend < 0 else "stable"
        
        return (f"Multi-ecosystem area with {ecosystem_count} ecosystem types. "
                f"Dominated by {dominant[0]} ({dominant[1]:.1f}%). "
                f"Total annual value: ${total_value:,.0f}. "
                f"Trend: {trend_text}.")
    
    # Legacy methods removed - now using pre-computed ESVD coefficients

    
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
        
        # First check if we have a cached area from the main app (for consistency)
        try:
            import streamlit as st
            if hasattr(st, 'session_state') and 'cached_area_ha' in st.session_state:
                cached_area = st.session_state.cached_area_ha
                if cached_area and cached_area > 0:
                    return cached_area
        except:
            pass  # Fall back to calculation if streamlit not available
        
        # Fallback: use same calculation as main app for consistency
        import numpy as np
        import math
        
        # Skip the last coordinate if it duplicates the first (polygon closure)
        coords = coords[:-1] if len(coords) > 1 and coords[-1] == coords[0] else coords
        
        if len(coords) < 3:
            return 100.0
        
        # Convert to NumPy array for consistency with main calculation
        coords_array = np.array(coords, dtype=np.float32)
        lons = coords_array[:, 0]
        lats = coords_array[:, 1]
        
        # Get average latitude for longitude correction
        avg_lat = float(np.mean(lats))
        
        # Convert to approximate area in km² with latitude-corrected longitude  
        # 1° latitude ≈ 111.32 km everywhere
        # 1° longitude ≈ 111.32 * cos(latitude) km
        lat_km_per_deg = 111.32
        lon_km_per_deg = 111.32 * math.cos(math.radians(avg_lat))
        
        # Use same vectorized shoelace formula as main app
        area_km2 = 0.5 * abs(np.sum(lons * np.roll(lats, -1) - lats * np.roll(lons, -1))) * lat_km_per_deg * lon_km_per_deg
        
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
    
    def _extract_coordinates(self, area_bounds: Dict) -> Optional[Tuple[float, float]]:
        """
        Extract center coordinates from area bounds for regional adjustment
        """
        try:
            if not area_bounds or 'coordinates' not in area_bounds:
                return None
            
            coords = area_bounds['coordinates']
            if len(coords) < 3:
                return None
            
            # Calculate centroid
            lats = [coord[1] for coord in coords]
            lons = [coord[0] for coord in coords]
            
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
            
            return (center_lat, center_lon)
        except Exception:
            return None
    
    def _apply_esvd_values(self, esvd_category: Dict, quality_multiplier: float, data_point: Dict) -> Dict[str, float]:
        """
        Apply ESVD values with ecosystem quality adjustments
        """
        result = {}
        
        for service, value in esvd_category.items():
            if service == 'total':
                continue
                
            # Apply quality and satellite-based adjustments
            if isinstance(value, (int, float)):
                # Apply base quality multiplier
                adjusted_value = value * quality_multiplier
                
                # Apply additional satellite-based adjustments
                if 'provisioning' in str(service).lower():
                    # Adjust provisioning based on vegetation health
                    red = data_point.get('red_mean', 0)
                    nir = data_point.get('nir_mean', 0)
                    ndvi = (nir - red) / (nir + red) if (nir + red) != 0 else 0
                    vegetation_factor = max(0.5, min(1.5, ndvi * 2))
                    adjusted_value *= vegetation_factor
                
                elif 'regulating' in str(service).lower():
                    # Adjust regulating based on vegetation cover
                    red = data_point.get('red_mean', 0)
                    nir = data_point.get('nir_mean', 0)
                    ndvi = (nir - red) / (nir + red) if (nir + red) != 0 else 0
                    regulation_factor = max(0.6, min(1.4, (ndvi + 0.5) * 1.2))
                    adjusted_value *= regulation_factor
                
                result[service] = float(adjusted_value)
            else:
                result[service] = 0.0
        
        result['total'] = sum(result.values())
        return result
    
    def _calculate_legacy_values(self, satellite_data: Dict, area_bounds: Dict, ecosystem_type: str) -> Dict[str, Any]:
        """
        Fallback calculation using legacy coefficients when ESVD fails
        """
        try:
            time_series = satellite_data['time_series']
            area_ha = self._calculate_area_hectares(area_bounds)
            
            # Use legacy calculation method
            services_time_series = []
            total_values = []
            
            for data_point in time_series:
                quality = self._assess_ecosystem_quality(data_point)
                quality_multiplier = self.quality_multipliers[quality]
                
                # Use simplified legacy values for fallback
                base_value_per_ha = 2000  # Base ecosystem value per hectare
                
                provisioning_value = {'total': base_value_per_ha * 0.3 * area_ha * quality_multiplier}
                regulating_value = {'total': base_value_per_ha * 0.4 * area_ha * quality_multiplier}
                cultural_value = {'total': base_value_per_ha * 0.2 * area_ha * quality_multiplier}
                supporting_value = {'total': base_value_per_ha * 0.1 * area_ha * quality_multiplier}
                
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
            annual_change = trend * 365 if trend != 0 else 0
            
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
                'valuation_summary': self._generate_valuation_summary(current_value, trend, ecosystem_type),
                'data_source': 'Legacy coefficients (fallback)',
                'esvd_metadata': {'status': 'fallback_used'},
                'regional_adjustment': 1.0,
                'database_version': 'Legacy v1.0'
            }
            
        except Exception as e:
            return {'error': f'Legacy calculation also failed: {str(e)}'}

# Main ecosystem detection function that should be imported by app.py
def detect_ecosystem_type_enhanced(coordinates: List, num_samples: int = 10) -> Dict[str, Any]:
    """
    Enhanced ecosystem detection using OpenLandMap STAC API - replaces USGS integration
    """
    try:
        if not coordinates or len(coordinates) < 3:
            return {
                'primary_ecosystem': 'Grassland',
                'confidence': 0.5,
                'successful_queries': 0,
                'ecosystem_distribution': {'Grassland': {'count': 1, 'confidence': 0.5}},
                'error': 'Insufficient coordinates provided'
            }
        
        # Extract coordinate bounds
        lats = [coord[1] for coord in coordinates if len(coord) >= 2]
        lons = [coord[0] for coord in coordinates if len(coord) >= 2]
        
        if not lats or not lons:
            return {
                'primary_ecosystem': 'Grassland',
                'confidence': 0.5,
                'successful_queries': 0,
                'ecosystem_distribution': {'Grassland': {'count': 1, 'confidence': 0.5}},
                'error': 'Invalid coordinate format'
            }
        
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)
        
        # Generate sample points
        sample_points = []
        for i in range(num_samples):
            lat = min_lat + (max_lat - min_lat) * np.random.random()
            lon = min_lon + (max_lon - min_lon) * np.random.random()
            sample_points.append((lat, lon))
        
        # Query ecosystem types using OpenLandMap STAC API
        ecosystem_results = []
        successful_queries = 0
        stac_data_collected = []
        
        for lat, lon in sample_points:
            try:
                # Use new OpenLandMap STAC API instead of USGS
                stac_result = openlandmap_stac.get_ecosystem_type(lat, lon)
                if stac_result and stac_result.get('ecosystem_type'):
                    ecosystem_results.append({
                        'ecosystem_type': stac_result['ecosystem_type'],
                        'confidence': stac_result.get('confidence', 0.7),
                        'source': stac_result.get('data_source', 'OpenLandMap STAC'),
                        'coordinates': stac_result.get('coordinates', {'lat': lat, 'lon': lon})
                    })
                    stac_data_collected.append(stac_result)
                    successful_queries += 1
            except Exception as e:
                print(f"STAC query failed for ({lat}, {lon}): {e}")
                continue
        
        if not ecosystem_results:
            # Fallback to center point detection
            center_lat = (min_lat + max_lat) / 2
            center_lon = (min_lon + max_lon) / 2
            fallback_result = openlandmap_stac._geographic_fallback_detection(center_lat, center_lon)
            
            return {
                'primary_ecosystem': fallback_result,
                'confidence': 0.65,
                'successful_queries': 0,
                'ecosystem_distribution': {fallback_result: {'count': 1, 'confidence': 0.65}},
                'error': 'STAC API queries failed, used geographic fallback',
                'stac_data': []
            }
        
        # Count ecosystem types
        ecosystem_counts = {}
        total_confidence = 0
        
        for result in ecosystem_results:
            ecosystem_type = result.get('ecosystem_type', 'Grassland')
            confidence = result.get('confidence', 0.5)
            
            if ecosystem_type not in ecosystem_counts:
                ecosystem_counts[ecosystem_type] = {'count': 0, 'confidence': 0}
            
            ecosystem_counts[ecosystem_type]['count'] += 1
            ecosystem_counts[ecosystem_type]['confidence'] += confidence
            total_confidence += confidence
        
        # Calculate averages
        for eco_type in ecosystem_counts:
            count = ecosystem_counts[eco_type]['count']
            ecosystem_counts[eco_type]['confidence'] = ecosystem_counts[eco_type]['confidence'] / count
        
        # Find primary ecosystem
        primary_ecosystem = max(ecosystem_counts.items(), key=lambda x: x[1]['count'])[0]
        primary_confidence = ecosystem_counts[primary_ecosystem]['confidence']
        
        return {
            'primary_ecosystem': primary_ecosystem,
            'confidence': primary_confidence,
            'successful_queries': successful_queries,
            'ecosystem_distribution': ecosystem_counts,
            'sample_points': len(sample_points),
            'detection_method': 'OpenLandMap STAC API',
            'stac_data': stac_data_collected  # Include raw STAC data for transparency
        }
        
    except Exception as e:
        return {
            'primary_ecosystem': 'Grassland',
            'confidence': 0.5,
            'successful_queries': 0,
            'ecosystem_distribution': {'Grassland': {'count': 1, 'confidence': 0.5}},
            'error': f'Detection failed: {str(e)}',
            'stac_data': []
        }

def get_ecosystem_service_values(ecosystem_type: str, coordinates: List, 
                               start_date: datetime, end_date: datetime,
                               num_samples: int = 10) -> Dict[str, Any]:
    """
    Get ecosystem service values for a given area and time period
    """
    try:
        # Initialize calculator
        calculator = EcosystemServicesCalculator()
        
        # Create area bounds from coordinates
        area_bounds = {'coordinates': coordinates}
        
        # Get satellite data
        from .usgs_integration import usgs_integrator
        satellite_data = usgs_integrator.get_landsat_data(
            area_bounds, start_date, end_date
        )
        
        # Calculate ecosystem services
        results = calculator.calculate_ecosystem_services_value(
            satellite_data, area_bounds, ecosystem_type
        )
        
        return results
        
    except Exception as e:
        return {'error': f'Failed to calculate ecosystem service values: {str(e)}'}