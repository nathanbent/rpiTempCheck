 #!/usr/bin/env python
import time
import board
import busio
import adafruit_bme280
from influxdb import InfluxDBClient
#import all your stuff 
 
# Create library object using our Bus I2C port
i2c = busio.I2C(board.SCL, board.SDA)
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)
 
# OR create library object using our Bus SPI port
# spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
# bme_cs = digitalio.DigitalInOut(board.D10)
# bme280 = adafruit_bme280.Adafruit_BME280_SPI(spi, bme_cs)
 
# change this to match the location's pressure (hPa) at sea level
bme280.sea_level_pressure = 1013.25
min_between_reads = .5
#Minutes beteween reads for while loop
#This should help to set basic parameters for what to expect to help weed out bad results
oldtemp = 75
oldpressure = 1005
oldhumidity = 50
errorscorrected = 0
runcount = 0


while True:
 
    def tempRead(): #read temperature, return float with 3 decimal places  
            fakedegrees = bme280.temperature  
            bmedegrees = (fakedegrees * 1.8) + 32
            return bmedegrees
      
    def pressRead():#read pressure, return float with 3 decimal places  
            bmepascals = bme280.pressure
            return bmepascals  
      
    def humidityRead(): #read humidity, return float with 3 decimal places  
            bmehumidity = bme280.humidity 
            return bmehumidity
    
    temptemp = tempRead()  
    temppressure = pressRead()  
    temphumidity = humidityRead()

    
#This should weed out bad results    

#This will make sure that it is run once to establish a baseline, and then scale from there
    if runcount > 0:

        if abs(temptemp - oldtemp) > 10:
            temperature = oldtemp
            errorscorrected = errorscorrected + 1 #count errors
        else:
            temperature = temptemp
            oldtemp = temptemp #allow for results to scale
            
        if abs(temppressure - oldpressure) > 10:
            pressure = oldpressure
            errorscorrected = errorscorrected + 1
        else:
            pressure = temppressure
            oldpressure = temppressure
        
        if abs(temphumidity - oldhumidity) > 5:
            humidity = oldhumidity
            errorscorrected = errorscorrected + 1
        else:
            humidity = temphumidity
            oldhumidity = humidity
    else:
        temperature = temptemp
        oldtemp = temptemp
        pressure = temppressure
        oldpressure = temppressure
        humidity = temphumidity
        oldhumidity = temphumidity

#this section will count how many times the script has run and will then calculate the amount of seconds it has been running

    runcount = runcount + 1
    runtime = runcount * (60*min_between_reads) - 30

    bme280_data = [
        {
            "measurement" : "bme280",
            "tags" : {
                "host": "RaspiTest"
            },
            "fields" : {
                "temperature": float(temperature),
                "humidity": float(humidity),
                "pressure": float(pressure),
                "errorscorrected" : float(errorscorrected),
                "readruncount" : float(runcount),
                "readruntime" : float(runtime)
            }
        }
    ]



    client = InfluxDBClient('192.168.1.15', 8086, 'bme280monitor', 'Subaru15', 'bme280')

    client.write_points(bme280_data)


    
    
    print("\nTemperature: %0.1f F" % temperature)
    print("Humidity: %0.1f %%" % humidity)
    print("Pressure: %0.1f hPa" % pressure)
    print("Run count: %0.1f" % runcount)
    print("Run time: %0.1f" % runtime)
    print("Errors Corrected: %0.1f" % errorscorrected)
    #print("Altitude = %0.2f meters" % bme280.altitude)
    time.sleep(60*min_between_reads)
