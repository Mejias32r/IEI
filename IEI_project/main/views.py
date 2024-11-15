from django.shortcuts import render

# Create your views here.

def ventana_carga(request):
    return render(request, 'ventana_carga/cargar.html')