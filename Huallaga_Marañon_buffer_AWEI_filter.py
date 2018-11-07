#############################################################################################################  
#   
#   Código filtro AWEI para buffer de ríos Huallaga y Marañon usando el API de GEE en Jupyter
#
#   Se requiere instalar ipyleaflet en jupyter para poder visualizar la imagen final en un mapa
#
#   Funciones definidas
#   
#   imageFilterAWEI: Recibe una imagen y le aplica un filtro basándose en el índice AWEI.
#   cloudMasking: Recibe una imagen y le aplica un filtro de nubosidad (por ahora se filtra con un valor de 10)
#   GetTileLayerUrl: Recibe una imagen de Earth Egine y retorna un objeto que se puede mostrar en el mapa interactivo.
#
#   Función principal: Genera una Geometría a partir de la información de dos Fusion Table (esto nos brinda la información de las coordenadas par delimitar el área de interés) concatenadas a las cuales se procede a relizar los filtros utilizados anteriormente en el código base (Revisar repositorio archivo base.py)
#
#############################################################################################################


########################FUNCTIONS DEF####################

def imageFilterAWEI(imageToFilter):

    return imageToFilter.expression("4*(green - swir2)-(0.25*nir + 2.75*swir1)", {"green": imageToFilter.select("B3"), "nir": imageToFilter.select("B5"), "swir1": imageToFilter.select("B6"), "swir2": imageToFilter.select("B7")})

def cloudMasking(image):

    clouds = ee.Algorithms.Landsat.simpleCloudScore(image).select(["cloud"])
    
    return image.updateMask(clouds.lt(5))

def whiteMasking(image):
    
    return image.gt(0.0).lt(0.1)

def GetTileLayerUrl(ee_image_object):
    
    map_id = ee.Image(ee_image_object).getMapId()
    tile_url_template = "https://earthengine.googleapis.com/map/{mapid}/{{z}}/{{x}}/{{y}}?token={token}"
    
    return tile_url_template.format(**map_id)
    
#########################################################   

import ee
import numpy
import ipyleaflet
from ipyleaflet import (
    Map, basemaps, basemap_to_tiles,
    WMSLayer, LayersControl, SplitMapControl
)

ee.Initialize()

buffer_huallaga = ee.FeatureCollection('ft:1PvD0WJKoyCPXFzeNE4qdr4wxoTBAHocgQXGFz9eK')
geometry_huallaga = buffer_huallaga.geometry()
coords_huallaga= geometry_huallaga.coordinates()

buffer_marañon = ee.FeatureCollection('ft:1T2lF-2KE7_M2ZwW_9YnfE8z_gPuINs4YcUwIdgj6')
geometry_marañon = buffer_marañon.geometry()
coords_marañon= geometry_marañon.coordinates()

coords_multipolygon = ee.List(coords_huallaga).cat(coords_marañon)

buffer_multipolygon = ee.Geometry.MultiPolygon(coords_multipolygon);

multipolygon_centroid = buffer_multipolygon.centroid()

startDate = ee.Date('2017-06-01')
endDate = ee.Date('2017-10-31')

landsat = ee.ImageCollection('LANDSAT/LC08/C01/T1_RT_TOA').filterBounds(buffer_multipolygon).filterDate(startDate, endDate)

landsat_AWEI = landsat.map(imageFilterAWEI)
landsat_cloud_masked = landsat.map(cloudMasking)
landsat_cloud_masked_median = landsat_cloud_masked.median()
landsat_cloud_masked_median_AWEI = imageFilterAWEI(landsat_cloud_masked_median).clip(buffer_multipolygon)

landsat_mosaic = landsat.mosaic().clip(buffer_multipolygon);
landsat_white = landsat.map(whiteMasking)

baseMap = ipyleaflet.Map(
    center=(multipolygon_centroid.getInfo()["coordinates"][1], multipolygon_centroid.getInfo()["coordinates"][0]), zoom = 8,
    layout={'width':'1000px', 'height':'400px'}
)

baseMap.add_layer(
    ipyleaflet.TileLayer(url = GetTileLayerUrl(
        landsat_mosaic.Or(landsat.mosaic())
   )
))

right_layer = ipyleaflet.TileLayer(url = GetTileLayerUrl(
        landsat_cloud_masked_median_AWEI.visualize(min = 0.0, max = 1.0, palette = ['FFFFFF', '000000'])
    ))
left_layer = ipyleaflet.TileLayer(url=GetTileLayerUrl(
        landsat_cloud_masked_median_AWEI.visualize(min = 0.0, max = 0.12, palette = ["FFFFFF", "000000"]).subtract(landsat_cloud_masked_median_AWEI)
    ))

control = SplitMapControl(left_layer = left_layer, right_layer = right_layer)
baseMap.add_control(control)

baseMap