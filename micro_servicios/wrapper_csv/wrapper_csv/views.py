import time
from django.http import JsonResponse
from django.shortcuts import render
import csv
from django.db import transaction
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.support.ui import Select
from selenium.webdriver.edge.service import Service
import requests
from selenium.webdriver import ActionChains
from .settings import FUENTES_DE_DATOS_DIR
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view

##Define structure of report
report = {
    "nombre": "Wrapper_CSV",
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

fila = 0

def buildMonument(driver, id, denominacion: str, provincia, municipio, utmeste, utmnorte, codclasificacion, clasificacion, codcategoria, categoria):
    try:
        report["total"]["count"] += 1
        global fila
        fila += 1
        mNombre = getName(denominacion)
        mDescripcion = clasificacion
        mCategoria = getCategoria(denominacion, categoria)
        mLongitud, mLatitud = getCoords(utmnorte, utmeste, driver)
        mCodigo_postal, mDireccion, provinciaAPI = getPostalandAddress(mLongitud, mLatitud)
        p = buildProvince(provincia)
        mEn_localidad = buildCity(municipio, p)
        report["Registrados"]["Monumentos"].append({
                    "nombre": mNombre,
                    "tipo": mCategoria,
                    "direccion": mDireccion,
                    "codigo_portal": mCodigo_postal,
                    "longitud": mLongitud,
                    "latitud": mLatitud,
                    "descripción": mDescripcion,
                    "en_localidad": mEn_localidad
                })
        report["Registrados"]["count"] += 1
    except ValueError as e:
        arguments = e.args[0]
        tipo, mensaje = arguments
        report["Descartados"]["total"] += 1
        errorMsg : str = (  "Error procesando la fila: " + str(fila) + 
                            " con el monumento: '" + denominacion + 
                            "' por la razón: " + str(mensaje) )
        report["Descartados"][tipo].append(errorMsg)
        print(errorMsg)
    except Exception as e:
        report["Descartados"]["total"] += 1
        report["Descartados"]["Monumento"].append("Error inesperado procesando la fila " + str(fila) + " : " + str(e))
        print(e)

def existe_provincia(nombre): ##Código de Cesar
    # Recorrer la lista de monumentos para buscar el nombre
    for monumento in report["Registrados"]["Provincias"]:
        if monumento.get("nombre", "").lower() == nombre.lower():
            return True
    return False

#Si la provincia esta mal escrita la corrige sino la deja igual
def provinceMispelled(palabra1, provinciaCorrecta):
    if len(palabra1) != len(provinciaCorrecta):
        return palabra1
    diferencias = sum(1 for a, b in zip(palabra1, provinciaCorrecta) if a != b)
    if diferencias == 1:
        return provinciaCorrecta
    else:
        return palabra1

def buildProvince(provincia: str):
    if provincia is None or provincia == "":
        raise ValueError(["Provincias","Falta la provincia"])
    provincia = provincia.capitalize()
    if (provincia != "Castellón" and 
        provincia != "Alicante" and 
        provincia != "Valencia"):
        if provinceMispelled(provincia, "Castellón") != provincia: #Si se ha corregido la provincia informar de ello
            report["Reparados"]["Provincias"].append({
                "linea" : fila,
                "nombre": provincia,
                "motivo": "La provincia esta mal escrita"
            })
            provincia = "Castellón"
        elif provinceMispelled(provincia, "Alicante") != provincia: #Si se ha corregido la provincia informar de ello
            report["Reparados"]["Provincias"].append({
                "linea" : fila,
                "nombre": provincia,
                "motivo": "La provincia esta mal escrita"
            })
            provincia = "Alicante"
        elif provinceMispelled(provincia, "Valencia") != provincia: #Si se ha corregido la provincia informar de ello
            report["Reparados"]["Provincias"].append({
                "linea" : fila,
                "nombre": provincia,
                "motivo": "La provincia esta mal escrita"
            })
            provincia = "Valencia"
        else:
            raise ValueError(["Provincias","Provincia '" + provincia + "' no reconocida"])
        report["Reparados"]["total"] += 1

    if not existe_provincia(provincia):
        report["Registrados"]["Provincias"].append({
                            "nombre": provincia
                        })
    
    return provincia

def existe_localidad(nombre): ##Código de Cesar
    # Recorrer la lista de monumentos para buscar el nombre
    for monumento in report["Registrados"]["Localidades"]:
        if monumento.get("nombre", "").lower() == nombre.lower():
            return True
    return False

def buildCity(municipio: str, p):
    if municipio is None or municipio == "":
        raise ValueError(["Localidades","Falta la localidad"])
    municipio = municipio.capitalize()
    if not existe_localidad(municipio):
        report["Registrados"]["Localidades"].append({
            "nombre": municipio,
            "en_provincia": p
        })
    return municipio

def getName(denominacion):
    for monumento in report["Registrados"]["Monumentos"]:
        if monumento.get("nombre", "").lower() == denominacion.lower():
            raise ValueError(["Monumento","Monumento repetido"])
    return denominacion

def getCategoria(denominacion, categoria):
    if (categoria == "Zona arqueológica"):
        return "Yacimiento arqueológico"
    elif (categoria == "Fondo de Museo (primera)" or 
          categoria == "Archivo" or 
          categoria == "Jardín Histórico"):
        return "Edificio Singular"
    elif (categoria == "Monumento"):
        if  ( "Iglesia"     in denominacion or 
              "Ermita"      in denominacion or
              "Catedral"    in denominacion):
            return "Iglesia-Monasterio"
        elif( "Monasterio"  in denominacion or
              "Convento"    in denominacion):
            return "Monasterio-Convento"
        elif( "Castillo"    in denominacion or
              "Fortaleza"   in denominacion or
              "Torre"       in denominacion):
            return "Castillo-Fortaleza-Torre"
        elif( denominacion.startswith("Puente") ):
            return "Puente"
        else:
            return "Edificio Singular"
    else:
        return "Otros"

def getCoords(utmnorte, utmeste, driver):
    if (utmnorte is None or utmnorte == "" or
        utmeste  is None or utmeste  == ""):
        raise ValueError(["Monumento","UTMNorte y/o UTMEste vacios"])
    if (int(utmnorte) < 500000  or int(utmnorte) > 900000):
        raise ValueError(["Monumento","Valor de UTMNorte fuera de rango"])
    if (int(utmeste)  < 3900000 or int(utmeste)  > 4700000):
        raise ValueError(["Monumento","Valor de UTMeste fuera de rango"])
    return transformData(utmnorte, utmeste, driver)

def getPostalandAddress(longd, latgd):
    if (longd is None or longd == "" or
        latgd is None or latgd == ""):
        raise ValueError(["Monumento","Longitud y/o Latitud vacias"])
    #"-0.37966""39.47391" for valencia. Tests
    time.sleep(1) #Evita hacer llamadas demasiado rápido a la API y que nos bloquee
    data = callAPI(latgd=latgd,longd=longd)
    address_data = data.get("address", {})
    road = address_data.get("road", "")
    house_number = address_data.get("house_number", "")
    city = address_data.get("town", "") + " " + address_data.get("city", "") + " " + address_data.get("village", "")
    postcode = address_data.get("postcode", "")
    province = address_data.get("province", "")
    country = address_data.get("country", "")

    # Crear la dirección completa
    address = f"{road} {house_number}, {postcode}, {city}, {province}, {country}".strip()
    print(address)

    if (postcode is None or postcode == "" or
        address  is None or address  == ""):
        raise ValueError(["Monumento","Error al encontrar el código postal o la dirección. Seguramente error con la API."])
    return postcode, address, province

# Swagger Schema for extractor_csv
@swagger_auto_schema(
    method='GET',
    operation_summary="Extract data from CSV",
    operation_description="Reads a CSV file and processes the monument data.",
    responses={
        200: openapi.Response(
            description="CSV processed successfully",
            examples={
                "application/json": {
                    "nombre": "Wrapper_CSV",
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
        500: "Error processing the CSV file",
        405: "Method Not Allowed",
    },
)

@api_view(['GET'])
def extractor_csv(request):
    if request.method != 'GET':
        return JsonResponse({"error": "Method not allowed."}, status=405)
    reset_globals()
    driver = startPage()
    with open(FUENTES_DE_DATOS_DIR + '/bienes_inmuebles_interes_cultural.csv', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=";")
        next(reader)
        for row in reader:
            id, denominacion, provincia, municipio, utmeste, utmnorte, codclasificacion, clasificacion, codcategoria, categoria = row
            buildMonument(driver, id, denominacion, provincia, municipio, utmeste, utmnorte, codclasificacion, clasificacion, codcategoria, categoria)
            print("una fila procesada  ----------------------------------")
    return JsonResponse(report)

##This method initializates the selenium scrapper
def startPage():
    options = Options()
    options.add_argument("--headless")  # Activar modo headless
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(EdgeChromiumDriverManager().install())
    driver = webdriver.Edge(service=service,options=options)
    driver.get("https://www.ign.es/web/calculadora-geodesica")
    time.sleep(2)

    text = driver.find_element(By.ID, "titlecoord2").text
    print(text)

    combo_box = driver.find_element(By.ID, "combo_tipo")
    select = Select(combo_box)
    select.select_by_index(0)

    layout = driver.find_element(By.XPATH, "//*[@id='sistrefe']/div[1]/div")
    #layout.click()
    actions = ActionChains(driver)
    actions.move_to_element(layout).click().perform()
 
    layout2 = driver.find_element(By.XPATH, "//*[@id='typecoords']/div[2]/div")
    #layout2.click()
    actions = ActionChains(driver)
    actions.move_to_element(layout2).click().perform()

    layout3 = driver.find_element(By.XPATH, "//*[@id='modotrab']/div[1]/div")
    #layout3.click()
    actions = ActionChains(driver)
    actions.move_to_element(layout3).click().perform()


    text = driver.find_element(By.ID, "titlecoord2").text
    print(text)
    return driver


##Introduces utmN and utmE to the page and gets longd and latgd
def transformData(utmN,utmE,driver):
    input = driver.find_element(By.ID, "datacoord1")
    input.clear()
    input.send_keys(utmN)
    input2 = driver.find_element(By.ID, "datacoord2")
    input2.clear()
    input2.send_keys(utmE)

    time.sleep(1)

    calculate = driver.find_element(By.ID,"trd_calc")
    actions = ActionChains(driver)
    actions.move_to_element(calculate).click().perform()
    #calculate.click()

    count = 0
    result = driver.find_element(By.ID,"results_manual").get_attribute("style")
    if result != "display: block;":
        while result != "display: block;":
            result = driver.find_element(By.ID,"results_manual").get_attribute("style")
            time.sleep(1)
            if count>=20:
                actions.move_to_element(calculate).click().perform()
                count = 0
                print("volvi a clickar")            
            count +=1
            print("Esperando primero")
    else:
        longd = driver.find_element(By.ID,"txt_etrs89_longd").get_attribute("value")
        result = driver.find_element(By.ID,"txt_etrs89_longd").get_attribute("value")
        while longd == result:
            result = driver.find_element(By.ID,"txt_etrs89_longd").get_attribute("value")
            time.sleep(1)
            if count>=20:
                actions.move_to_element(calculate).click().perform()
                print("volvi a clickar")
                count = 0
            count +=1
            print("Esperando segudno")
    
    longd = driver.find_element(By.ID,"txt_etrs89_longd").get_attribute("value")
    latgd = driver.find_element(By.ID,"txt_etrs89_latgd").get_attribute("value")

    print(longd)
    return [longd,latgd]


##Gets the longd and latgd using the API
def callAPI(longd : str,latgd : str):
    print("Empezado")
    url = "https://reverse-geocoder.p.rapidapi.com/v1/getAddressByLocation?lat="+latgd+"&lon="+longd+"&accept-language=en"
    headers = {
    "X-RapidAPI-Key": "6c2aa156f8mshecf0f16b67af41ep119458jsnff7511e9d279",
    "X-RapidAPI-Host": "reverse-geocoder.p.rapidapi.com"
    }
    response = requests.get(url,headers=headers)
    json = response.json()
    print(json)

    return json


##Resets the global variables
def reset_globals():
    global report, fila
    report = {
        "nombre": "Wrapper_CSV",
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
    fila = 0
##Execute
#extractor_csv(1)