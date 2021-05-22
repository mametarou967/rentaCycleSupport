# coding: utf-8

# GPS
import serial
import micropyGPS
import threading
import time
# GPIO
import RPi.GPIO as GPIO # RPi.GPIOモジュールを使用
# CSV
import csv

# GPS setup
gpsLatitude = 0.0
gpsLongitude = 0.0

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
    print("GPIO[ %d ]のコールバックが発生しました" % gpio_pin)
    print('緯度経度: %2.8f, %2.8f' % (gpsLatitude, gpsLongitude))

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN)
GPIO.add_event_detect(18, GPIO.RISING, callback=event_callback, bouncetime=200)

# Csv setup
with open('portList.csv',encoding="utf_8") as file:
    reader = csv.reader(file)
    
    for row in reader:
        tmpLatitude = float(row[0])
        tmpLongitude = float(row[1])
        print('緯度経度: %2.8f, %2.8f' % (tmpLatitude,tmpLongitude))

while True:
    
    if gps.clean_sentences > 20: # ちゃんとしたデーターがある程度たまったら出力する
        h = gps.timestamp[0] if gps.timestamp[0] < 24 else gps.timestamp[0] - 24
        gpsLatitude = gps.latitude[0]
        gpsLongitude = gps.longitude[0]
        # print('緯度経度: %2.8f, %2.8f' % (gps.latitude[0], gps.longitude[0]))
        # print('')
    time.sleep(3.0)
