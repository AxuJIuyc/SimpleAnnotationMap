import os
import cv2
import math
import numpy as np
import geojson

from downloader import main as download_map, wgs_to_tile
from OSM_extract_geojson import main as osmextract


# ============================= Редактируемый блок =============================
# Задайте координаты области и масштабирование
BOUNDS = [40.7137, 40.7046, -74.0303, -74.0422] # north, south, east, west
ZOOM = 17

# имя файлов 
SAVENAME = 'data/NewYork'

# параметры отрисовки
rectangle=True # ограничивающая рамка (для html файла)
simple_palette=True # Простая палитра
# thickness = 1
# isClosed = False
blackback=False, # затемнение фона
opacity=1 # Прозрачность разметки

# Задайте искомые тэги объектов
tags={'highway': True,
    'building': True,
    'natural': True,
    'landuse': True,
    'water': True}
# ==============================================================================

# ======================== Блок исполнительных функций ========================
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

# Перевод палитры
def HEX2RGB(hex_color):
    hex_color = hex_color.lstrip('#')
    
    # Разбиваем HEX на отдельные составляющие R, G и B
    b = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    r = int(hex_color[4:6], 16)
    
    return (r, g, b)

def draw_mask(image, mask, color, type, blackback=False, opacity=0.2):
    if type == 'Point':
        pass
    elif type == 'LineString':
        isClosed = False
        cv2.polylines(image, 
                    mask, 
                    isClosed,  
                    color,
                    thickness=1)
    elif type == 'Polygon':
        image = create_mask(image, mask, color, opacity)
    return image

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
    from PIL import Image

    # Задайте размеры изображения (x, y)
    y, x = shape
    # Создайте черное изображение
    black_image = Image.new('RGB', (x, y), (0, 0, 0))

    return np.asarray(black_image)


# =============================================================================

def sam():
    # Загрузка аннотаций OpenStreetMaps и создание html-файла
    if not os.path.exists(f'{SAVENAME}.geojson'):    
        osmextract(SAVENAME, BOUNDS, tags, opacity, 
                   ZOOM, blackback, rectangle, simple_palette)
    # -------------------------------------------------------------------------

    # Чтение аннотаций
    with open(f'{SAVENAME}.geojson') as f:
        gj = geojson.load(f)
    features = gj['features']

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
    path = f'{SAVENAME}_{idx}_{lat}_{long}_{D_LAT}_{D_LONG}_{STYLE}_{ZOOM}.bmp'
    if not os.path.isfile(path):
        download_map(left, top, right, bottom, ZOOM, path, STYLE, SERVER)
        # sat = cv2.imread(path)
        # cv2.imshow(f'{SAVENAME}', sat)
        # cv2.waitKey(0)
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

    palette = {}
    # Преобразование мировых координат объекта в пиксели
    for map_obj in features:
        mask_type = map_obj['geometry']['type']
        if mask_type == 'Point':
            continue
        elif mask_type == 'LineString':
            polygon_coordinates = map_obj['geometry']['coordinates']
        elif mask_type == 'Polygon':
            polygon_coordinates = map_obj['geometry']['coordinates'][0]
        polygon_pixels = [geocoordinates_to_pixels(coord, 
                                                   bounds_coords, 
                                                   bounds_pxls) for coord in polygon_coordinates]
        
        HEXcolor = map_obj['properties']['color']
        if HEXcolor not in palette:
            palette[HEXcolor] = HEX2RGB(HEXcolor)
        color = palette[HEXcolor]
        
        img = draw_mask(img, np.int32([polygon_pixels]), color, mask_type, 
                  blackback=blackback, opacity=opacity)
    
    cv2.imwrite(f'{SAVENAME}.bmp', img)
    cv2.imshow(f'{SAVENAME}.bmp', img)
    cv2.waitKey(0)
# -----------------------------------------------------------------------------

if __name__ == '__main__':
    sam()