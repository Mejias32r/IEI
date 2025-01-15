from django.http import JsonResponse
from django.shortcuts import render
import requests
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view

@swagger_auto_schema(
    method='GET',
    operation_summary="Extrae HTML",
    operation_description="Extrae HTML para cargarlo.",
    responses={
        200:""
    },
)
@api_view(['GET'])
def cargar_venta_busqueda(request):
    return render(request, 'busqueda.html')

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
def cargar_filtrado(request):
    print("cargar filtrado llamado")

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
def cargar_todos(request):
    print("cargar todos llamado local")
    url = "http://localhost:8080/main/get-monumentos/"
    response = requests.get(url)

    if response.status_code == 200:
        # Convertir la respuesta JSON a un diccionario de Python
        return JsonResponse(response.json(), safe=False)
    else:
        print("Error al recibir")
        print(response.status_code)