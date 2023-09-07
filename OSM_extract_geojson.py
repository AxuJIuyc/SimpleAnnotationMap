import osmnx as ox
import folium
import geopandas as gpd
import pandas as pd
import geojson


def draw_polygon(map, geom, color, opacity, info):
    coords = []
    for coord in geom:
        coords.append(coord[::-1])
    pg = folium.Polygon(locations=coords, 
                    color=color, 
                    fill_color=color,
                    fill_opacity=opacity)
    popup = folium.Popup(info, parse_html=True)
    popup.add_to(pg)
    pg.add_to(map)


def draw(map, geometry, color_line, color_fill=None, opacity=0.2, info='object name'):
    """
    geometry: feature['geometry']
    color_line: ['red'; 'blue'; 'green'; etc.] 
                color for <LineString>,<Point>,<Polygon>
    color_fill: ['red'; 'blue'; 'green'; etc.] 
                fill color for <Polygon>
    """
    if not color_fill:
        color_fill = color_line

    gtype = geometry.geom_type
    if gtype == 'LineString':
        coords = []
        for lon, lat in zip(geometry.coords.xy[0], geometry.coords.xy[1]):
            coords.append((lat, lon))
        folium.PolyLine(coords, color=color_line, weight=3).add_to(map)
    elif gtype == 'Point':
        lat, lon = (geometry.y, geometry.x)
        folium.CircleMarker(location=[lat, lon], 
                            radius=6, 
                            color=color_line).add_to(map)
    elif gtype == 'Polygon':
        draw_polygon(map, 
                     geometry.exterior.coords[:], 
                     color_line, 
                     opacity, 
                     info)

    elif gtype == 'MultiPolygon':
        for polygon in geometry.geoms:
            draw_polygon(map, 
                     polygon.exterior.coords[:], 
                     color_line, 
                     opacity, 
                     info)

def check_uniq_subtags(feature, tag, uniq_tags={}):
    '''
    feature: object in osmnx.features
    tag: main tag like 'highway', 'building', etc.
    uniq_tags: unical subtags
    '''
    if tag not in uniq_tags:
        uniq_tags.update({tag:[]})
    if tag in feature and pd.notna(feature[tag]):
        if feature[tag] not in uniq_tags[tag]:
            uniq_tags[tag].append(feature[tag])
    return uniq_tags

def add_feature(map, feature_collection, feature, color, opacity, tag):
    draw(map, feature['geometry'], color_line=color, opacity=opacity, info=f"{tag}:{feature[tag]}")
    # Создайте объект GeoJSON для текущей фичи и добавьте его в FeatureCollection
    geojson_feature = geojson.Feature(geometry=feature['geometry'], properties={"color": color})
    geojson_feature['properties']['tag'] = tag
    geojson_feature['properties']['subtag'] = feature[tag]
    feature_collection['features'].append(geojson_feature)

def extract_feature(map, feature_collection, feature, tags, palette, opacity=0.2):
    for tag in tags:
        if tag in feature and pd.notna(feature[tag]):
            flag = 0
            if palette['name'] == 'simplep':
                flag = 1
                if feature[tag] in tags:
                    color = tags[feature[tag]]
                else:
                    color = tags[tag]
                color = palette[color]
                add_feature(map, feature_collection, feature, color, opacity, tag)
                continue
            for subtag, color in zip(tags[tag][0], tags[tag][1]):
                if subtag in feature[tag]:
                    flag = 1
                    color = palette[color]
                    add_feature(map, feature_collection, feature, color, opacity)
                    continue
            if flag == 0: # if there is an unaccounted tag
                add_feature(map, feature_collection, feature, palette['black'], opacity)
                print("unaccounted tag:", f"{tag}: {feature[tag]}")

