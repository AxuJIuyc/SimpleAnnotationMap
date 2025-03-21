import os
import osmnx as ox
import folium
import pandas as pd
import geojson
from palette import rgb2hex, hand_palette


def extract_feature(map, feature_collection, features, tags, palette, opacity=0.2):
    features = features.copy()
    features.reset_index(inplace=True)
    
    for tag in tags:
        if tag not in features or not tags[tag]:
            continue
        color = palette.get(tag, {}).get('color', [255,0,255])
        geom_types = palette.get(tag, {}).get('geom_types', [])
        positive_subtags = palette.get(tag, {}).get('positive_subtags', [])
        negative_subtags = palette.get(tag, {}).get('negative_subtags', [])
        
        fs = features[pd.notna(features[tag])]#[['geometry', tag]]
        # Фильтрация по negative_subtags (если список не пустой)
        if negative_subtags:
            fs = fs[~fs[tag].isin(negative_subtags)]
        # Фильтрация по positive_subtags (если список не пустой)
        if positive_subtags:
            fs = fs[fs[tag].isin(positive_subtags)]   
        
        if geom_types:
            fs = fs[fs['geometry'].geom_type.isin(geom_types)] 
            print(tag, geom_types, fs.shape)
            for id, row in fs.iterrows():
                add_feature(map, feature_collection, row, color, opacity, tag)
        else:
            for id, row in fs.iterrows():
                add_feature(map, feature_collection, row, color, opacity, tag)
        

def add_feature(map, feature_collection, feature, color, opacity, tag):
    hexcolor = rgb2hex(color)
    draw(map, feature['geometry'], color_line=hexcolor, opacity=opacity, info=f"{tag}:{feature[tag]}")
    # Создайте объект GeoJSON для текущей фичи и добавьте его в FeatureCollection
    geojson_feature = geojson.Feature(geometry=feature['geometry'], properties={"color": color})
    geojson_feature['properties']['tag'] = tag
    geojson_feature['properties']['subtag'] = feature[tag]
    
    if 'avg_width' in hand_palette[tag]:
        # if 'lanes' in feature:
        lanes = feature['lanes']
        if pd.notna(lanes):
            geojson_feature['properties']['lanes'] = lanes
        # if 'width' in feature:    
        width = feature['width']
        if pd.notna(width):
            geojson_feature['properties']['width'] = width 
        
    feature_collection['features'].append(geojson_feature)
    
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
    else:
        print("Неизвестный тип gtype:", gtype)
        
def create_html_mask(tags, bounds, name, save_folder, palette, zoom=18, opacity=0.2, rectangle=True):
    # Соберите объекты определенных типов в заданной области с помощью osmnx
    north, south, east, west = bounds
    bbox = [west, south, east, north]
    features = ox.features.features_from_bbox(bbox, tags)

    # Создайте объект FeatureCollection для хранения всех данных
    feature_collection = geojson.FeatureCollection([])

    # Создайте карту folium с базовым слоем Google Satellite
    center_lat = (north+south)/2
    center_lon = (east+west)/2
    m = folium.Map(location=[center_lat, center_lon], 
                zoom_start=zoom, 
                tiles='http://mt0.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', 
                attr='Google Satellite')

    # Добавление комментария в HTML-код
    # bounds = north, south, east, west
    html_comment = f'check area bounds (north, south, east, west): {bounds}'
    # Сохранение карты в HTML-файле с комментарием
    m.get_root().html.add_child(folium.Element(html_comment))

    # Добавьте выбранные объекты на карту
    extract_feature(m, feature_collection, features, tags, palette, opacity)
        
    # Отрисовка рамки по границам     
    if rectangle:
            folium.Rectangle(((north, west), (south, east)), color='white').add_to(m)

    # Сохраните карту в HTML-файл
    if save_folder:
        os.makedirs(save_folder, exist_ok=True)
        m.save(os.path.join(save_folder, f"{name}_op{opacity}.html"))

        # Создайте GeoJSON-файл
        with open(f'{save_folder}/{name}.geojson', 'w') as f:
            geojson.dump(feature_collection, f)
        
    return features, m
# =====================================================================
if __name__ == "__main__":
    # Задайте место
    north, south, east, west =  48.92085, 48.91483, 2.29661, 2.28353 # Paris
    bounds = north, south, east, west

    # Задайте искомые тэги объектов
    tags={
        'highway': True,
        'building': True,
        'natural': True,
        'landuse': True,
        'leisure': True,
        'shop': True,
        'water': True,
        'footway': False
    }

    # Уровень зума (0-21)
    zoom=18

    # Отрисовка рамки по искомой области
    rectangle = True

    # Сохранение
    save_folder = "data/t1/"
    name = 'paris'

    # Палитра цветов
    palette = hand_palette


    features, map = create_html_mask(tags, bounds, name, save_folder, palette, zoom, opacity=0.2, rectangle=True)
# ======================================================================
