# Наложить аннотации на PNG
import os
from downloader import main as download_map, wgs_to_tile
import cv2
from tqdm import tqdm
import json
from palette import hand_palette, scale
import math
import numpy as np
from PIL import Image, ImageDraw
import geojson


# Нормировка объектов к изображению
def geocoordinates_to_pixels(coord, bounds_coords, bounds_pxls):
    min_lon, min_lat, max_lon, max_lat = bounds_coords
    min_x, min_y, max_x, max_y = bounds_pxls
    
    x = (coord[0] - min_lon) / (max_lon - min_lon) * (max_x - min_x) + min_x
    y = (coord[1] - min_lat) / (max_lat - min_lat) * (max_y - min_y) + min_y
    
    return int(x), int(y)


# Позиция тайла в мировые координаты
def tile_to_lat_lon(tile_x, tile_y, zoom):
    n = 2.0 ** zoom
    lon_deg = tile_x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * tile_y / n)))
    lat_deg = math.degrees(lat_rad)
    return lat_deg, lon_deg

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

def world2pixels(bounds, bounds_coords, bounds_pxls):
    """
        Преобразование мировых координат объекта в пиксели
    """
    n, s, e, w = bounds
    x0,y0 = geocoordinates_to_pixels([w,n], bounds_coords, bounds_pxls)
    x1,y1 = geocoordinates_to_pixels([e,s], bounds_coords, bounds_pxls)
    return x0, y0, x1, y1

def draw_img(polygon_coordinates, bounds_coords, bounds_pxls, 
             mask_type, map_obj, img, line_thickness=3, opacity=1):
    pixels = [geocoordinates_to_pixels(coord, 
                                    bounds_coords, 
                                    bounds_pxls) for coord in polygon_coordinates]
 
    color = map_obj['properties']['color']
    metainfo = {
        'tag':map_obj['properties']['tag'], 
        'subtag': map_obj['properties']['subtag'], 
        'coords': pixels, 
        'color': color
        }
    opacity = int(opacity*255)
    img = draw_mask(img, np.int32([pixels]), color, mask_type, 
                opacity=opacity, line_thickness=line_thickness)
    return img, metainfo

def create_mask(image, mask, color, alpha=255):
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
        # image = Image.fromarray(image)
        image = np.array(image)
        cv2.fillPoly(image, [mask], color=color)
        cv2.addWeighted(image, opacity / 255.0, image, 1 - (opacity / 255.0), 0, image)
    return image
    
def draw_masks(mask, features, bounds_coords, bounds_pxls, zoom, opacity=1, show=False):
    if show:
        cv2.namedWindow("mask", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("mask", 1024, 640)

    mask_info = []
    tags_dict = {}  # Словарь для хранения объектов, сгруппированных по тегам

    # Группируем объекты по тегам
    for map_obj in tqdm(features):
        mask_type = map_obj['geometry']['type']
        if mask_type == 'Point':
            continue  # Пропускаем точки

        coordinates = map_obj['geometry']['coordinates']
        if mask_type == 'Polygon':
            coordinates = [coordinates[0]]  # Оборачиваем в список для единообразия
        elif mask_type == 'MultiPolygon':
            coordinates = [poly[0] for poly in coordinates]  # Берём первые кольца каждого полигона

        line_thickness = 3
        if mask_type == 'LineString':
            width = map_obj['properties'].get('width', None)
            lanes = map_obj['properties'].get('lanes', None)
            tag = map_obj['properties']['tag']
            rlw = hand_palette[tag]['avg_width']
            if width:
                line_thickness = int(scale(zoom, width=float(width)))
            elif lanes:
                line_thickness = int(scale(zoom, arlw=float(rlw), lanes=int(lanes)))

        color = tuple(reversed(map_obj['properties']['color']))  # Преобразуем в BGR
        alpha = int(opacity * 255)  # Преобразуем прозрачность

        # Заполняем словарь по тегам
        tag = map_obj['properties']['tag']
        if tag not in tags_dict:
            tags_dict[tag] = {'polygons': [], 'polylines': [], 'line_thicknesses': [], 'colors': []}
        
        # Добавляем в соответствующую группу (полигон или линия)
        if mask_type in ['Polygon', 'MultiPolygon']:
            for poly_coords in coordinates:
                pixels = np.array([geocoordinates_to_pixels(coord, bounds_coords, bounds_pxls) 
                                   for coord in poly_coords], dtype=np.int32)
                if len(pixels) > 0:
                    tags_dict[tag]['polygons'].append(pixels)
                    tags_dict[tag]['colors'].append((*color, alpha))  # Добавляем альфа-канал

        elif mask_type == 'LineString':
            pixels = np.array([geocoordinates_to_pixels(coord, bounds_coords, bounds_pxls) 
                               for coord in coordinates], dtype=np.int32)
            if len(pixels) > 1:  # Линия должна состоять как минимум из двух точек
                tags_dict[tag]['polylines'].append(pixels)
                tags_dict[tag]['line_thicknesses'].append(line_thickness)
                tags_dict[tag]['colors'].append(color)

        mask_info.append({'tag': map_obj['properties']['tag'], 
                          'subtag': map_obj['properties']['subtag'], 
                          'coords': pixels.tolist(), 
                          'color': color})

    mask = np.array(mask)
    # Отрисовываем полигоны и линии в порядке тегов
    for tag, group in tags_dict.items():
        # Сначала отрисовываем полигоны для этого тега
        for polygon, color in zip(group['polygons'], group['colors']):
            mask = cv2.fillPoly(mask, [polygon], color)
        
        # Затем отрисовываем линии для этого тега
        for polyline, color, thickness in zip(group['polylines'], group['colors'], group['line_thicknesses']):
            mask = cv2.polylines(mask, [polyline], isClosed=False, color=color, thickness=thickness)

    if show:
        cv2.imshow('mask', mask)
        cv2.waitKey(0)

    cv2.destroyAllWindows()
    return mask, mask_info
  
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

def create_background(shape, color):
    """_summary_

    Args:
        shape (_type_): (y, x) - shape of image
        color (_type_): (R,G,B) from 0 to 255

    Returns:
        _type_: _description_
    """
    # Задайте размеры изображения (x, y)
    y, x = shape
    # Создайте изображение
    image = Image.new('RGB', (x, y), color)

    return np.asarray(image)[:,:,::-1]

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
    mask_path = f'{save_folder}/masks'
    source_path = f'{save_folder}/sources'
    json_path = f'{save_folder}/jsons'
    for dirpath in [mask_path, source_path, json_path]:
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)

    print("Image shape (H,W):", img.shape[:2])
    # Вычисление и отрисовка масок
    mask, mask_info = draw_masks(img, features, bounds_coords, bounds_pxls, zoom, opacity=opacity, show=show) 
    with open(f'{json_path}/{name}.json', 'w') as f:
        json.dump(mask_info, f)
    aim_area = mask[y0:y1, x0:x1]
    cv2.imwrite(f'{mask_path}/{name}.bmp', aim_area)

    # Сохранение целевой области с исходного изображения
    img = cv2.imread(path)
    img = img[y0:y1, x0:x1]
    cv2.imwrite(f'{source_path}/{name}.bmp', img)
    
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