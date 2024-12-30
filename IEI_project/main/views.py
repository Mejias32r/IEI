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
        request_data = json.loads(request.body)
        if 'castilla-Leon' not in request_data or 'comunidad-Valenciana' not in request_data or 'euskadi'not in request_data:
            return JsonResponse({"status": "error", "message": "Falta algun check por pasar"}, status = 400)
        else:
            print(request_data)
            if request_data['castilla-Leon'] == True:
                url = 'http://127.0.0.1:8001/extractor'
                headers = {'Content-Type': 'application/json'}
                response = requests.get(url, headers=headers)
                print(response)
                if response.status_code == 200:        
                    datos = response.json()
                    print(datos)
                else:
                    return JsonResponse({"status": "error", "message": "Error al cargar los datos de Castilla y León"}, status = 500) 
        
            return JsonResponse({"status": "success","message": "Almacen de datos cargado correctamente"}, status = 200)
    else:
        return JsonResponse({"status": "error", "message": "Método no permitido. Usa POST"}, status = 405)


def reset_ids(tabla):
    with connection.cursor() as cursor:
        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{tabla}';")
