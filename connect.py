import secrets
import network

def do_connect(ssid, pwd):
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

def check_connection():
    if sta_if.isconnected() == True
        print("WIFI is still conected")
        return True
    else
        print("No WIFI connection")
        return False

# Attempt to connect to WiFi network
do_connect(secrets.SSID, secrets.WIFI_PASS)
