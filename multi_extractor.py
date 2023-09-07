from simple_annotation_map import sam
import os


# Задайте координаты области и масштабирование
ZOOM = 16
resolution = (1024, 1024) # W,H

# имя файлов 
SAVENAME = f'data/Beijing/Beijing_z{ZOOM}'



# Задайте искомые тэги объектов
tags={'highway': True,
    'building': True,
    'natural': True,
    'landuse': True,
    'water': True}

directory_path = os.path.dirname(SAVENAME)
if not os.path.exists(directory_path):
    os.makedirs(directory_path)

dif = 2**ZOOM
w, h = resolution[0]//256, resolution[1]//256
dX, dY = w*360/dif, h*180/dif

# k = 2
# dX, dY = k*0.02, k*0.012
X, Y = 116.0539, 39.9312

steps = 11
for i in range(10, steps):
    for j in range(10, steps):
        print(f'Tile {i}_{j} in work')
        x0, y0 = X+dX*i, Y-dY*j
        x1, y1 = x0+dX, y0-dY
        bounds = [y0,y1,x1,x0]
        sam(f'{SAVENAME}_{i}_{j}', bounds, ZOOM, tags)