from simple_annotation_map import sam
import os
import osmnx


# Set area coordinates and scaling
X, Y = 14.33673, 51.58668
ZOOM = 17
resolution = (1024, 1024) # W,H
steps = 40
# имя файлов 
SAVENAME = f'data/Germany/Spremberg_z{ZOOM}'

# Specify the required object tags
tags={'highway': True,
    'building': True,
    'natural': True,
    'landuse': True,
    'water': True,
    'tourism': True,
    'leisure': True,
    'railway': True,
    'foot': True}

directory_path = os.path.dirname(SAVENAME)
if not os.path.exists(directory_path):
    os.makedirs(directory_path)

dif = 2**ZOOM
w, h = resolution[0]//256, resolution[1]//256
dX, dY = w*360/dif, h*180/dif

for i in range(1, steps):
    for j in range(0, steps):
        print(f'Tile {i}_{j} in work')
        x0, y0 = X+dX*i, Y-dY*j
        x1, y1 = x0+dX, y0-dY
        bounds = [y0,y1,x1,x0]
        try:
            sam(f'{SAVENAME}_{i}_{j}', bounds, ZOOM, tags)
        except osmnx._errors.InsufficientResponseError:
            print(f'No data elements in server response for tile {i}_{j}')
