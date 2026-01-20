"""
Pre-computed ESVD Coefficients with Country-Specific Regional Adjustment
Calculated from authentic ESVD APR2024 V1.1 database (10,874 records)
Static values for optimal performance while maintaining research authenticity

Regional Adjustment Methodology:
- Uses World Bank GDP per capita data (2020) for country-specific adjustments
- Applies income elasticity method from environmental economics literature  
- Formula: 1 + (elasticity × (country_GDP/global_GDP - 1))
- Bounded to prevent extreme values (0.4 to 2.5 multiplier range)
- Aligns with 2020 Int$ baseline year used in ESVD coefficients
"""

def get_country_from_coordinates(lat: float, lon: float) -> str:
    """
    Map coordinates to country code using geographic boundaries
    
    Args:
        lat: Latitude 
        lon: Longitude
        
    Returns:
        Country code string for GDP lookup
    """
    
    # North America
    if lat >= 25 and -130 <= lon <= -60:
        # United States (continental)
        if lat >= 25 and lat <= 49 and -125 <= lon <= -66:
            if lon >= -95:  # East of -95° longitude (rough US-Canada border area)
                return 'united_states'
            else:
                return 'united_states'  # Most of US territory
        # Alaska
        elif lat >= 54 and lat <= 71 and -169 <= lon <= -130:
            return 'united_states'
        # Canada
        elif lat >= 41 and lat <= 84 and -141 <= lon <= -52:
            return 'canada'
        # Mexico
        elif lat >= 14 and lat <= 32 and -118 <= lon <= -86:
            return 'mexico'
    
    # Europe
    elif lat >= 35 and -10 <= lon <= 50:
        # United Kingdom & Ireland
        if lat >= 50 and lat <= 61 and -8 <= lon <= 2:
            if lon <= -3:  # West of -3° (rough Ireland boundary)
                return 'ireland'
            else:
                return 'united_kingdom'
        # Germany
        elif lat >= 47 and lat <= 55 and 6 <= lon <= 15:
            return 'germany'
        # France
        elif lat >= 42 and lat <= 51 and -5 <= lon <= 8:
            return 'france'
        # Spain
        elif lat >= 36 and lat <= 44 and -10 <= lon <= 4:
            return 'spain'
        # Italy
        elif lat >= 36 and lat <= 47 and 6 <= lon <= 19:
            return 'italy'
        # Netherlands
        elif lat >= 51 and lat <= 54 and 3 <= lon <= 7:
            return 'netherlands'
        # Switzerland
        elif lat >= 46 and lat <= 48 and 6 <= lon <= 11:
            return 'switzerland'
        # Austria
        elif lat >= 46 and lat <= 49 and 9 <= lon <= 17:
            return 'austria'
        # Belgium
        elif lat >= 49 and lat <= 52 and 2 <= lon <= 7:
            return 'belgium'
        # Poland
        elif lat >= 49 and lat <= 55 and 14 <= lon <= 24:
            return 'poland'
        # Sweden
        elif lat >= 55 and lat <= 69 and 11 <= lon <= 24:
            return 'sweden'
        # Norway
        elif lat >= 58 and lat <= 72 and 4 <= lon <= 31:
            return 'norway'
        # Denmark
        elif lat >= 54 and lat <= 58 and 8 <= lon <= 13:
            return 'denmark'
        # Finland
        elif lat >= 60 and lat <= 70 and 20 <= lon <= 32:
            return 'finland'
        # Russia (European part)
        elif lat >= 45 and lat <= 68 and 19 <= lon <= 50:
            return 'russia'
        # Default to regional average for other European countries
        else:
            return 'europe_average'
    
    # Asia-Pacific Developed
    elif lat >= -50 and 110 <= lon <= 180:
        # Japan
        if lat >= 24 and lat <= 46 and 123 <= lon <= 146:
            return 'japan'
        # Australia
        elif lat >= -44 and lat <= -10 and 113 <= lon <= 154:
            return 'australia'
        # New Zealand
        elif lat >= -47 and lat <= -34 and 166 <= lon <= 179:
            return 'new_zealand'
        # South Korea
        elif lat >= 33 and lat <= 39 and 124 <= lon <= 132:
            return 'south_korea'
        # Singapore
        elif lat >= 1 and lat <= 2 and 103 <= lon <= 104:
            return 'singapore'
    
    # Asia Emerging
    elif lat >= -10 and 60 <= lon <= 140:
        # China
        if lat >= 18 and lat <= 54 and 73 <= lon <= 135:
            return 'china'
        # India
        elif lat >= 8 and lat <= 37 and 68 <= lon <= 97:
            return 'india'
        # Indonesia
        elif lat >= -11 and lat <= 6 and 95 <= lon <= 141:
            return 'indonesia'
        # Thailand
        elif lat >= 5 and lat <= 21 and 97 <= lon <= 106:
            return 'thailand'
        # Vietnam
        elif lat >= 8 and lat <= 24 and 102 <= lon <= 110:
            return 'vietnam'
        # Malaysia
        elif lat >= 1 and lat <= 7 and 100 <= lon <= 120:
            return 'malaysia'
        # Philippines
        elif lat >= 5 and lat <= 21 and 116 <= lon <= 127:
            return 'philippines'
        # Bangladesh
        elif lat >= 20 and lat <= 27 and 88 <= lon <= 93:
            return 'bangladesh'
        # Pakistan
        elif lat >= 24 and lat <= 37 and 61 <= lon <= 77:
            return 'pakistan'
    
    # Latin America
    elif lat >= -55 and -120 <= lon <= -30:
        # Brazil
        if lat >= -34 and lat <= 5 and -74 <= lon <= -32:
            return 'brazil'
        # Argentina
        elif lat >= -55 and lat <= -22 and -74 <= lon <= -53:
            return 'argentina'
        # Chile
        elif lat >= -56 and lat <= -17 and -76 <= lon <= -66:
            return 'chile'
        # Colombia
        elif lat >= -4 and lat <= 12 and -79 <= lon <= -67:
            return 'colombia'
        # Peru
        elif lat >= -18 and lat <= 0 and -81 <= lon <= -68:
            return 'peru'
        # Venezuela
        elif lat >= 0 and lat <= 12 and -73 <= lon <= -59:
            return 'venezuela'
    
    # Middle East & North Africa
    elif lat >= 15 and lat <= 40 and -15 <= lon <= 60:
        # Saudi Arabia
        if lat >= 16 and lat <= 32 and 34 <= lon <= 56:
            return 'saudi_arabia'
        # Israel
        elif lat >= 29 and lat <= 34 and 34 <= lon <= 36:
            return 'israel'
        # Turkey
        elif lat >= 36 and lat <= 42 and 26 <= lon <= 45:
            return 'turkey'
        # Egypt
        elif lat >= 22 and lat <= 32 and 25 <= lon <= 35:
            return 'egypt'
        # UAE
        elif lat >= 22 and lat <= 26 and 51 <= lon <= 56:
            return 'uae'
    
    # Sub-Saharan Africa
    elif lat >= -35 and lat <= 15 and -20 <= lon <= 52:
        # South Africa
        if lat >= -35 and lat <= -22 and 16 <= lon <= 33:
            return 'south_africa'
        # Nigeria
        elif lat >= 4 and lat <= 14 and 3 <= lon <= 15:
            return 'nigeria'
        # Kenya
        elif lat >= -5 and lat <= 5 and 34 <= lon <= 42:
            return 'kenya'
        # Ethiopia
        elif lat >= 3 and lat <= 15 and 33 <= lon <= 48:
            return 'ethiopia'
        # Ghana
        elif lat >= 5 and lat <= 11 and -4 <= lon <= 1:
            return 'ghana'
    
    # Default to global average
    return 'global_average'