# SimpleAnnotationMap
Transfer Open Street Maps markup to Google Maps
<div>
  <img src="https://github.com/AxuJIuyc/SimpleAnnotationMap/blob/main/test/sources/test.bmp" width=500 alt="Paris" />
  <img src="https://github.com/AxuJIuyc/SimpleAnnotationMap/blob/main/test/masks/test.bmp" width=500 alt="Paris" />
</div>


Fast start:
1) Open simple_annotation_map.py
2) Change the BOUNDS coordinates of the desired location from OpenStreetMaps
3) Run simple_annotation_map.py

At the output you will get:
1) original image
2) interactive html file
3) {name}.geojson with real coordinates all objects
4) .bmp image with applied masks
5) .json with pixel coordinates all objects

Use multi_extractor for automatic saving many images
