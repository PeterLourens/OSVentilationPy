# This file is executed on every boot (including wake-boot from deepsleep)

from sr74hc595_bitbang import SR74HC595_BITBANG
from machine import Pin, SoftI2C
from valveControl import clearOutputs

from secrets import *
from connect import *

clearOutputs()
print("\nclearing outputs")

do_connect(secrets.SSID, secrets.WIFI_PASS)

#led = Pin(2, Pin.OUT)

#def do_connect(ssid, pwd):
#    import network
#    sta_if = network.WLAN(network.STA_IF)
#    if not sta_if.isconnected():
#        led.value(1)
#        print('connecting to network...')
#        sta_if.active(True)
#        sta_if.connect(ssid, pwd)
#        while not sta_if.isconnected():
#            pass
#    print('network config:', sta_if.ifconfig())
#    led.value(0)
 
# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
 
# Attempt to connect to WiFi network
#do_connect(secrets.SSID, secrets.WIFI_PASS)

#import webrepl
#webrepl.start()
