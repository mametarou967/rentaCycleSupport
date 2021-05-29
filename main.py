# coding: utf-8
import webbrowser ,sys
import urllib.parse
import requests
import json
# GPS
import serial
import micropyGPS
import threading
import time
# GPIO
import RPi.GPIO as GPIO # RPi.GPIOモジュールを使用
# CSV
import csv
import math

API_KEY = "your api key"
WEATHER_CONFIRM_INTERVAL = 60
WEATHER_PIN = 16

# GPS setup
gpsLatitude = 0.0
gpsLongitude = 0.0
gpsValid = False
rentaCyclePortList = []

gps = micropyGPS.MicropyGPS(9, 'dd') # MicroGPSオブジェクトを生成する。
                                     # 引数はタイムゾーンの時差と出力フォーマット

def rungps(): # GPSモジュールを読み、GPSオブジェクトを更新する
    s = serial.Serial('/dev/serial0', 9600, timeout=10)
    s.readline() # 最初の1行は中途半端なデーターが読めることがあるので、捨てる
    while True:
        sentence = s.readline().decode('utf-8') # GPSデーターを読み、文字列に変換する
        if sentence[0] != '$': # 先頭が'$'でなければ捨てる
            continue
        for x in sentence: # 読んだ文字列を解析してGPSオブジェクトにデーターを追加、更新する
            gps.update(x)

gpsthread = threading.Thread(target=rungps, args=()) # 上の関数を実行するスレッドを生成
gpsthread.daemon = True
gpsthread.start() # スレッドを起動

# Button setup
def event_callback(gpio_pin):
    #for row in rentaCyclePortList:
    #    print('緯度経度: %2.8f, %2.8f' % (row[0],row[1]))
    print("GPIO[ %d ]のコールバックが発生しました" % gpio_pin)
    print('current緯度経度: %2.8f, %2.8f' % (gpsLatitude, gpsLongitude))
    nearPointResult = nearPoint(gpsLatitude,gpsLongitude,rentaCyclePortList)
    print('near緯度経度: %2.8f, %2.8f' % (nearPointResult[0], nearPointResult[1]))
    if gpsValid == True:
        webbrowser.open("https://www.google.com/maps/dir/?api=1&origin=%2.8f,%2.8f&destination=%2.8f,%2.8f&travelmode=walking" % (gpsLatitude,gpsLongitude,nearPointResult[0], nearPointResult[1]),2,True)
    # webbrowser.open("https://www.google.com/maps/dir/?api=1&origin=34.356722,132.337222&destination=34.4418632303169,132.41688967757966&travelmode=walking",2,True)
    

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN)
GPIO.add_event_detect(18, GPIO.RISING, callback=event_callback, bouncetime=200)

# Timer setup
def helloWorld():
    print("hello World")

tim = threading.Timer(1,helloWorld)
tim.start()

def checkWeather(iLat,iLon):
    url = "http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&APPID={key}"
    url1 = url.format(lat = iLat,lon = iLon, key = API_KEY)
    response = requests.get(url1)
    data = response.json()
    weather = data["weather"][0]["main"]

    if((weather == "broken clouds") or (weather == "shower rain") or (weather == "rain") or (weather == "thunderstorm") or (weather == "snow") or (weather == "mist")
       ):
        print("weather bad")
        return False
    else:
        print("weather good")
        return True

# Csv setup
# 複数の座標のうちx, yに一番近い座標を求める

def nearPoint(x, y, points):
	result = [0.0,0.0]
	stdval = 100.0
	for point in points:
		distance = math.sqrt((point[0] - x) ** 2 + (point[1] - y) ** 2)
		if distance < stdval:
			result = (point[0],point[1])
			stdval = distance
	return result

with open('portList.csv',encoding="utf_8") as file:
    reader = csv.reader(file)
    
    for row in reader:
        rentaCyclePortList.append((float(row[0]),float(row[1])))

badWeather = False
start = time.time()
GPIO.setmode(GPIO.BCM)
GPIO.setup(WEATHER_PIN,GPIO.OUT)
GPIO.output(16,False)
while True:
    if gps.clean_sentences > 20: # ちゃんとしたデーターがある程度たまったら出力する
        h = gps.timestamp[0] if gps.timestamp[0] < 24 else gps.timestamp[0] - 24
        gpsLatitude = gps.latitude[0]
        gpsLongitude = gps.longitude[0]
        if gpsLatitude > 0 and gpsLongitude > 0:
            gpsValid = True
    
    elapsed_time = time.time() - start
    if(badWeather == False and elapsed_time > WEATHER_CONFIRM_INTERVAL):
        GPIO.output(16,True)
        if(gpsValid == True and checkWeather(gpsLatitude,gpsLongitude)):
            badWeather = True
    time.sleep(3.0)
