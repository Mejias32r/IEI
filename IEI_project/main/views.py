from django.shortcuts import render
from django.db import connection
from django.http import JsonResponse
from django.db import transaction
from .models import Provincia, Localidad, Monumento
from django.views.decorators.csrf import csrf_exempt
import requests
import json
import unicodedata
# Create your views here.

def ventana_carga(request):
    return render(request, 'ventana_carga/cargar.html')

@csrf_exempt
def vaciar_almacen_datos(request):
    if request.method == "DELETE":
            try:
                with transaction.atomic():
                    # Borrar registros en orden inverso a las relaciones
                    Monumento.objects.all().delete()
                    Localidad.objects.all().delete()
                    Provincia.objects.all().delete()
                    
                    # Reiniciar IDs
                    reset_ids("app_monumento")
                    reset_ids("app_localidad")
                    reset_ids("app_provincia")
                
                return JsonResponse({"status": "success", "message": "La base de datos ha reiniciada correctamente."}, status = 200)
            except Exception as e:
                return JsonResponse({"status": "error", "message": f"Ocurrió un error: {str(e)}"}, status = 500)
    else:
        return JsonResponse({"status": "error", "message": "Método no permitido. Usa DELETE."}, status = 405)


@csrf_exempt
def cargar_almacen_datos(request):
    if request.method == 'POST':
        method_response = ""
        report1 = {}
        report2 = {}
        report3 = {}
        request_data = json.loads(request.body)
        if 'castilla-Leon' not in request_data or 'comunidad-Valenciana' not in request_data or 'euskadi'not in request_data:
            return JsonResponse({"status": "error", "message": "Falta algun check por pasar"}, status = 400)
        else:
            if request_data['castilla-Leon'] == True:
                url = 'http://127.0.0.1:8001/extractor'
                headers = {'Content-Type': 'application/json'}
                response = requests.get(url, headers=headers)   
                if response.status_code == 200:        
                    datos = response.json()
                    report1 = datos
                    procesar_datos(datos)
                else:
                    return JsonResponse({"status": "error", "message": "Error al cargar los datos de Castilla y León"}, status = 500) 
            if request_data['comunidad-Valenciana'] == True:
                url = 'http://127.0.0.1:8002/extractor'
                headers = {'Content-Type': 'application/json'}
                response = requests.get(url, headers=headers)   
                if response.status_code == 200:        
                    datos = response.json()
                    report2 = datos
                    procesar_datos(datos)
                else:
                    return JsonResponse({"status": "error", "message": "Error al cargar los datos de la Comunidad Valernciana"}, status = 500) 
            if request_data['euskadi'] == True:
                url = 'http://127.0.0.1:8003/extractor'
                headers = {'Content-Type': 'application/json'}
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    datos = response.json()
                    report3 = datos
                    procesar_datos(datos)
                else:
                    return JsonResponse({"status": "error", "message": "Error al cargar los datos de Euskadi"}, status = 500)
            return JsonResponse(
                {"status": "success",
                 "message": "Almacen de datos cargado correctamente",
                  "informe": [report1, report2, report3]
                },
                  status = 200)
    else:
        return JsonResponse({"status": "error", "message": "Método no permitido. Usa POST"}, status = 405)


def procesar_datos(datos):
    provincias_data = datos.get('Registrados', {}).get('Provincias', [])
    procesar_provincias(provincias_data)
    localidades_data = datos.get('Registrados', {}).get('Localidades', [])
    procesar_localidades(localidades_data)
    monumentos_data = datos.get('Registrados', {}).get('Monumentos', [])
    procesar_monumentos(monumentos_data)

def procesar_provincias(provincias_data):
    for provincia in provincias_data:
        nombre = provincia.get('nombre')
        if not Provincia.objects.filter(nombre=nombre).exists():
            Provincia.objects.create(nombre=nombre)

def procesar_localidades(localidades_data):
    for localidad in localidades_data:
        nombre = localidad.get('nombre')
        en_provincia_nombre = localidad.get('en_provincia')
        
        # Buscar la provincia asociada
        try:
            provincia = Provincia.objects.get(nombre=en_provincia_nombre)
        except Provincia.DoesNotExist:
            print(f"Provincia '{en_provincia_nombre}' no encontrada. Saltando localidad '{nombre}'.")
            continue
        # Verificar si la localidad ya existe
        if not Localidad.objects.filter(nombre=nombre, en_provincia=provincia).exists():
            Localidad.objects.create(nombre=nombre, en_provincia=provincia)

