from django.shortcuts import render
from django.db import connection
from django.http import JsonResponse
from django.db import transaction
from .models import Provincia, Localidad, Monumento
from django.views.decorators.csrf import csrf_exempt
import requests
import json
import unicodedata
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view
# Create your views here.

@swagger_auto_schema(
    method='GET',
    operation_summary="Extrae HTML",
    operation_description="Extrae HTML para cargarlo.",
    responses={
        200:""
    },
)
@api_view(['GET'])
def ventana_carga(request):
    return render(request, 'ventana_carga/cargar.html')

@swagger_auto_schema(
    method='DELETE',
    operation_summary="Vacía la base de datos de monumentos.",
    operation_description="Vacía la base de datos de monumentos con los datos de todos o alguno de los extractores.",
    responses={
        200: openapi.Response(
            description="La base de datos ha reiniciada correctamente.",
            examples={
                "application/json": {
                    "status": "success", "message": "La base de datos ha reiniciada correctamente."
                }
            },
        ),
        500: openapi.Response(
            description="Ocurrió un error: (error)",
            examples={
                "application/json": {
                    "status": "error", "message": f"Ocurrió un error: (error))"
                }
            },
        ),
        405: openapi.Response(
            description="Método no permitido. Usa DELETE.",
            examples={
                "application/json": {
                    "status": "error", "message": "Método no permitido. Usa DELETE."
                }
            },
        ),
    },
)
@api_view(['DELETE'])
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

cargar_almacen_datos_post_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'castilla-Leon': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Checked status for Castilla y León"),
        'comunidad-Valenciana': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Checked status for Comunidad Valenciana"),
        'euskadi': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Checked status for Euskadi"),
    },
    required=['castilla-Leon', 'comunidad-Valenciana', 'euskadi'],  # Optional: adjust based on whether you want them required
)

@swagger_auto_schema(
    method='POST',
    operation_summary="Rellena la base de datos.",
    operation_description="Rellena la base de datos según las fuentes de datos seleccionadas en el cuerpo de la petición.",
    responses={
        200: openapi.Response(
            description="La base de datos ha reiniciada correctamente.",
            examples={
                "application/json": {
                    "nombre": "Wrapper_XML",
                    "total": {
                    "count": 123
                    },
                    "Registrados": {
                    "count": 123,
                    "Provincias": [
                        {
                        "nombre": "Ávila"
                        },
                        "...",
                    ],
                    "Localidades": [
                        {
                        "nombre": "Raso (El)",
                        "en_provincia": "Ávila"
                        },
                        "...",
                    ],
                    "Monumentos": [
                        {
                        "nombre": "Risco La Zorrera",
                        "tipo": "Yacimientos arqueológico",
                        "direccion": "Risco La Zorrera, Candeleda",
                        "codigo_portal": "05489",
                        "longitud": "-5.339664",
                        "latitud": "40.170041",
                        "descripción": "Descubierto en 1986 consta de dos paneles verticales y un tercero horizontal que cubre los anteriores. Pueden distinguirse tres fases de ejecuci&oacute;n, predominando en la primera los trazos de color rojo, en la segunda destaca una figura de forma humana, y la tercera incluye figuras animales y humanas alargadas.Se ha interpretado como la representaci&oacute;n de un templo o altar. Est&aacute; protegido por una verja.",
                        "en_localidad": "Raso (El)"
                        },
                        "...",
                    ]
                    },
                    "Descartados": {
                    "total": 123,
                    "Provincias": [
                        {
                        "linea": 6,
                        "nombre": "Salamanca",
                        "motivo": "Provincia repetida."
                        },
                        "...",
                    ],
                    "Localidades": [
                        {
                        "linea": 13,
                        "nombre": "Íscar",
                        "motivo": "Localidad repetida."
                        },
                        "...",
                    ],
                    "Monumento": [
                        {
                        "linea": 3,
                        "nombre": "Monasterio de Santa María de Retuerta",
                        "motivo": "Faltan coordenadas."
                        },
                        "...",
                    ]
                    },
                    "Reparados": {
                    "total": 123,
                    "Provincias": [],
                    "Localidades": [],
                    "Monumento": [
                        {
                        "linea": 1,
                        "nombre": "Risco La Zorrera",
                        "motivo": "Código postal reparado añadiendo un 0 inicial."
                        },
                        "...",
                    ]
                    }
                }
            },
        ),
        500: openapi.Response(
            description="Error al cargar los datos de (Comunidad Autónoma)",
            examples={
                "application/json": {
                    "status": "error", "message": "Error al cargar los datos de Euskadi"
                }
            },
        ),
        405: openapi.Response(
            description="Método no permitido. Usa POST.",
            examples={
                "application/json": {
                    "status": "error", "message": "Método no permitido. Usa POST"
                }
            },
        ),
    },
    request_body=cargar_almacen_datos_post_body
)
@api_view(['POST'])
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


