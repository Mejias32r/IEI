from django.shortcuts import render
from IEI_project.settings import FUENTES_DE_DATOS_DIR
from main.models import Monument
from main.models import Localidad
from main.models import Provincia

import xml.etree.ElementTree as ET
import json

def transform_xml_to_json(request):
    # Parse the XML file
    tree = ET.parse(FUENTES_DE_DATOS_DIR + '/monumentos_castilla_y_leon.xml')
    root = tree.getroot()

    # Initialize the resulting JSON structure and TODO list
    report = {}
    todos = []

    # Iterate through the monuments
    for monument in root.findall('monumento'):
        temp_json = {}

        # Map the name
        name = monument.find('nombre')
        if name is not None:
            nameConstructor = name.text
        else:
            nameConstructor = ""

        # Map the type of monument
        monument_type = monument.find('tipoMonumento')
        if monument_type is not None:
            if monument_type.text == "Yacimientos arqueológicos":
                temp_json['monumentType'] = "Archaeological Site"
            else:
                todos.append(f"TODO: Map for 'tipoMonumento' {monument_type.text}.")
        else:
            todos.append("TODO: Descartado.")

        # Map the address
        street = monument.find('calle')
        municipality = monument.find('./poblacion/municipio')
        if street is not None and municipality is not None:
            temp_json['address'] = f"{street.text}, {municipality.text}"
        elif municipality is not None:
            temp_json['address'] = f"Pertenece al municipio {municipality.text}"
        
        # Map the postal code
        codigoPostal = monument.find('codigoPostal')
        if codigoPostal is not None:
            if len(codigoPostal.text) == 5:
                codigoPostalConstructor = codigoPostal.text
            elif len(codigoPostal.text) == 4:
                todos.append("TODO: Reparado.")
                codigoPostalConstructor = "0" + codigoPostal.text
        else:
            todos.append("TODO: Descartado.")
            
        # Map coordinates
        latitude = monument.find('./coordenadas/latitud')
        longitude = monument.find('./coordenadas/longitud')
        if latitude is not None and longitude is not None:
            temp_json['coordinates'] = {
                "latitude": latitude.text,
                "longitude": longitude.text
            }
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
                descriptionConstructor =+ f"Este monumento es un {constructionType.text}"
                if historical_periods is not None:
                    list_historical_periods = ','.join([period.text for period in historical_periods])
                    descriptionConstructor += f" que pertenece a el/los periodos históricos {list_historical_periods}"
            descriptionConstructor =+ "."               
            
        # Map the province
        province = monument.find('./poblacion/provincia')
        if province is not None:
            provinceConstructor = Provincia(nombre = province.text)
            if not Provincia.objects.filter(nombre=province.text).exists():
                provinceConstructor.save
            else:
                provinceConstructor = Provincia.objects.get(nombre=province.text)
        else:
            todos.append("TODO: Descartado.")
            
        # Map  the localidad
        localidad = monument.find('./poblacion/localidad')
        if localidad is not None:
            localidadConstructor = Localidad(nombre = localidad.text, en_provincia = provinceConstructor)
            if not Localidad.objects.filter(nombre=localidad.text).exists():
                localidadConstructor.save
            else:
                localidadConstructor = Localidad.objects.get(nombre=localidad.text)
        else:
            todos.append("TODO: Descartado.")

        # Add the monument's data to the result JSON
        monument = Monument.objects.create(
            nombre=nameConstructor,
            tipo=temp_json['monumentType'],
            direccion=temp_json['address'],
            longitud=temp_json['coordinates']['longitude'],
            latitud=temp_json['coordinates']['latitude'],
            codigo_postal = codigoPostalConstructor,
            descripcion=descriptionConstructor,
            en_localidad= localidadConstructor,
        )
        monument.save()
    
    return report


#revisar valores de latitud y longitud y codigo postal no mayor que 52