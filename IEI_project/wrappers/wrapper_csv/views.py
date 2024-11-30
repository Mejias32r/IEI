import time
from django.http import JsonResponse
from django.shortcuts import render
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.support.ui import Select
from selenium.webdriver.edge.service import Service
import requests
from selenium.webdriver import ActionChains
from IEI_project.settings import FUENTES_DE_DATOS_DIR
from main.models import Monumento, Provincia, Localidad


def buildMonument(driver, id, denominacion: str, provincia, municipio, utmeste, utmnorte, codclasificacion, clasificacion, codcategoria, categoria):
    try:
        report["Total"]["count"] += 1
        m = Monumento()
        p = buildProvince(provincia)
        m.en_localidad = buildCity(municipio, p)
        m.nombre = denominacion
        m.descripcion = clasificacion
        getCategoria(denominacion, categoria, m)
        #TODO: Descomentar cuando transformData() funcione correctamente
        m.longitud, m.latitud = transformData(utmnorte, utmeste, driver)
        m.codigo_postal, m.direccion = getPostalandAddress(m.longitud, m.latitud)
        m.save()
        report["Registrados"]["count"] += 1
        print(m.tipo) #Test
    except ValueError as e:
        report["Descartados"]["count"] += 1
        report["Descartados"]["razones"].append(e)
    except Exception as e:
        report["Descartados"]["count"] += 1
        report["Descartados"]["razones"].append(f"Error inesperado: {str(e)}.")
        print(e)

def buildProvince(provincia):
    if provincia is None or provincia == "":
        raise ValueError("Falta la provincia")
    p = Provincia( nombre = provincia )
    if not Provincia.objects.filter(nombre = provincia).exists():
        p.save()
    else:
        p = Provincia.objects.get(nombre = provincia)
    return p

def buildCity(municipio, p):
    if municipio is None or municipio == "":
        raise ValueError("Falta la localidad")
    l = Localidad(nombre=municipio, en_provincia=p)
    if not Localidad.objects.filter(nombre=municipio).exists():
        l.save()
    else:
        l = Localidad.objects.get(nombre=municipio)
    return l

def getCategoria(denominacion, categoria, m):
    if (categoria == "Zona arqueológica"):
        m.tipo = "Yacimiento arqueológico"
    elif (categoria == "Fondo de Museo (primera)" or 
          categoria == "Archivo" or 
          categoria == "Jardín Histórico"):
        m.tipo = "Edificio Singular"
    elif (categoria == "Monumento"):
        if  ( "Iglesia"     in denominacion or 
              "Ermita"      in denominacion or
              "Catedral"    in denominacion):
            m.tipo = "Iglesia-Monasterio"
        elif( "Monasterio"  in denominacion or
              "Convento"    in denominacion):
            m.tipo = "Monasterio-Convento"
        elif( "Castillo"    in denominacion or
              "Fortaleza"   in denominacion or
              "Torre"       in denominacion):
            m.tipo = "Castillo-Fortaleza-Torre"
        elif( denominacion.startswith("Puente") ):
            m.tipo = "Puente"
        else:
            m.tipo = "Edificio Singular"
    else:
        m.tipo = "Otros"

def getPostalandAddress(longd, latgd):
    #"-0.37966""39.47391" for valencia. Tests
    data = callAPI(latgd=latgd,longd=longd)
    address_data = data.get("address", {})
    road = address_data.get("road", "")
    house_number = address_data.get("house_number", "")
    city = address_data.get("city", "")
    postcode = address_data.get("postcode", "")
    province = address_data.get("province", "")
    country = address_data.get("country", "")

    # Crear la dirección completa
    address = f"{road} {house_number}, {postcode}, {city}, {province}, {country}".strip()

    return postcode, address

def readCSVtoJson(request):
    driver = startPage()
    with open(FUENTES_DE_DATOS_DIR + '/monumentos_comunidad_valenciana.csv', encoding='utf-8') as file:
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

    time.sleep(5)

    calculate = driver.find_element(By.ID,"trd_calc")
    actions = ActionChains(driver)
    actions.move_to_element(calculate).click().perform()
    #calculate.click()

    result = driver.find_element(By.ID,"results_manual").get_attribute("style")
    if result != "display: block;":
        while result != "display: block;":
            result = driver.find_element(By.ID,"results_manual").get_attribute("style")
            time.sleep(1)
            print("Esperando primero")
    else:
        longd = driver.find_element(By.ID,"txt_etrs89_longd").get_attribute("value")
        result = driver.find_element(By.ID,"txt_etrs89_longd").get_attribute("value")
        while longd == result:
            result = driver.find_element(By.ID,"txt_etrs89_longd").get_attribute("value")
            time.sleep(1)
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

##Define structure of report
report = {
        "Total": {"count": 0},
        "Registrados": {"count": 0},
        "Descartados": {"count": 0, "razones": []},
        "Reparados": {"count": 0, "detalles": []},
    }
##Execute
readCSVtoJson(1)
