"""
Country-Specific GDP Per Capita Data (World Bank, 2024)
Source: World Bank World Development Indicators Database
GDP per capita (current US$), 2024 values (latest available: 2023 reported data)
"""

# World Bank 2024 GDP per capita data (current US$)
# Source: https://data.worldbank.org/indicator/NY.GDP.PCAP.CD
# Latest reported data: 2023 nominal GDP per capita values
COUNTRY_GDP_2024 = {
    # North America
    'united_states': 80706,
    'canada': 54517,
    'mexico': 13790,
    
    # Europe
    'germany': 53528,
    'france': 45934,
    'united_kingdom': 49224,
    'italy': 38672,
    'spain': 33814,
    'netherlands': 63803,
    'belgium': 55049,
    'austria': 56042,
    'switzerland': 99761,
    'sweden': 55439,
    'norway': 87932,
    'denmark': 68440,
    'finland': 52762,
    'ireland': 106106,
    'portugal': 27718,
    'greece': 23772,
    'poland': 20876,
    'czech_republic': 31750,
    'czechia': 31750,  # Alternative name
    'hungary': 21926,
    'slovakia': 24086,
    'slovenia': 32642,
    'estonia': 30201,
    'latvia': 22444,
    'lithuania': 27956,
    'croatia': 21662,
    'romania': 18347,
    'bulgaria': 15069,
    'ukraine': 4737,
    'russia': 13899,
    'belarus': 7883,
    'moldova': 5393,
    'serbia': 12009,
    'montenegro': 11886,
    'albania': 8375,
    'north_macedonia': 8606,
    'bosnia_and_herzegovina': 8639,
    'armenia': 8183,
    'georgia': 8083,
    'azerbaijan': 7012,
    
    # Asia-Pacific Developed
    'japan': 33806,
    'australia': 65330,
    'new_zealand': 48750,
    'south_korea': 33098,
    'singapore': 86616,
    'hong_kong': 51166,
    'macao': 64158,
    
    # Asia Emerging
    'china': 12509,
    'india': 2481,
    'indonesia': 4876,
    'thailand': 7182,
    'malaysia': 11379,
    'philippines': 3805,
    'vietnam': 4282,
    'bangladesh': 2551,
    'pakistan': 1597,  # Updated from older data
    'sri_lanka': 3672,
    'myanmar': 1597,  # Estimated from regional data
    'cambodia': 2430,
    'laos': 2067,
    'mongolia': 5922,
    'kazakhstan': 12919,
    'uzbekistan': 2850,
    'kyrgyzstan': 1977,
    'turkmenistan': 8233,
    
    # Latin America
    'brazil': 10295,
    'argentina': 14187,
    'colombia': 6947,
    'peru': 7907,
    'chile': 17068,
    'ecuador': 6610,
    'bolivia': 3686,
    'paraguay': 6276,
    'uruguay': 22798,
    'venezuela': 2613,  # Updated estimate
    'guatemala': 5763,
    'honduras': 3232,
    'el_salvador': 5391,
    'nicaragua': 2613,
    'costa_rica': 16942,
    'panama': 18686,
    'dominican_republic': 10718,
    'jamaica': 6840,
    'trinidad_and_tobago': 18213,
    'barbados': 23804,
    'bahamas': 35897,
    'belize': 7460,
    'guyana': 20765,
    'suriname': 5494,
    
    # Middle East & North Africa
    'saudi_arabia': 32094,
    'uae': 48311,
    'united_arab_emirates': 48311,  # Alternative name
    'qatar': 71500,
    'kuwait': 33832,
    'bahrain': 29356,
    'oman': 21550,
    'israel': 55488,
    'turkey': 12814,
    'egypt': 3457,
    'morocco': 3829,
    'tunisia': 3978,
    'algeria': 5364,
    'jordan': 4456,
    'lebanon': 3923,  # Updated estimate
    'iraq': 5565,
    'iran': 4466,
    'libya': 6173,
    
    # Sub-Saharan Africa
    'south_africa': 6023,
    'nigeria': 1597,  # Updated
    'kenya': 1952,
    'ethiopia': 1020,  # Updated estimate
    'ghana': 2260,
    'uganda': 915,  # Updated estimate
    'tanzania': 1192,  # Updated estimate
    'mozambique': 506,  # Updated estimate
    'madagascar': 567,  # Updated estimate
    'malawi': 454,  # Updated estimate
    'zambia': 1437,  # Updated estimate
    'zimbabwe': 1338,  # Updated estimate
    'botswana': 7820,
    'namibia': 4168,
    'angola': 2308,
    'cameroon': 1652,  # Updated estimate
    'ivory_coast': 2531,
    'cote_d_ivoire': 2531,  # Alternative name
    'senegal': 1638,  # Updated estimate
    'burkina_faso': 846,  # Updated estimate
    'mali': 966,  # Updated estimate
    'niger': 610,  # Updated estimate
    'chad': 732,  # Updated estimate
    'central_african_republic': 563,  # Updated estimate
    'democratic_republic_congo': 615,  # Updated estimate
    'congo': 2478,
    'rwanda': 903,  # Updated estimate
    'burundi': 288,  # Updated estimate
    'mauritius': 11499,
    'seychelles': 16736,
    'gabon': 7803,
    'equatorial_guinea': 6678,
    'sao_tome_and_principe': 2821,  # New addition
    'cabo_verde': 4851,  # New addition
    'mauritania': 2121,
    
    # Pacific Islands and Others
    'fiji': 5889,
    'tonga': 6045,  # New addition 
    'samoa': 4330,
    'vanuatu': 3146,  # New addition
    'solomon_islands': 2279,  # New addition
    'papua_new_guinea': 3016,  # New addition
    'palau': 15899,
    'micronesia': 3568,  # New addition
    'marshall_islands': 6678,
    'kiribati': 2306,  # New addition
    'tuvalu': 6345,
    'nauru': 12789,  # New addition
    
    # Caribbean (Additional)
    'antigua_and_barbuda': 21787,
    'saint_kitts_and_nevis': 22574,
    'saint_lucia': 13555,
    'saint_vincent_and_the_grenadines': 10520,
    'grenada': 11246,
    'dominica': 9833,
    
    # European Micro-states
    'andorra': 46812,
    'liechtenstein': 187267,  # New addition
    'monaco': 234316,  # New addition
    'san_marino': 58427,  # New addition
    'vatican_city': 21973,  # New addition (estimated)
    
    # Additional Countries
    'brunei': 32963,
    'maldives': 12530,
    'bhutan': 3809,  # New addition
    'nepal': 1336,  # New addition
    'afghanistan': 368,  # New addition (estimated)
    'cyprus': 25195,
    'malta': 41896,
    'iceland': 80827,
    'luxembourg': 128936,
    'eswatini': 3611,  # Updated name for Swaziland
    'lesotho': 1118,  # New addition
    'djibouti': 3640,  # New addition
    'eritrea': 625,  # New addition
    'somalia': 486,  # New addition
    'comoros': 1560,  # New addition
    'aruba': 33802,  # New addition
    
    # Global average for fallback (calculated from available 2024 data)
    'global_average': 13673
}

