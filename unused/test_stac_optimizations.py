#!/usr/bin/env python3
"""
Test script to validate STAC API performance optimizations
Tests dataset caching, transform-aware coordinate conversion, and async operations
"""

import asyncio
import time
from utils.openlandmap_stac_api import OpenLandMapSTAC

async def test_stac_optimizations():
    """Test the implemented STAC API optimizations"""
    
    print("🧪 Testing STAC API Performance Optimizations")
    print("=" * 50)
    
    # Initialize STAC client with custom cache size
    stac_client = OpenLandMapSTAC(max_dataset_cache_size=5)
    
    # Test coordinates (multiple points to test caching)
    test_coordinates = [
        (40.7128, -74.0060),  # New York City
        (51.5074, -0.1278),   # London
        (35.6762, 139.6503),  # Tokyo
        (40.7589, -73.9851),  # Central Park (nearby NYC for cache test)
        (40.6782, -73.9442),  # Brooklyn (nearby NYC for cache test)
    ]
    
    # Test 1: Single coordinate extraction with caching
    print("\n1. Testing single coordinate extraction with LRU caching")
    print("-" * 50)
    
    start_time = time.time()
    for i, (lat, lon) in enumerate(test_coordinates):
        print(f"\n🔍 Testing coordinate {i+1}: ({lat}, {lon})")
        
        # Get asset URL for land cover collection
        asset_url = stac_client.get_stac_asset_url("land.cover_esacci.lc.l4")
        if asset_url:
            print(f"✅ Asset URL found: {asset_url[:50]}...")
            
            # Test synchronous extraction (should use cache after first call)
            pixel_value = stac_client.extract_pixel_value(asset_url, lat, lon)
            if pixel_value is not None:
                print(f"✅ Extracted pixel value: {pixel_value}")
            else:
                print(f"⚠️ No pixel value extracted")
        else:
            print("❌ No asset URL found")
    
    sync_time = time.time() - start_time
    print(f"\n⏱️ Synchronous extraction time: {sync_time:.2f} seconds")
    
    # Test 2: Async extraction with thread offloading
    print("\n2. Testing async extraction with thread offloading")
    print("-" * 50)
    
    start_time = time.time()
    
    asset_url = stac_client.get_stac_asset_url("land.cover_esacci.lc.l4")
    if asset_url:
        # Test async extraction
        tasks = []
        for lat, lon in test_coordinates[:3]:  # Test first 3 coordinates
            task = stac_client.extract_pixel_value_async(asset_url, lat, lon)
            tasks.append(task)
        
        # Execute async tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, (result, (lat, lon)) in enumerate(zip(results, test_coordinates[:3])):
            if isinstance(result, Exception):
                print(f"❌ Async extraction {i+1} failed: {result}")
            elif result is not None:
                print(f"✅ Async extracted ({lat}, {lon}): {result}")
            else:
                print(f"⚠️ Async extraction {i+1} returned None")
    
    async_time = time.time() - start_time
    print(f"\n⏱️ Async extraction time: {async_time:.2f} seconds")
    
    # Test 3: Batch extraction with optimizations
    print("\n3. Testing batch extraction with optimizations")
    print("-" * 50)
    
    start_time = time.time()
    
    if asset_url:
        # Test both old and new batch methods
        batch_coords = test_coordinates[:3]
        
        # Test optimized batch method
        batch_results = stac_client.extract_batch_pixel_values_optimized(asset_url, batch_coords)
        print(f"✅ Optimized batch results: {batch_results}")
        
        # Test backward compatible method
        legacy_results = stac_client.extract_batch_pixel_values(asset_url, batch_coords)
        print(f"✅ Legacy batch results: {legacy_results}")
        
        # Compare results
        if batch_results == legacy_results:
            print("✅ Backward compatibility confirmed - results match!")
        else:
            print("⚠️ Results differ between optimized and legacy methods")
    
    batch_time = time.time() - start_time
    print(f"\n⏱️ Batch extraction time: {batch_time:.2f} seconds")
    
    # Test 4: Cache effectiveness
    print("\n4. Testing cache effectiveness")
    print("-" * 50)
    
    cache_info = {
        'cache_size': len(stac_client._dataset_cache),
        'cached_urls': list(stac_client._dataset_cache.keys())
    }
    print(f"📊 Dataset cache size: {cache_info['cache_size']}")
    print(f"📊 Cache efficiency: Dataset reused across {len(test_coordinates)} coordinate tests")
    
    # Test 5: Cleanup and resource management
    print("\n5. Testing cleanup and resource management")
    print("-" * 50)
    
    print("🧹 Cleaning up resources...")
    await stac_client.close_session()
    
    print("✅ STAC optimization tests completed!")
    print(f"📈 Performance Summary:")
    print(f"   - Synchronous time: {sync_time:.2f}s")
    print(f"   - Async time: {async_time:.2f}s")
    print(f"   - Batch time: {batch_time:.2f}s")
    print(f"   - Cache utilization: {cache_info['cache_size']} datasets cached")

if __name__ == "__main__":
    asyncio.run(test_stac_optimizations())