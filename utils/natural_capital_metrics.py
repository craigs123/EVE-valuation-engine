"""
Natural Capital Metrics Calculation Module
Calculates various ecosystem health and natural capital indicators
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Tuple
import math

class NaturalCapitalCalculator:
    """
    Calculates natural capital metrics from satellite data
    """
    
    def __init__(self):
        self.carbon_conversion_factors = {
            'forest': 150,  # tons CO2/hectare
            'grassland': 50,
            'wetland': 200,
            'agricultural': 30,
            'urban': 5
        }
        
        self.biodiversity_weights = {
            'vegetation_diversity': 0.4,
            'habitat_connectivity': 0.3,
            'edge_density': 0.2,
            'fragmentation': 0.1
        }
    
    def calculate_metric(self, metric_name: str, satellite_data: Dict, area_bounds: Dict) -> Dict[str, Any]:
        """
        Calculate a specific natural capital metric
        
        Args:
            metric_name: Name of the metric to calculate
            satellite_data: Satellite data dictionary
            area_bounds: Area boundary information
            
        Returns:
            Dictionary containing metric results
        """
        try:
            if metric_name == 'NDVI':
                return self._calculate_ndvi(satellite_data, area_bounds)
            elif metric_name == 'forest_cover':
                return self._calculate_forest_cover(satellite_data, area_bounds)
            elif metric_name == 'carbon_storage':
                return self._calculate_carbon_storage(satellite_data, area_bounds)
            elif metric_name == 'water_quality':
                return self._calculate_water_quality(satellite_data, area_bounds)
            elif metric_name == 'biodiversity_index':
                return self._calculate_biodiversity_index(satellite_data, area_bounds)
            else:
                return {'error': f'Unknown metric: {metric_name}'}
                
        except Exception as e:
            return {'error': f'Error calculating {metric_name}: {str(e)}'}
    
    def _calculate_ndvi(self, satellite_data: Dict, area_bounds: Dict) -> Dict[str, Any]:
        """
        Calculate Normalized Difference Vegetation Index
        """
        if not satellite_data.get('time_series'):
            return {'error': 'No time series data available for NDVI calculation'}
        
        time_series = satellite_data['time_series']
        ndvi_time_series = []
        ndvi_values = []
        
        for data_point in time_series:
            red = data_point.get('red_mean', 0)
            nir = data_point.get('nir_mean', 0)
            
            # Calculate NDVI: (NIR - Red) / (NIR + Red)
            if (nir + red) != 0:
                ndvi = (nir - red) / (nir + red)
            else:
                ndvi = 0
            
            ndvi_values.append(ndvi)
            ndvi_time_series.append({
                'date': data_point['date'],
                'value': ndvi,
                'quality': data_point.get('data_quality', 'unknown')
            })
        
        # Calculate statistics
        current_ndvi = ndvi_values[-1] if ndvi_values else 0
        previous_ndvi = ndvi_values[-2] if len(ndvi_values) > 1 else current_ndvi
        mean_ndvi = np.mean(ndvi_values) if ndvi_values else 0
        std_ndvi = np.std(ndvi_values) if ndvi_values else 0
        trend = np.polyfit(range(len(ndvi_values)), ndvi_values, 1)[0] if len(ndvi_values) > 1 else 0
        
        # Interpret NDVI values
        vegetation_health = self._interpret_ndvi(current_ndvi)
        
        return {
            'current_value': float(current_ndvi),
            'previous_value': float(previous_ndvi),
            'mean_value': float(mean_ndvi),
            'std_value': float(std_ndvi),
            'trend_slope': float(trend),
            'vegetation_health': vegetation_health,
            'time_series': ndvi_time_series,
            'spatial_data': {
                'min_ndvi': float(min(ndvi_values)) if ndvi_values else 0,
                'max_ndvi': float(max(ndvi_values)) if ndvi_values else 0,
                'coefficient_of_variation': float(std_ndvi / mean_ndvi) if mean_ndvi != 0 else 0
            }
        }
    
    def _calculate_forest_cover(self, satellite_data: Dict, area_bounds: Dict) -> Dict[str, Any]:
        """
        Calculate forest cover percentage using NDVI and other indices
        """
        if not satellite_data.get('time_series'):
            return {'error': 'No time series data available for forest cover calculation'}
        
        time_series = satellite_data['time_series']
        forest_cover_series = []
        forest_percentages = []
        
        for data_point in time_series:
            red = data_point.get('red_mean', 0)
            nir = data_point.get('nir_mean', 0)
            swir1 = data_point.get('swir1_mean', 0)
            
            # Calculate NDVI
            if (nir + red) != 0:
                ndvi = (nir - red) / (nir + red)
            else:
                ndvi = 0
            
            # Calculate NDWI (Normalized Difference Water Index) for water masking
            if (nir + swir1) != 0:
                ndwi = (nir - swir1) / (nir + swir1)
            else:
                ndwi = 0
            
            # Forest classification based on NDVI thresholds and spectral characteristics
            # Typical forest NDVI > 0.6, non-water (NDWI < 0.3), high NIR reflectance
            forest_threshold = 0.6
            water_threshold = 0.3
            
            # Simulate pixel-level classification
            total_pixels = 100  # Assuming 100 pixels in the area
            forest_pixels = 0
            
            # Generate realistic distribution based on mean values
            for _ in range(total_pixels):
                pixel_ndvi = np.random.normal(ndvi, 0.1)
                pixel_ndwi = np.random.normal(ndwi, 0.05)
                pixel_nir = np.random.normal(nir, 0.02)
                
                if (pixel_ndvi > forest_threshold and 
                    pixel_ndwi < water_threshold and 
                    pixel_nir > 0.3):
                    forest_pixels += 1
            
            forest_percentage = (forest_pixels / total_pixels) * 100
            forest_percentages.append(forest_percentage)
            
            forest_cover_series.append({
                'date': data_point['date'],
                'value': forest_percentage,
                'ndvi_base': ndvi,
                'quality': data_point.get('data_quality', 'unknown')
            })
        
        # Calculate statistics
        current_cover = forest_percentages[-1] if forest_percentages else 0
        previous_cover = forest_percentages[-2] if len(forest_percentages) > 1 else current_cover
        mean_cover = np.mean(forest_percentages) if forest_percentages else 0
        trend = np.polyfit(range(len(forest_percentages)), forest_percentages, 1)[0] if len(forest_percentages) > 1 else 0
        
        # Calculate area in hectares (approximate)
        area_ha = self._calculate_area_hectares(area_bounds)
        forest_area_ha = (current_cover / 100) * area_ha
        
        return {
            'current_value': float(current_cover),
            'previous_value': float(previous_cover),
            'mean_value': float(mean_cover),
            'trend_slope': float(trend),
            'forest_area_hectares': float(forest_area_ha),
            'total_area_hectares': float(area_ha),
            'time_series': forest_cover_series,
            'spatial_data': {
                'forest_density': 'high' if current_cover > 70 else 'medium' if current_cover > 30 else 'low',
                'canopy_closure': float(current_cover * 0.8),  # Approximate canopy closure
                'fragmentation_index': self._calculate_fragmentation_index(forest_percentages)
            }
        }
    
    def _calculate_carbon_storage(self, satellite_data: Dict, area_bounds: Dict) -> Dict[str, Any]:
        """
        Estimate carbon storage based on vegetation indices and land cover
        """
        if not satellite_data.get('time_series'):
            return {'error': 'No time series data available for carbon storage calculation'}
        
        # First get forest cover data
        forest_data = self._calculate_forest_cover(satellite_data, area_bounds)
        if 'error' in forest_data:
            return forest_data
        
        time_series = satellite_data['time_series']
        carbon_series = []
        carbon_estimates = []
        
        area_ha = self._calculate_area_hectares(area_bounds)
        
        for i, data_point in enumerate(time_series):
            # Get corresponding forest cover
            forest_cover = forest_data['time_series'][i]['value'] if i < len(forest_data['time_series']) else 0
            
            # Calculate different land cover types (simplified)
            forest_fraction = forest_cover / 100
            grassland_fraction = max(0, (100 - forest_cover - 20) / 100)  # Assume 20% other/urban
            other_fraction = 1 - forest_fraction - grassland_fraction
            
            # Calculate carbon storage for different land covers
            forest_carbon = (forest_fraction * area_ha * self.carbon_conversion_factors['forest'])
            grassland_carbon = (grassland_fraction * area_ha * self.carbon_conversion_factors['grassland'])
            other_carbon = (other_fraction * area_ha * self.carbon_conversion_factors['urban'])
            
            total_carbon = forest_carbon + grassland_carbon + other_carbon
            carbon_estimates.append(total_carbon)
            
            carbon_series.append({
                'date': data_point['date'],
                'value': total_carbon,
                'forest_carbon': forest_carbon,
                'grassland_carbon': grassland_carbon,
                'other_carbon': other_carbon,
                'quality': data_point.get('data_quality', 'unknown')
            })
        
        # Calculate statistics
        current_carbon = carbon_estimates[-1] if carbon_estimates else 0
        previous_carbon = carbon_estimates[-2] if len(carbon_estimates) > 1 else current_carbon
        mean_carbon = np.mean(carbon_estimates) if carbon_estimates else 0
        trend = np.polyfit(range(len(carbon_estimates)), carbon_estimates, 1)[0] if len(carbon_estimates) > 1 else 0
        
        return {
            'current_value': float(current_carbon),
            'previous_value': float(previous_carbon),
            'mean_value': float(mean_carbon),
            'trend_slope': float(trend),
            'carbon_per_hectare': float(current_carbon / area_ha) if area_ha > 0 else 0,
            'total_area_hectares': float(area_ha),
            'time_series': carbon_series,
            'spatial_data': {
                'forest_carbon_density': float(self.carbon_conversion_factors['forest']),
                'grassland_carbon_density': float(self.carbon_conversion_factors['grassland']),
                'sequestration_potential': float(trend * 365) if trend > 0 else 0  # Annual potential
            }
        }
    
    def _calculate_water_quality(self, satellite_data: Dict, area_bounds: Dict) -> Dict[str, Any]:
        """
        Calculate water quality proxies using spectral indices
        """
        if not satellite_data.get('time_series'):
            return {'error': 'No time series data available for water quality calculation'}
        
        time_series = satellite_data['time_series']
        water_quality_series = []
        turbidity_values = []
        chlorophyll_values = []
        
        for data_point in time_series:
            red = data_point.get('red_mean', 0)
            green = data_point.get('green_mean', 0)
            blue = data_point.get('blue_mean', 0)
            nir = data_point.get('nir_mean', 0)
            
            # Calculate water quality indices
            
            # Turbidity proxy using red/green ratio
            if green != 0:
                turbidity_index = red / green
            else:
                turbidity_index = 1
            
            # Chlorophyll-a proxy using blue/green ratio
            if blue != 0:
                chlorophyll_index = green / blue
            else:
                chlorophyll_index = 1
            
            # Normalized difference turbidity index
            if (red + green) != 0:
                ndti = (red - green) / (red + green)
            else:
                ndti = 0
            
            # Water quality score (0-100, higher is better)
            # Lower turbidity and moderate chlorophyll indicate better water quality
            turbidity_score = max(0, 100 - (turbidity_index - 1) * 100)
            chlorophyll_score = max(0, 100 - abs(chlorophyll_index - 1.5) * 50)
            
            water_quality_score = (turbidity_score + chlorophyll_score) / 2
            
            turbidity_values.append(turbidity_index)
            chlorophyll_values.append(chlorophyll_index)
            
            water_quality_series.append({
                'date': data_point['date'],
                'value': water_quality_score,
                'turbidity_index': turbidity_index,
                'chlorophyll_index': chlorophyll_index,
                'ndti': ndti,
                'quality': data_point.get('data_quality', 'unknown')
            })
        
        # Calculate statistics
        current_quality = water_quality_series[-1]['value'] if water_quality_series else 0
        previous_quality = water_quality_series[-2]['value'] if len(water_quality_series) > 1 else current_quality
        mean_quality = np.mean([point['value'] for point in water_quality_series]) if water_quality_series else 0
        trend = np.polyfit(range(len(water_quality_series)), 
                          [point['value'] for point in water_quality_series], 1)[0] if len(water_quality_series) > 1 else 0
        
        return {
            'current_value': float(current_quality),
            'previous_value': float(previous_quality),
            'mean_value': float(mean_quality),
            'trend_slope': float(trend),
            'water_quality_class': self._classify_water_quality(current_quality),
            'time_series': water_quality_series,
            'spatial_data': {
                'mean_turbidity': float(np.mean(turbidity_values)) if turbidity_values else 0,
                'mean_chlorophyll': float(np.mean(chlorophyll_values)) if chlorophyll_values else 0,
                'quality_variability': float(np.std([point['value'] for point in water_quality_series])) if water_quality_series else 0
            }
        }
    
    def _calculate_biodiversity_index(self, satellite_data: Dict, area_bounds: Dict) -> Dict[str, Any]:
        """
        Calculate biodiversity indicators using spectral diversity and landscape metrics
        """
        if not satellite_data.get('time_series'):
            return {'error': 'No time series data available for biodiversity calculation'}
        
        time_series = satellite_data['time_series']
        biodiversity_series = []
        diversity_values = []
        
        for data_point in time_series:
            # Calculate spectral diversity metrics
            red_std = data_point.get('red_std', 0)
            green_std = data_point.get('green_std', 0)
            nir_std = data_point.get('nir_std', 0)
            
            # Spectral diversity index (higher variability suggests more diverse vegetation)
            spectral_diversity = (red_std + green_std + nir_std) / 3
            
            # Vegetation diversity proxy using NDVI variability
            red = data_point.get('red_mean', 0)
            nir = data_point.get('nir_mean', 0)
            
            if (nir + red) != 0:
                ndvi = (nir - red) / (nir + red)
            else:
                ndvi = 0
            
            # Habitat connectivity (simplified - based on vegetation continuity)
            connectivity_index = min(1.0, ndvi * 2) if ndvi > 0 else 0
            
            # Edge density proxy (higher spectral variability suggests more edges)
            edge_density = spectral_diversity * 10  # Scale to 0-1 range
            
            # Fragmentation index (inverse of connectivity)
            fragmentation = 1 - connectivity_index
            
            # Composite biodiversity index
            biodiversity_score = (
                spectral_diversity * self.biodiversity_weights['vegetation_diversity'] +
                connectivity_index * self.biodiversity_weights['habitat_connectivity'] +
                edge_density * self.biodiversity_weights['edge_density'] +
                (1 - fragmentation) * self.biodiversity_weights['fragmentation']
            ) * 100  # Scale to 0-100
            
            diversity_values.append(biodiversity_score)
            
            biodiversity_series.append({
                'date': data_point['date'],
                'value': biodiversity_score,
                'spectral_diversity': spectral_diversity,
                'connectivity_index': connectivity_index,
                'edge_density': edge_density,
                'fragmentation': fragmentation,
                'quality': data_point.get('data_quality', 'unknown')
            })
        
        # Calculate statistics
        current_diversity = diversity_values[-1] if diversity_values else 0
        previous_diversity = diversity_values[-2] if len(diversity_values) > 1 else current_diversity
        mean_diversity = np.mean(diversity_values) if diversity_values else 0
        trend = np.polyfit(range(len(diversity_values)), diversity_values, 1)[0] if len(diversity_values) > 1 else 0
        
        return {
            'current_value': float(current_diversity),
            'previous_value': float(previous_diversity),
            'mean_value': float(mean_diversity),
            'trend_slope': float(trend),
            'diversity_class': self._classify_biodiversity(current_diversity),
            'time_series': biodiversity_series,
            'spatial_data': {
                'habitat_types_estimated': max(1, int(current_diversity / 20)),  # Rough estimate
                'landscape_heterogeneity': float(np.std(diversity_values)) if diversity_values else 0,
                'conservation_priority': 'high' if current_diversity > 70 else 'medium' if current_diversity > 40 else 'low'
            }
        }
    
    def _interpret_ndvi(self, ndvi_value: float) -> str:
        """Interpret NDVI value for vegetation health"""
        if ndvi_value < 0.1:
            return 'bare_soil_water'
        elif ndvi_value < 0.3:
            return 'sparse_vegetation'
        elif ndvi_value < 0.6:
            return 'moderate_vegetation'
        elif ndvi_value < 0.8:
            return 'dense_vegetation'
        else:
            return 'very_dense_vegetation'
    
    def _classify_water_quality(self, quality_score: float) -> str:
        """Classify water quality based on score"""
        if quality_score >= 80:
            return 'excellent'
        elif quality_score >= 60:
            return 'good'
        elif quality_score >= 40:
            return 'fair'
        elif quality_score >= 20:
            return 'poor'
        else:
            return 'very_poor'
    
    def _classify_biodiversity(self, diversity_score: float) -> str:
        """Classify biodiversity based on score"""
        if diversity_score >= 80:
            return 'very_high'
        elif diversity_score >= 60:
            return 'high'
        elif diversity_score >= 40:
            return 'medium'
        elif diversity_score >= 20:
            return 'low'
        else:
            return 'very_low'
    
    def _calculate_area_hectares(self, area_bounds: Dict) -> float:
        """Calculate approximate area in hectares from coordinates"""
        if not area_bounds or 'coordinates' not in area_bounds:
            return 100.0  # Default area
        
        coords = area_bounds['coordinates']
        if len(coords) < 3:
            return 100.0
        
        # Simple polygon area calculation using shoelace formula
        # Convert to approximate hectares (very rough approximation)
        coords_array = np.array(coords)
        lats = coords_array[:, 1]
        lons = coords_array[:, 0]
        
        # Use average latitude for more accurate area calculation
        avg_lat = np.mean(lats)
        lat_to_km = 111.32  # km per degree latitude
        lon_to_km = 111.32 * np.cos(np.radians(avg_lat))  # km per degree longitude
        
        # Convert to km coordinates
        x_km = (lons - lons[0]) * lon_to_km
        y_km = (lats - lats[0]) * lat_to_km
        
        # Shoelace formula for area
        area_km2 = 0.5 * abs(sum(x_km[i] * y_km[i+1] - x_km[i+1] * y_km[i] 
                                 for i in range(-1, len(x_km)-1)))
        
        # Convert km² to hectares (1 km² = 100 hectares)
        area_hectares = area_km2 * 100
        
        return max(1.0, area_hectares)  # Minimum 1 hectare
    
    def _calculate_fragmentation_index(self, forest_percentages: List[float]) -> float:
        """Calculate landscape fragmentation index"""
        if not forest_percentages:
            return 0.0
        
        # Simple fragmentation metric based on variability in forest cover
        std_dev = np.std(forest_percentages)
        mean_cover = np.mean(forest_percentages)
        
        if mean_cover == 0:
            return 1.0  # Maximum fragmentation
        
        # Coefficient of variation as fragmentation proxy
        fragmentation = min(1.0, std_dev / mean_cover)
        return fragmentation