# Swagger Schema for get_monumentos
@swagger_auto_schema(
    method='GET',
    operation_summary="Retrieve all monuments",
    operation_description="Fetch all monuments.",
    responses={
        200: openapi.Response(
            description="List of monuments",
            examples={
                "application/json": {
                    "table":{
                        "name": "nombre",
                        "type": "tipo",
                        "addres": "direccion",
                        "locality": "localidad",
                        "postalCode": "codigo postal",
                        "provincie": "provincia",
                        "description": "descripcion"
                    },
                    "coordinates":["longitud", "latitud"],
                }
            },
        ),
        405: openapi.Response(
            description="Método no permitido. Usa GET.",
            examples={
                "application/json": {
                    "status": "error", "message": "Método no permitido. Usa GET."
                }
            },
        ),
        404: openapi.Response(
            description="No hay datos en la base de datos.",
            examples={
                "application/json": {
                    "status": "error", "message": "No hay datos en la base de datos"
                }
            },
        ),
        404: openapi.Response(
            description="No hay datos en la base de datos.",
            examples={
                "application/json": {
                    "status": "error", "message": "No hay datos en la base de datos"
                }
            },
        ),
    },
)
@api_view(['GET'])
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

# Define the query parameters for the GET method
get_monumentos_filtered_query_params = [
    openapi.Parameter('tipo', openapi.IN_QUERY, description="Filter by type of monument", type=openapi.TYPE_STRING, required=False),
    openapi.Parameter('provincia', openapi.IN_QUERY, description="Filter by province", type=openapi.TYPE_STRING, required=False),
    openapi.Parameter('localidad', openapi.IN_QUERY, description="Filter by locality", type=openapi.TYPE_STRING, required=False),
    openapi.Parameter('codigo_postal', openapi.IN_QUERY, description="Filter by postal code", type=openapi.TYPE_STRING, required=False),
]

# Swagger Schema for get_monumentos_filtered
@swagger_auto_schema(
    method='GET',
    operation_summary="Retrieve monuments with optional filters",
    operation_description="Fetch monuments based on optional filters. If no filters are provided, all monuments will be returned.",
    responses={
        200: openapi.Response(
            description="List of monuments",
            examples={
                "application/json": {
                    "table":{
                        "name": "nombre",
                        "type": "tipo",
                        "addres": "direccion",
                        "locality": "localidad",
                        "postalCode": "codigo postal",
                        "provincie": "provincia",
                        "description": "descripcion"
                    },
                    "coordinates":["longitud", "latitud"],
                }
            },
        ),
        405: openapi.Response(
            description="Método no permitido. Usa GET.",
            examples={
                "application/json": {
                    "status": "error", "message": "Método no permitido. Usa GET."
                }
            },
        ),
        404: openapi.Response(
            description="No hay datos en la base de datos.",
            examples={
                "application/json": {
                    "status": "error", "message": "No hay datos en la base de datos"
                }
            },
        ),
        404: openapi.Response(
            description="No se encontraron monumentos que coincidan con los filtros aplicados.",
            examples={
                "application/json": {
                    "status": "error", "message": "No se encontraron monumentos que coincidan con los filtros aplicados"
                }
            },
        ),
    },
    manual_parameters=get_monumentos_filtered_query_params
)
@api_view(['GET'])
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