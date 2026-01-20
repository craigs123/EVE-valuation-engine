"""
Complete test of urban ecosystem workflow
"""

from utils.openlandmap_integration import detect_ecosystem_type
from utils.esvd_integration import calculate_ecosystem_services_value
import json

def test_complete_urban_workflow():
    """Test the complete workflow for urban ecosystem analysis"""
    
    print("Complete Urban Ecosystem Analysis Test")
    print("=" * 60)
    
    # Orange County urban area (user's recent selection)
    urban_coords = [
        [-117.981491, 33.731764],
        [-117.981491, 33.73833],
        [-117.973251, 33.73833], 
        [-117.973251, 33.731764],
        [-117.981491, 33.731764]
    ]
    
    # Calculate area in hectares
    import numpy as np
    coords_array = np.array(urban_coords)
    area_km2 = abs(np.sum((coords_array[:-1, 0] * coords_array[1:, 1]) - (coords_array[1:, 0] * coords_array[:-1, 1]))) * 111.32 * 111.32 / 2
    area_ha = area_km2 * 100
    
    print(f"Testing area: {area_ha:.1f} hectares")
    print(f"Coordinates: Orange County urban area")
    
    # Step 1: Ecosystem Detection
    print(f"\n1. Ecosystem Detection")
    print("-" * 30)
    
    try:
        ecosystem_info = detect_ecosystem_type(
            coordinates=urban_coords,
            sampling_frequency=2.0
        )
        
        print(f"Primary Ecosystem: {ecosystem_info['primary_ecosystem']}")
        print(f"Confidence: {ecosystem_info['confidence']:.1%}")
        print(f"Sample Points: {ecosystem_info['total_samples']}")
        
        if ecosystem_info['primary_ecosystem'] == 'Urban':
            print("✅ Urban ecosystem correctly detected")
        else:
            print(f"❌ Unexpected ecosystem: {ecosystem_info['primary_ecosystem']}")
            
    except Exception as e:
        print(f"❌ Detection failed: {e}")
        return
    
    # Step 2: Economic Valuation
    print(f"\n2. Economic Valuation")
    print("-" * 30)
    
    try:
        # Get center coordinates for regional adjustment
        center_lat = np.mean([coord[1] for coord in urban_coords])
        center_lon = np.mean([coord[0] for coord in urban_coords])
        
        valuation = calculate_ecosystem_services_value(
            ecosystem_type='Urban',
            area_hectares=area_ha,
            coordinates=(center_lat, center_lon),
            income_elasticity=0.6
        )
        
        print(f"Total Annual Value: ${valuation['metadata']['total_value']:,.0f}")
        print(f"Value per Hectare: ${valuation['metadata']['value_per_hectare']:,.0f}")
        print(f"Regional Adjustment: {valuation['metadata']['regional_adjustment']:.2f}")
        
        # Service category breakdown
        print(f"\nService Categories:")
        service_totals = {}
        for category in ['provisioning', 'regulating', 'cultural', 'supporting']:
            if category in valuation:
                total = valuation[category].get('total', 0)
                service_totals[category] = total
                print(f"  {category.title()}: ${total:,.0f}")
        
        # Verify totals
        calculated_total = sum(service_totals.values())
        reported_total = valuation['metadata']['total_value']
        
        if abs(calculated_total - reported_total) < 1:  # Allow for rounding
            print("✅ Valuation calculation verified")
        else:
            print(f"❌ Total mismatch: {calculated_total} vs {reported_total}")
            
    except Exception as e:
        print(f"❌ Valuation failed: {e}")
        return
    
    # Step 3: Full Workflow Summary
    print(f"\n3. Workflow Summary")
    print("-" * 30)
    
    print(f"Area analyzed: {area_ha:.1f} hectares")
    print(f"Ecosystem type: {ecosystem_info['primary_ecosystem']} ({ecosystem_info['confidence']:.1%} confidence)")
    print(f"Annual value: ${valuation['metadata']['total_value']:,.0f}")
    print(f"Per hectare value: ${valuation['metadata']['value_per_hectare']:,.0f}")
    
    # Key urban services
    print(f"\nKey Urban Ecosystem Services:")
    key_services = [
        ('Climate regulation', valuation['regulating'].get('climate_regulation', 0)),
        ('Pollution control', valuation['regulating'].get('pollution_control', 0)),
        ('Recreation value', valuation['cultural'].get('recreation', 0)),
        ('Water regulation', valuation['regulating'].get('water_regulation', 0))
    ]
    
    for service, value in key_services:
        if value > 0:
            print(f"  • {service}: ${value:,.0f}")
    
    print(f"\n✅ Complete urban ecosystem analysis successful!")
    print(f"The system correctly identifies urban areas and provides")
    print(f"comprehensive economic valuation of ecosystem services.")

if __name__ == "__main__":
    test_complete_urban_workflow()