import math


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

def world2pixels(bounds, bounds_coords, bounds_pxls):
    """
        Преобразование мировых координат объекта в пиксели
    """
    n, s, e, w = bounds
    x0,y0 = geocoordinates_to_pixels([w,n], bounds_coords, bounds_pxls)
    x1,y1 = geocoordinates_to_pixels([e,s], bounds_coords, bounds_pxls)
    return x0, y0, x1, y1

