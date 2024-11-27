from django.shortcuts import render
from django.db import transaction
from django.http import JsonResponse
from IEI_project.settings import FUENTES_DE_DATOS_DIR
from main.models import Monumento
from main.models import Localidad
from main.models import Provincia

import xml.etree.ElementTree as ET
import json

@transaction.atomic
def transform_xml_to_json(request):
    # Parse the XML file
    tree = ET.parse(FUENTES_DE_DATOS_DIR + '/monumentos_entrega.xml')
    root = tree.getroot()

    # Initialize the resulting JSON structure and counters
    report = {
        "Total": {"count": 0},
        "Registrados": {"count": 0},
        "Descartados": {"count": 0, "razones": []},
        "Reparados": {"count": 0, "detalles": []},
    }

    # Iterate through the monuments
    for monument in root.findall('monumento'):
        try:
            report["Total"]["count"] += 1
            
            # Map the name
            name = monument.find('nombre')
            nameConstructor = name.text if name is not None else ""

            # Map the type of monument
            monument_type = monument.find('tipoMonumento')
            if monument_type is not None and monument_type.text != "":
                type = monument_type.text
                if type == "Yacimientos arqueológicos":
                    monumnentTypeConstructor = "Archaeological Site"
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
                    report["Descartados"]["count"] += 1
                    report["Descartados"]["razones"].append(f"Tipo de monumento no reconocido: {type}.")
                    continue
            else:
                report["Descartados"]["count"] += 1
                report["Descartados"]["razones"].append("Falta el tipo de monumento.")
                continue

            # Map the address
            street = monument.find('calle')
            municipality = monument.find('./poblacion/municipio')
            if street is not None and municipality is not None and street.text != "" and municipality.text != "":
                addressConstructor = f"{street.text}, {municipality.text}"
            elif municipality is not None:
                addressConstructor = f"Pertenece al municipio {municipality.text}"
            else:
                addressConstructor = ""

            # Map coordinates
            latitude = monument.find('./coordenadas/latitud')
            longitude = monument.find('./coordenadas/longitud')
            if latitude is not None and longitude is not None and latitude.text != "" and longitude.text != "":
                latitudeConstructor = latitude.text.replace('#', '').strip()
                longitudeConstructor = longitude.text.replace('#', '').strip()
                if float(longitudeConstructor) > 180 or float(longitudeConstructor) < -180 or float(latitudeConstructor) > 90 or float(latitudeConstructor) < -90:
                    report["Descartados"]["count"] += 1
                    report["Descartados"]["razones"].append("Coordenadas fuera de rango.")
                    continue
            else:
                report["Descartados"]["count"] += 1
                report["Descartados"]["razones"].append("Faltan coordenadas.")
                continue

            # Map the description
            description = monument.find('Descripcion')
            constructionType = monument.find('tipoConstruccion')
            historical_periods = monument.findall('periodoHistorico')
            if description is not None:
                descriptionConstructor = description.text.strip()
            else:
                descriptionConstructor = ""
                if constructionType is not None:
                    descriptionConstructor += f"Este monumento es un {constructionType.text}"
                    if historical_periods is not None:
                        list_historical_periods = ','.join([period.text for period in historical_periods])
                        descriptionConstructor += f" que pertenece a el/los periodos históricos {list_historical_periods}"
                descriptionConstructor += "."

            # Map the province
            province = monument.find('./poblacion/provincia')
            if province is not None and province.text != "":
                provinceConstructor = Provincia(nombre=province.text)
                if not Provincia.objects.filter(nombre=province.text).exists():
                    provinceConstructor.save()
                else:
                    provinceConstructor = Provincia.objects.get(nombre=province.text)
            else:
                report["Descartados"]["count"] += 1
                report["Descartados"]["razones"].append("Falta la provincia.")
                continue

            # Map the localidad
            localidad = monument.find('./poblacion/localidad')
            if localidad is not None and localidad.text != "":
                localidadConstructor = Localidad(nombre=localidad.text, en_provincia=provinceConstructor)
                if not Localidad.objects.filter(nombre=localidad.text).exists():
                    localidadConstructor.save()
                else:
                    localidadConstructor = Localidad.objects.get(nombre=localidad.text)
            else:
                report["Descartados"]["count"] += 1
                report["Descartados"]["razones"].append("Falta la localidad.")
                continue
            
            # Map the postal code
            codigoPostal = monument.find('codigoPostal')
            if codigoPostal is not None and codigoPostal.text != "":
                if len(codigoPostal.text) == 5:
                    codigoPostalConstructor = codigoPostal.text
                elif len(codigoPostal.text) == 4:
                    report["Reparados"]["count"] += 1
                    report["Reparados"]["detalles"].append(
                        "Código postal reparado añadiendo un 0 inicial."
                    )
                    codigoPostalConstructor = "0" + codigoPostal.text
                else:
                    report["Descartados"]["count"] += 1
                    report["Descartados"]["razones"].append("Código postal inválido.")
                    continue
                first_two_digits = int(codigoPostalConstructor[:2])
                if first_two_digits > 52:
                    report["Descartados"]["count"] += 1
                    report["Descartados"]["razones"].append("Código postal fuera de rango.")
                    continue
            else:
                report["Descartados"]["count"] += 1
                report["Descartados"]["razones"].append("Falta el código postal.")
                continue

            # Add the monument's data to the result JSON
            monument = Monumento.objects.create(
                nombre=nameConstructor,
                tipo=monumnentTypeConstructor,
                direccion=addressConstructor,
                longitud=longitudeConstructor,
                latitud=latitudeConstructor,
                codigo_postal=codigoPostalConstructor,
                descripcion=descriptionConstructor,
                en_localidad=localidadConstructor,
            )
            monument.save()
            report["Registrados"]["count"] += 1
        except Exception as e:
            report["Descartados"]["count"] += 1
            report["Descartados"]["razones"].append(f"Error inesperado: {str(e)}.")

    return JsonResponse(report)
