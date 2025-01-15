from django.shortcuts import render
from django.db import transaction
from django.http import JsonResponse
from .settings import FUENTES_DE_DATOS_DIR
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view

import xml.etree.ElementTree as ET
import html
import json

# Swagger Schema for extractor_xml
@swagger_auto_schema(
    method='GET',
    operation_summary="Extract data from XML",
    operation_description="Reads a XML file and processes the monument data.",
    responses={
        200: openapi.Response(
            description="XML processed successfully",
            examples={
                "application/json": {
                    "nombre": "Wrapper_XML",
                        "total": {"count": 0},
                        "Registrados": {
                            "count": 0,
                            "Provincias": ["..."],
                            "Localidades": ["..."],
                            "Monumentos": ["..."]
                        },
                        "Descartados": {
                            "total": 0,
                            "Provincias": ["..."],
                            "Localidades": ["..."],
                            "Monumento": ["..."]
                        },
                        "Reparados": {
                            "total": 0,
                            "Provincias": ["..."],
                            "Localidades": ["..."],
                            "Monumento": ["..."]
                        }
                }
            },
        ),
        500: "Error processing the XML file",
        405: "Method Not Allowed",
    },
)
@api_view(['GET'])
def extractor_xml(request):
    if request.method == 'GET':
        print(FUENTES_DE_DATOS_DIR)
        # Parse the XML file
        tree = ET.parse(FUENTES_DE_DATOS_DIR + '//monumentos_entrega.xml')
        root = tree.getroot()

        # Initialize the resulting JSON structure and counters
        report = {
            "nombre": "Wrapper_XML",
            "total": {"count": 0},
            "Registrados": {
                "count": 0,
                "Provincias": [],
                "Localidades": [],
                "Monumentos": []
            },
            "Descartados": {
                "total": 0,
                "Provincias": [],
                "Localidades": [],
                "Monumento": []
            },
            "Reparados": {
                "total": 0,
                "Provincias": [],
                "Localidades": [],
                "Monumento": []
            }
        }
        
        counter = 0

        # Iterate through the monuments
        
        for monument in root.findall('monumento'):
            try:
                counter += 1
                report["total"]["count"] += 1
                
                # Map the name
                name = monument.find('nombre')
                nameConstructor = name.text if name is not None else ""
                if existe_monumento(report, nameConstructor):
                    report["Descartados"]["total"] += 1
                    report["Descartados"]["Monumento"].append({
                        "linea": counter,
                        "nombre": nameConstructor,
                        "motivo": "Monumento repetido."
                    })

                # Map the type of monument
                monument_type = monument.find('tipoMonumento')
                if monument_type is not None and monument_type.text is not None:
                    type = monument_type.text
                    if type == "Yacimientos arqueológicos":
                        monumnentTypeConstructor = "Yacimientos arqueológico"
                    elif type == "Iglesias y Ermitas" or type == "Catedrales":
                        monumnentTypeConstructor = "Iglesia-Ermitas"
                    elif type == "Monasterios" or type == "Santuarios" or (type == "Reales Sitios" and ("Monasterio" in nameConstructor or "Convento" in nameConstructor)):
                        monumnentTypeConstructor = "Monasterio-Convento"
                    elif type == "Castillos" or type == "Torres" or type == "Murallas y puertas":
                        monumnentTypeConstructor = "Castillo-Fortaleza-Torre"
                    elif type == "Palacios" or type == "Sinagogas" or type == "Casas Nobles" or (type == "Reales Sitios" and ("Palacio" in nameConstructor)) or type == "Casas Consistoriales":
                        monumnentTypeConstructor = "Edificio singular"
                    elif type == "Puentes":
                        monumnentTypeConstructor = "Puente"
                    elif type == "Otros edificios" or type == "Esculturas" or type == "Hórreos" or type == "Jardín Histórico" or type == "Paraje pintoresco" or type == "Fuentes"  or type == "Molinos" or type == "Otras localidades" or type == "Cruceros" or type == "Plazas Mayores" or type == "Conjunto Etnológico" or type == "Sitio Histórico":
                        monumnentTypeConstructor = "Otros"
                    else:
                        report["Descartados"]["total"] += 1
                        report["Descartados"]["Monumento"].append({
                            "linea": counter,
                            "nombre": nameConstructor,
                            "motivo": f"Tipo de monumento no reconocido: {type}."
                        })
                        continue
                else:
                    report["Descartados"]["total"] += 1
                    report["Descartados"]["Monumento"].append({
                        "linea": counter,
                        "nombre": nameConstructor,
                        "motivo": "Falta el tipo de monumento."
                    })
                    continue

                # Map the address
                street = monument.find('calle')
                municipality = monument.find('./poblacion/municipio')
                if street is not None and municipality is not None and street.text is not None and municipality.text is not None:
                    addressConstructor = f"{street.text}, {municipality.text}"
                elif municipality is not None:
                    addressConstructor = f"Pertenece al municipio {municipality.text}"
                else:
                    addressConstructor = ""

                # Map coordinates
                latitude = monument.find('./coordenadas/latitud')
                longitude = monument.find('./coordenadas/longitud')
                if latitude is not None and longitude is not None and latitude.text is not None and longitude.text is not None:
                    latitudeConstructor = latitude.text.replace('#', '').strip()
                    longitudeConstructor = longitude.text.replace('#', '').strip()
                    if float(longitudeConstructor) > 180 or float(longitudeConstructor) < -180 or float(latitudeConstructor) > 90 or float(latitudeConstructor) < -90:
                        report["Descartados"]["total"] += 1
                        report["Descartados"]["Monumento"].append({
                            "linea": counter,
                            "nombre": nameConstructor,
                            "motivo": "Coordenadas fuera de rango."
                        })
                        continue
                else:
                    report["Descartados"]["total"] += 1
                    report["Descartados"]["Monumento"].append({
                        "linea": counter,
                        "nombre": nameConstructor,
                        "motivo": "Faltan coordenadas."
                    })
                    continue

                # Map the description
                description = monument.find('Descripcion')
                constructionType = monument.find('tipoConstruccion')
                historical_periods = monument.findall('periodoHistorico')
                if description is not None:
                    descriptionConstructor = description.text.strip()
                    descriptionConstructor = descriptionConstructor.replace("\u003Cp align=\"justify\"\u003E", "").replace("\u003C/p\u003E", "").replace("\u003Cp\u003E","").replace("\u003Cbr /\u003E","").replace("\n","")
                else:
                    descriptionConstructor = ""
                    if constructionType is not None:
                        descriptionConstructor += f"Este monumento es un {constructionType.text}"
                        if historical_periods is not None:
                            list_historical_periods = ','.join([period.text for period in historical_periods])
                            descriptionConstructor += f" que pertenece a el/los periodos históricos {list_historical_periods}"
                    descriptionConstructor += "."
                    descriptionConstructor = descriptionConstructor.replace("\u003Cp align=\"justify\"\u003E", "").replace("\u003C/p\u003E", "").replace("\u003Cp\u003E","").replace("\u003Cbr /\u003E","").replace("\n","")

                # Map the province
                province = monument.find('./poblacion/provincia')
                if province is not None and province.text is not None:
                    provinceConstructor = province.text
                    if existe_provincia(report, province.text):
                        report["Descartados"]["Provincias"].append({
                            "linea": counter,
                            "nombre": provinceConstructor,
                            "motivo": "Provincia repetida."
                        })
                    else:
                        report["Registrados"]["Provincias"].append({
                            "nombre": provinceConstructor
                        })
                else:
                    report["Descartados"]["total"] += 1
                    report["Descartados"]["Provincias"].append({
                        "linea": counter,
                        "nombre": nameConstructor,
                        "motivo": "Falta el nombre."
                    })
                    report["Descartados"]["Monumento"].append({
                        "linea": counter,
                        "nombre": nameConstructor,
                        "motivo": "Falta la localidad."
                    })
                    continue

                # Map the localidad
                localidad = monument.find('./poblacion/localidad')
                if localidad is not None and localidad.text is not None:
                    localidadName = localidad.text
                    if existe_localidad(report, localidadName):
                        report["Descartados"]["Localidades"].append({
                            "linea": counter,
                            "nombre": localidadName,
                            "motivo": "Localidad repetida."
                        })
                    else:
                        report["Registrados"]["Localidades"].append({
                            "nombre": localidadName,
                            "en_provincia": provinceConstructor
                        })
                else:
                    report["Descartados"]["total"] += 1
                    report["Descartados"]["Localidades"].append({
                        "linea": counter,
                        "nombre": nameConstructor,
                        "motivo": "Falta el nombre."
                    })
                    report["Descartados"]["Monumento"].append({
                        "linea": counter,
                        "nombre": nameConstructor,
                        "motivo": "Falta la localidad."
                    })
                    continue
                
                # Map the postal code
                codigoPostal = monument.find('codigoPostal')
                if codigoPostal is not None and codigoPostal.text is not None:
                    if len(codigoPostal.text) == 5:
                        codigoPostalConstructor = codigoPostal.text
                    elif len(codigoPostal.text) == 4:
                        report["Reparados"]["total"] += 1
                        report["Reparados"]["Monumento"].append({
                            "linea": counter,
                            "nombre": nameConstructor,
                            "motivo": "Código postal reparado añadiendo un 0 inicial."
                        })
                        codigoPostalConstructor = "0" + codigoPostal.text
                    else:
                        report["Descartados"]["total"] += 1
                        report["Descartados"]["Monumento"].append({
                            "linea": counter,
                            "nombre": nameConstructor,
                            "motivo": "Código postal inválido."
                        })
                        continue
                    first_two_digits = int(codigoPostalConstructor[:2])
                    if first_two_digits > 52:
                        report["Descartados"]["total"] += 1
                        report["Descartados"]["Monumento"].append({
                            "linea": counter,
                            "nombre": nameConstructor,
                            "motivo": "Código postal fuera de rango."
                        })
                        continue
                else:
                    report["Descartados"]["total"] += 1
                    report["Descartados"]["Monumento"].append({
                        "linea": counter,
                        "nombre": nameConstructor,
                        "motivo": "Falta el código postal."
                    })
                    continue 

                # Add the monument's data to the result JSON
                report["Registrados"]["Monumentos"].append({
                    "nombre": nameConstructor,
                    "tipo": monumnentTypeConstructor,
                    "direccion": addressConstructor,
                    "codigo_portal": codigoPostalConstructor,
                    "longitud": longitudeConstructor,
                    "latitud": latitudeConstructor,
                    "descripción": descriptionConstructor,
                    "en_localidad": localidadName
                })
                
                report["Registrados"]["count"] += 1
                
            except Exception as e:
                report["Descartados"]["total"] += 1
                report["Descartados"]["Monumento"].append({
                    "linea": counter,
                    "nombre": str(e),
                    "motivo": f"Error inesperado: {str(e)}."
                })

        return JsonResponse(report)
    else:
        return JsonResponse({"error": "Method not allowed."}, status=405)


def existe_monumento(report, nombre):
    # Recorrer la lista de monumentos para buscar el nombre
    for monumento in report["Registrados"]["Monumentos"]:
        if monumento.get("nombre", "").lower() == nombre.lower():
            return True
    return False

def existe_localidad(report, nombre):
    # Recorrer la lista de monumentos para buscar el nombre
    for monumento in report["Registrados"]["Localidades"]:
        if monumento.get("nombre", "").lower() == nombre.lower():
            return True
    return False

def existe_provincia(report, nombre):
    # Recorrer la lista de monumentos para buscar el nombre
    for monumento in report["Registrados"]["Provincias"]:
        if monumento.get("nombre", "").lower() == nombre.lower():
            return True
    return False