from django.shortcuts import render
from django.http import JsonResponse
from django.http import JsonResponse
from main.models import Monumento
from main.models import Localidad
from main.models import Provincia
from IEI_project.settings import FUENTES_DE_DATOS_DIR
from .models import Provincia, Localidad, Monumento, Tipo
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
            return tipo_enum  # Devuelve el valor del enum
    return Tipo.OTROS  # Devuelve "OT" si no encuentra coincidencias

# Función principal que procesa el archivo JSON
def conversor_json(request):
    json_path = f"{FUENTES_DE_DATOS_DIR}/monumentos_pais_vasco.json"

    try:
        with open(json_path, "r", encoding="utf-8") as file:
            monumentos = json.load(file)
    except FileNotFoundError:
        return render(request, "error.html", {"error": "Archivo JSON no encontrado."})
    except json.JSONDecodeError:
        return render(request, "error.html", {"error": "Error al decodificar el archivo JSON."})

    report = {
        "Total": {"count": 0},  # Contador total de monumentos procesados
        "Registrados": {"count": 0},  # Monumentos registrados correctamente
        "Descartados": {"count": 0, "razones": []},  # Monumentos descartados y sus razones
        "Reparados": {"count": 0, "detalles": []},  # Monumentos con datos corregidos
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
                report["Descartados"]["razones"].append("Falta el minicipio")
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
            if codigo_postal is not None:    
                if len(codigo_postal) == 4:
                    report["Reparados"]["count"] += 1
                    report["Reparados"]["detalles"].append("Código postal reparado añadiendo un 0 inicial.")
                    codigo_postal = "0" + codigo_postal
                elif len(codigo_postal) != 5 or not codigo_postal.isdigit():
                    report["Descartados"]["count"] += 1
                    report["Descartados"]["razones"].append("Código postal invalido")
                    continue

                first_two_digits = int(codigo_postal[:2])
                if first_two_digits > 52:
                    report["Descartados"]["count"] += 1
                    report["Descartados"]["razones"].append("Código postal fuera de rango.")
                    continue
            else:
                report["Descartados"]["count"] += 1
                report["Descartados"]["razones"].append("Falta el código postal.")
                continue    

            # Crear o actualizar monumento
            direccion = item.get("address")
            descripcion = item.get("documentDescription")
            latitud = item.get("latwgs84")
            longitud = item.get("lonwgs84")
            if direccion is None:
                report["Descartados"]["count"] += 1
                report["Descartados"]["razones"].append("Falta la direccion")
                continue
            elif descripcion is None:
                report["Descartados"]["count"] += 1
                report["Descartados"]["razones"].append("Falta la direccion")
                continue
            elif latitud is None:
                report["Descartados"]["count"] += 1
                report["Descartados"]["razones"].append("Falta la direccion")
                continue
            elif longitud is None:
                report["Descartados"]["count"] += 1
                report["Descartados"]["razones"].append("Falta la direccion")
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
