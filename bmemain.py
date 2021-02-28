#!/usr/bin/env python
# BMEmain Script
# V .5 - MySQL, April 2020
# V 1.0 - InfluxDB, May 2020
# V 1.5 - Modularity, to be called in other programs.  Feb 2021

# Want to do
# Improve readability, improve robustness
import time
import board
import busio
import adafruit_bme280
from influxdb import InfluxDBClient
from datetime import datetime

time_between_reads = .5
time_between_reads_0 = 0  # For when this file gets imported
start_time = time.time()
credentials = ['host_name', 'influxdb_host', 'influxdb_port', 'influxdb_user', 'influxdb_pass', 'influxdb_db']
built_in_credentials = False
credentials_file = "credentials.txt"
i2c = busio.I2C(board.SCL, board.SDA)
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)


def temp_read():  # read temperature, return float with 3 decimal places
    fake_degrees = bme280.temperature
    bme_degrees = (fake_degrees * 1.8) + 32
    return bme_degrees


def humidity_read():  # read humidity, return float with 3 decimal places
    bme_humidity = bme280.humidity
    return bme_humidity


def press_read():  # read pressure, return float with 3 decimal places
    bme_pascals = bme280.pressure
    return bme_pascals


def credentials_setup():
    global credentials
    global credentials_file
    try:
        with open(credentials_file) as f:
            credentials = f.read().splitlines()
    except OSError:
        credentials_file_open = open(credentials_file, 'w')
        spot = 0
        for value in credentials:
            input_value = input("What is the " + value + " for this program? ")
            credentials[spot] = input_value
            credentials_file_open.write(input_value + '\n')
            spot += 1


def write_to_influx(temperature, humidity, pressure, run_count, run_time, errors_corrected, influx_credentials):
    host_name, influxdb_host, influxdb_port, influxdb_user, influxdb_pass, influxdb_db = influx_credentials
    bme280_data = [
        {
            "measurement": "bme280",
            "tags": {
                "host": host_name
            },
            "fields": {
                "temperature": float(temperature),
                "humidity": float(humidity),
                "pressure": float(pressure),
                "errorscorrected": float(errors_corrected),
                "readruncount": float(run_count),
                "readruntime": float(run_time)
            }
        }
    ]
    print(run_time)
    print((run_count))
    try:
        client = InfluxDBClient(influxdb_host, influxdb_port, influxdb_user, influxdb_pass, influxdb_db)

        client.write_points(bme280_data)
    except:
        print("Error encountered BME, waiting for next pass to try again")


def bme280_check_script(credentials):
    global credentials_file
    global time_between_reads
    bme280.sea_level_pressure = 1013.25
    # This should help to set basic parameters for what to expect to help weed out bad results
    old_temp = 75
    old_humidity = 50
    old_pressure = 1005
    errors_corrected = 0
    run_count = 0
    run_loop = True
    while run_loop is True:

        temp_temp = temp_read()
        temp_humidity = humidity_read()
        temp_pressure = press_read()

        # This should weed out bad results
        # This will make sure that it is run once to establish a baseline, and then scale from there
        if run_count > 0:

            if abs(temp_temp - old_temp) > 5 * time_between_reads:
                temperature = old_temp
                errors_corrected = errors_corrected + 1  # count errors
            else:
                temperature = temp_temp
                old_temp = temp_temp  # allow for results to scale
            if abs(temp_humidity - old_humidity) > 25 * time_between_reads:
                humidity = old_humidity
                errors_corrected = errors_corrected + 1
            else:
                humidity = temp_humidity
                old_humidity = humidity
            if abs(temp_pressure - old_pressure) > 10 * time_between_reads:
                pressure = old_pressure
                errors_corrected = errors_corrected + 1
            else:
                pressure = temp_pressure
                old_pressure = temp_pressure

        else:
            temperature = temp_temp
            old_temp = temp_temp
            humidity = temp_humidity
            old_humidity = temp_humidity
            pressure = temp_pressure
            old_pressure = temp_pressure


        # this section will count how many times the script has run
        # and will then calculate the amount of seconds it has been running

        run_count = run_count + 1
        run_time = time.time() - start_time

        write_to_influx(temperature, humidity, pressure, run_count, run_time, errors_corrected, credentials)



        print("\nTemperature: %0.1f F" % temperature)
        print("Humidity: %0.1f %%" % humidity)
        print("Pressure: %0.1f hPa" % pressure)
        print("Run count: %0.1f" % run_count)
        print("Run time: %0.1f" % run_time)
        print("Errors Corrected: %0.1f" % errors_corrected)
        # print("Altitude = %0.2f meters" % bme280.altitude)
        if __name__ == "__main__":
            time.sleep(60 * time_between_reads)
        else:
            run_loop = False
            return temperature, humidity

def bme_main():
    global credentials
    if built_in_credentials is True:
        credentials = credentials
    else:
        credentials_setup()
    bme280_check_script(credentials)


def main():
    bme_main()


if __name__ == "__main__":
    main()
