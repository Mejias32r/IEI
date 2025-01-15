from django.urls import path
from . import views
from rest_framework import permissions
from rest_framework.permissions import AllowAny
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
    openapi.Info(
        title="API Base de Datos Monumentos",
        default_version='v1',
        description="API para la gestión de la base de datos de monumentos",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('ventana-carga/', views.ventana_carga, name="ventana_carga"),
    path('vaciar-almacen-datos/', views.vaciar_almacen_datos, name = "vaciar-almacen-datos"),
    path('cargar-almacen-datos/', views.cargar_almacen_datos, name = "cagar-almacen-datos"),
    path('get-monumentos', views.get_monumentos, name = "obtener-monumentos"),
    path('get-monumentos/', views.get_monumentos_filtered, name="obtener-monumento-filtrado"),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]