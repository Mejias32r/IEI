from django.shortcuts import render
from django.db import connection
from django.http import JsonResponse
from django.db import transaction
from .models import Provincia, Localidad, Monumento
from django.views.decorators.csrf import csrf_exempt
import requests
import json
# Create your views here.

def ventana_carga(request):
    return render(request, 'ventana_carga/cargar.html')

@csrf_exempt
def vaciar_almacen_datos(request):
    if request.method == "POST":
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
        return JsonResponse({"status": "error", "message": "Método no permitido. Usa POST."}, status = 405)


@csrf_exempt
def cargar_almacen_datos(request):
    if request.method == 'POST':
        method_response = ""
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
                    procesar_datos(datos)
                else:
                    return JsonResponse({"status": "error", "message": "Error al cargar los datos de Castilla y León"}, status = 500) 
        
            return JsonResponse(
                {"status": "success",
                 "message": "Almacen de datos cargado correctamente",
                  "informe": datos
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
        direccion = monumento.get('dirección')
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
        print("accedido al otro método")
        response = [ 
            
        ]
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
