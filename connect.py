import secrets
import network
import time

from machine import Pin

led = Pin(2, Pin.OUT)

def do_connect(ssid, pwd):
    global sta_if
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        try:
            led.value(1)
            print('connecting to network...')
            sta_if.active(True)
            sta_if.connect(ssid, pwd)
            time.sleep_ms(1000)
            while not sta_if.isconnected():
                #print("WIFI connection not connected, try again")
                #sta_if.disconnect()
                #sta_if.connect(ssid, pwd)
                #time.sleep_ms(1000)
                pass
        except OSError:
            pass
    print('network config:', sta_if.ifconfig())
    led.value(0)

def check_connection():
    if sta_if.isconnected():
        print("WIFI is connected")
        return True
    else:
        print("No WIFI connection")
        return False

# Attempt to connect to WiFi network
#do_connect(secrets.SSID, secrets.WIFI_PASS)


