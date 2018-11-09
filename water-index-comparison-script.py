#############################################################################################################  
#   
#   Código comparación de índices de detección de agua para los ríos Huallaga y Marañon usando el API de GEE
#
#   Funciones definidas
#   
#   getAWEI: Recibe una imagen y le aplica un filtro basándose en el índice AWEI.
#   getNDWI: Recibe una imagen y le aplica un filtro basándose en el índice AWEI.
#   getMNDWI: Recibe una imagen y le aplica un filtro basándose en el índice AWEI.
#   getNDMI: Recibe una imagen y le aplica un filtro basándose en el índice AWEI.
#   getWRI: Recibe una imagen y le aplica un filtro basándose en el índice AWEI.
#   getAWEIsh: Recibe una imagen y le aplica un filtro basándose en el índice AWEI.
#   maskClouds: Recibe una imagen y seleccionando los bits 10 y 11 de la banda QA60 se filtran las nubes de la imagen del satélite Sentinel 2
#
#   Función principal: Código que evalúa los diferentes índices de detección de agua para los ríos Huallaga y Marañon (buffers). 
#   Adicionalmente, se utiliza un filtro de porcentaje de píxel nuboso del 35% (esto debido a que para valores menores 
#   se filtraban tramos de buffer con información).
#
############################################################################################################# 

########################FUNCTIONS DEF########################################### 

#AWEI (Automated Water Extarction Index)
def getAWEI(image):
    AWEI = image.expression('4*(green - swir2)-(0.25*nir + 2.75*swir1)', {'green':image.select('B3'), 'swir2':image.select('B12'), 'nir':image.select('B8'), 'swir1':image.select('B11')}) 
    return AWEI

#NDWI(Normalized Difference Water Index)
def getNDWI(image):
    NDWI = image.expression('(green - nir)/(green + nir)', {'green':image.select('B3'), 'nir':image.select('B8')}) 
    return NDWI

#MNDWI (Modified Normalized Difference Water Index)
def getMNDWI(image):
    MNDWI = image.expression('(green - swir2)/(green + swir2)', {'green':image.select('B3'), 'swir2':image.select('B12')}) 
    return MNDWI 

#NDMI (Normalized Difference Moisture Index)
def getNDMI(image):
    NDMI = image.expression('(red - nir)/(red + nir)', {'red':image.select('B4'), 'nir':image.select('B8')})
    return NDMI

#WRI (Water Ratio Index)
def getWRI(image):
    WRI = image.expression('(green + red)/(nir + swir2)', {'green':image.select('B3'), 'red':image.select('B4'), 'nir':image.select('B8'), 'swir2':image.select('B12')}) 
    return WRI

#AWEIsh 
def getAWEIsh(image):
    AWEIsh = image.expression('(blue + 2.5*green - 1.5*(nir + swir1) - 0.25*swir2)', {'blue':image.select('B2'), 'green':image.select('B3'), 'nir':image.select('B8'), 'swir1':image.select('B11'), 'swir2':image.select('B12')}); 
    return AWEIsh

#Sentinel QA60 band cloud mask
def maskClouds(image):
    qa = image.select('QA60')
    cloudBitMask = ee.Number(2).pow(10).int()
    cirrusBitMask = ee.Number(2).pow(11).int()
    mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(qa.bitwiseAnd(cirrusBitMask).eq(0))
    return image.updateMask(mask).divide(10000)
    
################################################################################ 

import ee
from ipyleaflet import (
    Map, basemaps, basemap_to_tiles,
    WMSLayer, LayersControl, SplitMapControl
)

buffer_huallaga = ee.FeatureCollection("ft:1EBinDHxAN9WBMQXImPCnLDuCm_foWX5Jyj48TB8d")
geometry_huallaga = buffer_huallaga.geometry()
coords_huallaga= geometry_huallaga.coordinates()

buffer_marañon = ee.FeatureCollection("ft:1T2lF-2KE7_M2ZwW_9YnfE8z_gPuINs4YcUwIdgj6")
geometry_marañon = buffer_marañon.geometry()
coords_marañon= geometry_marañon.coordinates()

coords_multipolygon = ee.List(coords_huallaga).cat(coords_marañon)

buffer_multipolygon = ee.Geometry.MultiPolygon(coords_multipolygon);

multipolygon_centroid = buffer_multipolygon.centroid()

startDate = ee.Date('2017-06-01')
endDate = ee.Date('2017-10-31')

#Sentinel 2
sentinelCollection = ee.ImageCollection('COPERNICUS/S2').filterBounds(buffer_multipolygon).filterDate(startDate, endDate)

composite = sentinelCollection.filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 35)).map(maskClouds);
              
sentinelAWEI = composite.map(getAWEI).median();
sentinelNDWI = composite.map(getNDWI).median();
sentinelMNDWI = composite.map(getMNDWI).median();
sentinelNDMI = composite.map(getNDMI).median();
sentinelWRI = composite.map(getWRI).median();
sentinelAWEIsh = composite.map(getAWEIsh).median();

baseMap = ipyleaflet.Map(
    center=(multipolygon_centroid.getInfo()["coordinates"][1], multipolygon_centroid.getInfo()["coordinates"][0]), zoom = 8,
    layout={'width':'1000px', 'height':'600px'}
)

#Visualización (AWEI y WRI por defecto)
right_layer = ipyleaflet.TileLayer(url = GetTileLayerUrl(
        sentinelAWEI.clip(buffer_multipolygon).visualize(min = 0.0, max = 1.0, palette = ["FFFFFF", "000000"])))
left_layer = ipyleaflet.TileLayer(url = GetTileLayerUrl(
        sentinelWRI.clip(buffer_multipolygon).visualize(min = 0.0, max = 2.0, palette = ["999999", "000000"])))

control = SplitMapControl(left_layer = left_layer, right_layer = right_layer)
baseMap.add_control(control)

baseMap


