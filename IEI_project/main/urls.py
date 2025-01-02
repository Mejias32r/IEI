from django.urls import path
from . import views

urlpatterns = [
    path('ventana-carga/', views.ventana_carga, name="ventana_carga"),
    path('vaciar-almacen-datos/', views.vaciar_almacen_datos, name = "vaciar-almacen-datos"),
    path('cargar-almacen-datos/', views.cargar_almacen_datos, name = "cagar-almacen-datos"),
    path('get-monumentos/', views.get_monumentos, name = "obtener-monumentos"),
]
