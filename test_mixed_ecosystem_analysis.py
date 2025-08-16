#!/usr/bin/env python3
"""
Test Mixed Ecosystem Analysis and UI Flow
"""

import sys
sys.path.append('.')

from utils.openlandmap_integration import detect_ecosystem_type
from utils.esvd_integration import calculate_mixed_ecosystem_services_value

def test_mixed_ecosystem_workflow():
    """Test the complete mixed ecosystem workflow"""
    
    # Test coordinates (LA area - known mixed urban/agriculture)
    test_coords = [
        [-118.190918, 33.998027],
        [-118.190918, 34.302606], 
        [-117.855835, 34.302606],
        [-117.855835, 33.998027],
        [-118.190918, 33.998027]  # Close polygon
    ]
    
    print("=== Testing Mixed Ecosystem Detection ===")
    
    try:
        # Test ecosystem detection
        detection_result = detect_ecosystem_type(
            coordinates=test_coords,
            max_sampling_limit=20,
            progress_callback=lambda current, total: print(f"Detection progress: {current}/{total}")
        )
        
        print(f"Detection result keys: {list(detection_result.keys())}")
        print(f"Primary ecosystem: {detection_result.get('primary_ecosystem', 'NOT_FOUND')}")
        
        # Check if mixed ecosystems detected
        if 'ecosystem_distribution' in detection_result:
            ecosystem_dist = detection_result['ecosystem_distribution']
            print(f"Mixed ecosystems found: {len(ecosystem_dist)} types")
            
            for eco_type, data in ecosystem_dist.items():
                print(f"  - {eco_type}: {data['count']} samples ({data.get('confidence', 0)}% confidence)")
            
            # Test mixed ecosystem valuation
            print("\n=== Testing Mixed Ecosystem Valuation ===")
            valuation_result = calculate_mixed_ecosystem_services_value(
                ecosystem_distribution=ecosystem_dist,
                area_hectares=1000,
                coordinates=(34.15, -118.02)
            )
            
            print(f"Total value: ${valuation_result['metadata']['total_value']:,.0f}")
            print(f"Ecosystem composition: {valuation_result['metadata']['ecosystem_composition']}")
            print(f"Calculation method: {valuation_result['metadata']['calculation_method']}")
            
            return True
            
        else:
            print("No mixed ecosystem distribution found")
            return False
            
    except Exception as e:
        print(f"ERROR in mixed ecosystem workflow: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pie_chart_data():
    """Test pie chart data generation"""
    print("\n=== Testing Pie Chart Data Generation ===")
    
    # Sample mixed ecosystem data
    test_distribution = {
        'Forest': {'count': 7, 'confidence': 85},
        'Agricultural': {'count': 2, 'confidence': 70},
        'Urban': {'count': 1, 'confidence': 60}
    }
    
    total_samples = sum(data['count'] for data in test_distribution.values())
    
    ecosystems = []
    percentages = []
    sample_counts = []
    
    for eco_type, data in test_distribution.items():
        proportion = data['count'] / total_samples * 100
        ecosystems.append(eco_type)
        percentages.append(proportion)
        sample_counts.append(data['count'])
    
    print(f"Ecosystems: {ecosystems}")
    print(f"Percentages: {percentages}")
    print(f"Sample counts: {sample_counts}")
    
    # Test if this would work in plotly
    try:
        import plotly.graph_objects as go
        
        fig = go.Figure(data=[go.Pie(
            labels=ecosystems, 
            values=percentages,
            customdata=sample_counts
        )])
        
        print("SUCCESS: Pie chart data generation works")
        return True
        
    except Exception as e:
        print(f"ERROR: Pie chart generation failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting Mixed Ecosystem Analysis Tests...")
    
    success1 = test_mixed_ecosystem_workflow()
    success2 = test_pie_chart_data()
    
    if success1 and success2:
        print("\n✅ All tests passed - Mixed ecosystem analysis working correctly")
    else:
        print("\n❌ Some tests failed - Check implementation")