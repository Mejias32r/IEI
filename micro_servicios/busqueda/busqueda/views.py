from django.http import JsonResponse
from django.shortcuts import render
import requests


def cargar_venta_busqueda(request):
    return render(request, 'busqueda.html')

def cargar_filtrado(request):
    print("cargar filtrado llamado")

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