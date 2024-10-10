import machine
import os
import dht
import micropython

from time import sleep
from scd41 import SCD4X
from machine import Pin, SoftI2C


def readDHT22():
    sensor = dht.DHT22(Pin(15))
    DHT22Reading = [0,0]
    try:
        sensor.measure()
        DHT22Reading[0] = sensor.temperature()
        DHT22Reading[1] = sensor.humidity()
        return DHT22Reading
    except OSError as e:
        print('Failed to read DHT22 sensor.')

def initSCD41():
    # Init SCD41 sensor
    print("\nInit SCD41 sensor....")
    i2c0 = SoftI2C(scl=Pin(17), sda=Pin(16), freq=100000)
    global scd4x
    scd4x = SCD4X(i2c0)
    print("Sensor found at address:", i2c0.scan())
    scd4x.start_periodic_measurement()
    # Wait 5 seconds for sensor to become ready
    sleep(5)
    return scd4x

def readSCD41(scd4x):
    # Read sensor values and return array
    #i2c0 = SoftI2C(scl=Pin(17), sda=Pin(16), freq=100000)
    #scd4x = SCD4X(i2c0)
    #scd4x.start_periodic_measurement()
    #sleep(5)
    SCD41Reading=[0,0,0]
    SCD41Reading[0] = scd4x.temperature
    SCD41Reading[1] = scd4x.relative_humidity
    SCD41Reading[2] = scd4x.co2
    return SCD41Reading