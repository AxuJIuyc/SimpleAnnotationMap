# ============================= Palettes =======================================
def hand_palette():
    palette = {
        'highway':[128,0,0],    'natural':[0,128,0],        'landuse':[128,128,0],
        'building':[0,0,128],   'bridge':[128,0,0],         'water':[0,128,128],
        'wood':[0,128,0],       'beach':[128,128,0],        'grassland':[128,128,0],
        'forest':[0,128,0],     'golf_course':[128,128,0],  'cliff':[128,128,0],
        'leisure':[0,128,0],    'wetland':[0,128,128],      'bay':[0,128,128],
        'river':[0,128,128],    'tourism':[0,128,128],      'railway':[128,0,0], 
        'foot':[128,0,0], #' ':[], ' ':[],
        # ' ':[], ' ':[], ' ':[],
        # ' ':[], ' ':[], ' ':[],
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

class Tag(dict):
    def __init__(self, tagtype, name, color):
        super().__init__(self.create(tagtype, name, color))
    
    def create(self, name, color, tagtype='tag'):
        if tagtype == 'subtag':
            tag = {
                'name': name,
                'color': color}
        elif tagtype == 'tag':
            tag = {
                'name': name,
                'color': color,
                'subtags': []}
        return tag
    
    def subtag(self, subtag):
        self['su']


# class Palettes():
#     def __init__():
#         pass

#     def simpleColors():
#         return {}

#     def HEXp():
#         return {'red': '#ff0000', 'lightred': '#ff3b3b', 'darkred': '#a80000', '2darkred': '#730000',
#         'pink': '#ff7d7d', 'darkpink': '#8a4646', 'lightpink': '#ffabab',
#         'orange': '#de7f12', 'lightorange': '#ff8800', 'darkorange': '#ab5b00', 'skinny': '#ffbc70',
#         'yellow': '#ffe100', 'darkyellow': '#b09b00', 'lemon': '#ffec61', 
#         'lime': '#9dd600', 'lightlime': '#bbff00', 'darklime': '#6d9400',
#         'green': '#48cf00', 'lightgreen': '#59ff00', 'darkgreen': '#328f00',
#         'cyan': '#02bd9e', 'lightcyan': '#03ffd5', 'darkcyan': '#00705e',
#         'lightblue': '#007eb0', 'lightlightblue': '#00b7ff', 'darklightblue': '#207191',
#         'blue': '#0028c7', 'blue2': '#0028c7', 
#         'purple': '#4e00ad', 'lightpurple': '#7300ff', '2lightpurple': '#9a47ff', 'darkpurple': '#3e007d',
#         'fuchsia': '#b500af', 'lightfuchsia': '#ff00f7', 'darkfuchsia': '#6b0068',
#         'white': '#ffffff', 'black': '#000000', 'gray': '#878787',
#         }

class Tags():
    def __init__():
        pass


    def all_tags():
        return []
    tags = {'highway': [['crossing', 'bus_stop', 'secondary', 'residential', 
                        'service', 'unclassified', 'track', 'footway',
                        'path', 'steps'],
                        ['2darkred','white','lightred','red',
                        'darkred','pink','darkpink','lightpink',
                        'darkorange', 'lightpink'],
                        {'color': 'red'}],
            'natural': [['water', 'wood', 'scrub', 'tree', 
                        'beach', 'scree', 'grassland', 'heath'],
                        ['cyan', 'green', 'darkgreen', 'green', 
                        'darkyellow', 'skinny', 'lightgreen', 'orange'],
                        {'color': 'green'}],
            'landuse': [['residential', 'allotments', 'farmland', 'industrial',
                         'construction', 'grass', 'commercial', 'forest',
                         'farmyard', 'reservoir'],
                        ['yellow', 'lemon', 'lightorange', 'darkpurple',
                         'darkfuchsia', 'lightgreen', 'darklightblue', 'darkgreen',
                         'lightblue', 'lightlightblue'],
                        {'color': 'yellow'}],
            'building': [['yes', 'house', 'garage', 'detached',
                          'university', 'industrial', 'office', 'service',
                          'construction', 'residential', 'terrace', 'apartments'],
                        ['blue','blue2','lightblue', 'lightlightblue',
                         'purple', 'lightpurple', '2lightpurple', 'lightlightblue',
                         'fuchsia', 'lightfuchsia', 'darkfuchsia', 'darkpurple'],
                        {'color': 'blue'}],
            'bridge': [['yes'],
                    ['orange'],
                    {'color': 'red'}]}