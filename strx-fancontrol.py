#!/usr/bin/python
#2022-02-18 kwb script zur variablen Steuerung von 2 getrennten Luefterstufen für den Stratux.
#               Eine Temperaturmessung erfolgt mittels Temperaturfuehler(DS180)welcher die Temperatur der SDRs staendig
#               mißt. Der gesetzte Schwellwert <temp_SDRs> bestimmt das Anschalten des Luefters fuer die Radios.
#               Die 2. Temperaturmessung erfolgt durch messung der CPU Temperatur des Stratux. Der im Webinterface des 
#               Stratux gesetzte Schwellwert <temp_thershold_fan> bestimmt das Anschalten des Lüfters fuer die CPU.
#
#2022-02-21 kwb Aenderungen zur Steuerung aus dem Webinterface eingebaut. Temp. Schwellwerte zur 
#               Lueftersteuerung können jetzt variabel aus dem Stratux-Webinterface <Temperature Threshold Fancontrol>
#		gesetzt werden.
#2022-02-22 kwb 2.Luefterstufe für die SDRs eingebaut
#
#
import re
import glob
import os
import time
import RPi.GPIO as GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.OUT)
GPIO.setup(14, GPIO.OUT)
fan1 = "off"
fan2 = "off"
temp_SDRs = 48

#set device-file to sensor
device_file = glob.glob('/sys/bus/w1/devices/28*/w1_slave')[0]
#set stratux config file
strxconf_file = glob.glob('/boot/stratux.conf')[0]
temp_file = open(strxconf_file)
content = temp_file.read()
temp_file.close()
#check value of temperature threshold was put in stratux webinterface
temp_threshold = content[len(content)-3:len(content)-1]
#floating value
temp_threshold_fan = float(temp_threshold)

#funktion: measure CPU temperature
def getCPUtemperature():
    res = os.popen('vcgencmd measure_temp').readline()
    return(res.replace("temp=","").replace("'C\n",""))

try:
    #repeat loop with key-break (Strg+c)
    while True:
       #stop for 10s
       time.sleep(10)
       #check DS1820-Temperatur Sensor
       tempfile = open(device_file)
       content = tempfile.read()
       tempfile.close()
       #check value of temperature from DS1820 sensor and cut them
       tempdata = content[len(content)-6:len(content)]          
       #check errors during floating
       try:
          #floating value and divide by 1000
          temp_floatDS1820 = float(tempdata)/1000
       except:
          time.sleep(0.5)      

       #CPU-Temperature Convert value to number
       temp_floatCPU = float(getCPUtemperature())

       print(f"Temperature CPU:{temp_floatCPU}°C")
       print(f"Temperature SDRs:{temp_floatDS1820}°C")

       #fan stage CPU: if temperature > threshold, turn on fan CPU
       if (temp_floatCPU > temp_threshold_fan) and fan1 == "off":
           #temperature is above threshold and fan is currently off, so turn on fan
           GPIO.output(23, True)
           fan1 = "on"
       elif (temp_floatCPU > temp_threshold_fan) and fan1 == "on":
           #fan is currently on, NOT turn on control line (GPIO) again
            print(f"Temperature CPU:{temp_floatCPU}°C. -> fan CPU is currently on.")
       else:
           #temperature is below threshold, turn off fan
           GPIO.output(23, False)
           fan1 = "off"

       #fan stage SDR's: if temperature > temperatur threshold radios, turn on fan radios
       if (temp_floatDS1820 > temp_SDRs) and fan2 == "off":
           #temperature is above threshold and fan is currently off, so turn on fan
           GPIO.output(14, True)
           fan2 = "on"
       elif (temp_floatDS1820 > temp_SDRs) and fan2 == "on":
           #fan is currently on, NOT turn on control line (GPIO) again
            print(f"Temperature Radios:{temp_floatDS1820}°C. -> fan SDRs is currently on.")
       else:
           #temperature is below threshold, turn off fan
           GPIO.output(14, False)
           fan2 = "off"

# key-break (Strg+c) turn off fan's
except KeyboardInterrupt:
    GPIO.output(14, False)
    GPIO.output(23, False)
    pass
