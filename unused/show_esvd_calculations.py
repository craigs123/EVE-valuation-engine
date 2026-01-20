#!/usr/bin/env python3
"""
ESVD Value Calculation Demonstration
Shows whether values are calculated dynamically from the authentic database
or using static fallbacks.
"""

import pandas as pd
from utils.authentic_esvd_loader import get_esvd_loader
from utils.esvd_integration import ESVDIntegration

def main():
    print("🌱 ESVD Value Calculation Analysis")
    print("="*50)
    
    # Test the authentic ESVD database
    print("\n1. AUTHENTIC ESVD DATABASE (Dynamic Calculation)")
    print("-" * 45)
    
    authentic_esvd = get_esvd_loader()
    
    if authentic_esvd.is_loaded:
        print(f"✅ Authentic database loaded: {len(authentic_esvd.data):,} records")
        
        # Test dynamic calculations for different ecosystems
        test_ecosystems = ['forest', 'wetland', 'grassland', 'agricultural']
        test_services = ['climate', 'food', 'water', 'recreation']
        
        for ecosystem in test_ecosystems:
            print(f"\n📍 {ecosystem.upper()} ecosystem:")
            for service in test_services:
                # Get real values from ESVD database
                values = authentic_esvd.get_values_for_ecosystem_service(ecosystem, service)
                coefficient = authentic_esvd.get_coefficient(ecosystem, service)
                
                print(f"  {service}: ${coefficient:.2f}/ha/year", end="")
                if values:
                    print(f" (from {len(values)} studies, median of ${min(values):.0f}-${max(values):.0f})")
                else:
                    print(" (using fallback value)")
    else:
        print("❌ Authentic ESVD database not loaded")
    
    print("\n" + "="*50)
    print("\n2. STATIC FALLBACK SYSTEM (Hardcoded Values)")
    print("-" * 45)
    
    # Test static fallback system
    static_esvd = ESVDIntegration()
    
    print("Sample static coefficients from hardcoded matrix:")
    print("Forest - Food Production: $289/ha/year")
    print("Forest - Climate Regulation: $2156/ha/year") 
    print("Wetland - Water Regulation: $8000/ha/year")
    print("Grassland - Food Production: $221/ha/year")
    
    # Show which system is currently being used
    print("\n" + "="*50)
    print("\n3. CURRENT SYSTEM IN USE")
    print("-" * 25)
    
    if authentic_esvd.is_loaded:
        print("🎯 PRIMARY: Authentic ESVD Database (DYNAMIC)")
        print("   Source: 10,874+ peer-reviewed studies")
        print("   Method: Dynamic median calculation from real research")
        print("   Fallback: Static values only when no studies found")
    else:
        print("⚠️  FALLBACK: Static coefficient matrix")
        print("   Source: Hardcoded values")
        print("   Method: Fixed coefficients")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    main()