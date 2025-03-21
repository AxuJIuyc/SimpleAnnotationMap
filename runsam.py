from OSM_extract_geojson import create_html_mask
from simple_annotation_map import create_mapmask
from palette import hand_palette
import os.path as osp


if __name__ == "__main__":
    # Задайте место
    north, south, east, west =  48.950000, 48.943961, 2.334906, 2.321087 # Paris
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
        'footway': False,
        'railway': True,
        'constraction': False,
        'sport': True
    }

    # Уровень зума (0-21)
    zoom=18

    # Отрисовка рамки по искомой области
    rectangle = True

    # Сохранение
    save_folder = "data/"
    name = 'paris'

    # Палитра цветов
    palette = hand_palette

    save_folder = osp.join(save_folder, name)
    features, map = create_html_mask(tags, bounds, name, save_folder, palette, zoom, opacity=0.2, rectangle=True)
    geo_json = osp.join(save_folder, f"{name}.geojson")
    create_mapmask(bounds, geo_json, save_folder, name, zoom, background_color=(128,128,0), opacity=1, show=True)
    