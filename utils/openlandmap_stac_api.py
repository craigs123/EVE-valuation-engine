"""
OpenLandMap STAC API Integration for Ecosystem Detection
Replaces USGS with reliable global land cover data from OpenLandMap STAC collections
"""

import requests
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
import json
import math
import rasterio
from rasterio.windows import Window
import pystac_client
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import logging

class OpenLandMapSTAC:
    """
    OpenLandMap STAC API integration for ecosystem detection
    """
    
    def __init__(self):
        self.stac_base_url = "https://s3.eu-central-1.wasabisys.com/stac/openlandmap"
        self.raw_values_endpoint = "/api/raw-values"  # For numerical land mask values
        
        # Connection pooling: persistent HTTP session
        self._session = None
        self._session_connector = None
        
        # Caching - clear cache to force new asset URL discovery with updated logic
        self._collection_cache = {}  # Cache collection metadata
        self._asset_url_cache = {}   # Cache GeoTIFF asset URLs
        
        # Define key STAC collections for comprehensive environmental data
        self.collections = [
            {
                "id": "log.oc_iso.10694",
                "name": "Soil Organic Carbon",
                "category": "soil",
                "unit": "g/kg"
            },
            {
                "id": "land.cover_esacci.lc.l4", 
                "name": "Land Cover",
                "category": "landcover",
                "unit": "class"
            },
            {
                "id": "evi_mod13q1.tmwm.inpaint",
                "name": "Vegetation Index",
                "category": "vegetation", 
                "unit": "index"
            },
            {
                "id": "fapar_essd.lstm",
                "name": "Photosynthetic Activity",
                "category": "vegetation",
                "unit": "fraction"
            },
            {
                "id": "dtm.bareearth_ensemble",
                "name": "Terrain Elevation",
                "category": "terrain",
                "unit": "meters"
            }
        ]
        
        # Only landcover collection for ecosystem detection (optimization)
        self.landcover_collection = {
            "id": "land.cover_esacci.lc.l4", 
            "name": "Land Cover",
            "category": "landcover",
            "unit": "class"
        }
        
        # Complete ESA CCI Land Cover (Level 1 & 2) to ESVD ecosystem coefficient mapping
        # Handles both Level 1 and Level 2 codes from ESA CCI Level 4 data
        # Official descriptions available in utils/esa_landcover_codes.py
        self.landcover_to_esvd = {
            # Cropland Classes
            10: "Cropland", 11: "Cropland", 12: "Cropland", 
            20: "Cropland", 30: "Cropland", 40: "Grassland",
            
            # Forest Classes  
            50: "Forest", 60: "Forest", 61: "Forest", 62: "Forest",
            70: "Forest", 71: "Forest", 72: "Forest", 
            80: "Forest", 81: "Forest", 82: "Forest",
            90: "Forest", 100: "Forest",
            
            # Shrubland Classes
            110: "Shrubland", 120: "Shrubland", 121: "Shrubland", 122: "Shrubland",
            
            # Grassland Classes
            130: "Grassland", 140: "Grassland",
            
            # Sparse Vegetation / Desert Classes
            150: "Desert", 151: "Desert", 152: "Desert", 153: "Desert",
            
            # Wetland Classes
            160: "Wetland",         # Tree cover, flooded, fresh or brakish water
            170: "Wetland",         # Tree cover, flooded, saline water
            180: "Wetland",         # Shrub or herbaceous cover, flooded, fresh/saline/brakish water
            
            # Urban Classes
            190: "Urban",           # Urban areas
            
            # Bare Areas Classes
            200: "Desert",          # Bare areas
            201: "Desert",          # Consolidated bare areas
            202: "Desert",          # Unconsolidated bare areas
            
            # Water Bodies Classes
            210: "Rivers and Lakes",  # Water bodies (freshwater)
            211: "Marine",            # Marine/oceanic water bodies
            
            # Snow and Ice Classes
            220: "Polar",           # Permanent snow and ice
        }
        
        # Geographic fallbacks removed - only use genuine STAC API data
    
    def clear_cache(self):
        """Clear all caches to force fresh STAC catalog queries"""
        self._collection_cache.clear()
        self._asset_url_cache.clear()
        print("🧹 STAC cache cleared - will use updated date prioritization logic")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create persistent HTTP session with connection pooling"""
        if self._session is None or self._session.closed:
            # Create connector with connection pooling
            self._session_connector = aiohttp.TCPConnector(
                limit=10,  # Total connection pool size
                limit_per_host=5,  # Max connections per host
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            # Create session with timeout
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self._session = aiohttp.ClientSession(
                connector=self._session_connector,
                timeout=timeout
            )
        return self._session
    
    async def close_session(self):
        """Close the persistent HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
        if self._session_connector:
            await self._session_connector.close()
    
    def __del__(self):
        """Cleanup session on destruction"""
        if self._session and not self._session.closed:
            try:
                import asyncio
                asyncio.create_task(self.close_session())
            except:
                pass
    
    async def query_stac_collections(self, lat: float, lon: float) -> Optional[List[Dict]]:
        """
        Query multiple OpenLandMap STAC collections for environmental data
        """
        results = []
        
        # Use persistent session instead of creating new one
        session = await self._get_session()
        
        tasks = []
        for collection in self.collections:
            task = self._query_single_collection(session, collection, lat, lon)
            tasks.append(task)
        
        # Execute all queries in parallel
        collection_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for collection, result in zip(self.collections, collection_results):
            if isinstance(result, dict):
                results.append(result)
        
        return results if results else None

    async def query_landcover_only(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Optimized method to query only landcover collection for ecosystem detection
        """
        session = await self._get_session()
        return await self._query_single_collection(session, self.landcover_collection, lat, lon)
    
    async def _query_single_collection(self, session: aiohttp.ClientSession, 
                                     collection: Dict, lat: float, lon: float) -> Optional[Dict]:
        """
        Query a single STAC collection
        """
        try:
            collection_url = f"{self.stac_base_url}/{collection['id']}/collection.json"
            
            async with session.get(collection_url) as response:
                if response.status == 200:
                    collection_data = await response.json()
                    
                    if collection_data.get('links'):
                        # For land cover, extract real pixel data from GeoTIFF
                        if collection['category'] == 'landcover':
                            # Extract real pixel data from OpenLandMap GeoTIFF
                            sample_value, data_source, raw_response = await self._extract_real_pixel_data(session, lat, lon, collection_data)
                            
                            # Only return data if we actually extracted a real pixel value
                            if sample_value is not None:
                                return {
                                    "collection": collection["id"],
                                    "name": collection["name"],
                                    "category": collection["category"],
                                    "value": sample_value,
                                    "unit": collection["unit"],
                                    "metadata": {
                                        "title": collection_data.get("title", ""),
                                        "description": collection_data.get("description", ""),
                                        "license": collection_data.get("license", ""),
                                        "source": data_source,
                                        "raw_response": raw_response
                                    }
                                }
                            else:
                                print(f"🚫 No real pixel data available for land cover at ({lat}, {lon})")
                                return None
                        # No synthetic data generation for landmask - only return real STAC data
                        elif collection['category'] == 'landmask':
                            print(f"❌ No synthetic data generation for landmask category at ({lat}, {lon})")
                            return None
                        # No synthetic data generation for other categories - only return real STAC data  
                        else:
                            print(f"❌ No synthetic data generation for {collection['category']} category at ({lat}, {lon})")
                            return None
        except Exception as e:
            print(f"Failed to query collection {collection['id']}: {e}")
            return None
    
    def extract_pixel_value(self, asset_url: str, lat: float, lon: float) -> Optional[float]:
        """
        Extract pixel value from Cloud Optimized GeoTIFF using HTTP range requests
        Returns actual pixel value or None if extraction fails
        """
        try:
            # Open COG directly from HTTP URL
            with rasterio.open(asset_url) as dataset:
                # Get geographic bounds
                bounds = dataset.bounds
                width, height = dataset.width, dataset.height
                
                # Check coordinate bounds
                if not (bounds.left <= lon <= bounds.right and 
                        bounds.bottom <= lat <= bounds.top):
                    print(f"🌍 Coordinates ({lat}, {lon}) outside data coverage for {asset_url}")
                    return None
                
                # Transform geographic coordinates to pixel coordinates
                pixel_x = int((lon - bounds.left) / (bounds.right - bounds.left) * width)
                pixel_y = int((bounds.top - lat) / (bounds.top - bounds.bottom) * height)
                
                # Ensure pixel coordinates are within image bounds
                if not (0 <= pixel_x < width and 0 <= pixel_y < height):
                    print(f"📍 Pixel coordinates ({pixel_x}, {pixel_y}) outside image bounds")
                    return None
                
                # Read pixel value using window-based reading
                window = Window(pixel_x, pixel_y, 1, 1)
                pixel_value = dataset.read(1, window=window)[0, 0]
                
                # Handle NoData values
                if dataset.nodata is not None and pixel_value == dataset.nodata:
                    print(f"🚫 NoData value encountered at ({lat}, {lon})")
                    return None
                
                print(f"✅ PIXEL EXTRACTED: Value {pixel_value} at ({lat}, {lon}) from COG")
                return float(pixel_value)
                
        except Exception as e:
            print(f"❌ GeoTIFF extraction failed for {asset_url}: {e}")
            return None

    def extract_batch_pixel_values(self, asset_url: str, coordinates: List[tuple]) -> List[Optional[float]]:
        """
        Batch extract pixel values from Cloud Optimized GeoTIFF for multiple coordinates
        Opens the file once and samples all coordinates efficiently
        Returns list of pixel values in same order as input coordinates
        """
        try:
            # Open COG directly from HTTP URL once
            with rasterio.open(asset_url) as dataset:
                # Get geographic bounds
                bounds = dataset.bounds
                width, height = dataset.width, dataset.height
                
                # Filter coordinates that are within bounds
                valid_coords = []
                coord_indices = []
                
                for i, (lat, lon) in enumerate(coordinates):
                    if (bounds.left <= lon <= bounds.right and 
                        bounds.bottom <= lat <= bounds.top):
                        valid_coords.append((lon, lat))  # Note: rasterio expects (x, y) = (lon, lat)
                        coord_indices.append(i)
                
                if not valid_coords:
                    print(f"🌍 No coordinates within data coverage for {asset_url}")
                    return [None] * len(coordinates)
                
                # Use rasterio.sample for efficient batch sampling
                pixel_values = [None] * len(coordinates)
                sampled_values = list(dataset.sample(valid_coords))
                
                # Map sampled values back to original coordinate order
                for coord_idx, sampled_value in zip(coord_indices, sampled_values):
                    if len(sampled_value) > 0:
                        value = sampled_value[0]  # First band
                        # Handle NoData values
                        if dataset.nodata is not None and value == dataset.nodata:
                            pixel_values[coord_idx] = None
                        else:
                            pixel_values[coord_idx] = float(value)
                    else:
                        pixel_values[coord_idx] = None
                
                print(f"✅ BATCH EXTRACTED: {len([v for v in pixel_values if v is not None])}/{len(coordinates)} pixels from COG")
                return pixel_values
                
        except Exception as e:
            print(f"❌ Batch GeoTIFF extraction failed for {asset_url}: {e}")
            return [None] * len(coordinates)
    
    def get_stac_asset_url(self, collection_id: str) -> Optional[str]:
        """
        Get GeoTIFF asset URL from STAC catalog with caching, prioritizing most recent data
        """
        # Check cache first
        if collection_id in self._asset_url_cache:
            return self._asset_url_cache[collection_id]
        
        try:
            # Updated fallback URLs for more recent years
            asset_url_attempts = [
                # Try the latest known versions first (2020-2021)
                "https://s3.openlandmap.org/arco/lcv_land.cover_esacci.lc.l4_c_250m_s0..0cm_2020_v1.0.tif",
                "https://s3.eu-central-1.wasabisys.com/openlandmap/lcv_land.cover_esacci.lc.l4_c_250m_s0..0cm_2020_v1.0.tif",
                "https://s3.openlandmap.org/arco/lcv_land.cover_esacci.lc.l4_c_250m_s0..0cm_2021_v1.0.tif",
                "https://s3.openlandmap.org/arco/lcv_land.cover_esacci.lc.l4_c_250m_s0..0cm_2019_v1.0.tif",
            ]
            
            # First try STAC catalog query - but search for most recent data
            collection_url = f"{self.stac_base_url}/{collection_id}/collection.json"
            response = requests.get(collection_url, timeout=10)
            
            if response.status_code == 200:
                collection_data = response.json()
                print(f"📋 STAC collection found: {collection_data.get('title', collection_id)}")
                
                # Collect all available STAC items and their years
                available_items = []
                
                # Get STAC items to extract asset URLs
                if 'links' in collection_data:
                    for link in collection_data['links']:
                        if link.get('rel') in ['child', 'item']:
                            item_url = link['href']
                            # Make sure it's a full URL
                            if not item_url.startswith('http'):
                                item_url = f"{self.stac_base_url}/{collection_id}/{item_url}"
                            
                            # Extract year from item URL to prioritize recent data
                            year = None
                            if '19' in item_url or '20' in item_url:
                                # Extract 4-digit year from URL
                                import re
                                year_match = re.search(r'(\d{4})\d{4}_\d{8}', item_url)
                                if year_match:
                                    year = int(year_match.group(1))
                            
                            available_items.append({
                                'url': item_url,
                                'year': year or 1900  # Default to very old year if no year found
                            })
                    
                    # Sort by year descending (most recent first)
                    available_items.sort(key=lambda x: x['year'], reverse=True)
                    print(f"🗓️ Found {len(available_items)} STAC items, sorted by year:")
                    for item in available_items[:5]:  # Show top 5 most recent
                        print(f"   📅 Year {item['year']}: {item['url']}")
                    
                    # Try items starting with the most recent
                    for item in available_items:
                        item_url = item['url']
                        year = item['year']
                        
                        # Skip items older than 2010 to focus on more recent data
                        if year < 2010:
                            print(f"⏭️ Skipping old data from year {year}")
                            continue
                        
                        print(f"🔗 Trying STAC item from year {year}: {item_url}")
                        
                        # Get STAC item
                        item_response = requests.get(item_url, timeout=10)
                        if item_response.status_code == 200:
                            item_data = item_response.json()
                            
                            # Extract GeoTIFF asset URL
                            if 'assets' in item_data:
                                print(f"🎯 Available assets in {year}: {list(item_data['assets'].keys())}")
                                for asset_key, asset in item_data['assets'].items():
                                    asset_type = asset.get('type', '')
                                    asset_href = asset.get('href', '')
                                    
                                    if ('image/tiff' in asset_type or 'tiff' in asset_href.lower() or 
                                        asset_key in ['data', 'main', 'cog', 'asset']):
                                        asset_url = asset['href']
                                        print(f"✅ Found GeoTIFF asset from year {year}: {asset_url}")
                                        # Cache the asset URL
                                        self._asset_url_cache[collection_id] = asset_url
                                        return asset_url
            
            # If STAC catalog fails, try known asset URLs directly
            print(f"🔄 STAC catalog search failed, trying known recent asset URLs...")
            for asset_url in asset_url_attempts:
                try:
                    # Test if the asset URL is accessible
                    test_response = requests.head(asset_url, timeout=5)
                    if test_response.status_code == 200:
                        print(f"✅ Found working recent asset URL: {asset_url}")
                        # Cache the asset URL
                        self._asset_url_cache[collection_id] = asset_url
                        return asset_url
                    else:
                        print(f"❌ Recent asset URL not accessible ({test_response.status_code}): {asset_url}")
                except Exception as e:
                    print(f"❌ Recent asset URL test failed: {e}")
                    
            print(f"⚠️ No accessible recent GeoTIFF asset found for collection {collection_id}")
            return None
            
        except Exception as e:
            print(f"❌ STAC catalog query failed for {collection_id}: {e}")
            return None
    
    async def _extract_real_pixel_data(self, session: aiohttp.ClientSession, lat: float, lon: float, collection_metadata: dict) -> tuple:
        """
        Extract real pixel data from OpenLandMap GeoTIFF files
        Returns (pixel_value, data_source, raw_response)
        """
        collection_id = "land.cover_esacci.lc.l4"
        
        try:
            # Get GeoTIFF asset URL from STAC catalog
            asset_url = self.get_stac_asset_url(collection_id)
            
            if asset_url:
                # Extract pixel value from GeoTIFF
                pixel_value = self.extract_pixel_value(asset_url, lat, lon)
                
                if pixel_value is not None:
                    # Convert to integer land cover code
                    landcover_code = int(pixel_value)
                    
                    # Apply forest type mapping for codes 70 & 71 based on geographic location
                    base_ecosystem_type = self.landcover_to_esvd.get(landcover_code, "Unknown")
                    if (base_ecosystem_type == "Forest" or landcover_code in [70, 71]):
                        specific_forest_type = self._determine_forest_type_from_coordinates(lat, lon)
                        print(f"🌲 GeoTIFF Forest mapping: ESA code {landcover_code} → {specific_forest_type} at ({lat:.4f}, {lon:.4f})")
                        # Store both the ESA code and the specific forest type
                        ecosystem_type = specific_forest_type
                    else:
                        ecosystem_type = base_ecosystem_type
                    
                    raw_response = {
                        "extraction_method": "geotiff_pixel_extraction",
                        "asset_url": asset_url,
                        "coordinates": {"lat": lat, "lon": lon},
                        "raw_pixel_value": pixel_value,
                        "landcover_code": landcover_code,
                        "ecosystem_type": ecosystem_type,
                        "data_source": "cog_http_range_request",
                        "collection_metadata": collection_metadata
                    }
                    
                    data_source = "Real ESA Satellite Data (GeoTIFF Pixel)"
                    print(f"🎯 REAL PIXEL DATA: Land cover code {landcover_code} → {ecosystem_type} extracted from GeoTIFF for ({lat}, {lon})")
                    return landcover_code, data_source, raw_response
            
            # If pixel extraction failed, return None (no fallback)
            print(f"❌ GeoTIFF pixel extraction failed for ({lat}, {lon}) - no data available")
            return None, "No Data Available", {"error": "pixel_extraction_failed", "coordinates": {"lat": lat, "lon": lon}}
            
        except Exception as e:
            print(f"❌ GeoTIFF extraction error: {e}")
            return None, "Extraction Failed", {"error": str(e), "coordinates": {"lat": lat, "lon": lon}}
    
    # Simplified approach - no longer trying to extract pixel data from STAC
    # Following the working example pattern
    
    # Removed complex raster querying - following the working STAC pattern
    # STAC API is for metadata discovery, not pixel extraction
    
    
    
    
    
    
    
    
    def process_stac_data(self, lat: float, lon: float, stac_results: List[Dict]) -> Dict[str, Any]:
        """
        Process STAC results into categorized environmental data for ecosystem detection
        """
        climate = []
        land_cover = []
        soil = []
        ecosystem_type = None
        confidence = 0.0
        
        # Track actual data source used and preserve raw response
        actual_data_source = "Geographic Fallback"
        raw_response_data = None  # Preserve the actual raw response from pixel extraction
        
        # Process STAC results
        for result in stac_results:
            data_item = {
                "name": result["name"],
                "value": result["value"], 
                "unit": result["unit"],
                "description": result["metadata"].get("description", result["name"])
            }
            
            # Extract actual data source from result metadata AND preserve raw response
            if result["category"] == "landcover" and result.get("metadata", {}).get("source"):
                actual_data_source = result["metadata"]["source"]
                # CRITICAL: Preserve the raw response from pixel extraction
                raw_response_data = result["metadata"].get("raw_response", {})
            
            if result["category"] == "soil":
                soil.append(data_item)
            elif result["category"] == "landcover":
                # Convert land cover code to ESVD ecosystem type
                land_cover_code = result["value"]
                # Skip invalid codes (though we shouldn't get them anymore)
                if land_cover_code <= 0 or land_cover_code == -1:
                    continue
                base_ecosystem_type = self.landcover_to_esvd.get(land_cover_code, "Unknown")
                
                # For forest codes (especially 70 & 71), determine specific forest type based on geography
                if (base_ecosystem_type == "Forest" or 
                    land_cover_code in [70, 71]):  # ESA codes 70 & 71 are specific forest types
                    ecosystem_type = self._determine_forest_type_from_coordinates(lat, lon)
                    print(f"🌲 Forest mapping: ESA code {land_cover_code} → {ecosystem_type} at ({lat:.4f}, {lon:.4f})")
                else:
                    ecosystem_type = base_ecosystem_type
                    
                confidence = 0.90  # High confidence from STAC API
                
                # Add readable land cover type using centralized descriptions
                from .esa_landcover_codes import get_esa_description
                cover_type = get_esa_description(land_cover_code)
                
                land_cover.append({
                    **data_item,
                    "value": cover_type,
                    "unit": "class",
                    "code": land_cover_code
                })
            elif result["category"] in ["vegetation", "terrain"]:
                climate.append(data_item)
        
        # If no real pixel data found, return None (no fallback per guidance)
        if not ecosystem_type:
            print(f"❌ No real pixel data available for {lat}, {lon}. No fallback data provided.")
            
            return {
                "ecosystem_type": None,
                "confidence": 0.0,
                "landcover_class": None,
                "coordinates": {"lat": lat, "lon": lon},
                "data_source": "No Data Available",
                "raw_stac_data": {
                    "query_coordinates": {"lat": lat, "lon": lon},
                    "error": "no_real_data_available",
                    "stac_collections_queried": len(stac_results) if stac_results else 0,
                    "processing_method": "geotiff_pixel_extraction_failed"
                },
                "query_time": json.dumps({"timestamp": "now"}, default=str)
            }
        else:
            # Extract landcover_class from the processed land cover data
            landcover_class = 130  # Default to grassland if no code found
            if land_cover and len(land_cover) > 0:
                landcover_class = land_cover[0].get("code", 130)
        
        # Construct raw_stac_data that preserves the genuine pixel extraction data
        raw_stac_data = {
            "query_coordinates": {"lat": lat, "lon": lon},
            "landcover_code": landcover_class,
            "ecosystem_detected": ecosystem_type,
            "confidence_level": confidence,
            "stac_collections_queried": len(stac_results) if stac_results else 0,
            "processing_method": "stac_metadata_analysis"
        }
        
        # CRITICAL FIX: Add the raw response from pixel extraction if available
        if raw_response_data:
            raw_stac_data["raw_response"] = raw_response_data
            print(f"🔍 THREADING FIX: Raw response preserved for UI debugging: {raw_response_data.get('extraction_method', 'unknown')}")
        
        return {
            "ecosystem_type": ecosystem_type,
            "confidence": confidence,
            "landcover_class": landcover_class,  # Add the landcover code for integration
            "coordinates": {"lat": lat, "lon": lon},
            "climate": climate if climate else None,
            "landCover": land_cover if land_cover else None, 
            "soil": soil if soil else None,
            "data_source": actual_data_source,
            "raw_stac_data": raw_stac_data,  # Now contains the preserved raw response
            "query_time": json.dumps({"timestamp": "now"}, default=str)
        }
    
    def _determine_forest_type_from_coordinates(self, lat: float, lon: float) -> str:
        """
        Determine specific forest type based on coordinates using ESVD methodology
        Returns specific forest ecosystem types for ESVD coefficient matching
        """
        abs_lat = abs(lat)
        
        # Boreal forest zones (50-70° latitude)
        if 50 <= abs_lat <= 70:
            return 'Boreal Forest'
        
        # Tropical forest zones (0-25° latitude)  
        elif abs_lat <= 25:
            return 'Tropical Forest'
        
        # Mediterranean climate zones (30-45° latitude, specific regions)
        elif 30 <= abs_lat <= 45:
            # Mediterranean Basin
            if (30 <= lat <= 45 and -10 <= lon <= 45):
                return 'Temperate Forest'
            # California
            elif (32 <= lat <= 42 and -125 <= lon <= -115):
                return 'Temperate Forest'
            # Central Chile  
            elif (-40 <= lat <= -30 and -75 <= lon <= -70):
                return 'Temperate Forest'
            # South Africa (Western Cape)
            elif (-35 <= lat <= -30 and 15 <= lon <= 25):
                return 'Temperate Forest'
            # Southwestern Australia
            elif (-35 <= lat <= -30 and 110 <= lon <= 125):
                return 'Temperate Forest'
            else:
                return 'Temperate Forest'
        
        # Temperate forest zones (25-50° latitude, excluding Mediterranean)
        elif 25 < abs_lat < 50:
            return 'Temperate Forest'
        
        # Default fallback
        return 'Temperate Forest'
    
            
    async def get_batch_ecosystem_types(self, coordinates: List[tuple]) -> List[Dict[str, Any]]:
        """
        Batch ecosystem detection for multiple coordinates using optimized GeoTIFF sampling
        Opens GeoTIFF file once and samples all points efficiently
        """
        results = []
        
        try:
            # Get landcover asset URL (cached)
            collection_id = "land.cover_esacci.lc.l4"
            asset_url = self.get_stac_asset_url(collection_id)
            
            if asset_url:
                # Batch extract pixel values for all coordinates
                pixel_values = self.extract_batch_pixel_values(asset_url, coordinates)
                print(f"🔍 BATCH DEBUG: Got {len(pixel_values)} pixel values: {pixel_values}")
                
                # Process each coordinate and its corresponding pixel value
                for i, (lat, lon) in enumerate(coordinates):
                    pixel_value = pixel_values[i]
                    print(f"🔍 BATCH DEBUG: Processing point {i}, pixel_value={pixel_value}")
                    
                    if pixel_value is not None:
                        # Convert to integer land cover code
                        landcover_code = int(pixel_value)
                        
                        # Apply forest type mapping for codes 70 & 71 based on geographic location
                        base_ecosystem_type = self.landcover_to_esvd.get(landcover_code, "Unknown")
                        if (base_ecosystem_type == "Forest" or landcover_code in [70, 71]):
                            specific_forest_type = self._determine_forest_type_from_coordinates(lat, lon)
                            ecosystem_type = specific_forest_type
                        else:
                            ecosystem_type = base_ecosystem_type
                        
                        print(f"🔍 BATCH DEBUG: Point {i}, landcover_code={landcover_code}, ecosystem_type={ecosystem_type}")
                        
                        # Create raw response data for UI debugging (similar to single-point extraction)
                        raw_response = {
                            "extraction_method": "geotiff_batch_pixel_extraction",
                            "asset_url": asset_url,
                            "coordinates": {"lat": lat, "lon": lon},
                            "raw_pixel_value": pixel_value,
                            "landcover_code": landcover_code,
                            "ecosystem_type": ecosystem_type,
                            "data_source": "cog_http_range_request",
                            "batch_index": i
                        }
                        
                        results.append({
                            "ecosystem_type": ecosystem_type,
                            "confidence": 0.9,
                            "landcover_class": landcover_code,
                            "coordinates": {"lat": lat, "lon": lon},
                            "data_source": "Real ESA Satellite Data (GeoTIFF Pixel)",
                            "raw_stac_data": {"raw_response": raw_response},  # Add raw data for UI debugging
                            "query_time": json.dumps({"timestamp": "now"}, default=str)
                        })
                    else:
                        # No synthetic data generation - return error for failed pixel extraction
                        results.append({
                            "ecosystem_type": "Unknown",
                            "confidence": 0.0,
                            "landcover_class": None,
                            "coordinates": {"lat": lat, "lon": lon},
                            "data_source": "Error: No Real Data Available",
                            "error": "Pixel extraction failed - no real STAC data available",
                            "query_time": json.dumps({"timestamp": "now"}, default=str)
                        })
            else:
                # No asset URL available - return error for all coordinates
                for lat, lon in coordinates:
                    results.append({
                        "ecosystem_type": "Unknown",
                        "confidence": 0.0,
                        "landcover_class": None,
                        "coordinates": {"lat": lat, "lon": lon},
                        "data_source": "Error: STAC Asset Unavailable",
                        "error": "No GeoTIFF asset URL available from STAC catalog",
                        "query_time": json.dumps({"timestamp": "now"}, default=str)
                    })
            
        except Exception as e:
            print(f"Batch STAC API error: {e}")
            # No synthetic data generation - return error for all coordinates when batch fails
            for lat, lon in coordinates:
                results.append({
                    "ecosystem_type": "Unknown",
                    "confidence": 0.0,
                    "landcover_class": None,
                    "coordinates": {"lat": lat, "lon": lon},
                    "data_source": "Error: Batch Processing Failed",
                    "error": f"STAC batch processing failed: {str(e)}",
                    "query_time": json.dumps({"timestamp": "now"}, default=str)
                })
        
        return results
    
    def get_ecosystem_type(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Main method to get ecosystem type using OpenLandMap STAC API
        """
        try:
            # Since asyncio.run can be problematic in some environments, use sync approach
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                stac_results = loop.run_until_complete(self.query_stac_collections(lat, lon))
            finally:
                loop.close()
            
            if stac_results:
                return self.process_stac_data(lat, lon, stac_results)
            else:
                # No synthetic data generation - return error when STAC data unavailable
                return {
                    "ecosystem_type": "Unknown",
                    "confidence": 0.0,
                    "coordinates": {"lat": lat, "lon": lon},
                    "data_source": "Error: No Real STAC Data Available", 
                    "error": "No genuine STAC collection data available for these coordinates",
                    "query_time": json.dumps({"timestamp": "now"}, default=str)
                }
        except Exception as e:
            print(f"STAC API error: {e}")
            # No synthetic data generation - return error when STAC API fails completely
            return {
                "ecosystem_type": "Unknown",
                "confidence": 0.0,
                "landcover_class": None,
                "coordinates": {"lat": lat, "lon": lon},
                "data_source": "Error: STAC API Failed",
                "error": f"STAC API processing failed: {str(e)}",
                "query_time": json.dumps({"timestamp": "now"}, default=str)
            }

# Global instance
openlandmap_stac = OpenLandMapSTAC()