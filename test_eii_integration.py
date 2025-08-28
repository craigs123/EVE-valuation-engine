"""
Demo: EII-Based Quality Factor Integration
Shows how Single.Earth's Ecosystem Integrity Index can replace subjective quality sliders
with objective, satellite-based ecosystem health assessment
"""

from utils.ecosystem_integrity_integration import get_eii_quality_factor
import json

def demo_eii_quality_factors():
    """Demonstrate EII-based quality factor calculation for different scenarios"""
    
    print("🌱 Ecosystem Integrity Index (EII) Quality Factor Demo")
    print("=" * 60)
    
    # Test scenarios across different ecosystem conditions
    test_scenarios = [
        {
            'name': 'Amazon Rainforest (High Integrity)',
            'coordinates': (-3.4653, -62.2159),  # Heart of Amazon
            'area_hectares': 10000,
            'ecosystem_type': 'Tropical Forest'
        },
        {
            'name': 'European Agricultural Area (Moderate Integrity)',
            'coordinates': (50.8503, 4.3517),  # Belgium
            'area_hectares': 1000,  
            'ecosystem_type': 'Grassland'
        },
        {
            'name': 'Degraded Forest Edge (Low Integrity)',
            'coordinates': (40.7128, -74.0060),  # Near NYC
            'area_hectares': 500,
            'ecosystem_type': 'Temperate Forest'
        },
        {
            'name': 'Pristine Boreal Forest (Excellent Integrity)',
            'coordinates': (64.2008, -149.4937),  # Alaska
            'area_hectares': 50000,
            'ecosystem_type': 'Boreal Forest'
        },
        {
            'name': 'Tropical Wetland (High Function)',
            'coordinates': (-2.1833, -56.9167),  # Amazon wetlands
            'area_hectares': 5000,
            'ecosystem_type': 'Wetland'
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n📍 {scenario['name']}")
        print("-" * 40)
        
        # Get EII-based quality assessment
        eii_result = get_eii_quality_factor(
            coordinates=scenario['coordinates'],
            area_hectares=scenario['area_hectares'],
            ecosystem_type=scenario['ecosystem_type']
        )
        
        # Display results
        print(f"🔬 EII Score: {eii_result.get('eii_score', 'N/A')}")
        print(f"⚖️  Quality Factor: {eii_result['quality_factor']}x")
        print(f"📊 Confidence: {eii_result['confidence']}")
        print(f"💭 Assessment: {eii_result['interpretation']}")
        
        if eii_result.get('components'):
            components = eii_result['components']
            print(f"\n   📐 Structure: {components['structure']:.2f}")
            print(f"   🦋 Composition: {components['composition']:.2f}")
            print(f"   ⚡ Function: {components['function']:.2f}")
        
        # Show economic impact
        base_value = 1000  # Example base ESVD value per hectare
        adjusted_value = base_value * eii_result['quality_factor']
        
        print(f"\n💰 Economic Impact:")
        print(f"   Base Value: ${base_value:,}/ha/year")
        print(f"   EII-Adjusted: ${adjusted_value:,.0f}/ha/year")
        print(f"   Total Area Value: ${adjusted_value * scenario['area_hectares']:,.0f}/year")

def compare_quality_methods():
    """Compare EII-based vs user-slider quality factors"""
    
    print(f"\n\n🔄 Quality Factor Method Comparison")
    print("=" * 60)
    
    test_location = (-3.4653, -62.2159)  # Amazon
    area_hectares = 1000
    
    # Get EII-based assessment
    eii_result = get_eii_quality_factor(test_location, area_hectares, 'Tropical Forest')
    
    # Simulate user slider values
    user_scenarios = [
        ('Conservative User', 0.8),
        ('Average User', 1.0), 
        ('Optimistic User', 1.5),
        ('Expert User', 1.3)
    ]
    
    base_esvd_value = 1417  # Example: Forest cultural services $/ha/year
    
    print(f"\nBase ESVD Value: ${base_esvd_value}/ha/year")
    print(f"Test Area: {area_hectares:,} hectares\n")
    
    # EII Method
    eii_quality = eii_result['quality_factor'] 
    eii_value = base_esvd_value * eii_quality * area_hectares
    print(f"🔬 EII Method:")
    print(f"   Quality Factor: {eii_quality}x (calculated from satellite data)")
    print(f"   Total Value: ${eii_value:,.0f}/year")
    print(f"   Justification: {eii_result['interpretation']}")
    
    print(f"\n👤 User Slider Method:")
    for user_type, user_quality in user_scenarios:
        user_value = base_esvd_value * user_quality * area_hectares
        difference = ((user_value - eii_value) / eii_value) * 100
        
        print(f"   {user_type}: {user_quality}x → ${user_value:,.0f}/year ({difference:+.0f}%)")
    
    print(f"\n✨ EII Advantages:")
    print(f"   • Objective assessment based on satellite data")
    print(f"   • Consistent methodology across all locations") 
    print(f"   • Scientific backing from peer-reviewed research")
    print(f"   • Eliminates user bias and subjectivity")
    print(f"   • Provides detailed component breakdown")

def integration_roadmap():
    """Show implementation roadmap for EII integration"""
    
    print(f"\n\n🛣️  EII Integration Roadmap")
    print("=" * 60)
    
    phases = [
        {
            'phase': 'Phase 1: Hybrid Approach',
            'description': 'Show both EII-calculated and user-slider quality factors',
            'benefits': ['User education', 'Gradual transition', 'Comparison capabilities'],
            'implementation': ['Add EII toggle in sidebar', 'Display both values', 'Educational tooltips']
        },
        {
            'phase': 'Phase 2: EII as Default',
            'description': 'Use EII as default with user override capability',
            'benefits': ['Objective baseline', 'User trust building', 'Scientific credibility'],
            'implementation': ['EII as primary method', 'User adjustment slider ±20%', 'Clear data sources']
        },
        {
            'phase': 'Phase 3: Full EII Integration',
            'description': 'Replace user slider with comprehensive EII assessment',
            'benefits': ['Full automation', 'Maximum accuracy', 'Professional reporting'],
            'implementation': ['Google Earth Engine integration', 'Real satellite data', 'Component visualizations']
        }
    ]
    
    for i, phase in enumerate(phases, 1):
        print(f"\n{i}. {phase['phase']}")
        print(f"   {phase['description']}")
        print(f"   Benefits: {', '.join(phase['benefits'])}")
        print(f"   Implementation: {', '.join(phase['implementation'])}")

if __name__ == "__main__":
    demo_eii_quality_factors()
    compare_quality_methods()
    integration_roadmap()