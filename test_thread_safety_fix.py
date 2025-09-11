#!/usr/bin/env python3
"""
Test script to verify thread-safety fixes for rasterio dataset caching
This test verifies that corrupted pixel values (ESA codes like 3124, 2440, 2424) 
are now fixed and valid codes (0-250 range) are returned.
"""

import asyncio
import concurrent.futures
import time
import threading
from typing import List, Dict, Any
import sys
import os

# Add utils to path
sys.path.append('utils')

from openlandmap_stac_api import OpenLandMapSTAC

def test_concurrent_pixel_extraction(stac_api: OpenLandMapSTAC, test_coordinates: List[tuple], iterations: int = 10):
    """
    Test concurrent pixel extraction to verify thread-safety fixes
    """
    print(f"🧪 Testing concurrent pixel extraction with {len(test_coordinates)} coordinates x {iterations} iterations")
    
    all_results = []
    corrupted_values = []
    valid_esa_codes = []
    
    def extract_pixel_batch(thread_id: int) -> List[Dict[str, Any]]:
        """Extract pixels for all test coordinates in a single thread"""
        results = []
        
        for i, (lat, lon) in enumerate(test_coordinates):
            try:
                # Direct extraction to test the core thread-safety issue
                result = stac_api._extract_landcover_direct(lat, lon)
                
                if result and result.get('landcover_class') is not None:
                    esa_code = result['landcover_class']
                    ecosystem_type = result.get('ecosystem_type', 'Unknown')
                    
                    results.append({
                        'thread_id': thread_id,
                        'coord_idx': i,
                        'lat': lat,
                        'lon': lon,
                        'esa_code': esa_code,
                        'ecosystem_type': ecosystem_type,
                        'is_valid': 1 <= esa_code <= 250,
                        'is_corrupted': esa_code > 250 or esa_code < 1
                    })
                    
                    print(f"📍 Thread {thread_id}, Point {i}: ESA={esa_code} → {ecosystem_type} at ({lat:.4f}, {lon:.4f})")
                    
                else:
                    print(f"❌ Thread {thread_id}, Point {i}: Failed extraction at ({lat:.4f}, {lon:.4f})")
                    
            except Exception as e:
                print(f"⚠️ Thread {thread_id}, Point {i}: Error {e}")
        
        return results
    
    # Run concurrent extractions
    print(f"🚀 Starting {iterations} concurrent threads...")
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=iterations) as executor:
        # Submit all thread tasks
        future_to_thread = {
            executor.submit(extract_pixel_batch, thread_id): thread_id 
            for thread_id in range(iterations)
        }
        
        # Collect results
        for future in concurrent.futures.as_completed(future_to_thread):
            thread_id = future_to_thread[future]
            try:
                thread_results = future.result()
                all_results.extend(thread_results)
            except Exception as e:
                print(f"❌ Thread {thread_id} failed: {e}")
    
    end_time = time.time()
    print(f"⏱️ Completed {iterations} threads in {end_time - start_time:.2f} seconds")
    
    # Analyze results
    if all_results:
        for result in all_results:
            esa_code = result['esa_code']
            if result['is_corrupted']:
                corrupted_values.append(esa_code)
            elif result['is_valid']:
                valid_esa_codes.append(esa_code)
        
        # Statistics
        total_extractions = len(all_results)
        corrupted_count = len(corrupted_values)
        valid_count = len(valid_esa_codes)
        
        print(f"\n📊 THREAD-SAFETY TEST RESULTS:")
        print(f"  Total extractions: {total_extractions}")
        print(f"  Valid ESA codes: {valid_count} ({valid_count/total_extractions*100:.1f}%)")
        print(f"  Corrupted values: {corrupted_count} ({corrupted_count/total_extractions*100:.1f}%)")
        
        if corrupted_values:
            print(f"  🚨 CORRUPTED VALUES FOUND: {sorted(set(corrupted_values))}")
        else:
            print(f"  ✅ NO CORRUPTED VALUES - Thread-safety fix successful!")
        
        if valid_esa_codes:
            unique_valid = sorted(set(valid_esa_codes))
            print(f"  ✅ Valid ESA codes found: {unique_valid[:10]}{'...' if len(unique_valid) > 10 else ''}")
        
        # Check for consistency across threads
        coordinate_results = {}
        for result in all_results:
            key = (result['lat'], result['lon'])
            if key not in coordinate_results:
                coordinate_results[key] = []
            coordinate_results[key].append(result['esa_code'])
        
        inconsistent_coords = []
        for coord, codes in coordinate_results.items():
            unique_codes = set(codes)
            if len(unique_codes) > 1:
                inconsistent_coords.append((coord, unique_codes))
        
        if inconsistent_coords:
            print(f"  🚨 INCONSISTENT RESULTS across threads: {len(inconsistent_coords)} coordinates")
            for coord, codes in inconsistent_coords[:3]:  # Show first 3
                print(f"    {coord}: got codes {codes}")
        else:
            print(f"  ✅ CONSISTENT RESULTS across all threads")
        
        return {
            'total_extractions': total_extractions,
            'valid_count': valid_count,
            'corrupted_count': corrupted_count,
            'corrupted_values': corrupted_values,
            'valid_esa_codes': list(set(valid_esa_codes)),
            'inconsistent_coords': len(inconsistent_coords),
            'thread_safety_passed': corrupted_count == 0 and len(inconsistent_coords) == 0
        }
    else:
        print("❌ No results obtained from any thread")
        return None

