import os
import cv2
import math
import numpy as np
import geojson
from PIL import Image, ImageDraw
from tqdm import tqdm
import json

from downloader import main as download_map, wgs_to_tile
from OSM_extract_geojson import main as osmextract
from palette import rgb2hex, hex2rgb, hand_palette

# ============================= Editable block =============================
# Set area coordinates and scaling
BOUNDS = [49.1707, 49.1551, 2.4324, 2.4081] # north, south, east, west # NewYork
# BOUNDS = [54.8635, 54.8443, 82.8836, 82.8359] # north, south, east, west # NSK
ZOOM = 15

# file name
SAVENAME = 'data/test/test'

# drawing parameters
rectangle=True # bounding box (for html file)

blackback=True # darkening the background
opacity=255 # Markup transparency

# Specify the required object tags
tags={'highway': True,
    'building': True,
    'natural': True,
    'landuse': True,
    'water': True,
    'tourism': True,
    'leisure': True}
# ==============================================================================

# ======================== Executive functions block========================
# Позиция тайла в мировые координаты
def tile_to_lat_lon(tile_x, tile_y, zoom):
    n = 2.0 ** zoom
    lon_deg = tile_x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * tile_y / n)))
    lat_deg = math.degrees(lat_rad)
    return lat_deg, lon_deg

# Нормировка объектов к изображению
def geocoordinates_to_pixels(coord, bounds_coords, bounds_pxls):
    min_lon, min_lat, max_lon, max_lat = bounds_coords
    min_x, min_y, max_x, max_y = bounds_pxls
    
    x = (coord[0] - min_lon) / (max_lon - min_lon) * (max_x - min_x) + min_x
    y = (coord[1] - min_lat) / (max_lat - min_lat) * (max_y - min_y) + min_y
    
    return int(x), int(y)

def draw_mask(image, mask, color, objtype, opacity=255, line_thickness=3):
    color = color[::-1]
    if objtype == 'Point':
        pass
    elif objtype == 'LineString':
        isClosed = False
        image = np.array(image)
        cv2.polylines(image, 
                    mask, 
                    isClosed,  
                    color,
                    thickness=line_thickness)
    elif objtype == 'Polygon':
        image = Image.fromarray(image)
        image = create_mask2(image, mask, color, opacity)
    return image

def create_mask2(image, mask, color, alpha=255):
    obj = []
    # print(mask[0])
    for x,y in mask[0]:
        obj.append((x,y))

    # Create a new Image with the same size as the original image
    mask_image = Image.new("RGBA", image.size)

    # Create an ImageDraw object for the mask
    mask_draw = ImageDraw.Draw(mask_image)

    # Draw the polygon mask with the specified color and transparency
    mask_draw.polygon(obj, fill=(color[0],color[1],color[2], alpha))

    # Paste the mask onto the original image
    image.paste(mask_image, (0, 0), mask_image)

    # Optionally, display the result
    # image.show()

    return np.array(image)

def create_mask(image, mask, color, alpha):
    # Initialize blank mask image of same dimensions for drawing the shapes
    shapes = np.zeros_like(image, np.uint8)

    # Draw shapes
    cv2.fillPoly(shapes, mask, color)

    # Generate output by blending image with shapes image, using the shapes
    # images also as mask to limit the blending to those parts
    out = image.copy()
    mask = shapes.astype(bool)
    out[mask] = cv2.addWeighted(image, 1-alpha, shapes, alpha, 0)[mask]

    return out

def create_blackback(shape):
    # Задайте размеры изображения (x, y)
    y, x = shape
    # Создайте черное изображение
    black_image = Image.new('RGB', (x, y), (0, 0, 0))

    return np.asarray(black_image)

def draw_img(polygon_coordinates, bounds_coords, bounds_pxls, 
             mask_type, map_obj, img, line_thickness=3):
    pixels = [geocoordinates_to_pixels(coord, 
                                    bounds_coords, 
                                    bounds_pxls) for coord in polygon_coordinates]
 
    color = map_obj['properties']['color']
    metainfo = {'tag':map_obj['properties']['tag'], 
                 'subtag': map_obj['properties']['subtag'], 
                 'coords': pixels, 
                 'color': color}
    img = draw_mask(img, np.int32([pixels]), color, mask_type, 
                opacity=opacity, line_thickness=line_thickness)
    return img, metainfo

# Сортировка типов для правильного порядка отрисовки:
def custom_sort_key(item):
    geometry_type = item['geometry']['type']
    tag = item['properties']['tag']

    tag_order = {'landuse': 0, 'water': 1, 
                 'building': 2, 'highway': 3, 
                 'nature': 4}
    
    if geometry_type == 'Multipolygon':
        return (0, tag_order.get(tag, 5))
    elif geometry_type == 'Polygon':
        return (1, tag_order.get(tag, 5))
    else:
        return (2, tag_order.get(tag, 5))