def main(savename, bounds, tags, opacity, 
         zoom=15, rectangle=False, simple_palette=False):
    opacity = 0.2
    north, south, east, west = bounds
    center_lat = (north+south)/2
    center_lon = (east+west)/2
    print("Prepare tiles...")
    # Соберите объекты определенных типов в заданной области с помощью osmnx
    features = ox.features.features_from_bbox(north, south, east, west, tags)

    # Создайте объект FeatureCollection для хранения всех данных
    feature_collection = geojson.FeatureCollection([])

    # Создайте карту folium с базовым слоем Google Satellite
    m = folium.Map(location=[center_lat, center_lon], 
                zoom_start=zoom, 
                tiles='http://mt0.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', 
                attr='Google Satellite')

    # Добавление комментария в HTML-код
    html_comment = f'check area bounds (north, south, east, west): {bounds}'
    # Сохранение карты в HTML-файле с комментарием
    m.get_root().html.add_child(folium.Element(html_comment))

    HEXp = {'red': '#ff0000', 'lightred': '#ff3b3b', 'darkred': '#a80000', '2darkred': '#730000',
            'pink': '#ff7d7d', 'darkpink': '#8a4646', 'lightpink': '#ffabab',
            'orange': '#de7f12', 'lightorange': '#ff8800', 'darkorange': '#ab5b00', 'skinny': '#ffbc70',
            'yellow': '#ffe100', 'darkyellow': '#b09b00', 'lemon': '#ffec61', 
            'lime': '#9dd600', 'lightlime': '#bbff00', 'darklime': '#6d9400',
            'green': '#48cf00', 'lightgreen': '#59ff00', 'darkgreen': '#328f00',
            'cyan': '#02bd9e', 'lightcyan': '#03ffd5', 'darkcyan': '#00705e',
            'lightblue': '#007eb0', 'lightlightblue': '#00b7ff', 'darklightblue': '#207191',
            'blue': '#0028c7', 'blue2': '#0028c7', 
            'purple': '#4e00ad', 'lightpurple': '#7300ff', '2lightpurple': '#9a47ff', 'darkpurple': '#3e007d',
            'fuchsia': '#b500af', 'lightfuchsia': '#ff00f7', 'darkfuchsia': '#6b0068',
            'white': '#ffffff', 'black': '#000000', 'grray': '#878787',
            'name': 'HEXp'
            }

    simplep = {'red': '#800000', 'blue': '#000080', 'green': '#008000', 
               'yellow': '#808000', 'purple': '#800080', 'white': '#ffffff', 
               'black': '#000000', 'gray': '#878787', 'cyan': '#008080',
               'name': 'simplep'}

    simpletags = {'highway': 'red', 'natural': 'green', 'landuse': 'yellow', 
                  'building': 'blue', 'bridge': 'red', 'water': 'cyan', 
                  'bay':'cyan', 'river':'cyan', 'tourism':'green', 
                  'leisure':'green', 'cliff':'yellow'}

    tags = {'highway': [['crossing', 'bus_stop', 'secondary', 'residential', 
                        'service', 'unclassified', 'track', 'footway',
                        'path', 'steps'],
                        ['2darkred','white','lightred','red',
                        'darkred','pink','darkpink','lightpink',
                        'darkorange', 'lightpink']],
            'natural': [['water', 'wood', 'scrub', 'tree', 
                        'beach', 'scree', 'grassland', 'heath'],
                        ['cyan', 'green', 'darkgreen', 'green', 
                        'darkyellow', 'skinny', 'lightgreen', 'orange']],
            'landuse': [['residential', 'allotments', 'farmland', 'industrial',
                         'construction', 'grass', 'commercial', 'forest',
                         'farmyard', 'reservoir'],
                        ['yellow', 'lemon', 'lightorange', 'darkpurple',
                         'darkfuchsia', 'lightgreen', 'darklightblue', 'darkgreen',
                         'lightblue', 'lightlightblue']],
            'building': [['yes', 'house', 'garage', 'detached',
                          'university', 'industrial', 'office', 'service',
                          'construction', 'residential', 'terrace', 'apartments'],
                        ['blue','blue2','lightblue', 'lightlightblue',
                         'purple', 'lightpurple', '2lightpurple', 'lightlightblue',
                         'fuchsia', 'lightfuchsia', 'darkfuchsia', 'darkpurple']],
            'bridge': [['yes'],
                    ['orange']]}

    # Добавьте выбранные объекты на карту
    print('Add features to html')
    uniq_tags = {}
    for id, feature in features.iterrows():
        # print('==feature==')
        # print(feature)
        # print("feature['geometry']:",feature['geometry'])
        if simple_palette:
            extract_feature(m, feature_collection, feature, simpletags, simplep, opacity)
        else:
            uniq_tags = check_uniq_subtags(feature, 'landuse', uniq_tags)
            uniq_tags = check_uniq_subtags(feature, 'highway', uniq_tags)
            uniq_tags = check_uniq_subtags(feature, 'natural', uniq_tags)
            uniq_tags = check_uniq_subtags(feature, 'building', uniq_tags)

            extract_feature(m, feature_collection, feature, tags, HEXp, opacity)

    # print("=================================")
    # print("Tags in the area:")
    # for tags in uniq_tags.items():
    #     print(tags)
    # print("=================================")

    # if create_mask:
    #     folium.raster_layers.ImageOverlay(image='black.jpg', 
    #                                       bounds=[[0, 0], [180, 180]]).add_to(m)
    
    if rectangle:
        folium.Rectangle(((north, west), (south, east)), color='white').add_to(m)

    # Сохраните карту в HTML-файл
    m.save(f'{savename}_op{opacity}.html')

    # Создайте GeoJSON-файл
    with open(f'{savename}.geojson', 'w') as f:
        geojson.dump(feature_collection, f)

if __name__ == "__main__":
    # Имя файла сохранения
    savename = 'data/len2_fields'
    
    # Задайте координаты области и масштабирование
    bounds = [54.8635, 54.8443, 82.8836, 82.8359] # north, south, east, west
    zoom = 15
    
    # Прозрачность разметки; затемнение фона; ограничивающая рамка
    # Простая палитра
    opacity = 0.2
    rectangle=True
    simple_palette=True
    
    # Задайте искомые тэги объектов
    tags={'highway': True,
        'building': True,
        'natural': True,
        'landuse': True,}
    
    main(savename, bounds, tags, opacity, zoom, rectangle, simple_palette)
