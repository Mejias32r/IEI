from django.shortcuts import render
from django.http import JsonResponse
from django.http import JsonResponse
from main.models import Monumento
from main.models import Localidad
from main.models import Provincia
from main.models import Tipo
from IEI_project.settings import FUENTES_DE_DATOS_DIR
import json

# Diccionario que mapea los nombres de monumentos a los valores del enum `Tipo`
TIPOS_MONUMENTOS = {
    Tipo.YACIMIENTO_ARQUEOLOGICO: ["yacimiento"],
    Tipo.IGLESIA_ERMITA: ["iglesia", "ermita", "catedral", "parroquia", "basílica", "santuario"],
    Tipo.MONASTERIO_CONVENTO: ["monasterio", "convento"],
    Tipo.CASTILLO_FORTALEZA_TORRE: ["castillo", "fuerte", "torre", "muralla"],
    Tipo.EDIFICIO_SINGULAR: ["palacio", "casa", "edificio", "monumento"],
    Tipo.PUENTE: ["puente", "viaducto"],
}

# Función para determinar el tipo basado en las palabras clave
def determinar_tipo(nombre):

    nombre_lower = nombre.lower()
    for tipo_enum, palabras_clave in TIPOS_MONUMENTOS.items():
        if any(palabra in nombre_lower for palabra in palabras_clave):
            return tipo_enum 
    return Tipo.OTROS 

def manejar_claves_duplicadas(pares):
    "Devuelve un diccionario con solo la primera aparición de cada clave."
    resultado = {}
    for clave, valor in pares:
        if clave not in resultado:
            resultado[clave] = valor
    return resultado

# Función principal que procesa el archivo JSON
def conversor_json(request):
    json_path = f"{FUENTES_DE_DATOS_DIR}/monumentos_pais_vasco_entrega.json"

    try:
        with open(json_path, "r", encoding="utf-8") as file:
            monumentos = json.load(file, object_pairs_hook=manejar_claves_duplicadas)
    except FileNotFoundError:
        return render(request, "error.html", {"error": "Archivo JSON no encontrado."})
    except json.JSONDecodeError:
        return render(request, "error.html", {"error": "Error al decodificar el archivo JSON."})

    report = {
        "Total": {"count": 0},  
        "Registrados": {"count": 0},  
        "Descartados": {"count": 0, "razones": []},  
        "Reparados": {"count": 0, "detalles": []},  
    }

    for item in monumentos:
        try:

            report["Total"]["count"] += 1

            if not item.get("territory"):
                report["Descartados"]["count"] += 1
                report["Descartados"]["razones"].append("Falta el territorio")
                continue
            elif (not item.get("municipality")):
                report["Descartados"]["count"] += 1
                report["Descartados"]["razones"].append("Falta el municipio")
                continue
            elif(not item.get("documentName")):
                report["Descartados"]["count"] += 1
                report["Descartados"]["razones"].append("Falta el nombre del monumento")
                continue
                

            # Crear o buscar provincia
            provincia, _ = Provincia.objects.get_or_create(nombre=item.get("territory"))

            # Crear o buscar localidad
            localidad, _ = Localidad.objects.get_or_create(
                nombre=item.get("municipality"),
                en_provincia=provincia
            )

            # Determinar el tipo de monumento
            tipo = determinar_tipo(item.get("documentName"))

            # Validar código postal
            codigo_postal = item.get("postalCode")
            if codigo_postal is not '':    
                if len(codigo_postal) == 4:
                    report["Reparados"]["count"] += 1
                    report["Reparados"]["detalles"].append("Codigo postal reparado añadiendo un 0 inicial.")
                    codigo_postal = "0" + codigo_postal
                elif len(codigo_postal) != 5 or not codigo_postal.isdigit():
                    report["Descartados"]["count"] += 1
                    report["Descartados"]["razones"].append("Codigo postal invalido")
                    continue

                first_two_digits = int(codigo_postal[:2])
                if first_two_digits > 52:
                    report["Descartados"]["count"] += 1
                    report["Descartados"]["razones"].append("Codigo postal fuera de rango.")
                    continue
            else:
                report["Descartados"]["count"] += 1
                report["Descartados"]["razones"].append("Falta el codigo postal.")
                continue    

            # Crear o actualizar monumento
            direccion = item.get("address")
            descripcion = item.get("documentDescription")
            latitud = item.get("latwgs84")

            valor_float_lat = float(latitud)
            parte_entera_lat = int(valor_float_lat)
            
            longitud = item.get("lonwgs84")

            valor_float_lon = float(longitud)
            parte_entera_lon = int(valor_float_lon)
            if direccion is '':
                report["Descartados"]["count"] += 1
                report["Descartados"]["razones"].append("Falta la direccion")
                continue
            elif descripcion is '':
                report["Descartados"]["count"] += 1
                report["Descartados"]["razones"].append("Falta la descripcion")
                continue
            elif latitud is '':
                report["Descartados"]["count"] += 1
                report["Descartados"]["razones"].append("Falta la latitud")
                continue
            elif not(-180 <= parte_entera_lat <= 180):
                report["Descartados"]["count"] += 1
                report["Descartados"]["razones"].append("Latitud fuera de rango")
                continue
            elif longitud is '' or None:
                report["Descartados"]["count"] += 1
                report["Descartados"]["razones"].append("Falta la longitud")
                continue
            elif not (-180 <= parte_entera_lon <= 180):
                report["Descartados"]["count"] += 1
                report["Descartados"]["razones"].append("Longitud fuera de rango")
                continue

            Monumento.objects.update_or_create(
                nombre=item.get("documentName"),
                en_localidad=localidad,
                defaults={
                    "tipo": tipo,
                    "direccion": item.get("address"),
                    "codigo_postal": codigo_postal,
                    "latitud": item.get("latwgs84"),
                    "longitud": item.get("lonwgs84"),
                    "descripcion": item.get("documentDescription"),
                }
            )

            report["Registrados"]["count"] += 1

        except Exception as e:
            report["Descartados"]["count"] += 1
            report["Descartados"]["razones"].append(f"Error inesperado: {str(e)}.")

    
    return JsonResponse(report)
