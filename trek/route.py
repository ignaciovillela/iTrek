from geopy.distance import geodesic
import json
from ruta.models import Ruta, Punto, PuntoInteres

def distancia(p1, p2):
    return geodesic((p1["latitud"], p1["longitud"]), (p2["latitud"], p2["longitud"])).meters

def fusionar_puntos_cercanos(puntos, umbral=10):
    if not puntos:
        return []

    puntos_fusionados = []
    grupo_actual = [puntos[0]]

    for i in range(1, len(puntos)):
        distancia_entre_puntos = distancia(grupo_actual[-1], puntos[i])

        if distancia_entre_puntos <= umbral:
            # Si el punto está dentro del umbral, agrégalo al grupo actual
            grupo_actual.append(puntos[i])
        else:
            # Fusionar el grupo actual en un único punto promedio
            latitud_promedio = sum(p["latitud"] for p in grupo_actual) / len(grupo_actual)
            longitud_promedio = sum(p["longitud"] for p in grupo_actual) / len(grupo_actual)

            # Fusionar información de interés si está presente
            interes = None
            for p in grupo_actual:
                if "interes" in p:
                    interes = p["interes"]
                    break

            # Agregar el punto fusionado a la lista final
            puntos_fusionados.append({
                "latitud": latitud_promedio,
                "longitud": longitud_promedio,
                "orden": grupo_actual[0]["orden"],
                "interes": interes
            })

            # Iniciar un nuevo grupo con el punto actual
            grupo_actual = [puntos[i]]

    # Fusionar el último grupo
    if grupo_actual:
        latitud_promedio = sum(p["latitud"] for p in grupo_actual) / len(grupo_actual)
        longitud_promedio = sum(p["longitud"] for p in grupo_actual) / len(grupo_actual)
        interes = None
        for p in grupo_actual:
            if "interes" in p:
                interes = p["interes"]
                break
        puntos_fusionados.append({
            "latitud": latitud_promedio,
            "longitud": longitud_promedio,
            "orden": grupo_actual[0]["orden"],
            "interes": interes
        })

    return puntos_fusionados

from sklearn.cluster import DBSCAN
import numpy as np

def dbscan_clustering_with_order(data, eps_meters=5, order_weight=10):
    puntos = data["puntos"]
    result = []

    # Convertir datos a matriz de coordenadas
    coords = np.array([[p["latitud"], p["longitud"], p["orden"]] for p in puntos])
    lat_long_factor = 1 / 111_000  # Aproximación de grados a metros
    coords[:, :2] /= lat_long_factor  # Escalar latitud y longitud a metros
    coords[:, 2] *= order_weight  # Escalar el orden para penalizar diferencias grandes

    # Separar puntos con interés para preservarlos
    points_with_interest = [p for p in puntos if p.get("interes")]
    points_without_interest = [p for p in puntos if not p.get("interes")]
    coords_without_interest = np.array([[p["latitud"], p["longitud"], p["orden"]] for p in points_without_interest])
    coords_without_interest[:, :2] /= lat_long_factor
    coords_without_interest[:, 2] *= order_weight

    if len(points_without_interest) > 0:
        # Agrupación con DBSCAN
        dbscan = DBSCAN(eps=eps_meters, min_samples=1, metric="euclidean")
        labels = dbscan.fit_predict(coords_without_interest)

        # Agrupar puntos por etiqueta
        clusters = {}
        for label, punto in zip(labels, points_without_interest):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(punto)

        # Fusionar puntos en cada cluster
        for cluster in clusters.values():
            if len(cluster) == 1:
                result.append(cluster[0])  # Punto único no se modifica
            else:
                # Fusionar puntos del cluster
                lat_avg = sum(p["latitud"] for p in cluster) / len(cluster)
                long_avg = sum(p["longitud"] for p in cluster) / len(cluster)
                orden = cluster[0]["orden"]
                result.append({
                    "latitud": lat_avg,
                    "longitud": long_avg,
                    "orden": orden,
                    "interes": {}  # No se preserva interés para clusters fusionados
                })

    # Agregar puntos con interés directamente al resultado
    result.extend(points_with_interest)

    # Ordenar el resultado por el campo "orden"
    result.sort(key=lambda x: x["orden"])
    return result

# Ejemplo de uso
data_new = {
    'puntos': [
        {'latitud': -33.4564725, 'longitud': -70.5733309, 'orden': 1, 'interes': {}},
        {'latitud': -33.4564781, 'longitud': -70.5733255, 'orden': 2, 'interes': {}},
        {'latitud': -33.4564987, 'longitud': -70.5733334, 'orden': 3, 'interes': {}},
        {'latitud': -33.4564860, 'longitud': -70.5733250, 'orden': 4, 'interes': {}},
        {'latitud': -33.4564724, 'longitud': -70.5733308, 'orden': 5, 'interes': {}},
        {'latitud': -33.4564725, 'longitud': -70.5733309, 'orden': 6, 'interes': {}},
    ]
}

# Procesar los datos con DBSCAN respetando el orden
result = dbscan_clustering_with_order(data_new, eps_meters=5, order_weight=10)
print(result)
