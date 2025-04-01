# Наложить аннотации на PNG
import os
import cv2
import json
import geojson

# from pyparsing import col
# from tqdm import tqdm
# import math
# import numpy as np
# from PIL import Image, ImageDraw

from downloader import main as download_map, wgs_to_tile
from palette import hand_palette
from drawing import draw_masks, create_background, draw_objects
from geoscale import tile_to_lat_lon, world2pixels


# Сортировка типов для правильного порядка отрисовки:
def custom_sort_key(item):
    geometry_type = item['geometry']['type']
    tag = item['properties']['tag']
    
    if geometry_type == 'Multipolygon':
        return (0, hand_palette[tag].get('draw_level', 100))
    elif geometry_type == 'Polygon':
        return (1, hand_palette[tag].get('draw_level', 100))
    else:
        return (2, hand_palette[tag].get('draw_level', 100))
  
def def_aim_area(bounds):
    """
        Границы искомой области
    """
    n, s, e, w = bounds
    x_m = round((w+e)/2, 5)
    y_m = round((s+n)/2, 5)
    # lat, long, idx = y_m, x_m, 1
    lat, long = y_m, x_m

    d_lat = round((n-y_m), 5)
    d_long = round((e-x_m), 5)

    return lat, long, d_lat, d_long         
        
def defbounds(bounds, zoom):    
    """
    Определение границ сформированного из тайлов изображения

    Args:
        bounds (_type_): _description_
        zoom (_type_): _description_

    Returns:
        _type_: _description_
    """
    n, s, e, w = bounds
    
    tile_x1, tile_y1 = wgs_to_tile(w, n, zoom)
    tile_x2, tile_y2 = wgs_to_tile(e, s, zoom)

    latlt, lonlt = tile_to_lat_lon(tile_x1, tile_y1, zoom) # N, W
    latrb, lonrb = tile_to_lat_lon(tile_x2+1, tile_y2+1, zoom) # S, E
    print(f"Left-Top Latitude:\t {latlt}, \tLongitude: {lonlt}")
    print(f"Right-Bottom Latitude:\t {latrb}, \tLongitude: {lonrb}")
    bounds_coords = (lonlt, latlt, lonrb, latrb)
    return bounds_coords

def geojson_sort(gj, criterion=custom_sort_key):
    """Сортировка аннотаций для корректной отрисовки

    Args:
        gj (_type_): _description_
        criterion (_type_, optional): _description_. Defaults to custom_sort_key.

    Returns:
        _type_: _description_
    """
    features = []
    for obj in gj['features']:
        if obj['geometry']['type'] != 'Point':
            features.append(obj) 
    features = sorted(features, key=criterion) ##############
    return features



# ++++++++++++++++++++++++++++++++++++
def create_mapmask(
    bounds,
    geo_json, 
    save_folder, 
    name="VoidPlaceName",
    zoom=18,
    server="Google_wt_labels", 
    style = 's',
    background_color = (128,128,0),
    opacity=1,
    show=False
    ):
    # server="Google_wt_labels"
    # style = 's' # m - map, s - satellite, y - satellite with labels
    
    # Чтение аннотаций
    with open(geo_json) as f:
        gj = geojson.load(f)

    # Сортировка аннотаций для корректной отрисовки
    features = geojson_sort(gj, criterion=custom_sort_key)

    download_path = f'{save_folder}/download'
    os.makedirs(download_path, exist_ok=True) 
    
    # Границы искомой области
    lat, long, d_lat, d_long = def_aim_area(bounds)
    # path = f'{download_path}/{name}_{idx}_{lat}_{long}_{D_LAT}_{D_LONG}_{STYLE}_{zoom}.bmp'
    # Загрузка и сшивка тайлов Google Maps
    path = f'{download_path}/{name}_{lat}_{long}_{d_lat}_{d_long}_{style}_{zoom}.bmp'
    nums = [lat + d_lat, long - d_long, lat - d_lat, long + d_long]
    top, left, bottom, right = nums
    if not os.path.isfile(path):
        download_map(left, top, right, bottom, zoom, path, style, server)

    # Определение границ сформированного из тайлов изображения
    bounds_coords = defbounds(bounds, zoom)

    img = cv2.imread(path)
    y,x,_ = img.shape  
    bounds_pxls = (0,0,x,y)

    img = create_background(img.shape[:2], background_color)
        
    # Преобразование мировых координат объекта в пиксели
    x0, y0, x1, y1 = world2pixels(bounds, bounds_coords, bounds_pxls)

    # Подготовка директорий
    mask_path = f'{save_folder}'
    source_path = f'{save_folder}'
    json_path = f'{save_folder}'
    for dirpath in [mask_path, source_path, json_path]:
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)

    print("Image shape (H,W):", img.shape[:2])
    # Вычисление и отрисовка масок
    mask, mask_info, objects = draw_masks(img, features, bounds_coords, bounds_pxls, zoom, opacity=opacity, show=show) 
    with open(f'{json_path}/{name}.json', 'w') as f:
        json.dump(mask_info, f)
    aim_area = mask[y0:y1, x0:x1]
    cv2.imwrite(f'{mask_path}/{name}_seg.bmp', aim_area)
    if show:
        # mask = draw_objects(mask, objects)
        cv2.imshow('mask', cv2.resize(mask, dsize=None, fx=0.5, fy=0.5))
        cv2.waitKey(1)    

    # Сохранение целевой области с исходного изображения
    img = cv2.imread(path)
    if show:
        obj_img = draw_objects(img, objects)
        cv2.imshow('objects', cv2.resize(obj_img, dsize=None, fx=0.3, fy=0.3))
        cv2.imwrite(f'{source_path}/{name}_objects.bmp', obj_img)
        cv2.waitKey(0)
    img = img[y0:y1, x0:x1]
    cv2.imwrite(f'{source_path}/{name}.bmp', img)
    
    cv2.destroyAllWindows()
    
    # Objects annotates
    # dx, dy = x1-x0, y1-y0
    h,w,_ = img.shape
    create_objects_anno(objects, zoom, save_folder, (w,h), x0,y0)
    
    
    
