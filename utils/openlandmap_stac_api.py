"""
OpenLandMap STAC API Integration for Ecosystem Detection
Replaces USGS with reliable global land cover data from OpenLandMap STAC collections
"""

import requests
import asyncio
import aiohttp
import time
import random
from typing import Dict, List, Optional, Any, Tuple
import json
import math
import rasterio
from rasterio.windows import Window
from rasterio.crs import CRS
from rasterio.warp import transform_bounds, transform
import pystac_client
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import logging
import certifi
from functools import lru_cache
from collections import OrderedDict
import threading
import gc
import weakref
from contextlib import contextmanager

# Enhanced GDAL environment configuration for reliable HTTP COG access
HTTP_ENV = {
    'GDAL_DISABLE_READDIR_ON_OPEN': 'EMPTY_DIR',
    'CPL_VSIL_CURL_USE_HEAD': 'NO', 
    'CPL_VSIL_CURL_ALLOWED_EXTENSIONS': '.tif,.tiff',
    'VSI_CACHE': 'TRUE',
    'VSI_CACHE_SIZE': '50000000',  # Increased cache for large COGs
    'SSL_CERT_FILE': certifi.where(),
    # Enhanced timeout and retry configuration for reliability
    'GDAL_HTTP_TIMEOUT': '60',  # Increased timeout for large files
    'GDAL_HTTP_CONNECTTIMEOUT': '30', 
    'GDAL_HTTP_MAX_RETRY': '5',  # More retries
    'GDAL_HTTP_RETRY_DELAY': '2',
    'CPL_VSIL_CURL_RETRY_DELAY': '2',
    # Additional SSL and HTTP configurations
    'CURL_CA_BUNDLE': certifi.where(),
    'GDAL_HTTP_UNSAFESSL': 'YES',  # Allow self-signed certificates
    'GDAL_HTTP_VERSION': '2',
    'CPL_VSIL_CURL_VERBOSE': 'NO',
    'GDAL_NUM_THREADS': 'ALL_CPUS',
    'VSI_CACHE_SIZE': '50000000',
    'GDAL_CACHEMAX': 512  # Limit GDAL memory cache to 512MB
}

