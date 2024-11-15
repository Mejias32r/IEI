from django.shortcuts import render

def cargar_ventana_principal(request):
    return render(request, 'ventana_principal/ventana_principal.html')