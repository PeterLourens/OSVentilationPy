#from umqtt.simple import MQTTClient
from robust import *
from time import sleep

import time

global mqttServer
global mqqtUser
global mqttPass
global ClientID

mqttServer = '192.168.0.15'
mqttUser = ''
mqttPass = ''
ClientID = "OSVentilationPy"

def mqttConnect():
    print('\nConnected to MQTT Broker "%s"' % (mqttServer))
    client = MQTTClient(ClientID, mqttServer, 1883, mqttUser, mqttPass)
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


