#!/usr/bin/env python3
"""
Quick test script to verify STAC API reliability fixes
Tests the key functions to ensure no crashes and proper data extraction
"""

import asyncio
import sys
import os

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

def test_stac_api_fixes():
    """Test the STAC API fixes for reliability"""
    
    try:
        # Import the fixed STAC API
        from utils.openlandmap_stac_api import openlandmap_stac
        from utils.openlandmap_integration import OpenLandMapIntegrator
        
        print("🧪 Testing STAC API reliability fixes...")
        
        # Test coordinates (known locations with data)
        test_coordinates = [
            (40.7128, -74.0060),  # New York City 
            (51.5074, -0.1278),   # London
            (35.6762, 139.6503),  # Tokyo
            (0.0, 0.0),           # Null Island (should handle gracefully)
        ]
        
        integrator = OpenLandMapIntegrator()
        results = []
        
        for lat, lon in test_coordinates:
            print(f"\n🔍 Testing coordinates: ({lat}, {lon})")
            
            try:
                # Test single ecosystem detection
                result = openlandmap_stac.get_ecosystem_type(lat, lon)
                
                if result:
                    ecosystem_type = result.get('ecosystem_type', 'Unknown')
                    landcover_class = result.get('landcover_class', 'N/A')
                    data_source = result.get('data_source', 'Unknown')
                    
                    print(f"   ✅ Ecosystem: {ecosystem_type}")
                    print(f"   📊 Land cover code: {landcover_class}")
                    print(f"   🌐 Data source: {data_source}")
                    
                    # Verify no None values in critical fields
                    if ecosystem_type and ecosystem_type != 'Unknown':
                        results.append(True)
                        print(f"   ✅ Valid result - no None values")
                    else:
                        results.append(False)
                        print(f"   ⚠️ Got None/Unknown ecosystem type")
                else:
                    results.append(False)
                    print(f"   ❌ No result returned")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results.append(False)
        
        # Test batch processing
        print(f"\n🔍 Testing batch ecosystem detection...")
        try:
            batch_results = openlandmap_stac.get_batch_ecosystem_types(test_coordinates[:2])
            
            if batch_results and len(batch_results) > 0:
                valid_batch_count = sum(1 for r in batch_results if r.get('ecosystem_type') and r['ecosystem_type'] != 'Unknown')
                print(f"   ✅ Batch processing: {valid_batch_count}/{len(batch_results)} valid results")
                results.append(valid_batch_count > 0)
            else:
                print(f"   ❌ Batch processing failed")
                results.append(False)
                
        except Exception as e:
            print(f"   ❌ Batch processing error: {e}")
            results.append(False)
        
        # Summary
        success_rate = sum(results) / len(results) if results else 0
        print(f"\n📊 Test Summary:")
        print(f"   Success rate: {success_rate:.1%} ({sum(results)}/{len(results)})")
        
        if success_rate >= 0.6:  # 60% or higher
            print(f"   ✅ STAC API reliability fixes appear successful!")
            return True
        else:
            print(f"   ⚠️ STAC API may still have issues")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_stac_api_fixes()
    sys.exit(0 if success else 1)