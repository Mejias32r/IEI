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



import time


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
    layout.click()
 
    layout2 = driver.find_element(By.XPATH, "//*[@id='typecoords']/div[2]/div")
    layout2.click()

    layout3 = driver.find_element(By.XPATH, "//*[@id='modotrab']/div[1]/div")
    #layout3.click()
    actions = ActionChains(driver)
    actions.move_to_element(layout3).click().perform()


    text = driver.find_element(By.ID, "titlecoord2").text
    print(text)

    list = transformData("706092","4257316",driver)
    print(list[0]+" "+list[1])
    
    callAPI(list[0],list[1])
    return driver





def readCSVtoJson():
    driver = startPage()
    print("Voy a abrir")
    with open('cv.csv', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            print(row)




def transformData(utmN,utmE,driver):
    input = driver.find_element(By.ID, "datacoord1")
    input.send_keys(utmN)
    input2 = driver.find_element(By.ID, "datacoord2")
    input2.send_keys(utmE)

    calculate = driver.find_element(By.ID,"trd_calc")
    calculate.click()

    result = driver.find_element(By.ID,"results_manual").get_attribute("style")
    while result != "display: block;":
        result = driver.find_element(By.ID,"results_manual").get_attribute("style")
        time.sleep(1)
        print("Esperando")
    
    longd = driver.find_element(By.ID,"txt_etrs89_longd").get_attribute("value")
    latgd = driver.find_element(By.ID,"txt_etrs89_latgd").get_attribute("value")

    print(longd)
    return [longd,latgd]

def callAPI(longd,latgd):
    url = "https://reverse-geocoder.p.rapidapi.com/v1/getAddressByLocation?lat="+latgd+"&lon="+longd+"&accept-language=en"
    headers = {
    "X-RapidAPI-Key": "6c2aa156f8mshecf0f16b67af41ep119458jsnff7511e9d279",
    "X-RapidAPI-Host": "reverse-geocoder.p.rapidapi.com"
    }
    response = requests.get(url,headers=headers)
    json = response.json()
    print(json)
    




 

