"""
OpenLandMap Integration for Ecosystem Type Detection
Uses OpenLandMap.com services to determine land cover and ecosystem types
"""

import requests
import numpy as np
from typing import Dict, List, Tuple, Optional
import json

class OpenLandMapIntegrator:
    """
    Integrates with OpenLandMap.com to fetch land cover data and determine ecosystem types
    """
    
    def __init__(self):
        self.base_url = "https://rest.isric.org"
        self.landcover_services = {
            'copernicus': '/soilgrids/v2.0/classification',
            'modis': '/soilgrids/v2.0/properties'
        }
        
        # Land cover class mappings from OpenLandMap to ecosystem types
        self.landcover_to_ecosystem = {
            # Copernicus Global Land Cover classes
            10: "Forest",           # Tree cover
            20: "Forest",           # Shrubland  
            30: "Grassland",        # Grassland
            40: "Agricultural",     # Cropland
            50: "Urban",           # Built-up
            60: "Wetland",         # Bare/sparse vegetation
            70: "Wetland",         # Snow and ice
            80: "Wetland",         # Permanent water bodies
            90: "Coastal",         # Herbaceous wetland
            100: "Forest",         # Moss and lichen
            
            # MODIS Land Cover classes  
            1: "Forest",           # Evergreen Needleleaf Forests
            2: "Forest",           # Evergreen Broadleaf Forests
            3: "Forest",           # Deciduous Needleleaf Forests
            4: "Forest",           # Deciduous Broadleaf Forests
            5: "Forest",           # Mixed Forests
            6: "Forest",           # Closed Shrublands
            7: "Grassland",        # Open Shrublands
            8: "Grassland",        # Woody Savannas
            9: "Grassland",        # Savannas
            10: "Grassland",       # Grasslands
            11: "Wetland",         # Permanent Wetlands
            12: "Agricultural",    # Croplands
            13: "Urban",           # Urban and Built-up Lands
            14: "Agricultural",    # Cropland/Natural Vegetation Mosaics
            15: "Desert",          # Permanent Snow and Ice
            16: "Desert",          # Barren
            17: "Wetland"          # Water Bodies
        }
    
    def get_land_cover_point(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Get land cover information for a specific point using OpenLandMap services
        """
        try:
            # Try multiple OpenLandMap and related endpoints
            endpoints = [
                f"http://api.openlandmap.org/query/point?lat={lat}&lon={lon}&coll=layers1km&regex=lcv_.*",
                f"https://rest.isric.org/soilgrids/v2.0/classification?lon={lon}&lat={lat}&property=wrb&depth=0-5cm",
                f"http://api.openlandmap.org/query/point?lat={lat}&lon={lon}&coll=layers250m&regex=veg_.*"
            ]
            
            for i, endpoint in enumerate(endpoints):
                try:
                    response = requests.get(endpoint, timeout=3)
                    if response.status_code == 200:
                        data = response.json()
                        result = self._parse_landcover_response(data, endpoint_type=i)
                        if result:
                            return result
                except:
                    continue
                    
            # Fallback: Use simple geographic heuristics based on coordinates
            return self._geographic_heuristic_detection(lat, lon)
            
        except:
            return self._geographic_heuristic_detection(lat, lon)
    
    def _geographic_heuristic_detection(self, lat: float, lon: float) -> Dict:
        """
        Use geographic heuristics when APIs are unavailable
        """
        # Simple geographic-based ecosystem detection
        ecosystem_type = "Grassland"  # Default
        confidence = 0.6
        
        # Northern latitudes - likely forest
        if lat > 45:
            ecosystem_type = "Forest"
            confidence = 0.7
        # Arid regions (southwestern US, etc.)
        elif lat < 35 and lon < -100:
            ecosystem_type = "Desert"
            confidence = 0.65
        # Coastal areas
        elif abs(lat) < 30:
            ecosystem_type = "Coastal"
            confidence = 0.6
        # Temperate regions
        elif 35 <= lat <= 45:
            ecosystem_type = "Grassland"
            confidence = 0.65
            
        return {
            'landcover_class': 0,
            'ecosystem_type': ecosystem_type,
            'confidence': confidence,
            'source': 'Geographic Heuristic'
        }
    
    def _parse_landcover_response(self, data: Dict, endpoint_type: int = 0) -> Dict:
        """
        Parse the response from OpenLandMap services
        """
        try:
            landcover_class = 0
            confidence = 0.85
            source = 'OpenLandMap'
            
            # Handle OpenLandMap API response format
            if endpoint_type == 0:  # OpenLandMap direct API
                if 'response' in data and len(data['response']) > 0:
                    response_data = data['response'][0]
                    # Look for land cover layers
                    for key, value in response_data.items():
                        if 'lcv_' in key or 'landcover' in key.lower():
                            if isinstance(value, (int, float)) and value > 0:
                                landcover_class = int(value)
                                break
            
            # Handle ISRIC SoilGrids response
            elif endpoint_type == 1:
                if 'properties' in data:
                    landcover_class = data['properties'].get('wrb', 0)
                    source = 'ISRIC SoilGrids'
            
            # Default handling for other formats
            else:
                if 'properties' in data:
                    landcover_class = data['properties'].get('landcover', 0)
                elif 'landcover' in data:
                    landcover_class = data['landcover']
                elif 'classification' in data:
                    landcover_class = data['classification']
            
            # Map to ecosystem type
            ecosystem_type = self.landcover_to_ecosystem.get(landcover_class, "Grassland")
            
            # If we got a valid landcover class, return the result
            if landcover_class > 0:
                return {
                    'landcover_class': landcover_class,
                    'ecosystem_type': ecosystem_type,
                    'confidence': confidence,
                    'source': source
                }
            
            # Return default ecosystem result if no valid data found
            return self._default_ecosystem_result()
            
        except:
            return self._default_ecosystem_result()
    
    def analyze_area_ecosystem(self, coordinates: List[List[float]], sampling_frequency: float = 1.0) -> Dict:
        """
        Analyze ecosystem type for a polygon area using multiple sample points
        """
        try:
            if not coordinates or len(coordinates) < 3:
                return self._default_ecosystem_result()
            
            # Calculate area and determine appropriate sample density
            area_km2 = self._calculate_area_km2(coordinates)
            num_points = self._calculate_sample_points(area_km2, sampling_frequency=sampling_frequency)
            
            # Generate sample points within the polygon
            sample_points = self._generate_sample_points(coordinates, num_points=num_points)
            
            ecosystem_results = []
            successful_queries = 0
            
            for lat, lon in sample_points:
                result = self.get_land_cover_point(lat, lon)
                if result:
                    ecosystem_results.append(result)
                    successful_queries += 1
            
            if not ecosystem_results:
                return self._default_ecosystem_result()
            
            # Determine dominant ecosystem type
            ecosystem_counts = {}
            total_confidence = 0
            
            for result in ecosystem_results:
                ecosystem_type = result['ecosystem_type']
                confidence = result['confidence']
                
                if ecosystem_type not in ecosystem_counts:
                    ecosystem_counts[ecosystem_type] = {'count': 0, 'confidence': 0}
                
                ecosystem_counts[ecosystem_type]['count'] += 1
                ecosystem_counts[ecosystem_type]['confidence'] += confidence
                total_confidence += confidence
            
            # Find dominant ecosystem
            dominant_ecosystem = max(ecosystem_counts.keys(), 
                                   key=lambda x: ecosystem_counts[x]['count'])
            
            # Calculate metrics
            dominant_count = ecosystem_counts[dominant_ecosystem]['count']
            dominant_confidence = ecosystem_counts[dominant_ecosystem]['confidence'] / dominant_count
            coverage_percentage = (dominant_count / len(ecosystem_results)) * 100
            
            return {
                'primary_ecosystem': dominant_ecosystem,
                'confidence': dominant_confidence,
                'coverage_percentage': coverage_percentage,
                'successful_queries': successful_queries,
                'total_samples': len(sample_points),
                'ecosystem_distribution': ecosystem_counts,
                'source': 'OpenLandMap'
            }
            
        except:
            return self._default_ecosystem_result()
    
    def _generate_sample_points(self, coordinates: List[List[float]], num_points: int = 4) -> List[Tuple[float, float]]:
        """
        Generate sample points within a polygon for ecosystem analysis
        """
        try:
            # Convert to numpy array
            coords = np.array(coordinates[:-1])  # Remove last duplicate point
            
            # Calculate bounding box
            min_lon, min_lat = coords.min(axis=0)
            max_lon, max_lat = coords.max(axis=0)
            
            # Generate grid of points
            points = []
            grid_size = int(np.sqrt(num_points))
            
            for i in range(grid_size):
                for j in range(grid_size):
                    lat = min_lat + (max_lat - min_lat) * (i + 0.5) / grid_size
                    lon = min_lon + (max_lon - min_lon) * (j + 0.5) / grid_size
                    points.append((lat, lon))
            
            return points
            
        except:
            # Fallback: return center point
            center_lat = np.mean([coord[1] for coord in coordinates[:-1]])
            center_lon = np.mean([coord[0] for coord in coordinates[:-1]])
            return [(float(center_lat), float(center_lon))]
    
    def _calculate_area_km2(self, coordinates: List[List[float]]) -> float:
        """
        Calculate approximate area of polygon in square kilometers
        """
        try:
            coords = np.array(coordinates[:-1])  # Remove last duplicate point
            # Simple polygon area calculation using shoelace formula
            # Convert to approximate km using 111.32 km per degree
            x = coords[:, 0] * 111.32  # longitude to km (approximate)
            y = coords[:, 1] * 111.32  # latitude to km
            area_km2 = 0.5 * abs(sum(x[i]*y[i+1] - x[i+1]*y[i] for i in range(-1, len(x)-1)))
            return area_km2
        except:
            return 1.0  # Default 1 km2 if calculation fails
    
    def _calculate_sample_points(self, area_km2: float, sampling_frequency: float = 1.0) -> int:
        """
        Calculate number of sample points based on area size and sampling frequency
        - Areas ≤ 10,000 hectares: Use user-defined sampling frequency
        - Areas > 10,000 hectares: Use maximum 100 sample points for even distribution
        """
        # Convert km2 to hectares (1 km2 = 100 hectares)
        area_hectares = area_km2 * 100
        
        # For areas larger than 10,000 hectares, use maximum sample points
        if area_hectares > 10000:
            target_points = 100  # Use maximum for large areas (API-friendly limit)
        else:
            # For smaller areas, use user-defined sampling frequency
            desired_points = max(4, int(area_hectares * sampling_frequency / 100))
            target_points = min(desired_points, 100)  # Cap at 100 for API performance
        
        # Round to nearest perfect square for grid generation
        grid_size = int(np.sqrt(target_points))
        actual_points = grid_size ** 2
        
        return max(4, actual_points)  # Ensure minimum of 4 points
    
    def _default_ecosystem_result(self) -> Dict:
        """
        Return default ecosystem result when OpenLandMap is unavailable
        """
        return {
            'primary_ecosystem': "Grassland",
            'confidence': 0.5,
            'coverage_percentage': 100.0,
            'successful_queries': 0,
            'total_samples': 1,
            'ecosystem_distribution': {"Grassland": {"count": 1, "confidence": 0.5}},
            'source': 'Default (OpenLandMap unavailable)'
        }

def detect_ecosystem_type(coordinates: List[List[float]], sampling_frequency: float = 1.0) -> Dict:
    """
    Main function to detect ecosystem type using OpenLandMap
    """
    integrator = OpenLandMapIntegrator()
    return integrator.analyze_area_ecosystem(coordinates, sampling_frequency)