class OpenLandMapSTAC:
    """
    OpenLandMap STAC API integration for ecosystem detection
    """
    
    def __init__(self, max_dataset_cache_size: int = 15):
        self.stac_base_url = "https://s3.eu-central-1.wasabisys.com/stac/openlandmap"
        self.raw_values_endpoint = "/api/raw-values"  # For numerical land mask values
        
        # Connection pooling: persistent HTTP session
        self._session = None
        self._session_connector = None
        
        # Optimized memory footprint for pixel extraction
        self.max_cache_size_mb = 100  # Balanced cache size for performance
        
        # Enhanced metadata caching (as per technical guidance)
        self._collection_cache = {}  # Cache collection metadata  
        self._item_cache = {}        # Cache STAC item metadata
        self._asset_url_cache = {}   # Cache GeoTIFF asset URLs
        
        # Cache TTL for metadata (following guidance for performance)
        self._cache_ttl_seconds = 3600  # 1 hour cache
        self._cache_timestamps = {}     # Track cache age
        
        # Performance optimization: LRU Dataset Cache with STRONG references
        # CRITICAL FIX: Use strong references instead of weak ones for actual caching
        self._dataset_cache_size = min(max_dataset_cache_size, 10)  # Limit cache size to prevent memory issues
        self._dataset_cache = OrderedDict()  # Manual LRU implementation: url -> dataset
        self._cache_metadata = OrderedDict()  # url -> {opened_at, access_count, last_access}
        
        # Thread safety: Lock for cache operations
        self._cache_lock = threading.RLock()  # Reentrant lock for nested calls
        
        # THREAD-SAFETY FIX: Per-dataset locks for rasterio operations
        # Each dataset gets its own lock to prevent concurrent read() operations
        self._dataset_locks = {}  # url -> threading.Lock() for thread-safe dataset.read()
        self._locks_lock = threading.Lock()  # Lock for managing the locks dict itself
        
        # Thread pool for async I/O offloading
        self._thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="raster_io")
        
        # Cache statistics for validation
        self._cache_stats = {
            'hits': 0,
            'misses': 0, 
            'evictions': 0,
            'opens': 0,
            'closes': 0
        }
        
        # Define key STAC collections for comprehensive environmental data
        # Based on technical brief specifications
        self.collections = [
            {
                "id": "water.occurrence_jrc.surfacewater",
                "name": "Land Mask Percentage", 
                "category": "landmask",
                "unit": "percentage"
            },
            {
                "id": "land.cover_esacci.lc.l4", 
                "name": "Land Cover",
                "category": "landcover",
                "unit": "class"
            },
            {
                "id": "evi_mod13q1.tmwm.inpaint",
                "name": "Enhanced Vegetation Index",
                "category": "vegetation", 
                "unit": "index"
            },
            {
                "id": "fapar_essd.lstm",
                "name": "Fraction of Absorbed PAR",
                "category": "vegetation",
                "unit": "fraction"
            },
            {
                "id": "dtm.bareearth_ensemble",
                "name": "Elevation",
                "category": "terrain",
                "unit": "meters"
            },
            {
                "id": "log.oc_iso.10694",
                "name": "Soil Organic Carbon",
                "category": "soil",
                "unit": "g/kg"
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
            10: "agricultural", 11: "agricultural", 12: "agricultural", 
            20: "agricultural", 30: "agricultural", 40: "Grassland",
            
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
            
            # Additional NLCD/CORINE codes that may be encountered
            21: "Urban", 22: "Urban", 23: "Urban", 24: "Urban",  # Developed areas
            31: "Desert",           # Barren Land
            41: "Temperate Forest", 42: "Forest", 43: "Forest",  # NLCD Forest types
            52: "Shrubland",        # NLCD Shrub/Scrub
            95: "Wetland",          # NLCD Emergent Herbaceous Wetlands
            
            # Extended forest coverage (ESA codes 51-99)
            51: "Forest", 53: "Forest", 54: "Forest", 55: "Forest", 
            63: "Forest", 64: "Forest", 65: "Forest", 66: "Forest",
            73: "Forest", 74: "Forest", 75: "Forest", 76: "Forest",
            83: "Forest", 84: "Forest", 85: "Forest", 86: "Forest",
            91: "Forest", 92: "Forest", 93: "Forest", 94: "Forest",
            96: "Forest", 97: "Forest", 98: "Forest", 99: "Forest",
            
            # Extended cropland coverage (ESA codes 13-29)
            13: "agricultural", 14: "agricultural", 15: "agricultural", 16: "agricultural",
            17: "agricultural", 18: "agricultural", 19: "agricultural", 
            21: "agricultural", 22: "agricultural", 23: "agricultural", 24: "agricultural",
            25: "agricultural", 26: "agricultural", 27: "agricultural", 28: "agricultural", 29: "agricultural",
            
            # Extended shrubland coverage (ESA codes 111-129)
            111: "Shrubland", 112: "Shrubland", 113: "Shrubland", 114: "Shrubland",
            115: "Shrubland", 116: "Shrubland", 117: "Shrubland", 118: "Shrubland", 119: "Shrubland",
            123: "Shrubland", 124: "Shrubland", 125: "Shrubland", 126: "Shrubland",
            127: "Shrubland", 128: "Shrubland", 129: "Shrubland",
            
            # Extended grassland coverage (ESA codes 131-149)
            131: "Grassland", 132: "Grassland", 133: "Grassland", 134: "Grassland",
            135: "Grassland", 136: "Grassland", 137: "Grassland", 138: "Grassland", 139: "Grassland",
            141: "Grassland", 142: "Grassland", 143: "Grassland", 144: "Grassland",
            145: "Grassland", 146: "Grassland", 147: "Grassland", 148: "Grassland", 149: "Grassland"
        }
        
        # Geographic fallbacks removed - only use genuine STAC API data
    
    def clear_cache(self):
        """Clear all caches to force fresh STAC catalog queries"""
        with self._cache_lock:
            self._collection_cache.clear()
            self._asset_url_cache.clear()
            self._clear_dataset_cache_unsafe()  # Already holds lock
            print("🧹 STAC cache cleared - will use updated date prioritization logic")
    
    def _clear_dataset_cache(self):
        """Clear dataset cache and close all open datasets - thread-safe version"""
        with self._cache_lock:
            self._clear_dataset_cache_unsafe()
    
    def _clear_dataset_cache_unsafe(self):
        """Clear dataset cache without acquiring lock - use when lock already held"""
        closed_count = 0
        for asset_url, dataset in self._dataset_cache.items():
            if dataset and not dataset.closed:
                try:
                    dataset.close()
                    closed_count += 1
                    self._cache_stats['closes'] += 1
                except Exception as e:
                    print(f"⚠️ Failed to close dataset {asset_url[:50]}: {e}")
        
        self._dataset_cache.clear()
        self._cache_metadata.clear()
        
        # THREAD-SAFETY FIX: Clear all dataset locks when clearing cache
        with self._locks_lock:
            self._dataset_locks.clear()
        
        # Reset cache statistics
        self._cache_stats.update({
            'hits': 0, 'misses': 0, 'evictions': 0, 'opens': 0, 'closes': 0
        })
        
        gc.collect()  # Force garbage collection
        print(f"🧹 Dataset cache cleared: {closed_count} COG handles closed, locks cleared")
    
    def _get_cached_dataset(self, asset_url: str):
        """Get dataset from cache or open new one with LRU management - THREAD SAFE VERSION"""
        with self._cache_lock:
            # Check if dataset is in cache
            if asset_url in self._dataset_cache:
                dataset = self._dataset_cache[asset_url]
                
                # Verify dataset is still valid (not closed)
                if dataset and not dataset.closed:
                    # Move to end (most recently used) for LRU
                    self._dataset_cache.move_to_end(asset_url)
                    
                    # Update metadata
                    metadata = self._cache_metadata.get(asset_url, {})
                    metadata['access_count'] = metadata.get('access_count', 0) + 1
                    metadata['last_access'] = time.time()
                    self._cache_metadata[asset_url] = metadata
                    self._cache_metadata.move_to_end(asset_url)
                    
                    self._cache_stats['hits'] += 1
                    print(f"📂 CACHE HIT: {asset_url[:50]}... (hits: {self._cache_stats['hits']})")
                    return dataset
                else:
                    # Dataset was closed, remove from cache
                    print(f"🚫 Stale dataset removed: {asset_url[:50]}...")
                    self._dataset_cache.pop(asset_url, None)
                    self._cache_metadata.pop(asset_url, None)
            
            # Cache miss - need to open new dataset
            self._cache_stats['misses'] += 1
            print(f"📂 CACHE MISS: {asset_url[:50]}... (misses: {self._cache_stats['misses']})")
            
            try:
                # Open dataset with enhanced GDAL environment
                with rasterio.Env(**HTTP_ENV):
                    try:
                        dataset = rasterio.open(asset_url)
                        self._cache_stats['opens'] += 1
                        print(f"✅ Successfully opened COG: {asset_url[:50]}... [Format: {dataset.driver}]")
                    except Exception as open_error:
                        print(f"❌ COG open failed: {open_error}")
                        print(f"   URL: {asset_url}")
                        return None
                    
                    # Check if cache is full and needs eviction
                    if len(self._dataset_cache) >= self._dataset_cache_size:
                        # Remove oldest (least recently used) dataset
                        oldest_url, oldest_dataset = self._dataset_cache.popitem(last=False)
                        self._cache_metadata.pop(oldest_url, None)
                        
                        # THREAD-SAFETY FIX: Clean up dataset lock when evicting
                        with self._locks_lock:
                            if oldest_url in self._dataset_locks:
                                del self._dataset_locks[oldest_url]
                        
                        # Close evicted dataset
                        if oldest_dataset and not oldest_dataset.closed:
                            try:
                                oldest_dataset.close()
                                self._cache_stats['closes'] += 1
                                self._cache_stats['evictions'] += 1
                                print(f"🗑️ EVICTED: {oldest_url[:50]}... (evictions: {self._cache_stats['evictions']})")
                            except Exception as e:
                                print(f"⚠️ Failed to close evicted dataset: {e}")
                    
                    # Add new dataset to cache with STRONG reference
                    self._dataset_cache[asset_url] = dataset  # STRONG REFERENCE
                    self._cache_metadata[asset_url] = {
                        'opened_at': time.time(),
                        'access_count': 1,
                        'last_access': time.time()
                    }
                    
                    # THREAD-SAFETY FIX: Create per-dataset lock for thread-safe read operations
                    with self._locks_lock:
                        if asset_url not in self._dataset_locks:
                            self._dataset_locks[asset_url] = threading.Lock()
                    
                    print(f"📂 CACHED NEW: {asset_url[:50]}... ({len(self._dataset_cache)}/{self._dataset_cache_size}) [opens: {self._cache_stats['opens']}]")
                    return dataset
                    
            except Exception as e:
                print(f"❌ Failed to open dataset {asset_url}: {e}")
                return None
    
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
        """Close the persistent HTTP session while preserving caches for performance"""
        if self._session and not self._session.closed:
            await self._session.close()
        if self._session_connector:
            await self._session_connector.close()
        
        # NOTE: Dataset cache and thread pool preserved for performance across reruns
        # Only call explicit cleanup when absolutely necessary
    
    def shutdown(self, clear_caches: bool = False):
        """
        Explicit shutdown method that works without async event loop
        
        Args:
            clear_caches: If True, clear all caches (not recommended for performance).
                         If False (default), preserve caches for performance across reruns.
        """
        # Only clear caches if explicitly requested - preserve for performance by default
        if clear_caches:
            print("🧹 WARNING: Clearing caches as requested (will hurt performance on next run)")
            self._clear_dataset_cache()
        else:
            print("📂 Preserving caches for optimal performance across reruns")
        
        # Shutdown thread pool without clearing caches
        if hasattr(self, '_thread_pool') and self._thread_pool:
            try:
                self._thread_pool.shutdown(wait=True)
                print("🧹 Thread pool shutdown complete")
            except Exception as e:
                print(f"⚠️ Thread pool shutdown error: {e}")
        
        # Close session if possible (non-async) but preserve caches
        if hasattr(self, '_session') and self._session and not self._session.closed:
            try:
                # Try to close session synchronously if possible
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if not loop.is_running():
                        loop.run_until_complete(self._session.close())
                        if self._session_connector:
                            loop.run_until_complete(self._session_connector.close())
                except:
                    # Can't close session cleanly, will be cleaned up by GC
                    pass
            except Exception as e:
                print(f"⚠️ Session cleanup warning: {e}")
        
        cache_status = "cleared" if clear_caches else "preserved"
        print(f"🧹 STAC API shutdown complete - Cache stats: {self._cache_stats}, Caches: {cache_status}")
    
    def get_cache_stats(self):
        """Get cache statistics safely"""
        with self._cache_lock:
            return dict(self._cache_stats)  # Return copy
    
    def print_cache_stats(self):
        """Print cache statistics for debugging"""
        stats = self.get_cache_stats()
        cache_size = len(self._dataset_cache)
        hit_rate = stats['hits'] / (stats['hits'] + stats['misses']) if (stats['hits'] + stats['misses']) > 0 else 0
        print(f"📊 CACHE STATS - Size: {cache_size}/{self._dataset_cache_size}, Hit Rate: {hit_rate:.2%}, "
              f"Hits: {stats['hits']}, Misses: {stats['misses']}, Opens: {stats['opens']}, "
              f"Closes: {stats['closes']}, Evictions: {stats['evictions']}")
    
    def __del__(self):
        """Cleanup session and resources on destruction - CACHE PRESERVATION VERSION"""
        try:
            # Only close session, preserve caches for performance
            if hasattr(self, '_session') and self._session and not self._session.closed:
                try:
                    # Try to close session gracefully without clearing caches
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if not loop.is_running():
                            loop.run_until_complete(self._session.close())
                            if self._session_connector:
                                loop.run_until_complete(self._session_connector.close())
                    except:
                        # Session will be cleaned up by GC
                        pass
                except Exception as e:
                    pass  # Silent cleanup
            # NOTE: Caches and thread pool preserved for performance across reruns
        except Exception as e:
            # Don't raise exceptions in __del__
            try:
                print(f"⚠️ Cleanup warning during destruction: {e}")
            except:
                pass  # Even print might fail during shutdown
    
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
        Query a single STAC collection with enhanced retry logic and proper error handling
        """
        max_retries = 3
        base_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                collection_url = f"{self.stac_base_url}/{collection['id']}/collection.json"
                
                async with session.get(collection_url) as response:
                    # FIX: Proper handling of non-200 responses
                    if response.status == 200:
                        collection_data = await response.json()
                        
                        # Only proceed if we have valid collection data with links
                        if collection_data and collection_data.get('links'):
                            # Extract real pixel data from GeoTIFF for all collection types
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
                                print(f"🚫 No real pixel data available for {collection['name']} at ({lat}, {lon})")
                                return None
                        else:
                            print(f"⚠️ Collection data missing or invalid for {collection['id']}")
                            # Continue to retry logic below
                    elif response.status == 429:
                        # Rate limiting - use longer backoff
                        print(f"⚠️ Rate limited (429) for collection {collection['id']}, attempt {attempt + 1}/{max_retries}")
                        if attempt < max_retries - 1:
                            # Exponential backoff with jitter for rate limiting
                            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                            await asyncio.sleep(delay)
                            continue
                    elif 500 <= response.status < 600:
                        # Server errors - retry with backoff
                        print(f"⚠️ Server error ({response.status}) for collection {collection['id']}, attempt {attempt + 1}/{max_retries}")
                        if attempt < max_retries - 1:
                            # Exponential backoff with jitter for server errors
                            delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                            await asyncio.sleep(delay)
                            continue
                    else:
                        # Client errors (4xx) - don't retry
                        print(f"❌ Client error ({response.status}) for collection {collection['id']} - not retrying")
                        return None
                        
            except asyncio.TimeoutError:
                print(f"⏰ Timeout for collection {collection['id']}, attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter for timeouts
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                    await asyncio.sleep(delay)
                    continue
            except Exception as e:
                print(f"⚠️ Attempt {attempt + 1}/{max_retries} failed for collection {collection['id']}: {e}")
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter for general errors
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                    await asyncio.sleep(delay)
                    continue
                    
        print(f"❌ Failed to query collection {collection['id']} after {max_retries} attempts")
        return None
    
    async def extract_pixel_value_async(self, asset_url: str, lat: float, lon: float) -> Optional[float]:
        """Async version of pixel value extraction with thread offloading - PERFORMANCE OPTIMIZED"""
        # Offload blocking I/O to thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._thread_pool, 
            self.extract_pixel_value, 
            asset_url, lat, lon
        )
    
    def extract_pixel_value(self, asset_url: str, lat: float, lon: float) -> Optional[float]:
        """
        Extract pixel value from Cloud Optimized GeoTIFF using optimized caching and transforms
        OPTIMIZED: Uses dataset cache, proper CRS transforms, and error handling
        Returns actual pixel value or None if extraction fails
        """
        try:
            # Get cached dataset or open new one with LRU management
            dataset = self._get_cached_dataset(asset_url)
            if not dataset:
                return None
            
            # Use transform-aware coordinate conversion instead of bounds math
            # This handles CRS transformations properly
            try:
                # Check if coordinates are within dataset bounds first
                bounds = dataset.bounds
                if not (bounds.left <= lon <= bounds.right and 
                        bounds.bottom <= lat <= bounds.top):
                    print(f"🌍 Coordinates ({lat:.4f}, {lon:.4f}) outside data coverage")
                    return None
                
                # Transform geographic coordinates to dataset pixel coordinates
                # This is CRS-aware and handles projection transformations
                if dataset.crs != CRS.from_epsg(4326):
                    # Transform coordinates to dataset CRS if needed
                    from rasterio.warp import transform_geom
                    lon_transformed, lat_transformed = transform(
                        CRS.from_epsg(4326), dataset.crs, [lon], [lat]
                    )
                    lon, lat = lon_transformed[0], lat_transformed[0]
                
                # Use dataset.index() for proper coordinate-to-pixel conversion
                # This uses the dataset's affine transform matrix
                row, col = dataset.index(lon, lat)
                
                # Ensure pixel coordinates are within image bounds
                if not (0 <= row < dataset.height and 0 <= col < dataset.width):
                    print(f"📍 Transform result ({row}, {col}) outside image bounds ({dataset.height}, {dataset.width})")
                    return None
                
                # Read pixel value using precise window-based reading
                window = Window(col, row, 1, 1)
                pixel_data = dataset.read(1, window=window)
                
                if pixel_data.size == 0:
                    print(f"🚫 No data read from window at ({row}, {col})")
                    return None
                
                pixel_value = pixel_data[0, 0]
                
                # Enhanced NoData handling for ESA land cover data
                if dataset.nodata is not None and pixel_value == dataset.nodata:
                    print(f"🚫 Dataset NoData value ({dataset.nodata}) encountered at ({lat:.4f}, {lon:.4f})")
                    return None
                
                # ESA CCI Land Cover specific nodata values
                if pixel_value in [0, 255]:
                    print(f"🚫 ESA NoData value ({pixel_value}) encountered at ({lat:.4f}, {lon:.4f})")
                    return None
                
                # Convert to integer for land cover classification codes
                try:
                    pixel_value_int = int(round(pixel_value))
                    # Validate range for ESA CCI codes (typically 10-220)
                    if pixel_value_int < 1 or pixel_value_int > 250:
                        print(f"🚫 Invalid ESA land cover code ({pixel_value_int}) at ({lat:.4f}, {lon:.4f})")
                        return None
                    
                    print(f"✅ PIXEL EXTRACTED: ESA code {pixel_value_int} (raw: {pixel_value}) at ({lat:.4f}, {lon:.4f}) [CACHED]")
                    return float(pixel_value_int)
                    
                except (ValueError, OverflowError):
                    print(f"🚫 Failed to convert pixel value ({pixel_value}) to integer at ({lat:.4f}, {lon:.4f})")
                    return None
                    
            except Exception as transform_error:
                print(f"❌ Coordinate transformation failed: {transform_error}")
                # Fallback to original bounds-based method if transform fails
                return self._extract_pixel_value_fallback(dataset, lat, lon)
                
        except Exception as e:
            print(f"❌ Optimized pixel extraction failed for {asset_url}: {e}")
            return None
    
    def _extract_pixel_value_fallback(self, dataset, lat: float, lon: float) -> Optional[float]:
        """
        Fallback pixel extraction using original bounds-based method
        Used when transform-aware method fails
        """
        try:
            bounds = dataset.bounds
            width, height = dataset.width, dataset.height
            
            # Original bounds-based coordinate conversion
            pixel_x = int((lon - bounds.left) / (bounds.right - bounds.left) * width)
            pixel_y = int((bounds.top - lat) / (bounds.top - bounds.bottom) * height)
            
            if not (0 <= pixel_x < width and 0 <= pixel_y < height):
                return None
            
            window = Window(pixel_x, pixel_y, 1, 1)
            pixel_value = dataset.read(1, window=window)[0, 0]
            
            # Basic nodata handling
            if dataset.nodata is not None and pixel_value == dataset.nodata:
                return None
            if pixel_value in [0, 255]:
                return None
            
            try:
                pixel_value_int = int(round(pixel_value))
                if 1 <= pixel_value_int <= 250:
                    print(f"✅ FALLBACK EXTRACTED: ESA code {pixel_value_int} at ({lat:.4f}, {lon:.4f})")
                    return float(pixel_value_int)
            except (ValueError, OverflowError):
                pass
            
            return None
            
        except Exception as e:
            print(f"❌ Fallback extraction failed: {e}")
            return None

    def extract_batch_pixel_values(self, asset_url: str, coordinates: List[tuple]) -> List[Optional[float]]:
        """
        Batch extract pixel values from Cloud Optimized GeoTIFF for multiple coordinates
        OPTIMIZED: Now uses dataset cache and transform-aware coordinate conversion
        Backward compatible wrapper for the optimized implementation
        Returns list of pixel values in same order as input coordinates
        Enhanced with proper nodata handling for ESA land cover data
        """
        try:
            # Convert tuple coordinates to proper format if needed
            if coordinates and isinstance(coordinates[0], tuple) and len(coordinates[0]) == 2:
                # Convert from (lat, lon) tuples to List[Tuple[float, float]]
                typed_coordinates = [(float(lat), float(lon)) for lat, lon in coordinates]
            else:
                typed_coordinates = coordinates
            
            # Use the optimized implementation with dataset caching
            result = self.extract_batch_pixel_values_optimized(asset_url, typed_coordinates)
            
            # Log performance improvement notice
            valid_count = len([v for v in result if v is not None])
            print(f"✅ BATCH EXTRACTED: {valid_count}/{len(coordinates)} valid ESA codes [OPTIMIZED-CACHED]")
            
            return result
            
        except Exception as e:
            print(f"❌ Optimized batch extraction wrapper failed for {asset_url}: {e}")
            # Fallback to basic individual extraction if optimized version fails
            print(f"🔄 Falling back to individual pixel extraction...")
            result = []
            for lat, lon in coordinates:
                try:
                    pixel_value = self.extract_pixel_value(asset_url, lat, lon)
                    result.append(pixel_value)
                except Exception as individual_error:
                    print(f"❌ Individual extraction failed for ({lat}, {lon}): {individual_error}")
                    result.append(None)
            return result
    
    def get_stac_asset_url(self, collection_id: str) -> Optional[str]:
        """
        Get GeoTIFF asset URL from STAC catalog with caching, prioritizing most recent data
        """
        # Check cache first
        if collection_id in self._asset_url_cache:
            return self._asset_url_cache[collection_id]
        
        try:
            # Collection-specific fallback URLs for different data types
            collection_fallback_urls = {
                # Land Cover Collection - Updated URLs for reliability
                "land.cover_esacci.lc.l4": [
                    "https://s3.eu-central-1.wasabisys.com/openlandmap/lcv_land.cover_esacci.lc.l4_c_250m_s0..0cm_2020_v1.0.tif",
                    "https://zenodo.org/records/3939038/files/ESACCI-LC-L4-LCCS-Map-300m-P1Y-2020-v2.1.1.tif",
                    "https://s3.openlandmap.org/arco/lcv_land.cover_esacci.lc.l4_c_250m_s0..0cm_2020_v1.0.tif",
                    "https://s3.openlandmap.org/arco/lcv_land.cover_esacci.lc.l4_c_250m_s0..0cm_2019_v1.0.tif",
                ],
                # Water Occurrence / Land Mask Collection
                "water.occurrence_jrc.surfacewater": [
                    "https://s3.openlandmap.org/arco/hyd_water.occurrence_jrc.surfacewater_p_250m_s0..0cm_1984..2020_v1.0.tif",
                    "https://s3.openlandmap.org/arco/hyd_water.occurrence_jrc.surfacewater_p_250m_s0..0cm_1984..2019_v1.0.tif",
                ],
                # Enhanced Vegetation Index Collection
                "evi_mod13q1.tmwm.inpaint": [
                    "https://s3.openlandmap.org/arco/veg_evi_mod13q1.tmwm.inpaint_d_250m_s0..0cm_2014..2019_v1.0.tif",
                    "https://s3.openlandmap.org/arco/veg_evi_mod13q1.tmwm.inpaint_d_250m_s0..0cm_2013..2018_v1.0.tif",
                ],
                # fAPAR Collection  
                "fapar_essd.lstm": [
                    "https://s3.openlandmap.org/arco/veg_fapar_essd.lstm_d_250m_s0..0cm_2014..2019_v1.0.tif",
                    "https://s3.openlandmap.org/arco/veg_fapar_essd.lstm_d_250m_s0..0cm_2013..2018_v1.0.tif",
                ],
                # Terrain Elevation Collection
                "dtm.bareearth_ensemble": [
                    "https://s3.openlandmap.org/arco/dtm_dtm.bareearth_ensemble_m_250m_s0..0cm_2018..2020_v1.0.tif",
                    "https://s3.openlandmap.org/arco/dtm_elevation_bareearth_ensemble_m_250m_s0..0cm_2018..2020_v1.0.tif",
                ],
                # Soil Organic Carbon Collection
                "log.oc_iso.10694": [
                    "https://s3.openlandmap.org/arco/sol_log.oc_iso.10694_m_250m_s0..0cm_2001..2020_v1.0.tif",
                    "https://s3.openlandmap.org/arco/sol_log.oc_iso.10694_m_250m_s5..15cm_2001..2020_v1.0.tif",
                ]
            }
            
            # Get fallback URLs for this collection type
            asset_url_attempts = collection_fallback_urls.get(collection_id, [])
            
            # First try STAC catalog query with retry logic - search for most recent data
            collection_url = f"{self.stac_base_url}/{collection_id}/collection.json"
            
            max_retries = 3
            response = None
            for attempt in range(max_retries):
                try:
                    response = requests.get(collection_url, timeout=10)
                    if response.status_code == 200:
                        break  # Success, exit retry loop
                    elif attempt < max_retries - 1:
                        print(f"⚠️ Attempt {attempt + 1}/{max_retries} failed with status {response.status_code}. Retrying...")
                        time.sleep(1 * (attempt + 1))  # Exponential backoff
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"⚠️ Attempt {attempt + 1}/{max_retries} failed: {e}. Retrying...")
                        time.sleep(1 * (attempt + 1))
                    else:
                        print(f"❌ Failed to get collection after {max_retries} attempts: {e}")
                        response = None
            
            if response and response.status_code == 200:
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
                        
                        # Get STAC item with retry logic
                        item_response = None
                        for item_attempt in range(max_retries):
                            try:
                                item_response = requests.get(item_url, timeout=10)
                                if item_response.status_code == 200:
                                    break
                                elif item_attempt < max_retries - 1:
                                    print(f"⚠️ Item attempt {item_attempt + 1}/{max_retries} failed. Retrying...")
                                    time.sleep(1 * (item_attempt + 1))
                            except Exception as e:
                                if item_attempt < max_retries - 1:
                                    print(f"⚠️ Item attempt {item_attempt + 1}/{max_retries} failed: {e}. Retrying...")
                                    time.sleep(1 * (item_attempt + 1))
                                else:
                                    print(f"❌ Failed to get item after {max_retries} attempts: {e}")
                                    item_response = None
                        
                        if item_response and item_response.status_code == 200:
                            item_data = item_response.json()
                            
                            # Extract GeoTIFF asset URL following technical brief specifications
                            if 'assets' in item_data:
                                print(f"🎯 Available assets in {year}: {list(item_data['assets'].keys())}")
                                for asset_key, asset in item_data['assets'].items():
                                    asset_type = asset.get('type', '')
                                    asset_href = asset.get('href', '')
                                    asset_roles = asset.get('roles', [])
                                    asset_main = asset.get('main', False)
                                    
                                    # Follow technical brief: look for roles: ['data'] or asset.main === true
                                    if ('data' in asset_roles or asset_main or 
                                        'image/tiff' in asset_type or 'tiff' in asset_href.lower() or 
                                        asset_key in ['data', 'main', 'cog', 'asset']):
                                        asset_url = asset['href']
                                        print(f"✅ Found GeoTIFF asset from year {year}: {asset_url}")
                                        print(f"   📋 Asset details: roles={asset_roles}, main={asset_main}, type={asset_type}")
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
    
    async def extract_pixel_value_async(self, asset_url: str, lat: float, lon: float) -> Optional[float]:
        """
        Async version of pixel extraction with thread offloading for blocking I/O
        OPTIMIZED: Prevents blocking the event loop during raster operations
        """
        try:
            # Offload blocking raster I/O to thread pool to prevent event loop blocking
            pixel_value = await asyncio.to_thread(
                self.extract_pixel_value, asset_url, lat, lon
            )
            return pixel_value
        except Exception as e:
            print(f"❌ Async pixel extraction failed for {asset_url}: {e}")
            return None
    
    async def extract_batch_pixel_values_async(self, asset_url: str, coordinates: List[Tuple[float, float]]) -> List[Optional[float]]:
        """
        Async batch pixel extraction with thread offloading
        OPTIMIZED: Uses dataset cache and prevents event loop blocking
        """
        try:
            # Offload blocking batch raster I/O to thread pool
            pixel_values = await asyncio.to_thread(
                self.extract_batch_pixel_values_optimized, asset_url, coordinates
            )
            return pixel_values
        except Exception as e:
            print(f"❌ Async batch extraction failed for {asset_url}: {e}")
            return [None] * len(coordinates)
    
    def extract_batch_pixel_values_optimized(self, asset_url: str, coordinates: List[Tuple[float, float]]) -> List[Optional[float]]:
        """
        Optimized batch pixel extraction using dataset cache and transform-aware conversion
        OPTIMIZED: Uses cached dataset and proper coordinate transforms
        """
        try:
            # Get cached dataset or open new one with LRU management
            dataset = self._get_cached_dataset(asset_url)
            if not dataset:
                return [None] * len(coordinates)
            
            # Filter coordinates that are within bounds
            bounds = dataset.bounds
            valid_coords = []
            coord_indices = []
            
            for i, (lat, lon) in enumerate(coordinates):
                if (bounds.left <= lon <= bounds.right and 
                    bounds.bottom <= lat <= bounds.top):
                    
                    # Handle CRS transformation if needed
                    if dataset.crs != CRS.from_epsg(4326):
                        try:
                            lon_transformed, lat_transformed = transform(
                                CRS.from_epsg(4326), dataset.crs, [lon], [lat]
                            )
                            valid_coords.append((lon_transformed[0], lat_transformed[0]))
                        except:
                            # Skip coordinates that fail transformation
                            continue
                    else:
                        valid_coords.append((lon, lat))
                    
                    coord_indices.append(i)
            
            if not valid_coords:
                print(f"🌍 No coordinates within data coverage for batch extraction")
                return [None] * len(coordinates)
            
            # Use rasterio.sample for efficient batch sampling with cached dataset
            pixel_values = [None] * len(coordinates)
            try:
                sampled_values = list(dataset.sample(valid_coords))
                
                # Process sampled values with enhanced nodata handling
                for coord_idx, sampled_value in zip(coord_indices, sampled_values):
                    if len(sampled_value) > 0:
                        value = sampled_value[0]
                        
                        # Enhanced NoData handling
                        if dataset.nodata is not None and value == dataset.nodata:
                            continue
                        if value in [0, 255]:
                            continue
                        
                        # Convert to integer for land cover codes
                        try:
                            value_int = int(round(value))
                            if 1 <= value_int <= 250:
                                pixel_values[coord_idx] = float(value_int)
                        except (ValueError, OverflowError):
                            continue
                
                valid_count = len([v for v in pixel_values if v is not None])
                print(f"✅ BATCH EXTRACTED: {valid_count}/{len(coordinates)} valid ESA codes [CACHED]")
                return pixel_values
                
            except Exception as sample_error:
                print(f"❌ Batch sampling failed: {sample_error}")
                # Fallback to individual extraction
                for i, (lat, lon) in enumerate(coordinates):
                    if i in coord_indices:
                        pixel_values[i] = self.extract_pixel_value(asset_url, lat, lon)
                return pixel_values
                
        except Exception as e:
            print(f"❌ Optimized batch extraction failed for {asset_url}: {e}")
            return [None] * len(coordinates)
    
    async def _extract_real_pixel_data(self, session: aiohttp.ClientSession, lat: float, lon: float, collection_metadata: dict) -> tuple:
        """
        Extract real pixel data from OpenLandMap GeoTIFF files - ASYNC OFFLOADED VERSION
        Returns (pixel_value, data_source, raw_response)
        """
        collection_id = "land.cover_esacci.lc.l4"
        
        try:
            # Get GeoTIFF asset URL from STAC catalog (this is fast, no need to offload)
            asset_url = self.get_stac_asset_url(collection_id)
            
            if asset_url:
                # CRITICAL FIX: Offload blocking I/O operations to thread pool
                loop = asyncio.get_event_loop()
                pixel_value = await loop.run_in_executor(
                    self._thread_pool, 
                    self.extract_pixel_value, 
                    asset_url, lat, lon
                )
                
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
        terrain = []  # FIX: Separate terrain data into its own category
        vegetation = []  # FIX: Separate vegetation data into its own category
        ecosystem_type = None
        
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
                    
                
                # Add readable land cover type using centralized descriptions
                from .esa_landcover_codes import get_esa_description
                cover_type = get_esa_description(land_cover_code)
                
                land_cover.append({
                    **data_item,
                    "value": cover_type,
                    "unit": "class",
                    "code": land_cover_code
                })
            elif result["category"] == "vegetation":
                vegetation.append(data_item)
                climate.append(data_item)  # Keep backward compatibility
            elif result["category"] == "terrain":
                terrain.append(data_item)  # FIX: Store terrain data separately
        
        # If no real pixel data found, return None (no fallback per guidance)
        if not ecosystem_type:
            print(f"❌ No real pixel data available for {lat}, {lon}. No fallback data provided.")
            
            return {
                "ecosystem_type": None,
    
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
            "stac_collections_queried": len(stac_results) if stac_results else 0,
            "processing_method": "stac_metadata_analysis"
        }
        
        # CRITICAL FIX: Add the raw response from pixel extraction if available
        if raw_response_data:
            raw_stac_data["raw_response"] = raw_response_data
            print(f"🔍 THREADING FIX: Raw response preserved for UI debugging: {raw_response_data.get('extraction_method', 'unknown')}")
        
        return {
            "ecosystem_type": ecosystem_type,
            "landcover_class": landcover_class,  # Add the landcover code for integration
            "coordinates": {"lat": lat, "lon": lon},
            "climate": climate if climate else None,
            "vegetation": vegetation if vegetation else None,  # FIX: Add separate vegetation category
            "terrain": terrain if terrain else None,  # FIX: Add separate terrain category
            "landCover": land_cover if land_cover else None, 
            "soil": soil if soil else None,
            "data_source": actual_data_source,
            "raw_stac_data": raw_stac_data,  # Now contains the preserved raw response
            "query_time": json.dumps({"timestamp": "now"}, default=str)
        }
    
    def _extract_landcover_direct(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Direct landcover extraction - delegates to cached version for better performance
        """
        return self._extract_landcover_direct_uncached(lat, lon)
    
    def _extract_landcover_direct_uncached(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Direct landcover extraction using fallback URLs when STAC collections fail (uncached version)
        """
        try:
            collection_id = "land.cover_esacci.lc.l4"
            asset_url = self.get_stac_asset_url(collection_id)
            
            if asset_url:
                pixel_value = self.extract_pixel_value(asset_url, lat, lon)
                
                if pixel_value is not None:
                    landcover_code = int(pixel_value)
                    
                    # Apply forest type mapping
                    base_ecosystem_type = self.landcover_to_esvd.get(landcover_code, "Unknown")
                    if (base_ecosystem_type == "Forest" or landcover_code in [70, 71]):
                        ecosystem_type = self._determine_forest_type_from_coordinates(lat, lon)
                    else:
                        ecosystem_type = base_ecosystem_type
                    
                    return {
                        "ecosystem_type": ecosystem_type,
                        "landcover_class": landcover_code,
                        "coordinates": {"lat": lat, "lon": lon},
                        "data_source": "Direct ESA Land Cover Extraction",
                        "raw_stac_data": {
                            "extraction_method": "direct_landcover_fallback",
                            "landcover_code": landcover_code,
                            "asset_url": asset_url
                        },
                        "query_time": json.dumps({"timestamp": "now"}, default=str)
                    }
        except Exception as e:
            print(f"❌ Direct landcover extraction failed: {e}")
        
        return None
    
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
    
            
    def get_batch_ecosystem_types(self, coordinates: List[tuple]) -> List[Dict[str, Any]]:
        """
        Batch ecosystem detection for multiple coordinates using optimized GeoTIFF sampling
        Opens GeoTIFF file once and samples all points efficiently
        Fixed to be synchronous to avoid asyncio issues
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
                    "landcover_class": None,
                    "coordinates": {"lat": lat, "lon": lon},
                    "data_source": "Error: Batch Processing Failed",
                    "error": f"STAC batch processing failed: {str(e)}",
                    "query_time": json.dumps({"timestamp": "now"}, default=str)
                })
        
        return results
    
    def get_ecosystem_type(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        FAST: Direct GeoTIFF extraction bypassing slow STAC metadata discovery
        """
        try:
            # Use cached version for better performance
            return self._get_ecosystem_type_cached(lat, lon)
        except Exception as e:
            print(f"Direct extraction error: {e}")
            return self._fallback_ecosystem_detection(lat, lon)
    
    def _get_ecosystem_type_cached(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Cached version of ecosystem type extraction with geographic quantization
        """
        try:
            import streamlit as st
            
            # Quantize coordinates to increase cache hit rate (1e-4 ≈ 11m resolution)
            quantized_lat = round(lat, 4)
            quantized_lon = round(lon, 4)
            
            @st.cache_data(ttl=3600, max_entries=10000)  # 1 hour TTL, 10k max entries
            def _cached_extract_landcover(q_lat: float, q_lon: float) -> Dict[str, Any]:
                # Skip complex STAC discovery - use direct landcover extraction immediately
                landcover_result = self._extract_landcover_direct_uncached(q_lat, q_lon)
                if landcover_result:
                    return landcover_result
                else:
                    return self._fallback_ecosystem_detection(q_lat, q_lon)
            
            return _cached_extract_landcover(quantized_lat, quantized_lon)
        except ImportError:
            # Fallback for non-Streamlit environments
            landcover_result = self._extract_landcover_direct(lat, lon)
            if landcover_result:
                return landcover_result
            else:
                return self._fallback_ecosystem_detection(lat, lon)
    
    def _query_stac_collections_sync(self, lat: float, lon: float) -> Optional[List[Dict]]:
        """
        Synchronous STAC collection query to avoid async/event loop issues
        """
        results = []
        
        try:
            import requests
            
            for collection in self.collections:
                try:
                    # Use synchronous requests instead of async
                    collection_url = f"{self.stac_base_url}/{collection['id']}/collection.json"
                    response = requests.get(collection_url, timeout=10)
                    
                    if response.status_code == 200:
                        collection_data = response.json()
                        
                        if collection_data and collection_data.get('links'):
                            # Extract pixel data synchronously
                            pixel_value = self._extract_pixel_sync(lat, lon, collection_data)
                            
                            if pixel_value is not None:
                                results.append({
                                    "collection": collection["id"],
                                    "name": collection["name"],
                                    "category": collection["category"],
                                    "value": pixel_value,
                                    "unit": collection["unit"],
                                    "metadata": {
                                        "title": collection_data.get("title", ""),
                                        "description": collection_data.get("description", ""),
                                        "license": collection_data.get("license", ""),
                                        "source": "stac_sync",
                                    }
                                })
                except Exception as e:
                    print(f"⚠️ Sync collection query failed for {collection['id']}: {e}")
                    continue
            
            return results if results else None
            
        except Exception as e:
            print(f"❌ Sync STAC query failed: {e}")
            return None
    
    def _extract_pixel_sync(self, lat: float, lon: float, collection: Dict) -> Optional[float]:
        """
        Synchronous pixel extraction following proven architecture
        Implements full flow: Collection Discovery → Item Selection → Asset Resolution → COG Access → Value Extraction
        """
        try:
            collection_id = collection['id']
            
            # Step 1: Collection Discovery (with caching)
            collection_data = self._get_collection_metadata_cached(collection_id)
            if not collection_data:
                return None
            
            # Step 2 & 3: Item Selection → Asset Resolution (with caching)
            asset_url = self._find_geotiff_asset_url(collection_data, collection_id)
            if not asset_url:
                return None
            
            # Step 4 & 5: COG Access → Value Extraction
            pixel_value = self._extract_single_pixel_safe(lat, lon, asset_url)
            return pixel_value
            
        except Exception as e:
            print(f"⚠️ Sync pixel extraction failed for {collection.get('id', 'unknown')}: {e}")
            return None
    
    def _extract_landcover_direct(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Direct land cover extraction using multiple fallback ESA data sources
        """
        try:
            # Try multiple land cover data sources as fallbacks
            landcover_urls = [
                # Primary ESA land cover URL (updated)
                "https://s3.eu-central-1.wasabisys.com/stac/openlandmap/land.cover_esacci.lc.l4/land.cover_esacci.lc.l4_20200101_20201231/land.cover_esacci.lc.l4_c_250m_s_20200101_20201231_go_epsg.4326_v20230608.tif",
                # Backup URLs
                "https://s3.openlandmap.org/arco/land.cover_esacci.lc.l4_c_250m_s_20200101_20201231_go_espg.4326_v20230608.tif",
                "https://cloud.vito.be/s3/arco/land.cover_esacci.lc.l4_c_250m_s_20200101_20201231_go_epsg.4326_v20230608.tif"
            ]
            
            # Try each URL until one works
            for esa_url in landcover_urls:
                print(f"🔍 Trying land cover URL: {esa_url[:80]}...")
            
                pixel_value = self._extract_single_pixel_safe(lat, lon, esa_url)
                if pixel_value is not None:
                    print(f"✅ Successfully extracted land cover pixel value: {pixel_value}")
                    break
                else:
                    print(f"⚠️ Failed to extract from {esa_url[:50]}..., trying next URL")
            
            if pixel_value is not None:
                # Process the ESA code through existing mapping
                esa_code = int(pixel_value)
                ecosystem_type = self.landcover_to_esvd.get(esa_code, "Grassland")
                
                # Debug the mapping for troubleshooting ESA codes 11, 40, 130
                if esa_code in [11, 40, 130, 41]:
                    print(f"🔍 ESA MAPPING DEBUG: Code {esa_code} → {ecosystem_type}")
                
                ecosystem_info = {"ecosystem_type": ecosystem_type}
                
                return {
                    "ecosystem_type": ecosystem_info["ecosystem_type"],
                    "landcover_class": int(pixel_value),
                    "coordinates": {"lat": lat, "lon": lon},
                    "data_source": "Direct ESA Land Cover Extraction",
                    "raw_stac_data": {
                        "pixel_value": pixel_value,
                        "asset_url": esa_url
                    },
                    "query_time": json.dumps({"timestamp": "now"}, default=str)
                }
            return None
            
        except Exception as e:
            print(f"⚠️ Direct land cover extraction failed: {e}")
            return None
    
    def _extract_single_pixel_safe(self, lat: float, lon: float, asset_url: str) -> Optional[float]:
        """
        Safe single pixel extraction with proper GDAL environment configuration
        """
        dataset = None
        try:
            import rasterio
            import os
            import numpy as np
            
            # Coordinate bounds checking (as per technical guidance)
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                print(f"⚠️ Out-of-bounds coordinates: ({lat}, {lon})")
                return None
            
            # Use cached dataset or open new one with proper GDAL environment
            dataset = self._get_cached_dataset(asset_url)
            if dataset is None:
                print(f"❌ Failed to open dataset: {asset_url[:50]}...")
                return None
            
            # Transform lat/lon to pixel coordinates using image bounds
            try:
                row, col = dataset.index(lon, lat)
            except Exception as coord_error:
                print(f"⚠️ Coordinate transformation failed for ({lat}, {lon}): {coord_error}")
                return None
            
            # Check pixel bounds (out-of-bounds returns null as per guidance)
            if not (0 <= row < dataset.height and 0 <= col < dataset.width):
                return None
            
            # THREAD-SAFETY FIX: Synchronize dataset.read() operations with per-dataset lock
            dataset_lock = None
            with self._locks_lock:
                dataset_lock = self._dataset_locks.get(asset_url)
            
            if dataset_lock is None:
                print(f"⚠️ No lock found for dataset {asset_url[:50]}...")
                return None
            
            # Read 1x1 pixel window with thread synchronization
            with dataset_lock:  # CRITICAL: Thread-safe dataset access
                try:
                    pixel_data = dataset.read(1, window=((row, row+1), (col, col+1)))
                    
                    if pixel_data.size > 0:
                        value = pixel_data[0, 0]
                        
                        # Enhanced NoData handling (as mentioned in guidance)
                        if dataset.nodata is not None and value == dataset.nodata:
                            return None
                        
                        # Handle masked arrays from COG
                        if hasattr(value, 'mask') and value.mask:
                            return None
                        
                        # Apply scaling factors from STAC metadata if available
                        # (Technical guidance mentions this is needed)
                        scaling_factor = getattr(dataset, 'scales', [1.0])[0] if hasattr(dataset, 'scales') else 1.0
                        offset = getattr(dataset, 'offsets', [0.0])[0] if hasattr(dataset, 'offsets') else 0.0
                        
                        scaled_value = float(value) * scaling_factor + offset
                        
                        # Detect if this is a landcover dataset for ESA validation
                        is_landcover = ('land.cover' in asset_url.lower() or 
                                      'lc.l4' in asset_url.lower() or
                                      'esacci' in asset_url.lower())
                        
                        # Apply ESA validation ONLY to landcover datasets (SCOPING FIX)
                        if is_landcover:
                            # Convert to integer for land cover codes
                            try:
                                pixel_value_int = int(round(scaled_value))
                                # Validate ESA CCI range (typically 10-220) only for landcover
                                if 1 <= pixel_value_int <= 250 and np.isfinite(scaled_value):
                                    return float(pixel_value_int)
                                else:
                                    print(f"⚠️ Invalid ESA landcover code: {pixel_value_int} at ({lat}, {lon})")
                                    return None
                            except (ValueError, OverflowError):
                                return None
                        else:
                            # For non-landcover datasets, return the raw scaled value if finite
                            if np.isfinite(scaled_value):
                                return scaled_value
                
                except Exception as read_error:
                    print(f"⚠️ Thread-safe pixel read failed: {read_error}")
                    return None
            
            return None
            
        except Exception as e:
            print(f"❌ COG access failed for {asset_url}: {e}")
            return None
        # THREAD-SAFETY FIX: Remove finally block that closes cached datasets!
        # Cached datasets must NOT be closed after each use - they stay open for reuse
    
    def _get_collection_metadata_cached(self, collection_id: str) -> Optional[Dict]:
        """
        Get collection metadata with caching (following technical guidance)
        Implements: Collection Discovery step
        """
        import time
        import requests
        
        cache_key = f"collection_{collection_id}"
        current_time = time.time()
        
        # Check cache validity
        if (cache_key in self._collection_cache and 
            cache_key in self._cache_timestamps and
            current_time - self._cache_timestamps[cache_key] < self._cache_ttl_seconds):
            return self._collection_cache[cache_key]
        
        try:
            collection_url = f"{self.stac_base_url}/{collection_id}/collection.json"
            response = requests.get(collection_url, timeout=10)
            
            if response.status_code == 200:
                collection_data = response.json()
                # Cache the metadata
                self._collection_cache[cache_key] = collection_data
                self._cache_timestamps[cache_key] = current_time
                return collection_data
                
        except Exception as e:
            print(f"⚠️ Collection metadata fetch failed for {collection_id}: {e}")
        
        return None
    
    def _get_latest_item_cached(self, collection_data: Dict, collection_id: str) -> Optional[Dict]:
        """
        Get latest STAC item with caching (following technical guidance)
        Implements: Item Selection step
        """
        import time
        import requests
        
        cache_key = f"item_{collection_id}"
        current_time = time.time()
        
        # Check cache validity
        if (cache_key in self._item_cache and 
            cache_key in self._cache_timestamps and
            current_time - self._cache_timestamps[cache_key] < self._cache_ttl_seconds):
            return self._item_cache[cache_key]
        
        try:
            # Find latest item link (rel: "item") as per guidance
            latest_item_url = None
            for link in collection_data.get('links', []):
                if link.get('rel') == 'item':
                    href = link.get('href')
                    if href:
                        # Fix relative URL resolution (key issue from logs)
                        if href.startswith('./'):
                            # Convert relative URL to absolute
                            base_url = f"{self.stac_base_url}/{collection_id}"
                            latest_item_url = f"{base_url}/{href[2:]}"  # Remove './' prefix
                        elif href.startswith('http'):
                            latest_item_url = href
                        else:
                            # Relative path without './'
                            base_url = f"{self.stac_base_url}/{collection_id}"
                            latest_item_url = f"{base_url}/{href}"
                        break  # Take first/latest item
            
            if latest_item_url:
                response = requests.get(latest_item_url, timeout=10)
                if response.status_code == 200:
                    item_data = response.json()
                    # Cache the item metadata
                    self._item_cache[cache_key] = item_data
                    self._cache_timestamps[cache_key] = current_time
                    return item_data
                    
        except Exception as e:
            print(f"⚠️ Item metadata fetch failed for {collection_id}: {e}")
        
        return None
    
    def _find_geotiff_asset_url(self, collection_data: Dict, collection_id: str = None) -> Optional[str]:
        """
        Find GeoTIFF asset URL following proven architecture
        Implements: Asset Resolution step (roles: ['data'] or asset.main === true)
        """
        try:
            if not collection_id:
                return None
            
            # Get latest item using cached approach
            item_data = self._get_latest_item_cached(collection_data, collection_id)
            if not item_data:
                return None
            
            assets = item_data.get('assets', {})
            
            # Select main data asset (following technical guidance)
            for asset_key, asset_info in assets.items():
                if isinstance(asset_info, dict):
                    # Check for main data asset (roles: ['data'] or asset.main === true)
                    roles = asset_info.get('roles', [])
                    is_main = asset_info.get('main', False)
                    asset_type = asset_info.get('type', '')
                    
                    # Priority: main data assets with GeoTIFF type
                    if ('data' in roles or is_main) and ('geotiff' in asset_type.lower() or 'tiff' in asset_type.lower()):
                        return asset_info.get('href')
            
            # Fallback: any GeoTIFF asset
            for asset_key, asset_info in assets.items():
                if isinstance(asset_info, dict):
                    asset_type = asset_info.get('type', '')
                    if 'geotiff' in asset_type.lower() or 'tiff' in asset_type.lower():
                        return asset_info.get('href')
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error finding GeoTIFF asset: {e}")
            return None
    
    async def _async_get_ecosystem_type(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Async method to handle STAC queries with proper session management
        """
        try:
            stac_results = await self.query_stac_collections(lat, lon)
            if stac_results:
                return self.process_stac_data(lat, lon, stac_results)
            else:
                # Fall back to direct asset URL approach if STAC collections fail
                print(f"📋 STAC collections failed, trying direct landcover extraction for ({lat}, {lon})")
                try:
                    # Try direct landcover extraction using fallback URLs
                    landcover_result = self._extract_landcover_direct(lat, lon)
                    if landcover_result:
                        return landcover_result
                except Exception as fallback_error:
                    print(f"⚠️ Direct landcover extraction also failed: {fallback_error}")
                
                # Return error when STAC data unavailable
                return {
                    "ecosystem_type": "Unknown",
                    "coordinates": {"lat": lat, "lon": lon},
                    "data_source": "Error: No Real STAC Data Available", 
                    "error": "No genuine STAC collection data available for these coordinates",
                    "query_time": json.dumps({"timestamp": "now"}, default=str)
                }
        except Exception as e:
            print(f"⚠️ Async STAC query failed: {e}")
            return self._fallback_ecosystem_detection(lat, lon)
    
    def _fallback_ecosystem_detection(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Fallback ecosystem detection when STAC API completely fails
        """
        return {
            "ecosystem_type": "Unknown",
            "landcover_class": None,
            "coordinates": {"lat": lat, "lon": lon},
            "data_source": "Error: STAC API Failed",
            "error": "STAC API processing failed - all methods exhausted",
            "query_time": json.dumps({"timestamp": "now"}, default=str)
        }

# Use Streamlit cache_resource to persist instance across reruns for better performance
def get_cached_openlandmap_stac():
    """
    Get persistent OpenLandMapSTAC instance using Streamlit cache_resource.
    This ensures the HTTP session, thread pool, and dataset cache survive across reruns.
    """
    try:
        import streamlit as st
        
        @st.cache_resource
        def _create_openlandmap_stac():
            return OpenLandMapSTAC()
        
        return _create_openlandmap_stac()
    except ImportError:
        # Fallback for non-Streamlit environments
        return OpenLandMapSTAC()

# Global instance with caching
openlandmap_stac = get_cached_openlandmap_stac()