"""
Country-Specific GDP Per Capita Data (World Bank, 2020)
Source: World Bank World Development Indicators Database
GDP per capita (current US$), 2020 values
"""

# World Bank 2020 GDP per capita data (current US$)
# Source: https://data.worldbank.org/indicator/NY.GDP.PCAP.CD
COUNTRY_GDP_2020 = {
    # North America
    'united_states': 63593,
    'canada': 43258,
    'mexico': 8346,
    
    # Europe
    'germany': 46259,
    'france': 40493,
    'united_kingdom': 40284,
    'italy': 31288,
    'spain': 27057,
    'netherlands': 52331,
    'belgium': 43821,
    'austria': 45437,
    'switzerland': 83717,
    'sweden': 51648,
    'norway': 75420,
    'denmark': 60170,
    'finland': 48810,
    'ireland': 85268,
    'portugal': 24252,
    'greece': 16876,
    'poland': 15694,
    'czech_republic': 23111,
    'hungary': 16731,
    'slovakia': 19582,
    'slovenia': 25655,
    'estonia': 23723,
    'latvia': 17861,
    'lithuania': 20234,
    'croatia': 14817,
    'romania': 12919,
    'bulgaria': 9737,
    'ukraine': 3727,
    'russia': 11654,
    
    # Asia-Pacific Developed
    'japan': 40146,
    'australia': 51812,
    'new_zealand': 42084,
    'south_korea': 31846,
    'singapore': 59798,
    'hong_kong': 46193,
    
    # Asia Emerging
    'china': 10500,
    'india': 1928,
    'indonesia': 3869,
    'thailand': 7189,
    'malaysia': 10401,
    'philippines': 3299,
    'vietnam': 3521,
    'bangladesh': 2457,
    'pakistan': 1193,
    'sri_lanka': 3682,
    'myanmar': 1400,
    'cambodia': 1512,
    'laos': 2535,
    'mongolia': 4339,
    
    # Latin America
    'brazil': 6797,
    'argentina': 8441,
    'mexico': 8346,  # Duplicate for regional classification
    'colombia': 6131,
    'peru': 6127,
    'chile': 13231,
    'ecuador': 5600,
    'bolivia': 3143,
    'paraguay': 5415,
    'uruguay': 16190,
    'venezuela': 1691,  # Limited data due to crisis
    'guatemala': 4622,
    'honduras': 2405,
    'el_salvador': 4187,
    'nicaragua': 1905,
    'costa_rica': 12508,
    'panama': 15575,
    
    # Middle East & North Africa
    'saudi_arabia': 20110,
    'uae': 35315,
    'qatar': 50807,
    'kuwait': 24941,
    'bahrain': 23504,
    'oman': 15343,
    'israel': 43592,
    'turkey': 8538,
    'egypt': 3547,
    'morocco': 3204,
    'tunisia': 3597,
    'algeria': 3691,
    'jordan': 4241,
    'lebanon': 5065,
    'iraq': 4157,
    'iran': 2836,
    
    # Sub-Saharan Africa
    'south_africa': 6001,
    'nigeria': 2097,
    'kenya': 1838,
    'ethiopia': 936,
    'ghana': 2328,
    'uganda': 817,
    'tanzania': 1077,
    'mozambique': 460,
    'madagascar': 515,
    'malawi': 412,
    'zambia': 1305,
    'zimbabwe': 1214,
    'botswana': 6711,
    'namibia': 4729,
    'angola': 1953,
    'cameroon': 1498,
    'ivory_coast': 2289,
    'senegal': 1488,
    'burkina_faso': 768,
    'mali': 876,
    'niger': 554,
    'chad': 664,
    'central_african_republic': 511,
    'democratic_republic_congo': 558,
    'rwanda': 820,
    'burundi': 261,
    
    # Global average for fallback
    'global_average': 11312
}

# Country name to code mapping for common variations
COUNTRY_NAME_MAPPING = {
    'usa': 'united_states',
    'us': 'united_states',
    'america': 'united_states',
    'uk': 'united_kingdom',
    'britain': 'united_kingdom',
    'korea': 'south_korea',
    'drc': 'democratic_republic_congo',
    'congo_drc': 'democratic_republic_congo',
    'uae': 'uae',
    'emirates': 'uae'
}

def get_country_gdp(country_code: str) -> float:
    """
    Get GDP per capita for a specific country
    
    Args:
        country_code: Country code or name
        
    Returns:
        GDP per capita in current US$ (2020)
    """
    # Normalize country code
    country_code = country_code.lower().replace(' ', '_')
    
    # Check direct mapping
    if country_code in COUNTRY_GDP_2020:
        return COUNTRY_GDP_2020[country_code]
    
    # Check alternative names
    if country_code in COUNTRY_NAME_MAPPING:
        return COUNTRY_GDP_2020[COUNTRY_NAME_MAPPING[country_code]]
    
    # Return global average as fallback
    return COUNTRY_GDP_2020['global_average']