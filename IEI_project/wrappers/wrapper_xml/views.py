from django.shortcuts import render
from IEI_project.settings import 

import xml.etree.ElementTree as ET
import json

def transform_xml_to_json(xml_file_path, save_function):
    """
    Transforms an XML file into a JSON structure following specific mappings
    and saves the JSON using the provided function. Missing mappings are flagged as TODOs.

    Args:
        xml_file_path (str): Path to the XML file.
        save_function (callable): Function to save the JSON data (e.g., into a database).
    """
    # Parse the XML file
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    # Initialize the resulting JSON structure and TODO list
    json_result = {}
    todos = []

    # Iterate through the monuments
    for monument in root.findall('monumento'):
        temp_json = {}

        # Map the name
        name = monument.find('nombre')
        if name is not None:
            temp_json['name'] = name.text
        else:
            todos.append("TODO: Handle missing 'nombre' element.")

        # Map the type of monument
        monument_type = monument.find('tipoMonumento')
        if monument_type is not None:
            if monument_type.text == "Yacimientos arqueológicos":
                temp_json['monumentType'] = "Archaeological Site"
            else:
                todos.append(f"TODO: Map for 'tipoMonumento' {monument_type.text}.")
        else:
            todos.append("TODO: Handle missing 'tipoMonumento' element.")

        # Map the address
        street = monument.find('calle')
        municipality = monument.find('./poblacion/municipio')
        if street is not None and municipality is not None:
            temp_json['address'] = f"{street.text}, {municipality.text}"
        elif municipality is not None:
            temp_json['address'] = f"Pertenece al municipio {municipality.text}"
        else:
            todos.append("TODO: Handle missing 'calle' and 'municipio' elements.")

        # Map the description
        description = monument.find('Descripcion')
        constructionType = monument.find('tipoConstruccion')
        historical_periods = monument.findall('periodoHistorico')
        if description is not None:
            temp_json['description'] = description.text.strip()
        else:
            todos.append(f"TODO: Handle missing 'Descripcion' element.")

        # Map coordinates
        latitude = monument.find('./coordenadas/latitud')
        longitude = monument.find('./coordenadas/longitud')
        if latitude is not None and longitude is not None:
            temp_json['coordinates'] = {
                "latitude": latitude.text,
                "longitude": longitude.text
            }
        else:
            todos.append("TODO: Handle missing 'coordenadas' elements.")

        # Add the monument's data to the result JSON
        json_result[temp_json.get('id', len(json_result))] = temp_json

    # Save the JSON
    #TODO: save JSON using the provided function