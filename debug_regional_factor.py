#!/usr/bin/env python3
"""
Quick debug script to test regional factor calculation for USA coordinates
"""

# Test typical USA coordinates
test_coordinates = [
    (40.7128, -74.0060),  # New York City
    (34.0522, -118.2437), # Los Angeles 
    (41.8781, -87.6298),  # Chicago
    (29.7604, -95.3698),  # Houston
    (39.9526, -75.1652),  # Philadelphia
]

def get_country_from_coordinates(lat: float, lon: float) -> str:
    """
    Map coordinates to country code using geographic boundaries
    """
    
    # North America
    if lat >= 14 and -141 <= lon <= -52:
        # Canada (prioritize northern latitudes)
        if lat >= 49 and -141 <= lon <= -52:
            return 'canada'
        # United States (continental)  
        elif lat >= 25 and lat <= 49 and -125 <= lon <= -66:
            return 'united_states'
        # Alaska (US)
        elif lat >= 54 and lat <= 71 and -169 <= lon <= -130:
            return 'united_states'
        # Mexico
        elif lat >= 14 and lat <= 32 and -118 <= lon <= -86:
            return 'mexico'
        # Default to US for overlapping areas
        else:
            return 'united_states'
    
    # Default to global average
    return 'global_average'

# Test the coordinates
print("Testing USA coordinate detection:")
print("="*50)

for i, (lat, lon) in enumerate(test_coordinates, 1):
    city_names = ["New York City", "Los Angeles", "Chicago", "Houston", "Philadelphia"]
    detected_country = get_country_from_coordinates(lat, lon)
    
    print(f"{i}. {city_names[i-1]}")
    print(f"   Coordinates: ({lat}, {lon})")
    print(f"   Detected: {detected_country}")
    
    # Check the coordinate ranges
    in_north_america = lat >= 14 and -141 <= lon <= -52
    in_continental_us = lat >= 25 and lat <= 49 and -125 <= lon <= -66
    
    print(f"   In North America bounds: {in_north_america}")
    print(f"   In Continental US bounds: {in_continental_us}")
    print()

# Test the regional factor calculation
print("Regional Factor Calculation Test:")
print("="*50)

# Simulate the calculation
USA_GDP = 63593
GLOBAL_GDP_AVERAGE = 11312
INCOME_ELASTICITY = 0.6

gdp_ratio = USA_GDP / GLOBAL_GDP_AVERAGE
adjustment_factor = 1 + (INCOME_ELASTICITY * (gdp_ratio - 1))
bounded_factor = max(0.4, min(2.5, adjustment_factor))

print(f"USA GDP per capita: ${USA_GDP:,}")
print(f"Global GDP average: ${GLOBAL_GDP_AVERAGE:,}")
print(f"GDP ratio: {gdp_ratio:.2f}")
print(f"Raw adjustment factor: {adjustment_factor:.2f}")
print(f"Bounded regional factor: {bounded_factor:.2f}x")