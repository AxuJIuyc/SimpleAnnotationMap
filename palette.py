# ============================= Palettes =======================================
def hand_palette():
    palette = {
        'highway':[128,0,0],    'natural':[0,128,0],        'landuse':[128,128,0],
        'building':[0,0,128],   'bridge':[128,0,0],         'water':[0,128,128],
        'wood':[0,128,0],       'beach':[128,128,0],        'grassland':[128,128,0],
        'forest':[0,128,0],     'golf_course':[128,128,0],  'cliff':[128,128,0],
        'leisure':[0,128,0],    'wetland':[0,128,128],      'bay':[0,128,128],
        'river':[0,128,128],    'tourism':[0,128,128],      'railway':[128,0,0], 
        'foot':[128,0,0]
    } 
    return palette



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