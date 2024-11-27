from django.urls import path
from . import views

urlpatterns = [
    path('', views.conversor_json, name="ventana_carga_json"),
]