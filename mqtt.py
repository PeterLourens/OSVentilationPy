#from umqtt.simple import MQTTClient
from robust import *
from time import sleep
from secrets import *

import time

def mqttConnect():
    print('\nConnected to MQTT Broker "%s"' % (MQTT_SERVER))
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_SERVER, MQTT_PORT, MQTT_USER, MQTT_PASS)
    client.connect()
    return client

def mqttReconnect():
    print('Failed to connect to MQTT broker, Reconnecting...')
    time.sleep(5)
    client.reconnect()

def mqttPublish(client,msg,topic,qos):
    #try:
        #client = mqttConnect()
        #client = mqttIsConnected()
        #client.ping()
        #client.ping()
    #except OSError as e:
        #print("\nLost connection to mqtt broker. Reconnecting....")
        #mqttReconnect()
    print('Send message %s on topic %s with QOS=%s' % (msg, topic, qos))
    client.publish(topic, msg, qos)
    time.sleep(1)




#def mqttIsConnected():
#    try:
#        client.ping()
#        client.ping()
#    except:
#        print("\nLost connection to mqtt broker.")
#        return False
#    else:
#        return True


