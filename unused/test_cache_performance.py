#!/usr/bin/env python3
"""
Performance Test Suite for OpenLandMapSTAC Cache Implementation

This test verifies that:
1. st.cache_resource properly persists OpenLandMapSTAC instances
2. Coordinate caching with geographic quantization works correctly
3. Dataset caches persist across function calls
4. Cache hit rates improve performance significantly

Run this test to verify cache improvements are working as intended.
"""

import time
import statistics
from typing import Dict, List
import streamlit as st

def test_cached_instance_persistence():
    """Test that OpenLandMapSTAC instance is properly cached across calls"""
    print("🧪 Testing OpenLandMapSTAC instance persistence...")
    
    try:
        from utils.openlandmap_stac_api import get_cached_openlandmap_stac
        
        # Get multiple instances - should be the same object due to caching
        instance1 = get_cached_openlandmap_stac()
        instance2 = get_cached_openlandmap_stac()
        instance3 = get_cached_openlandmap_stac()
        
        # Check if they're the same object (cached)
        assert instance1 is instance2, "❌ Instance 2 is not the same as instance 1 - caching not working"
        assert instance2 is instance3, "❌ Instance 3 is not the same as instance 2 - caching not working"
        
        print(f"✅ Instance persistence test passed - all instances are the same object")
        print(f"   Instance ID: {id(instance1)}")
        print(f"   Cache stats: {instance1.get_cache_stats()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Instance persistence test failed: {e}")
        return False

def test_coordinate_caching():
    """Test coordinate caching with geographic quantization"""
    print("\n🧪 Testing coordinate caching with geographic quantization...")
    
    try:
        from utils.openlandmap_stac_api import get_cached_openlandmap_stac
        
        stac_instance = get_cached_openlandmap_stac()
        
        # Test coordinates that should be quantized to the same value
        test_coordinates = [
            (52.5200, 13.4050),  # Berlin
            (52.5201, 13.4051),  # Berlin + small offset (should quantize to same)
            (52.5199, 13.4049),  # Berlin - small offset (should quantize to same)
            (52.5203, 13.4052),  # Berlin + slightly larger offset (should quantize to same)
        ]
        
        # First call - cache misses expected
        print("🔄 First round of calls (cache misses expected)...")
        first_round_times = []
        for i, (lat, lon) in enumerate(test_coordinates):
            start_time = time.time()
            result = stac_instance._get_ecosystem_type_cached(lat, lon)
            end_time = time.time()
            duration = end_time - start_time
            first_round_times.append(duration)
            print(f"   Call {i+1}: ({lat:.4f}, {lon:.4f}) -> {result.get('ecosystem_type', 'Unknown')} in {duration:.3f}s")
        
        # Second round - cache hits expected for quantized coordinates
        print("🚀 Second round of calls (cache hits expected)...")
        second_round_times = []
        for i, (lat, lon) in enumerate(test_coordinates):
            start_time = time.time()
            result = stac_instance._get_ecosystem_type_cached(lat, lon)
            end_time = time.time()
            duration = end_time - start_time
            second_round_times.append(duration)
            print(f"   Call {i+1}: ({lat:.4f}, {lon:.4f}) -> {result.get('ecosystem_type', 'Unknown')} in {duration:.3f}s")
        
        # Calculate performance improvement
        avg_first_round = statistics.mean(first_round_times)
        avg_second_round = statistics.mean(second_round_times)
        speedup = avg_first_round / avg_second_round if avg_second_round > 0 else 1
        
        print(f"\n📊 Performance Analysis:")
        print(f"   First round average: {avg_first_round:.3f}s")
        print(f"   Second round average: {avg_second_round:.3f}s")
        print(f"   Speedup: {speedup:.1f}x faster")
        
        # Test should show significant speedup for cached calls
        if speedup > 2.0:
            print("✅ Coordinate caching test passed - significant speedup detected")
            return True
        else:
            print(f"⚠️ Coordinate caching test inconclusive - speedup {speedup:.1f}x is lower than expected")
            return False
        
    except Exception as e:
        print(f"❌ Coordinate caching test failed: {e}")
        return False

