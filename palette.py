import pandas as pd


# ============================= Palettes =======================================
hand_palette = {
    'landuse': {
        'color': [128, 128, 0],
        'geom_types': ['Polygon', 'MultiPolygon'],
        'positive_subtags': [],
        'negative_subtags': [],
        'draw_level': 1
    },
    'water': {
        'color': [0, 128, 128],
        'geom_types': ['Polygon', 'MultiPolygon'],
        'positive_subtags': [],
        'negative_subtags': [],
        'draw_level': 0
    },
    'highway': {
        'color': [128, 0, 0],
        'geom_types': ['LineString'],
        'positive_subtags': [],
        'negative_subtags': ['footway', 'steps'],
        'avg_width': 3.25,
        'draw_level': 2,
        'object_detection': {
            'crossing': {'draw':True, 'color':(255,255,255), 'thickness':4},
        },        
    },
    'footway': {
        'color': [255, 0, 0],
        'geom_types': ['LineString', 'Polygon', 'MultiPolygon'],
        'positive_subtags': ['sidewalk'],
        'negative_subtags': [],
        'avg_width': 2,
        'draw_level': 2,
        'object_detection': {
            'crossing': {'draw':True, 'color':(255,255,255), 'thickness':4},
        }
    },
    'sport': {
        'color': [128, 0, 0],
        'geom_types': ['Polygon', 'MultiPolygon'],
        'positive_subtags': ['running'],
        'negative_subtags': [],
        'draw_level': 2
    },
    'railway': {
        'color': [128, 0, 128],
        'geom_types': ['LineString'],
        'positive_subtags': ['rail'],
        'negative_subtags': ['constraction'],
        'avg_width': 2.5,
        'draw_level': 3
    },
    'building': {
        'color': [0, 0, 128],
        'geom_types': ['Polygon'],
        'positive_subtags': [],
        'negative_subtags': [],
        'draw_level': 4,
        'object_detection': {
            'bbox': {'draw':True, 'color':(255,255,255), 'thickness':4},
            'corner': {'draw':True, 'color':(100,100,100), 'thickness':2}            
        }
    },
    'shop': {
        'color': [0, 0, 128],
        'geom_types': ['Polygon', 'MultiPolygon'],
        'positive_subtags': ['park'],
        'negative_subtags': [],
        'draw_level': 4,
        'object_detection': {
            'bbox': {'draw':True, 'color':(255,255,255), 'thickness':4},
            'corner': {'draw':True, 'color':(100,100,100), 'thickness':2}            
        }
    },
    'constraction': {
        'color': [0, 0, 0],
        'geom_types': ['LineString'],
        'positive_subtags': [],
        'negative_subtags': ['subway'],
        'avg_width': 1.5,
        'draw_level': 4
    },
    'natural': {
        'color': [0, 128, 0],
        'geom_types': ['Polygon', 'MultiPolygon'],
        'positive_subtags': [],
        'negative_subtags': ['water'],
        'draw_level': 5
    },
    'leisure': {
        'color': [0, 128, 0],
        'geom_types': ['Polygon', 'MultiPolygon'],
        'positive_subtags': ['park'],
        'negative_subtags': [],
        'draw_level': 5
    },
}


# =============================================================================
def rgb2hex(rgb_color):
    # Преобразуйте значения R, G и B в шестнадцатеричный формат и объедините их
    hex_color = "#{:02x}{:02x}{:02x}".format(rgb_color[0], rgb_color[1], rgb_color[2])
    
    return hex_color

# Перевод палитры
def hex2rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    
    # Разбиваем HEX на отдельные составляющие R, G и B
    b = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    r = int(hex_color[4:6], 16)
    
    return (r, g, b)


scale_table = pd.DataFrame(
    [
        [1,                     360,    156_543, "1:500*1e6",   "whole world"],
        [4,                     180,    78_272, "1:250*1e6",    ""],
        [16,                    90,     39_136, "1:150*1e6",    "subcontinental area"],
        [64,                    45,     19_568, "1:70*1e6",     "largest country"],
        [256,                   22.5,   9784,   "1:35*1e6",     ""],
        [1024,                  11.25,  4892,   "1:15*1e6",     "large African country"],
        [4096,                  5.625,  2446,   "1:10*1e6",     "large European country"],
        [16_384,                2.813,  1223,   "1:4*1e6",      "small country, US state"],
        [65_536,                1.406,  611.496, "1:2*1e6",     ""],
        [262_144,               0.703,  305.748, "1:1*1e6",     "wide area, large metropolitan area"],
        [1_048_576,             0.352,  152.874, "1:500*1e3",   "metropolitan area"],
        [4_194_304,             0.176,  76.437, "1:250*1e3",    "city"],
        [16_777_216,            0.088,  38.219, "1:150*1e3",    "town or city district"],
        [67_108_864,            0.044,  19.109, "1:70*1e3",     "village, or suburb"],
        [268_435_456,           0.022,  9.555,  "1:35*1e3",     ""],
        [1_073_741_824,         0.011,  4.777,  "1:15*1e3",     "small road"],
        [4_294_967_296,         0.005,  2.389,  "1:8*1e3",      "street"],
        [17_179_869_184,        0.003,  1.194,  "1:4*1e3",      "block, park, addresses"],
        [68_719_476_736,        0.001,  0.597,  "1:2*1e3",      "some buildings, trees"],
        [274_877_906_944,       0.0005, 0.299,  "1:1*1e3",      "local highway and crossing details"],
        [1_099_511_627_776,     0.00025, 0.149, "1:5*1e2",      "A mid0sized builing"],
    ], 
    columns=[
        "Tiles", 
        "Tile width", # (degrees of longitudes) 
        "m/pixel", # (on Equator) 
        "Scale", # (on screen) 
        "Examples" # Examples of areas to represent
    ]
).rename_axis("Level", axis=0)
    
def scale(zoom, arlw=3.25, lanes=0, width=0):
    """_summary_

    Args:
        zoom (_type_): _description_
        arlw (float, optional): avg_roadlane_width, meters. Defaults to 3.25.
        lanes (int, optional): _description_. Defaults to 0.
        width (int, optional): _description_. Defaults to 0.

    Returns:
        _type_: _description_
    """
    mp = scale_table.loc[zoom]['m/pixel']
    if width:
        p = width / mp
    elif lanes:
        width = arlw * lanes
        p = width / mp
    return p