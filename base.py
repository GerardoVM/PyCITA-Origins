#############################################################################################################  
#   
#   Código de prueba inicial con API de GEE (6/11)
#
#   Funciones definidas
#   
#   imageFilterAWEI: Recibe una imagen y le aplica un filtro basándose en el índice AWEI.
#   cloudMasking: Recibe una imagen y le aplica un filtro de nubosidad (por ahora se filtra con un valor de 10)
#
#   Función principal: Código inicial en el cual se obtiene una imagen satelital (Landsat 8) la cual está limitada a parámetros de fecha y una geometría
#   definida (polígono) para limitar el área de interés. A dicha imagen se le aplica combinación de filtros AWEI y/o nubosidad para obtener una imagen final #   con superficie de agua resaltada.
#
#############################################################################################################   



########################FUNCTIONS DEF########################################### 

def imageFilterAWEI(imageToFilter):

    return imageToFilter.expression("4*(green - swir2)-(0.25*nir + 2.75*swir1)", {"green": imageToFilter.select("B3"), "nir": imageToFilter.select("B5"), "swir1": imageToFilter.select("B6"), "swir2": imageToFilter.select("B7")})

def cloudMasking(image):

    clouds = ee.Algorithms.Landsat.simpleCloudScore(image).select(["cloud"])
    
    return image.updateMask(clouds.lt(10))
    
################################################################################    

import ee
ee.Initialize()

polygon = ee.Geometry.Polygon([[-78.172, -4.4423], [-77.6364, -4.4437], [-77.6378, -4.6983], [-78.1651, -4.6887]])

centroid = polygon.centroid()

startDate = ee.Date('2017-06-01')
endDate = ee.Date('2017-10-31')

landsat = ee.ImageCollection('LANDSAT/LC08/C01/T1_RT_TOA').filterBounds(polygon).filterDate(startDate, endDate)
        
landsat_AWEI = landsat.map(imageFilterAWEI)

landsat_cloud_masked = landsat.map(cloudMasking)

landsat_cloud_masked_median = landsat_cloud_masked.median()

landsat_cloud_masked_median_AWEI = imageFilterAWEI(landsat_cloud_masked_median)








