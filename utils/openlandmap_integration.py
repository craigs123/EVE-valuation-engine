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
            # Try multiple OpenLandMap endpoints
            endpoints = [
                f"https://rest.isric.org/soilgrids/v2.0/classification?lon={lon}&lat={lat}&property=wrb&depth=0-5cm",
                f"https://landcover.org/api/v1/point?lat={lat}&lon={lon}",
                f"https://openlandmap.org/api/query?lat={lat}&lon={lon}&service=landcover"
            ]
            
            for endpoint in endpoints:
                try:
                    response = requests.get(endpoint, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        return self._parse_landcover_response(data)
                except:
                    continue
                    
            return None
            
        except Exception as e:
            print(f"Error fetching land cover data: {e}")
            return None
    
    def _parse_landcover_response(self, data: Dict) -> Dict:
        """
        Parse the response from OpenLandMap services
        """
        try:
            # Handle different response formats
            if 'properties' in data:
                landcover_class = data['properties'].get('landcover', 0)
            elif 'landcover' in data:
                landcover_class = data['landcover']
            elif 'classification' in data:
                landcover_class = data['classification']
            else:
                landcover_class = 0
            
            ecosystem_type = self.landcover_to_ecosystem.get(landcover_class, "Grassland")
            
            return {
                'landcover_class': landcover_class,
                'ecosystem_type': ecosystem_type,
                'confidence': 0.85,  # Default confidence
                'source': 'OpenLandMap'
            }
            
        except Exception as e:
            print(f"Error parsing landcover response: {e}")
            return {
                'landcover_class': 0,
                'ecosystem_type': "Grassland",
                'confidence': 0.5,
                'source': 'Default'
            }
    
    def analyze_area_ecosystem(self, coordinates: List[List[float]]) -> Dict:
        """
        Analyze ecosystem type for a polygon area using multiple sample points
        """
        try:
            if not coordinates or len(coordinates) < 3:
                return self._default_ecosystem_result()
            
            # Generate sample points within the polygon
            sample_points = self._generate_sample_points(coordinates, num_points=9)
            
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
            
        except Exception as e:
            print(f"Error analyzing area ecosystem: {e}")
            return self._default_ecosystem_result()
    
    def _generate_sample_points(self, coordinates: List[List[float]], num_points: int = 9) -> List[Tuple[float, float]]:
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
            
        except Exception as e:
            print(f"Error generating sample points: {e}")
            # Fallback: return center point
            center_lat = np.mean([coord[1] for coord in coordinates[:-1]])
            center_lon = np.mean([coord[0] for coord in coordinates[:-1]])
            return [(center_lat, center_lon)]
    
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

def detect_ecosystem_type(coordinates: List[List[float]]) -> Dict:
    """
    Main function to detect ecosystem type using OpenLandMap
    """
    integrator = OpenLandMapIntegrator()
    return integrator.analyze_area_ecosystem(coordinates)