# =============================================================================

def sam(SAVENAME, BOUNDS, ZOOM, tags):
    directory_path = os.path.dirname(SAVENAME)
    name = SAVENAME.split('/')[-1]
    geojson_path = f'{directory_path}/geojsons'
    
    # Загрузка аннотаций OpenStreetMaps и создание html-файла
    if not os.path.exists(f'{geojson_path}/{name}.geojson'):
        osmextract(SAVENAME, BOUNDS, tags, ZOOM, rectangle)
    # -------------------------------------------------------------------------
    
    # Чтение аннотаций
    with open(f'{geojson_path}/{name}.geojson') as f:
        gj = geojson.load(f)

    # Сортировка аннотаций для корректной отрисовки
    features = []
    for obj in gj['features']:
        if obj['geometry']['type'] != 'Point':
            features.append(obj) 
    features = sorted(features, key=custom_sort_key)

    # Границы искомой области
    n, s, e, w = BOUNDS
    x_m = round((w+e)/2, 5)
    y_m = round((s+n)/2, 5)
    lat, long, idx = y_m, x_m, 1

    # Загрузка и сшивка тайлов Google Maps
    SERVER="Google_wt_labels"
    STYLE = 's' # m - map, s - satellite, y - satellite with labels

    D_LAT = round((n-y_m), 5)
    D_LONG = round((e-x_m), 5)

    nums = [lat + D_LAT, long - D_LONG, lat - D_LAT, long + D_LONG]
    top, left, bottom, right = nums
    download_path = f'{directory_path}/download'    
    path = f'{download_path}/{name}_{idx}_{lat}_{long}_{D_LAT}_{D_LONG}_{STYLE}_{ZOOM}.bmp'
    if not os.path.isfile(path):
        download_map(left, top, right, bottom, ZOOM, path, STYLE, SERVER)
    # -----------------------------------------------------------------------------
    
    # Определение границ сформированного из тайлов изображения
    tile_x1, tile_y1 = wgs_to_tile(w, n, ZOOM)
    tile_x2, tile_y2 = wgs_to_tile(e, s, ZOOM)

    latlt, lonlt = tile_to_lat_lon(tile_x1, tile_y1, ZOOM) # N, W
    latrb, lonrb = tile_to_lat_lon(tile_x2+1, tile_y2+1, ZOOM) # S, E
    print(f"Left-Top Latitude:\t {latlt}, \tLongitude: {lonlt}")
    print(f"Right-Bottom Latitude:\t {latrb}, \tLongitude: {lonrb}")
    bounds_coords = (lonlt, latlt, lonrb, latrb)

    img = cv2.imread(path)
    y,x,_ = img.shape  
    bounds_pxls = (0,0,x,y)

    if blackback:
        img = create_blackback(img.shape[:2])

    mask_info = []
    # Преобразование мировых координат объекта в пиксели
    for map_obj, _ in zip(features, tqdm(range(len(features)))):
        mask_type = map_obj['geometry']['type']
        if mask_type == 'Point':
            continue
        elif mask_type == 'LineString':
            coordinates = map_obj['geometry']['coordinates']
        elif mask_type == 'Polygon':
            coordinates = map_obj['geometry']['coordinates'][0]
        elif mask_type == 'MultiPolygon':
            mask_type = 'Polygon'
            for polygon in map_obj['geometry']['coordinates']:
                coordinates = polygon[0]
                img, metainfo = draw_img(coordinates, 
                            bounds_coords, 
                            bounds_pxls,
                            mask_type, 
                            map_obj, 
                            img)
                mask_info.append(metainfo)
            continue
        img, metainfo  = draw_img(coordinates, 
            bounds_coords, 
            bounds_pxls,
            mask_type, 
            map_obj, 
            img)
        mask_info.append(metainfo)
    
    x0,y0 = geocoordinates_to_pixels([w,n], bounds_coords, bounds_pxls)
    x1,y1 = geocoordinates_to_pixels([e,s], bounds_coords, bounds_pxls)
    aim_area = img[y0:y1, x0:x1]
    
    mask_path = f'{directory_path}/masks'
    source_path = f'{directory_path}/sources'
    json_path = f'{directory_path}/jsons'
    for dirpath in [mask_path, source_path, json_path]:
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)

    with open(f'{json_path}/{name}.json', 'w') as f:
        json.dump(mask_info, f)

    cv2.imwrite(f'{mask_path}/{name}.bmp', aim_area)

    img = cv2.imread(path)
    img = img[y0:y1, x0:x1]
    cv2.imwrite(f'{source_path}/{name}.bmp', img)
    # cv2.imshow(f'{SAVENAME}.bmp', aim_area)
    # cv2.waitKey(0)
# =============================================================================

if __name__ == '__main__':
    sam(SAVENAME, BOUNDS, ZOOM, tags)
