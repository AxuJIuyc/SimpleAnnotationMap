# SimpleAnnotationMap
Transfer Open Street Maps markup to Google Maps
<div>
  <img src="./data/paris/sources/paris.bmp" width=500 alt="Paris" />
  <img src="./data/paris/masks/paris.bmp" width=500 alt="Paris" />
</div>


## Install:
``` bash
git clone https://github.com/AxuJIuyc/SimpleAnnotationMap.git
cd SimpleAnnotationMap
pip install requirements.txt
```

## Fast start:
1) Open runsam.py
2) Change the BOUNDS coordinates of the desired location from OpenStreetMaps
3) Run 
``` bash
python runsam.py
```

At the output you will get:
1) original image
2) interactive html file
3) {name}.geojson with real coordinates all objects
4) .bmp image with applied masks
5) .json with pixel coordinates all objects

Use multi_extractor for automatic saving many images
You need redact 'hand_palette' or create new function in palette.py for add new tags