def create_objects_anno(objects, zoom, savedir, shape, dx,dy):
    from palette import scale_table
    boxes, corners, crossroads = objects
    mp = scale_table.loc[zoom]['m/pixel']
    imw, imh = shape
    
    
    filepath = os.path.join(savedir, 'boxes_annotates.txt')
    with open(filepath, 'w') as f:
        for box in boxes:
            tag, xyxy = box
            lbl = hand_palette[tag]['object_detection']['bbox']['name']
            
            x1,y1,x2,y2 = map(int, xyxy)
            x1,x2 = x1-dx, x2-dx
            y1,y2 = y1-dy, y2-dy
            
            if x1>imw or y1>imh or x2<0 or y2<0:
                continue
            
            row = f"{lbl} {x1} {y1} {x2} {y2}\n"
            f.write(row)
    
    filepath = os.path.join(savedir, 'corners_annotates.txt')
    with open(filepath, 'w') as f:
        for tag, xys in corners:
            for x,y in xys:
                radius = hand_palette[tag]['object_detection']['corner']['radius'] # meters
                radius =  radius / mp
                x, y = x-dx, y-dy
                x1,x2 = max(0, x-radius), min(x+radius, imw)
                y1, y2 = max(0, y-radius), min(y+radius, imh)
                x1,y1,x2,y2 = map(int, [x1,y1,x2,y2])
                if x1>imw or y1>imh or x2<0 or y2<0:
                    continue                
                lbl = hand_palette[tag]['object_detection']['corner']['name']
                row = f"{lbl} {x1} {y1} {x2} {y2}\n"
                f.write(row)
                
        for x,y in crossroads:
            radius = hand_palette['highway']['object_detection']['crossing']['radius'] # meters
            radius =  radius / mp
            x, y = x-dx, y-dy
            x1,x2 = max(0, x-radius), min(x+radius, imw)
            y1, y2 = max(0, y-radius), min(y+radius, imh)
            x1,y1,x2,y2 = map(int, [x1,y1,x2,y2])
            if x1>imw or y1>imh or x2<0 or y2<0:
                continue            
            lbl = hand_palette['highway']['object_detection']['crossing']['name']
            row = f"{lbl} {x1} {y1} {x2} {y2}\n"
            f.write(row)

    
# +++++++++++++++++++++
if __name__ == "__main__":
    # Путь до информации об области
    geo_json = './data/t1/paris.geojson'
    # Директория сохранения
    save_folder = "./data/t1/"
    # Имя области
    name="VoidPlaceName"

    # Уровень зума (0-21)
    zoom=18

    north, south, east, west =  48.92085, 48.91483, 2.29661, 2.28353 # Paris
    bounds = north, south, east, west
    
    create_mapmask(bounds, geo_json, save_folder, name, zoom, opacity=1, show=True)