import cv2
from PIL import Image, ImageDraw
from tqdm import tqdm
from palette import hand_palette, scale
import numpy as np
from geoscale import geocoordinates_to_pixels



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

def draw_filled_multipolygon(image, mp, color):
    """
    Заполняет пространство между полигонами в мультиполигоне, сохраняя фон внутри фигур.
    """
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    outer_contour, inner_contours = mp
    
    outer_contour = np.array(outer_contour)
    cv2.fillPoly(mask, [outer_contour], 255)  # Заполняем внешний контур
    for hole in inner_contours:
        hole = np.array(hole)
        cv2.fillPoly(mask, [hole], 0)  # Вырезаем внутренние отверстия

    # Закрашиваем маску цветом
    color_bgr = color[:3]  # Берем только 3 канала (BGR)
    color_layer = np.full_like(image, color_bgr, dtype=np.uint8)
    image[mask == 255] = color_layer[mask == 255]
    
    return image
    
def draw_masks(mask, features, bounds_coords, bounds_pxls, zoom, opacity=1, show=False):
    if show:
        cv2.namedWindow("mask", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("mask", 1024, 640)

    mask_info = []
    tags_dict = {}  # Словарь для хранения объектов, сгруппированных по тегам

    # Группируем объекты по тегам
    for map_obj in tqdm(features):
        tag = map_obj['properties']['tag']
        if tag not in tags_dict:
            tags_dict[tag] = {'polygons': [], 'polylines': [], 'multipolygons': [], 'line_thicknesses': [], 'colors': []}
        
        mask_type = map_obj['geometry']['type']
        if mask_type == 'Point':
            continue  # Пропускаем точки

        color = tuple(reversed(map_obj['properties']['color']))  # Преобразуем в BGR
        alpha = int(opacity * 255)  # Преобразуем прозрачность
        coordinates = map_obj['geometry']['coordinates']
        
        if mask_type in ['Polygon', 'MultiPolygon']:
            if len(coordinates) > 1:
                # Обрабатываем внешний контур
                # Обработка кривых массивов (вместо одинарной вложенности может появиться двойная)
                outer_coords =  coordinates[0]
                try:
                    while len(outer_coords) == 1:
                        outer_coords = outer_coords[0]
                except Exception as ex:
                    print(ex)
                    print(f"outer {tag}, broken\n")
                    continue

                outer_contour = [
                    geocoordinates_to_pixels(coord, bounds_coords, bounds_pxls) 
                        for coord in outer_coords
                ]
                
                # Обрабатываем внутренние контуры
                inner_contours = []
                inner_coords = coordinates[1:]
                try:
                    while len(inner_coords[0]) < 3:
                        inner_coords = inner_coords[0]
                except Exception as ex:
                    print(ex)
                    print(f"inner {tag}, broken\n")
                    continue
                
                for p in inner_coords:
                    pp = [geocoordinates_to_pixels(coord, bounds_coords, bounds_pxls) for coord in p]
                    inner_contours.append(pp)
                pixels = [outer_contour, inner_contours]
                tags_dict[tag]['multipolygons'].append(pixels)
                tags_dict[tag]['colors'].append((*color, alpha))  # Добавляем альфа-канал

            else:
                poly_coords = coordinates[0]
                pixels = np.array([geocoordinates_to_pixels(coord, bounds_coords, bounds_pxls) 
                                    for coord in poly_coords], dtype=np.int32)
                tags_dict[tag]['polygons'].append(pixels)
                tags_dict[tag]['colors'].append((*color, alpha))  # Добавляем альфа-канал

        elif mask_type == 'LineString':
            pixels = np.array([geocoordinates_to_pixels(coord, bounds_coords, bounds_pxls) 
                                for coord in coordinates], dtype=np.int32)
            width = map_obj['properties'].get('width', None)
            lanes = map_obj['properties'].get('lanes', None)
            tag = map_obj['properties']['tag']
            line_thickness = hand_palette[tag].get('avg_width', 3)
            if width:
                line_thickness = int(scale(zoom, width=float(width)))
            elif lanes:
                line_thickness = int(scale(zoom, arlw=float(line_thickness), lanes=int(lanes)))
            tags_dict[tag]['polylines'].append(pixels)
            tags_dict[tag]['line_thicknesses'].append(line_thickness)
            tags_dict[tag]['colors'].append(color)

        else:
            print('other')

        # if isinstance(pixels, list):
            # print(pixels)
        mask_info.append({'tag': map_obj['properties']['tag'], 
                          'subtag': map_obj['properties']['subtag'], 
                          'coords': pixels.tolist() if not isinstance(pixels, list) else pixels, 
                          'color': color})

    mask = np.array(mask)
    # Отрисовываем полигоны и линии в порядке тегов
    for tag, group in tags_dict.items():
        # Сначала отрисовываем полигоны для этого тега
        for polygon, color in zip(group['polygons'], group['colors']):
            mask = cv2.fillPoly(mask, [polygon], color)
        for mp, color in zip(group['multipolygons'], group['colors']):
            mask = draw_filled_multipolygon(mask, mp, color)
        
        # Затем отрисовываем линии для этого тега
        for polyline, color, thickness in zip(group['polylines'], group['colors'], group['line_thicknesses']):
            mask = cv2.polylines(mask, [polyline], isClosed=False, color=color, thickness=int(thickness))

    # for mp in multipoligons:
    #     draw_filled_multipolygon(mask, mp, bounds_coords, bounds_pxls)

    if show:
        cv2.imshow('mask', mask)
        cv2.waitKey(0)

    cv2.destroyAllWindows()
    return mask, mask_info

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