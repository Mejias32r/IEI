from django.shortcuts import render
from django.http import JsonResponse
from django.http import JsonResponse
from .settings import FUENTES_DE_DATOS_DIR
import json
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view


class Tipo():
    YACIMIENTO_ARQUEOLOGICO = "YA", 'Yacimiento_arqueológico'
    IGLESIA_ERMITA = "IE", 'Iglesia-Ermita'
    MONASTERIO_CONVENTO = "MC", 'Monasterio-Convento'
    CASTILLO_FORTALEZA_TORRE = "CFT", 'Castillo-Fortaleza-Torre'
    EDIFICIO_SINGULAR = "ES", 'Edificio singular'
    PUENTE = "PU", 'Puente'
    OTROS = "OT", 'Otros'

# Diccionario que mapea los nombres de monumentos a los valores del enum `Tipo`
TIPOS_MONUMENTOS = {
    "Yacimiento Arqueológico": ["yacimiento", "arqueológico"],
    "Iglesia-Ermita": ["iglesia", "ermita", "catedral", "parroquia", "basílica", "santuario"],
    "Monasterio-Convento": ["monasterio", "convento"],
    "Castillo-Fortaleza-Torre": ["castillo", "fuerte", "torre", "muralla"],
    "Edificio Singular": ["palacio", "casa", "edificio", "monumento"],
    "Puente": ["puente", "viaducto"],
    "Otros": ["otro", "desconocido"] 
}

NOMBRES_PROVINCIAS = {
    "Araba-Álava": ["álava", "araba", "alava"],
    "Bizkaia-Vizcaya": ["bizkaia", "vizcaya"],
    "Gipuzkoa-Gipúzcoa": ["gipuzkoa", "gipuzcoa", "gipúzcoa"],
}

def determinar_tipo(nombre):
    if not nombre:  # Verifica si `nombre` es None o vacío
        return False
    nombre_lower = nombre.lower()  
    for tipo, palabras_clave in TIPOS_MONUMENTOS.items():
        if any(palabra in nombre_lower for palabra in palabras_clave):
            return tipo  
    return "Otros"  

def conversor_dos_idiomas(provincia):
    provincia_lower = provincia.lower()
    for nombres, palabras_clave in NOMBRES_PROVINCIAS.items():
        if any(palabra in provincia_lower for palabra in palabras_clave):
            return nombres  

def manejar_claves_duplicadas(pares):
    "Devuelve un diccionario con solo la primera aparición de cada clave."
    resultado = {}
    for clave, valor in pares:
        if clave not in resultado:
            resultado[clave] = valor
    return resultado

def existe_monumento(report, nombre):
    if not nombre:  # Verifica si `nombre` es None o vacío
        return False
    # Recorrer la lista de monumentos para buscar el nombre
    for monumento in report["Registrados"]["Monumentos"]:
        if monumento.get("nombre", "").lower() == nombre.lower():
            return True
    return False

def existe_localidad(report, nombre):
    # Recorrer la lista de monumentos para buscar el nombre
    for monumento in report["Registrados"]["Localidades"]:
        if monumento.get("nombre", "").lower() == nombre.lower():
            return True
    return False

def existe_provincia(report, nombre):
    if not nombre:  # Verifica si `nombre` es None o vacío
        return False
    # Recorrer la lista de monumentos para buscar el nombre
    for monumento in report["Registrados"]["Provincias"]:
        if monumento.get("nombre", "").lower() == nombre.lower():
            return True
    return False

@swagger_auto_schema(
    method='GET',
    operation_summary="Extrae datos del JSON",
    operation_description="Lee un archivo JSON y procesa los datos de los monumentos. Devuelve un JSON con los datos procesados.",
    responses={
        200: openapi.Response(
            description="JSON procesado correctamente",
            examples={
                "application/json": {
                    "nombre": "Wrapper_JSON",
                        "total": {"count": 0},
                        "Registrados": {
                            "count": 0,
                            "Provincias": ["..."],
                            "Localidades": ["..."],
                            "Monumentos": ["..."]
                        },
                        "Descartados": {
                            "total": 0,
                            "Provincias": ["..."],
                            "Localidades": ["..."],
                            "Monumento": ["..."]
                        },
                        "Reparados": {
                            "total": 0,
                            "Provincias": ["..."],
                            "Localidades": ["..."],
                            "Monumento": ["..."]
                        }
                }
            },
        ),
        500: "Error processing the JSON file",
        405: "Method Not Allowed",
    },
)

