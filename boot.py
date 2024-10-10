# This file is executed on every boot (including wake-boot from deepsleep)

from sr74hc595_bitbang import SR74HC595_BITBANG
from machine import Pin, SoftI2C
from valveControl import clearOutputs

clearOutputs()
print("clearing outputs")

led = Pin(2, Pin.OUT)

def do_connect(ssid, pwd):
    import network
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        led.value(1)
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(ssid, pwd)
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())
    led.value(0)
 
# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
 
# Attempt to connect to WiFi network
do_connect('DIRK3', '095679706460482465742852')

import webrepl
webrepl.start()
