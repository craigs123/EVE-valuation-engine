"""
EVE Quality Factor Demonstration
Shows exactly how ecosystem quality factors are derived and applied
"""

import json

def demonstrate_quality_factor_methodology():
    """Demonstrate how EVE derives and applies quality factors"""
    
    print("=" * 80)
    print("EVE QUALITY FACTOR METHODOLOGY")
    print("=" * 80)
    print()
    
    print("🔬 QUALITY FACTOR DERIVATION:")
    print("-" * 50)
    print()
    
    print("1. SATELLITE DATA INPUTS:")
    print("   • Red band spectral reflectance (red_mean)")
    print("   • Near-infrared band reflectance (nir_mean)")
    print("   • Cloud coverage percentage")
    print("   • Data quality flags from satellite")
    print()
    
    print("2. QUALITY ASSESSMENT ALGORITHM:")
    print("   The _assess_ecosystem_quality() function uses a weighted scoring system:")
    print()
    
    # Show the actual algorithm
    print("   NDVI Calculation:")
    print("   NDVI = (NIR - Red) / (NIR + Red)")
    print()
    
    print("   Quality Score Components (Total = 100 points):")
    print("   ┌─────────────────────────────────────────────────────────┐")
    print("   │ Component         │ Weight │ Score Ranges               │")
    print("   ├─────────────────────────────────────────────────────────┤")
    print("   │ NDVI Health       │   40%  │ >0.7: 40pts, >0.5: 30pts   │")
    print("   │ Data Quality      │   30%  │ Good: 30pts, Fair: 20pts   │")
    print("   │ Cloud Coverage    │   20%  │ <10%: 20pts, <20%: 15pts   │")
    print("   │ Spectral Health   │   10%  │ NIR>0.3: 10pts, >0.2: 7pts │")
    print("   └─────────────────────────────────────────────────────────┘")
    print()
    
    print("3. QUALITY CATEGORIES & MULTIPLIERS:")
    quality_multipliers = {
        'excellent': 1.2,  # ≥85 points: Premium ecosystem health
        'good': 1.0,       # 70-84 points: Standard baseline
        'fair': 0.8,       # 55-69 points: Moderate degradation
        'poor': 0.6,       # 40-54 points: Significant degradation
        'degraded': 0.4    # <40 points: Severely degraded
    }
    
    for category, multiplier in quality_multipliers.items():
        print(f"   {category.upper()}: {multiplier}x multiplier")
    print()
    
    print("🧮 CALCULATION EXAMPLES:")
    print("-" * 50)
    
    # Example scenarios
    scenarios = [
        {
            "name": "Healthy Forest",
            "red": 0.04, "nir": 0.45, "cloud": 5, "data_quality": "good",
            "description": "Dense forest canopy, clear satellite view"
        },
        {
            "name": "Agricultural Land", 
            "red": 0.08, "nir": 0.35, "cloud": 15, "data_quality": "fair",
            "description": "Moderate vegetation, some cloud interference"
        },
        {
            "name": "Degraded Grassland",
            "red": 0.12, "nir": 0.20, "cloud": 25, "data_quality": "fair", 
            "description": "Sparse vegetation, overcast conditions"
        }
    ]
    
    for scenario in scenarios:
        print(f"\nExample: {scenario['name']}")
        print(f"Description: {scenario['description']}")
        print(f"Input Data: Red={scenario['red']}, NIR={scenario['nir']}, Cloud={scenario['cloud']}%, Quality={scenario['data_quality']}")
        
        # Calculate NDVI
        red, nir = scenario['red'], scenario['nir']
        ndvi = (nir - red) / (nir + red) if (nir + red) != 0 else 0
        
        # Calculate quality score
        quality_score = 0
        
        # NDVI contribution (40% weight)
        if ndvi > 0.7:
            ndvi_points = 40
        elif ndvi > 0.5:
            ndvi_points = 30
        elif ndvi > 0.3:
            ndvi_points = 20
        elif ndvi > 0.1:
            ndvi_points = 10
        else:
            ndvi_points = 0
        quality_score += ndvi_points
        
        # Data quality contribution (30% weight)
        if scenario['data_quality'] == 'good':
            quality_points = 30
        elif scenario['data_quality'] == 'fair':
            quality_points = 20
        else:
            quality_points = 10
        quality_score += quality_points
        
        # Cloud coverage contribution (20% weight)
        cloud = scenario['cloud']
        if cloud < 10:
            cloud_points = 20
        elif cloud < 20:
            cloud_points = 15
        elif cloud < 30:
            cloud_points = 10
        else:
            cloud_points = 5
        quality_score += cloud_points
        
        # Spectral health contribution (10% weight)
        if nir > 0.3:
            spectral_points = 10
        elif nir > 0.2:
            spectral_points = 7
        else:
            spectral_points = 3
        quality_score += spectral_points
        
        # Determine quality category
        if quality_score >= 85:
            quality_category = 'excellent'
        elif quality_score >= 70:
            quality_category = 'good'
        elif quality_score >= 55:
            quality_category = 'fair'
        elif quality_score >= 40:
            quality_category = 'poor'
        else:
            quality_category = 'degraded'
            
        multiplier = quality_multipliers[quality_category]
        
        print(f"Calculated NDVI: {ndvi:.3f}")
        print(f"Quality Score: {quality_score}/100 ({ndvi_points}+{quality_points}+{cloud_points}+{spectral_points})")
        print(f"Quality Category: {quality_category.upper()}")
        print(f"Quality Multiplier: {multiplier}x")
        print()
    
    print("💰 FINAL VALUE CALCULATION:")
    print("-" * 50)
    print()
    print("EVE applies the quality factor in the final calculation:")
    print()
    print("FINAL_VALUE = AUTHENTIC_ESVD_BASE × REGIONAL_ADJUSTMENT × QUALITY_FACTOR")
    print()
    print("Example with Forest Cultural Services:")
    print("• Authentic ESVD Base: $1,417/ha/year (from 46 peer-reviewed studies)")
    print("• Regional Adjustment: 1.0 (baseline for US/developed countries)")
    print("• Quality Factor: 1.2 (excellent ecosystem health)")
    print("• Final Value: $1,417 × 1.0 × 1.2 = $1,700/ha/year")
    print()
    print("This means healthy ecosystems provide up to 20% more value than")
    print("the baseline ESVD average, while degraded ecosystems provide")
    print("only 40% of the baseline value.")
    print()
    
    print("🌱 SCIENTIFIC RATIONALE:")
    print("-" * 50)
    print("• Healthier ecosystems provide more efficient services")
    print("• NDVI correlates with photosynthetic activity and biomass")
    print("• Clear satellite data ensures measurement accuracy")
    print("• Quality adjustment reflects real-world ecosystem performance")
    print("• Based on established ecological principles and remote sensing science")
    print("=" * 80)

if __name__ == "__main__":
    demonstrate_quality_factor_methodology()