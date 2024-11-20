from django.urls import path
from . import views

urlpatterns = [
    path('', views.readCSVtoJson, name="ventana_carga")
]