# Función principal que procesa el archivo JSON
@api_view(['GET'])
def extract_json(request):
    if request.method == 'GET':
        json_path = f"{FUENTES_DE_DATOS_DIR}/edificios_final.json"
        try:
            with open(json_path, "r", encoding="utf-8") as file:
                monumentos = json.load(file, object_pairs_hook=manejar_claves_duplicadas)
        except FileNotFoundError:
            return render(request, "error.html", {"error": "Archivo JSON no encontrado."})
        except json.JSONDecodeError:
            return render(request, "error.html", {"error": "Error al decodificar el archivo JSON."})

        
        report = {
                "nombre": "Wrapper_JSON",
                "total": {"count": 0},
                "Registrados": {
                    "count": 0,
                    "Provincias": [],
                    "Localidades": [],
                    "Monumentos": []
                },
                "Descartados": {
                    "total": 0,
                    "Provincias": [],
                    "Localidades": [],
                    "Monumento": []
                },
                "Reparados": {
                    "total": 0,
                    "Provincias": [],
                    "Localidades": [],
                    "Monumento": []
                }
            }
        
        counter = 0

        for item in monumentos:
            try:

                counter += 1
                report["total"]["count"] += 1
                    
                # Map the name
                if(not item.get("documentName")):
                    report["Descartados"]["total"] += 1
                    report["Descartados"]["Monumento"].append({
                        "linea": counter,
                        "nombre": "",
                        "motivo": "Monumento sin nombre."
                    })
                    continue
                nameConstructor = item.get("documentName")

                if existe_monumento(report, nameConstructor):
                    report["Descartados"]["total"] += 1
                    report["Descartados"]["Monumento"].append({
                        "linea": counter,
                        "nombre": nameConstructor,
                        "motivo": "Monumento repetido."
                    })
                    continue

                # Mapear el tipo de monumento
                monumentTypeConstructor = determinar_tipo(nameConstructor)

                # Mapear la provincia
                if not item.get("territory"):
                    report["Descartados"]["total"] += 1
                    report["Descartados"]["Provincias"].append({
                        "linea": counter,
                        "nombre": "",
                        "motivo": "Falta el nombre de la provincia."
                    })
                    report["Descartados"]["Monumento"].append({
                        "linea": counter,
                        "nombre": nameConstructor,
                        "motivo": "Falta la provincia."
                    })
                    continue

                provinceConstructor = conversor_dos_idiomas(item.get("territory"))

                if not existe_provincia(report, provinceConstructor):
                    report["Registrados"]["Provincias"].append({
                        "nombre": provinceConstructor
                    })   
                             

                # Mapear la localidad
                if not item.get("municipality"):
                    report["Descartados"]["total"] += 1
                    report["Descartados"]["Localidades"].append({
                        "linea": counter,
                        "nombre": "",
                        "motivo": "Falta el nombre de la localidad."
                    })
                    report["Descartados"]["Monumento"].append({
                        "linea": counter,
                        "nombre": nameConstructor,
                        "motivo": "Falta la localidad."
                    })
                    continue

                localidadNameConstructor = item.get("municipality")
                if  not existe_localidad(report, localidadNameConstructor):
                    report["Registrados"]["Localidades"].append({
                        "nombre": localidadNameConstructor,
                        "en_provincia": provinceConstructor
                    })  
                
                # Validar código postal
                codigo_postal = item.get("postalCode")
                if codigo_postal != '':    
                    if len(codigo_postal) == 4:
                        codigo_postal = "0" + codigo_postal
                        report["Reparados"]["total"] += 1
                        report["Reparados"]["Monumento"].append({
                            "linea": counter,
                            "nombre": nameConstructor,
                            "motivo": "Codigo postal reparado añadiendo un 0 inicial"
                        })
                        
                    elif len(codigo_postal) != 5 or not codigo_postal.isdigit():
                        report["Descartados"]["total"] += 1
                        report["Descartados"]["Monumento"].append({
                            "linea": counter,
                            "nombre": nameConstructor,
                            "motivo": "Codigo postal invalido."
                        })
                        continue

                    first_two_digits = int(codigo_postal[:2])
                    if first_two_digits > 52:
                        report["Descartados"]["total"] += 1
                        report["Descartados"]["Monumento"].append({
                            "linea": counter,
                            "nombre": nameConstructor,
                            "motivo": "Codigo postal fuera de rango."
                        })
                        continue
                else:
                    report["Descartados"]["total"] += 1
                    report["Descartados"]["Monumento"].append({
                            "linea": counter,
                            "nombre": nameConstructor,
                            "motivo": "Falta codigo postal."
                        })
                    continue    

                # Crear monumento
                direccion = item.get("address")
                latitud = item.get("latwgs84")

                valor_float_lat = float(latitud)
                parte_entera_lat = int(valor_float_lat)
                
                longitud = item.get("lonwgs84")

                valor_float_lon = float(longitud)
                parte_entera_lon = int(valor_float_lon)

                
                if latitud == '':
                    report["Descartados"]["total"] += 1
                    report["Descartados"]["Monumento"].append({
                            "linea": counter,
                            "nombre": nameConstructor,
                            "motivo": "Falta la latitud."
                        })
                    continue
                elif not(-180 <= parte_entera_lat <= 180):
                    report["Descartados"]["total"] += 1
                    report["Descartados"]["Monumento"].append({
                            "linea": counter,
                            "nombre": nameConstructor,
                            "motivo": "Latitud fuera de rango."
                        })
                    continue
                elif longitud == '' or None:
                    report["Descartados"]["total"] += 1
                    report["Descartados"]["Monumento"].append({
                            "linea": counter,
                            "nombre": nameConstructor,
                            "motivo": "Falta la longitud."
                        })
                    continue
                elif not (-180 <= parte_entera_lon <= 180):
                    report["Descartados"]["total"] += 1
                    report["Descartados"]["Monumento"].append({
                            "linea": counter,
                            "nombre": nameConstructor,
                            "motivo": "Longitud fuera de rango."
                        })
                    continue

                report["Registrados"]["Monumentos"].append({
                    "nombre": nameConstructor,
                    "tipo": monumentTypeConstructor,
                    "direccion": direccion,
                    "codigo_portal": codigo_postal,
                    "longitud": longitud,
                    "latitud": latitud,
                    "descripción": item.get("documentDescription"),
                    "en_localidad": localidadNameConstructor
                })

                report["Registrados"]["count"] += 1

            except Exception as e:
                report["Descartados"]["total"] += 1
                report["Descartados"]["Monumento"].append({
                            "linea": counter,
                            "nombre": nameConstructor,
                            "motivo": f"Error inesperado: {str(e)}."
                        })

        
        return JsonResponse(report)
    else:
        return JsonResponse({"error": "Method not allowed."}, status=405)