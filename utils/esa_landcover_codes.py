"""
ESA CCI Land Cover Classification Codes
Central authority for ESA land cover code descriptions and mappings
Based on ESA Climate Change Initiative Land Cover v2.0.7
"""

# Official ESA CCI Land Cover Code Descriptions
# Based on ESA CCI Land Cover 22-class classification system + Level 2 subcodes
ESA_LANDCOVER_DESCRIPTIONS = {
    # Cropland Classes
    10: "Cropland, rainfed",
    11: "Herbaceous cover",
    12: "Tree or shrub cover", 
    20: "Cropland, irrigated or post-flooding",
    30: "Mosaic cropland (>50%) / natural vegetation (<50%)",
    40: "Mosaic natural vegetation (>50%) / cropland (<50%)",
    
    # Forest Classes
    50: "Tree cover, broadleaved, evergreen, closed to open (>15%)",
    60: "Tree cover, broadleaved, deciduous, closed to open (>15%)",
    61: "Tree cover, broadleaved, deciduous, closed (>40%)",
    62: "Tree cover, broadleaved, deciduous, open (15-40%)",
    70: "Tree cover, needleleaved, evergreen, closed to open (>15%)",
    71: "Tree cover, needleleaved, evergreen, closed (>40%)",
    72: "Tree cover, needleleaved, evergreen, open (15-40%)",
    80: "Tree cover, needleleaved, deciduous, closed to open (>15%)",
    81: "Tree cover, needleleaved, deciduous, closed (>40%)",
    82: "Tree cover, needleleaved, deciduous, open (15-40%)",
    90: "Tree cover, mixed leaf type (broadleaved and needleleaved)",
    100: "Mosaic tree and shrub (>50%) / herbaceous cover (<50%)",
    
    # Shrubland Classes
    110: "Mosaic herbaceous cover (>50%) / tree and shrub (<50%)",
    120: "Shrubland",
    121: "Shrubland evergreen",
    122: "Shrubland deciduous",
    
    # Grassland Classes
    130: "Grassland",
    140: "Lichens and mosses",
    
    # Sparse Vegetation Classes
    150: "Sparse vegetation (tree, shrub, herbaceous cover) (<15%)",
    151: "Sparse tree (<15%)",
    152: "Sparse shrub (<15%)",
    153: "Sparse herbaceous cover (<15%)",
    
    # Wetland Classes
    160: "Tree cover, flooded, fresh or brakish water",
    170: "Tree cover, flooded, saline water",
    180: "Shrub or herbaceous cover, flooded, fresh/saline/brakish water",
    
    # Urban/Built-up Classes
    190: "Urban areas",
    
    # Bare Areas Classes
    200: "Bare areas",
    201: "Consolidated bare areas", 
    202: "Unconsolidated bare areas",
    
    # Water Bodies Classes
    210: "Water bodies",
    
    # Snow and Ice Classes
    220: "Permanent snow and ice",
    
    # Additional codes that may be returned by various systems
    21: "Developed, Open Space",
    22: "Developed, Low Intensity",
    23: "Developed, Medium Intensity", 
    24: "Developed, High Intensity",
    31: "Barren Land",
    41: "Deciduous Forest",
    42: "Evergreen Forest",
    43: "Mixed Forest",
    52: "Shrub/Scrub",
    95: "Emergent Herbaceous Wetlands"
}

# Default ESA Code Multipliers (100% = no adjustment)
# Users can customize these values in the application settings
ESA_DEFAULT_MULTIPLIERS = {code: 100 for code in ESA_LANDCOVER_DESCRIPTIONS.keys()}

def get_esa_description(code: int) -> str:
    """
    Get the official ESA CCI land cover description for a given code
    
    Args:
        code: ESA land cover code (integer)
    
    Returns:
        Official description string, or generic description if code not found
    """
    return ESA_LANDCOVER_DESCRIPTIONS.get(code, f"ESA Land Cover Class {code}")

def get_all_esa_codes() -> dict:
    """
    Get all ESA land cover codes and their descriptions
    
    Returns:
        Dictionary of {code: description} mappings
    """
    return ESA_LANDCOVER_DESCRIPTIONS.copy()

def get_default_multipliers() -> dict:
    """
    Get default multiplier values for all ESA land cover codes
    
    Returns:
        Dictionary of {code: multiplier_percentage} mappings (all set to 100%)
    """
    return ESA_DEFAULT_MULTIPLIERS.copy()

def is_valid_esa_code(code: int) -> bool:
    """
    Check if a code is a valid ESA land cover code
    
    Args:
        code: Land cover code to check
        
    Returns:
        True if code is valid, False otherwise
    """
    return code in ESA_LANDCOVER_DESCRIPTIONS