def procesar_monumentos(monumentos_data):
    for monumento in monumentos_data:
        nombre = monumento.get('nombre')
        direccion = monumento.get('direccion')
        codigo_postal = monumento.get('codigo_portal')
        longitud = monumento.get('longitud')
        latitud = monumento.get('latitud')
        descripcion = monumento.get('descripción', '')
        en_localidad_nombre = monumento.get('en_localidad')
        
        # Buscar la localidad asociada
        try:
            localidad = Localidad.objects.get(nombre=en_localidad_nombre)
        except Localidad.DoesNotExist:
            print(f"Localidad '{en_localidad_nombre}' no encontrada. Saltando monumento '{nombre}'.")
            continue
        
        # Verificar si el monumento ya existe
        if not Monumento.objects.filter(nombre=nombre, direccion=direccion, en_localidad=localidad).exists():
            Monumento.objects.create(
                nombre=nombre,
                tipo=monumento.get('tipo', 'OT'),  # Si no hay tipo, asigna 'Otros' por defecto
                direccion=direccion,
                codigo_postal=codigo_postal,
                longitud=longitud,
                latitud=latitud,
                descripcion=descripcion,
                en_localidad=localidad
            )

def reset_ids(tabla):
    with connection.cursor() as cursor:
        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{tabla}';")

def get_monumentos(request):
    if request.method == 'GET':
        response = []
        monumentos = Monumento.objects.all()
        if monumentos.count() == 0:
            return JsonResponse({"status": "error", "message": "No hay datos en la base de datos"}, status=404)
        else:
            for monumento in monumentos:
                response.append({
                    "table":{
                        "name": monumento.nombre,
                        "type": monumento.tipo,
                        "addres": monumento.direccion,
                        "locality": monumento.en_localidad.nombre,
                        "postalCode": monumento.codigo_postal,
                        "provincie": monumento.en_localidad.en_provincia.nombre,
                        "description": monumento.descripcion
                    },
                    "coordinates":[monumento.longitud, monumento.latitud],
                })
        return JsonResponse(response,safe = False ,status=200, json_dumps_params={'ensure_ascii': False})
    else:
        return JsonResponse({"status": "error", "message": "Método no permitido. Usa GET"}, status=405)
    
def get_monumentos_filtered(request):
    if request.method == 'GET':
        provincia = request.GET.get('provincia')
        localidad = request.GET.get('localidad')
        tipo = request.GET.get('tipo')
        codigo_postal = request.GET.get('codigo_postal')
        response = []

        # Inicializa el queryset de los monumentos
        monumentos = Monumento.objects.all()

        if provincia:
            provincia_normalizada = normalize_text(provincia)
            monumentos = [
                m for m in monumentos
                if provincia_normalizada in split_and_normalize(m.en_localidad.en_provincia.nombre)
            ]
            print(f"Filtro provincia normalizado: {provincia_normalizada}")

        # Filtro por localidad
        if localidad:
            localidad_normalizada = normalize_text(localidad)
            monumentos = [
                m for m in monumentos
                if localidad_normalizada in split_and_normalize(m.en_localidad.nombre)
            ]
            print(f"Filtro localidad normalizado: {localidad_normalizada}")

        # Filtro por tipo
        if tipo:
            tipo_normalizado = normalize_text(tipo)
            monumentos = [
                m for m in monumentos
                if normalize_text(m.tipo) == tipo_normalizado
            ]
            print(f"Filtro tipo normalizado: {tipo_normalizado}")

        # Filtro por código postal
        if codigo_postal:
            monumentos = [
                m for m in monumentos
                if m.codigo_postal == codigo_postal
            ]
            print(f"Filtro código postal: {codigo_postal}")

        # Si no hay resultados, devuelve un error
        if not monumentos:
            return JsonResponse(
                {"status": "error", "message": "No se encontraron monumentos que coincidan con los filtros aplicados"},
                status=404
            )

        # Construir la respuesta
        for monumento in monumentos:
            response.append({
                "table": {
                    "name": monumento.nombre,
                    "type": monumento.tipo,
                    "addres": monumento.direccion,
                    "locality": monumento.en_localidad.nombre,
                    "postalCode": monumento.codigo_postal,
                    "provincie": monumento.en_localidad.en_provincia.nombre,
                    "description": monumento.descripcion
                },
                "coordinates": [monumento.longitud, monumento.latitud],
            })

        return JsonResponse(response, safe=False, status=200, json_dumps_params={'ensure_ascii': False})

    else:
        return JsonResponse({"status": "error", "message": "Método no permitido. Usa GET"}, status=405)
    

def normalize_text(text):
    """Normaliza el texto eliminando tildes y convirtiendo a minúsculas."""
    normalized = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    ).lower()
    print(f"Original: {text} | Normalizado: {normalized}")
    return normalized

def split_and_normalize(text):
    """Divide un texto compuesto por '-' o '/' y normaliza cada parte."""
    parts = [part for separator in ['-', '/'] for part in text.split(separator)]
    return [normalize_text(part) for part in parts]