def test_cache_stats(stac_api: OpenLandMapSTAC):
    """Test cache statistics and thread-safety infrastructure"""
    print(f"\n🔍 CACHE INFRASTRUCTURE TEST:")
    
    # Print cache stats
    stac_api.print_cache_stats()
    
    # Check if per-dataset locks are working
    cache_size = len(stac_api._dataset_cache)
    locks_count = len(stac_api._dataset_locks)
    
    print(f"  Dataset cache size: {cache_size}")
    print(f"  Dataset locks count: {locks_count}")
    
    if cache_size > 0 and locks_count >= cache_size:
        print(f"  ✅ Per-dataset locks properly created")
    elif cache_size > 0:
        print(f"  🚨 Missing dataset locks! Cache={cache_size}, Locks={locks_count}")
    else:
        print(f"  ℹ️ No datasets cached yet")
    
    return {
        'cache_size': cache_size,
        'locks_count': locks_count,
        'locks_properly_created': locks_count >= cache_size if cache_size > 0 else True
    }

def main():
    """Main test function"""
    print("🧪 THREAD-SAFETY FIX VERIFICATION TEST")
    print("Testing fixes for corrupted ESA codes (3124, 2440, 2424 → valid 0-250 range)")
    print("=" * 80)
    
    # Initialize STAC API
    stac_api = OpenLandMapSTAC(max_dataset_cache_size=5)
    
    # Test coordinates from different regions to get diverse ESA codes
    test_coordinates = [
        (40.7128, -74.0060),   # New York City, USA (Urban)
        (51.5074, -0.1278),    # London, UK (Urban) 
        (35.6762, 139.6503),   # Tokyo, Japan (Urban)
        (-33.8688, 151.2093),  # Sydney, Australia (Urban)
        (52.5200, 13.4050),    # Berlin, Germany (Urban)
        (48.8566, 2.3522),     # Paris, France (Urban)
        (55.7558, 37.6173),    # Moscow, Russia (Urban/Forest)
        (39.9042, 116.4074),   # Beijing, China (Urban)
        (37.7749, -122.4194),  # San Francisco, USA (Urban)
        (45.4215, -75.6972),   # Ottawa, Canada (Forest/Urban)
    ]
    
    try:
        # Test 1: Cache infrastructure
        cache_test = test_cache_stats(stac_api)
        
        # Test 2: Concurrent pixel extraction
        thread_test = test_concurrent_pixel_extraction(
            stac_api, 
            test_coordinates, 
            iterations=8  # 8 concurrent threads
        )
        
        # Test 3: Cache stats after load
        print(f"\n🔍 CACHE STATS AFTER LOAD:")
        final_cache_test = test_cache_stats(stac_api)
        
        # Final assessment
        print(f"\n🏁 FINAL ASSESSMENT:")
        if thread_test and thread_test['thread_safety_passed']:
            print(f"✅ THREAD-SAFETY FIX SUCCESSFUL!")
            print(f"   - No corrupted values found")
            print(f"   - Consistent results across threads")
            print(f"   - Valid ESA codes: {len(thread_test['valid_esa_codes'])} unique codes")
        elif thread_test:
            print(f"🚨 THREAD-SAFETY ISSUES REMAIN:")
            if thread_test['corrupted_count'] > 0:
                print(f"   - {thread_test['corrupted_count']} corrupted values: {thread_test['corrupted_values'][:5]}")
            if thread_test['inconsistent_coords'] > 0:
                print(f"   - {thread_test['inconsistent_coords']} coordinates with inconsistent results")
        else:
            print(f"❌ TEST FAILED - No results obtained")
        
        if final_cache_test['locks_properly_created']:
            print(f"✅ Per-dataset locking infrastructure working correctly")
        else:
            print(f"🚨 Per-dataset locking infrastructure has issues")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        try:
            stac_api.shutdown(clear_caches=False)  # Preserve caches for performance
            print(f"\n🧹 Test cleanup completed")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")

if __name__ == "__main__":
    main()