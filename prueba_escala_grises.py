import cv2
import numpy as np
import os

def calcular_porcentaje_grises(imagen_path):
    # Cargar la imagen en color
    imagen = cv2.imread(imagen_path)
    if imagen is None:
        return None  # Si no se pudo cargar, omitir
    
    # Convertir a escala de grises
    gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    
    # Reconstruir la imagen en color desde escala de grises
    gris_bgr = cv2.cvtColor(gris, cv2.COLOR_GRAY2BGR)
    
    # Calcular la diferencia absoluta entre la imagen original y la convertida
    diferencia = cv2.absdiff(imagen, gris_bgr)
    
    # Determinar los píxeles donde la diferencia es baja (cercanos a escala de grises)
    umbral = 5  # Ajustar si es necesario
    mascara_gris = np.all(diferencia < umbral, axis=2)
    
    # Calcular porcentaje de píxeles en escala de grises
    porcentaje_grises = np.sum(mascara_gris) / mascara_gris.size * 100
    
    return porcentaje_grises

def procesar_carpeta(carpeta):
    # Obtener lista de archivos en la carpeta
    archivos = [f for f in os.listdir(carpeta) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))]

    # Procesar cada imagen
    resultados = {}
    for archivo in archivos:
        imagen_path = os.path.join(carpeta, archivo)
        porcentaje = calcular_porcentaje_grises(imagen_path)
        if porcentaje is not None:
            resultados[archivo] = porcentaje
    
    return resultados

# Ruta de la carpeta con imágenes
carpeta_imagenes = "validation"

# Procesar todas las imágenes
resultados = procesar_carpeta(carpeta_imagenes)

# Mostrar los resultados
for imagen, porcentaje in resultados.items():
    print(f"{imagen}: {porcentaje:.2f}% en escala de grises")
