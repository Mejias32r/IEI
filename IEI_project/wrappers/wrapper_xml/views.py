from django.shortcuts import render
from django.db import transaction
from IEI_project.settings import FUENTES_DE_DATOS_DIR
from main.models import Monumento
from main.models import Localidad
from main.models import Provincia

import xml.etree.ElementTree as ET
import json

@transaction.atomic
def transform_xml_to_json():
    # Parse the XML file
    tree = ET.parse(FUENTES_DE_DATOS_DIR + '/monumentos_castilla_y_leon.xml')
    root = tree.getroot()

    # Initialize the resulting JSON structure and TODO list
    report = {}
    todos = []

    # Iterate through the monuments
    for monument in root.findall('monumento'):
        # Map the name
        name = monument.find('nombre')
        if name is not None:
            nameConstructor = name.text
        else:
            nameConstructor = ""

        # Map the type of monument
        monument_type = monument.find('tipoMonumento')
        if monument_type is not None:
            type = monument_type.text
            if type == "Yacimientos arqueológicos":
                monumnentTypeConstructor = "Archaeological Site"
            elif type == "Iglesias y Ermita" or type == "Catedral":
                monumnentTypeConstructor = "Iglesia-Ermita"
            elif type == "Monasterios" or type == "Santuarios" or (type == "Real Sitio" and ("Monasterio" in nameConstructor or "Convento" in nameConstructor)):
                monumnentTypeConstructor = "Monasterio-Convento"
            elif type == "Castillos":
                monumnentTypeConstructor = "Castillo-Fortaleza-Torre"
            elif type == "Palacio" or type == "Sinagoga" or type == "Fuentes" or (type == "Real Sitio" and ("Palacio" in nameConstructor)):
                monumnentTypeConstructor = "Edificio singular"
            elif type == "Puente":
                monumnentTypeConstructor = "Puente"
            elif type == "Otros edificios" or type == "Esculturas" or type == "Hórreos" or type == "Jardín Histórico" or type == "Paraje pintoresco":
                monumnentTypeConstructor = "Otros"
            else:
                todos.append(f"TODO: Descartado")
        else:
            todos.append("TODO: Descartado.")

        # Map the address
        street = monument.find('calle')
        municipality = monument.find('./poblacion/municipio')
        if street is not None and municipality is not None:
            addressConstructor = f"{street.text}, {municipality.text}"
        elif municipality is not None:
            addressConstructor = f"Pertenece al municipio {municipality.text}"
        else:
            addressConstructor = ""
        
        # Map the postal code (revisar que cuadra rango)
        codigoPostal = monument.find('codigoPostal')
        if codigoPostal is not None:
            if len(codigoPostal.text) == 5:
                codigoPostalConstructor = codigoPostal.text
            elif len(codigoPostal.text) == 4:
                todos.append("TODO: Reparado.")
                codigoPostalConstructor = "0" + codigoPostal.text
            first_two_digits = int(codigoPostal.text[:2])
            if first_two_digits > 52:
                todos.append("TODO: Descartado.")
        else:
            todos.append("TODO: Descartado.")
            
        # Map coordinates (revisar que cuadra rango)
        latitude = monument.find('./coordenadas/latitud')
        longitude = monument.find('./coordenadas/longitud')
        if latitude is not None and longitude is not None:
            longitudeConstructor = latitude.text
            latitudeConstructor = latitude.text
            if float(longitudeConstructor) > 180 or float(longitudeConstructor) < -180 or float(latitudeConstructor) > 90 or float(latitudeConstructor) < -90:
                todos.append("TODO: Descartado.")
        else:
            todos.append("TODO: Descartado.")

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
        if province is not None:
            provinceConstructor = Provincia(nombre = province.text)
            if not Provincia.objects.filter(nombre=province.text).exists():
                provinceConstructor.save()
            else:
                provinceConstructor = Provincia.objects.get(nombre=province.text)
        else:
            todos.append("TODO: Descartado.")
            
        # Map  the localidad
        localidad = monument.find('./poblacion/localidad')
        if localidad is not None:
            localidadConstructor = Localidad(nombre = localidad.text, en_provincia = provinceConstructor)
            if not Localidad.objects.filter(nombre=localidad.text).exists():
                localidadConstructor.save()
            else:
                localidadConstructor = Localidad.objects.get(nombre=localidad.text)
        else:
            todos.append("TODO: Descartado.")

        # Add the monument's data to the result JSON
        monument = Monumento.objects.create(
            nombre=nameConstructor,
            tipo=monumnentTypeConstructor,
            direccion=addressConstructor,
            longitud=longitudeConstructor,
            latitud=latitudeConstructor,
            codigo_postal=codigoPostalConstructor,
            descripcion=descriptionConstructor,
            en_localidad= localidadConstructor,
        )
        monument.save()
    
    return report