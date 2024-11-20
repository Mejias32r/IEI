from django.shortcuts import render
import csv
import selenium
# Create your views here.

def readCSVtoJson(request):
    print("Voy a abrir")
    with open('cv.csv', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            print(row)



