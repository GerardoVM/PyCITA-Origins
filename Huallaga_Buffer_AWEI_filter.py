#############################################################################################################  
#   
#   Código filtro AWEI para buffer del río Huallaga API de GEE en Jupyter
#
#   IMPORTANTE:
#        
#   Se requiere instalar ipyleaflet en jupyter para poder visualizar la imagen final en un mapa.
#   Para visualizar el filtro del buffer se requiere tener la información respectiva en un Fusion Table (preferible generada desde un archivo kml) y reemplazar el id de la misma en el código
#   
#   Funciones definidas
#   
#   imageFilterAWEI: Recibe una imagen y le aplica un filtro basándose en el índice AWEI.
#   cloudMasking: Recibe una imagen y le aplica un filtro de nubosidad (por ahora se filtra con un valor de 10)
#   GetTileLayerUrl: Recibe una imagen de Earth Egine y retorna un objeto que se puede mostrar en el mapa interactivo.
#
#   Función principal: Genera una Geometría a partir de la información del Fusion Table (esto nos brinda la información de las coordenadas par delimitar el área de interés.
#   FInalmente, se procede a relizar los filtros utilizados anteriormente en el código base (Revisar repositorio archivo base.py)
#
#############################################################################################################


########################FUNCTIONS DEF########################################################################

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
    
##############################################################################################################   

import ee
import ipyleaflet
from ipyleaflet import (
    Map, basemaps, basemap_to_tiles,
    WMSLayer, LayersControl, SplitMapControl
)

ee.Initialize()

buffer_information = ee.FeatureCollection('ft:1PvD0WJKoyCPXFzeNE4qdr4wxoTBAHocgQXGFz9eK')
buffer_geometry = buffer_information.geometry()

centroid = geometry.centroid()
startDate = ee.Date('2017-06-01')
endDate = ee.Date('2017-10-31')

landsat = ee.ImageCollection('LANDSAT/LC08/C01/T1_RT_TOA').filterBounds(buffer_geometry).filterDate(startDate, endDate)
        
landsat_AWEI = landsat.map(imageFilterAWEI)

landsat_cloud_masked = landsat.map(cloudMasking)

landsat_cloud_masked_median = landsat_cloud_masked.median()

landsat_cloud_masked_median_AWEI = imageFilterAWEI(landsat_cloud_masked_median).clip(buffer_geometry)

landsat_mosaic = landsat.mosaic().clip(buffer_geometry);
landsat_white = landsat.map(whiteMasking)

baseMap = ipyleaflet.Map(
    center = (centroid.getInfo()["coordinates"][1], centroid.getInfo()["coordinates"][0]), zoom = 8,
    layout = {'width':'1000px', 'height':'400px'}
)

baseMap.add_layer(
    ipyleaflet.TileLayer(url = GetTileLayerUrl(
        landsat_mosaic.Or(landsat.mosaic())
   )
))

right_layer = ipyleaflet.TileLayer(url = GetTileLayerUrl(
        landsat_cloud_masked_median_AWEI.visualize(min = 0.0, max = 1.0, palette = ['FFFFFF', '000000'])
    ))
left_layer = ipyleaflet.TileLayer(url = GetTileLayerUrl(
        landsat_cloud_masked_median_AWEI.visualize(min = 0.0, max = 0.12, palette = ["FFFFFF", "000000"]).subtract(landsat_cloud_masked_median_AWEI)
    ))

control = SplitMapControl(left_layer = left_layer, right_layer = right_layer)
baseMap.add_control(control)

baseMap

