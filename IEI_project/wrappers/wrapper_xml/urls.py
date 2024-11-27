from django.urls import path
from . import views

urlpatterns = [
    path('', views.transform_xml_to_json, name="ventana_carga_xml"),
]