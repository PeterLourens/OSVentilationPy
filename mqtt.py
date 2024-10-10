from umqtt.simple import MQTTClient


mqtt_server = '192.168.0.15'
mqtt_user = ''
mqtt_pass = ''
topic = "OSVentilationPy"
ClientID = "OSVentilationPy"

def mqttConnect():
    print('\nConnected to MQTT Broker "%s"' % (mqtt_server))
    client = MQTTClient(ClientID, mqtt_server, 1883, mqtt_user, mqtt_pass)
    client.connect()
    return client

def mqttReconnect():
    print('Failed to connect to MQTT broker, Reconnecting...' % (mqttt_server))
    time.sleep(5)
    client.reconnect()

def mqttPublish(topic):
    try:
        client = connect()
    except OSError as e:
        reconnect()
        
    while True:
        print('send message %s on topic %s' % (msg, topic))
        client.publish(topic, msg, qos=0)
        time.sleep(1)