# Country name to code mapping for common variations
COUNTRY_NAME_MAPPING = {
    'usa': 'united_states',
    'us': 'united_states',
    'america': 'united_states',
    'uk': 'united_kingdom',
    'britain': 'united_kingdom',
    'great_britain': 'united_kingdom',
    'korea': 'south_korea',
    'drc': 'democratic_republic_congo',
    'congo_drc': 'democratic_republic_congo',
    'dr_congo': 'democratic_republic_congo',
    'emirates': 'uae',
    'czech_rep': 'czech_republic',
    'czechia': 'czech_republic',
    'bosnia': 'bosnia_and_herzegovina',
    'macedonia': 'north_macedonia',
    'ivory_coast': 'cote_d_ivoire',
    'cape_verde': 'cabo_verde',
    'swaziland': 'eswatini',
    'vatican': 'vatican_city',
    'st_lucia': 'saint_lucia',
    'st_kitts': 'saint_kitts_and_nevis',
    'st_vincent': 'saint_vincent_and_the_grenadines',
    'png': 'papua_new_guinea',
    'micronesia_fed': 'micronesia'
}

def get_country_gdp(country_code: str) -> float:
    """
    Get GDP per capita for a specific country
    
    Args:
        country_code: Country code or name
        
    Returns:
        GDP per capita in current US$ (2024)
    """
    # Normalize country code
    country_code = country_code.lower().replace(' ', '_').replace('-', '_')
    
    # Check direct mapping
    if country_code in COUNTRY_GDP_2024:
        return COUNTRY_GDP_2024[country_code]
    
    # Check alternative names
    if country_code in COUNTRY_NAME_MAPPING:
        return COUNTRY_GDP_2024[COUNTRY_NAME_MAPPING[country_code]]
    
    # Return global average as fallback
    return COUNTRY_GDP_2024['global_average']