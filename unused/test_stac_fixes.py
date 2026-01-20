#!/usr/bin/env python3
"""
Test script to verify STAC API fixes for land cover extraction and environmental indicators toggle
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

def test_land_cover_extraction():
    """Test land cover pixel extraction with fixed COG access"""
    print("🔬 TESTING: Land cover extraction with fixed COG access...")
    
    try:
        from utils.openlandmap_stac_api import openlandmap_stac
        
        # Test coordinates (Nevada area from logs)
        test_lat = 38.4064
        test_lon = -116.6016
        
        print(f"📍 Testing coordinates: ({test_lat}, {test_lon})")
        
        # Test direct land cover extraction
        result = openlandmap_stac.get_ecosystem_type(test_lat, test_lon)
        
        if result:
            print("✅ SUCCESS: Land cover extraction working!")
            print(f"   Ecosystem Type: {result.get('ecosystem_type', 'N/A')}")
            print(f"   Land Cover Class: {result.get('landcover_class', 'N/A')}")
            print(f"   Data Source: {result.get('data_source', 'N/A')}")
            return True
        else:
            print("❌ FAILURE: Land cover extraction returned None")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Land cover extraction failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environmental_indicators_toggle():
    """Test environmental indicators toggle for Fast Mode vs Comprehensive Mode"""
    print("\n🔬 TESTING: Environmental indicators toggle...")
    
    try:
        from utils.openlandmap_integration import OpenLandMapIntegrator
        
        integrator = OpenLandMapIntegrator()
        test_lat = 38.4064
        test_lon = -116.6016
        
        print(f"📍 Testing coordinates: ({test_lat}, {test_lon})")
        
        # Test Fast Mode (should skip environmental indicators)
        print("\n🚀 Testing Fast Mode (include_environmental_indicators=False)...")
        fast_result = integrator.get_land_cover_point(test_lat, test_lon, include_environmental_indicators=False)
        
        if fast_result:
            print("✅ Fast Mode result received")
            # Check if environmental indicators were skipped
            stac_data = fast_result.get('stac_data', {})
            env_categories = len([k for k in stac_data.keys() if k not in ['landcover', 'data_source', 'query_time']])
            print(f"   Environmental categories processed: {env_categories} (should be 0 for Fast Mode)")
            fast_mode_success = env_categories == 0
        else:
            print("❌ Fast Mode failed")
            fast_mode_success = False
        
        # Test Comprehensive Mode (should include environmental indicators)
        print("\n🔬 Testing Comprehensive Mode (include_environmental_indicators=True)...")
        comprehensive_result = integrator.get_land_cover_point(test_lat, test_lon, include_environmental_indicators=True)
        
        if comprehensive_result:
            print("✅ Comprehensive Mode result received")
            stac_data = comprehensive_result.get('stac_data', {})
            env_categories = len([k for k in stac_data.keys() if k not in ['landcover', 'data_source', 'query_time']])
            print(f"   Environmental categories processed: {env_categories} (should be > 0 for Comprehensive Mode)")
            comprehensive_mode_success = env_categories > 0
        else:
            print("❌ Comprehensive Mode failed")
            comprehensive_mode_success = False
        
        return fast_mode_success and comprehensive_mode_success
        
    except Exception as e:
        print(f"❌ ERROR: Environmental indicators toggle test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ecosystem_detection_pipeline():
    """Test the complete ecosystem detection pipeline"""
    print("\n🔬 TESTING: Complete ecosystem detection pipeline...")
    
    try:
        from utils.openlandmap_integration import detect_ecosystem_type
        
        # Test coordinates for a small area
        test_coordinates = [
            [-116.6016, 38.4064],  # Nevada
            [-116.6020, 38.4064],
            [-116.6020, 38.4060],
            [-116.6016, 38.4060],
            [-116.6016, 38.4064]   # Close polygon
        ]
        
        print(f"📍 Testing polygon with {len(test_coordinates)} coordinates")
        
        # Test with Fast Mode
        print("\n🚀 Testing pipeline with Fast Mode...")
        fast_result = detect_ecosystem_type(
            coordinates=test_coordinates,
            sampling_frequency=1.0,
            max_sampling_limit=4,
            include_environmental_indicators=False
        )
        
        if fast_result:
            print("✅ Fast Mode pipeline completed")
            print(f"   Primary Ecosystem: {fast_result.get('primary_ecosystem', 'N/A')}")
            print(f"   Confidence: {fast_result.get('confidence', 'N/A')}")
            print(f"   Successful Queries: {fast_result.get('successful_queries', 0)}")
            return True
        else:
            print("❌ Fast Mode pipeline failed")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Ecosystem detection pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 STAC API FIXES VERIFICATION TEST")
    print("=" * 50)
    
    # Run all tests
    test_results = []
    
    # Test 1: Land cover extraction
    test_results.append(test_land_cover_extraction())
    
    # Test 2: Environmental indicators toggle  
    test_results.append(test_environmental_indicators_toggle())
    
    # Test 3: Complete ecosystem detection pipeline
    test_results.append(test_ecosystem_detection_pipeline())
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 TEST SUMMARY:")
    print(f"   Land Cover Extraction: {'✅ PASS' if test_results[0] else '❌ FAIL'}")
    print(f"   Environmental Toggle: {'✅ PASS' if test_results[1] else '❌ FAIL'}")
    print(f"   Pipeline Integration: {'✅ PASS' if test_results[2] else '❌ FAIL'}")
    
    all_passed = all(test_results)
    print(f"\n🎯 OVERALL RESULT: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("🎉 STAC API fixes are working correctly!")
    else:
        print("⚠️  Some fixes need additional work.")