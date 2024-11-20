from django.urls import path
from . import views

urlpatterns = [
    path('ventana-carga/', views.ventana_carga, name="ventana_carga")
]
