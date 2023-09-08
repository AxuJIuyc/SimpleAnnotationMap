import os
import osmnx as ox
import folium
import geopandas as gpd
import pandas as pd
import geojson

from palette import rgb2hex, hand_palette


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
    hexcolor = rgb2hex(color)
    draw(map, feature['geometry'], color_line=hexcolor, opacity=opacity, info=f"{tag}:{feature[tag]}")
    # Создайте объект GeoJSON для текущей фичи и добавьте его в FeatureCollection
    geojson_feature = geojson.Feature(geometry=feature['geometry'], properties={"color": color})
    geojson_feature['properties']['tag'] = tag
    geojson_feature['properties']['subtag'] = feature[tag]
    feature_collection['features'].append(geojson_feature)

def extract_feature(map, feature_collection, feature, tags, palette, opacity=0.2):
    for tag in tags:
        if tag in feature and pd.notna(feature[tag]):
            if feature[tag] in palette:
                color = palette[feature[tag]]
            else:
                color = palette[tag]
            add_feature(map, feature_collection, feature, color, opacity, tag)
            continue

def main(savename, bounds, tags, 
         zoom=15, rectangle=True):
    opacity = 0.2
    north, south, east, west = bounds
    center_lat = (north+south)/2
    center_lon = (east+west)/2

    directory_path = os.path.dirname(savename)
    name = savename.split('/')[-1]
    html_path = f'{directory_path}/html'
    geojson_path = f'{directory_path}/geojsons'
    for dirpath in [html_path, geojson_path]:
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)

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

    # Добавьте выбранные объекты на карту
    print('Add features to html')
    uniq_tags = {}
    palette = hand_palette()
    for id, feature in features.iterrows():
        # print('==feature==')
        # print(feature)
        # print("feature['geometry']:",feature['geometry'])
        extract_feature(m, feature_collection, feature, tags, palette, opacity)
  
    if rectangle:
        folium.Rectangle(((north, west), (south, east)), color='white').add_to(m)
    
    # Сохраните карту в HTML-файл
    m.save(f'{html_path}/{name}_op{opacity}.html')

    # Создайте GeoJSON-файл
    with open(f'{geojson_path}/{name}.geojson', 'w') as f:
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
    
    # Задайте искомые тэги объектов
    tags={'highway': True,
        'building': True,
        'natural': True,
        'landuse': True,}
    
    main(savename, bounds, tags, zoom, rectangle)