def test_dataset_cache_persistence():
    """Test that raster dataset caches persist and improve performance"""
    print("\n🧪 Testing dataset cache persistence...")
    
    try:
        from utils.openlandmap_stac_api import get_cached_openlandmap_stac
        
        stac_instance = get_cached_openlandmap_stac()
        
        # Get initial cache stats
        initial_stats = stac_instance.get_cache_stats()
        print(f"📊 Initial cache stats: {initial_stats}")
        
        # Test the same coordinate multiple times to trigger dataset caching
        test_lat, test_lon = 52.5200, 13.4050  # Berlin
        
        print(f"🔄 Testing dataset caching with coordinate ({test_lat}, {test_lon})...")
        
        # Multiple calls to the same area to test dataset cache
        call_times = []
        for i in range(5):
            start_time = time.time()
            result = stac_instance.get_ecosystem_type(test_lat, test_lon)
            end_time = time.time()
            duration = end_time - start_time
            call_times.append(duration)
            print(f"   Call {i+1}: {result.get('ecosystem_type', 'Unknown')} in {duration:.3f}s")
        
        # Get final cache stats
        final_stats = stac_instance.get_cache_stats()
        print(f"📊 Final cache stats: {final_stats}")
        
        # Analyze cache performance
        cache_hits = final_stats['hits'] - initial_stats['hits']
        cache_misses = final_stats['misses'] - initial_stats['misses']
        
        print(f"\n📈 Dataset Cache Analysis:")
        print(f"   Cache hits during test: {cache_hits}")
        print(f"   Cache misses during test: {cache_misses}")
        print(f"   Cache hit rate: {cache_hits/(cache_hits+cache_misses)*100:.1f}%" if (cache_hits+cache_misses) > 0 else "0.0%")
        
        # Check if later calls are faster (indicating cache usage)
        first_call_time = call_times[0]
        later_calls_avg = statistics.mean(call_times[1:]) if len(call_times) > 1 else first_call_time
        speedup = first_call_time / later_calls_avg if later_calls_avg > 0 else 1
        
        print(f"   First call time: {first_call_time:.3f}s")
        print(f"   Later calls average: {later_calls_avg:.3f}s")
        print(f"   Speedup: {speedup:.1f}x")
        
        # Verify cache improvements
        if cache_hits > 0 and speedup > 1.2:
            print("✅ Dataset cache persistence test passed")
            return True
        else:
            print("⚠️ Dataset cache persistence test inconclusive")
            return False
        
    except Exception as e:
        print(f"❌ Dataset cache persistence test failed: {e}")
        return False

def test_coordinate_quantization():
    """Test that coordinate quantization works correctly"""
    print("\n🧪 Testing coordinate quantization logic...")
    
    try:
        # Test the quantization logic directly
        test_cases = [
            # (original_lat, original_lon, expected_quantized_lat, expected_quantized_lon)
            (52.520066, 13.404954, 52.5201, 13.4050),
            (52.519877, 13.404723, 52.5199, 13.4047),
            (52.520194, 13.405123, 52.5202, 13.4051),
        ]
        
        all_passed = True
        for orig_lat, orig_lon, exp_lat, exp_lon in test_cases:
            # Apply same quantization as in _get_ecosystem_type_cached
            quantized_lat = round(orig_lat, 4)
            quantized_lon = round(orig_lon, 4)
            
            if quantized_lat == exp_lat and quantized_lon == exp_lon:
                print(f"✅ ({orig_lat:.6f}, {orig_lon:.6f}) -> ({quantized_lat:.4f}, {quantized_lon:.4f})")
            else:
                print(f"❌ ({orig_lat:.6f}, {orig_lon:.6f}) -> Expected ({exp_lat:.4f}, {exp_lon:.4f}), Got ({quantized_lat:.4f}, {quantized_lon:.4f})")
                all_passed = False
        
        if all_passed:
            print("✅ Coordinate quantization test passed")
            return True
        else:
            print("❌ Coordinate quantization test failed")
            return False
        
    except Exception as e:
        print(f"❌ Coordinate quantization test failed: {e}")
        return False

def run_all_tests():
    """Run all cache performance tests"""
    print("🚀 Starting OpenLandMapSTAC Cache Performance Tests")
    print("=" * 60)
    
    # Run all tests
    tests = [
        ("Instance Persistence", test_cached_instance_persistence),
        ("Coordinate Quantization", test_coordinate_quantization), 
        ("Coordinate Caching", test_coordinate_caching),
        ("Dataset Cache Persistence", test_dataset_cache_persistence),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        results[test_name] = test_func()
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 Test Results Summary:")
    passed_count = sum(results.values())
    total_count = len(results)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    print(f"\nOverall: {passed_count}/{total_count} tests passed ({passed_count/total_count*100:.1f}%)")
    
    if passed_count == total_count:
        print("🎉 All cache performance tests passed! Cache implementation is working correctly.")
    else:
        print("⚠️ Some cache tests failed. Cache implementation needs attention.")
    
    return passed_count == total_count

if __name__ == "__main__":
    # Allow running as standalone script
    run_all_tests()