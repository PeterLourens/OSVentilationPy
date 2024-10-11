"""
mqtt.py
"""
from umqtt.simple import MQTTClient
from json import dumps
from utime import sleep, time

mqtt_broker = "xxx"
mqtt_broker_port = "8883"
mqtt_client_pub = "esp32_pub"
mqtt_client_sub = "esp32_sub"
mqtt_keep_alive = 60 #time in seconds until a keep alive is sent
with open('ca.crt') as f:
    ca_cert = f.read()
sub_received = False
message_sub = "empty"

# sub_received messages from subscriptions will be delivered to this callback
def mqtt_client_sub_callback(topic, msg):
    global sub_received
    global message_sub
    sub_received = True
    message_sub = msg
    #print(msg)
    
mqtt_pub = MQTTClient(mqtt_client_pub, mqtt_broker, mqtt_broker_port, ssl=True, ssl_params={"cert":"ca_cert"})
mqtt_sub = MQTTClient(mqtt_client_sub, mqtt_broker, mqtt_broker_port, ssl=True, ssl_params={"cert":"ca_cert"})
#mqtt_pub = MQTTClient(mqtt_client_pub, mqtt_broker, mqtt_broker_port)
#mqtt_sub = MQTTClient(mqtt_client_sub, mqtt_broker, mqtt_broker_port)
mqtt_sub.set_callback(mqtt_client_sub_callback)
   
#connect and reconnect to mqtt broker
def mqtt_connect():
    print("\nconnect to mqtt broker...")
    try:
        mqtt_pub.connect()
        mqtt_sub.connect(clean_session=False)
    except:
        print("\ncan't connect to mqtt broker...")
        return False
    else:
        print("\nconnected to mqtt broker...")
        return True


def mqtt_subscribe():
    try:
        mqtt_sub.subscribe(mqtt_client_pub,qos=1)
    except:
        print("\ncouldn't subscribe to mqtt broker...")
    else:
        print("subscribed to mqtt broker")
        pass
    

def mqtt_publish(message_pub):
    global message_sub
    global sub_received
    message_sub = "empty"
    sub_received = False
    sub_received_time = time()
        
    while str(message_sub, 'utf-8') != str(message_pub):
        published = False
        while not published:
            try:
                mqtt_pub.publish(mqtt_client_pub, dumps(message_pub), qos=0)
            except:
                print("\ncouldn't publish to mqtt broker...")
            else:
                print("published {} to mqtt broker".format(message_pub))
                published = True
        while not sub_received:
            try:
                mqtt_sub.check_msg()
            except:
                print("\ncouldn't wait for msg from mqtt broker...")
                sleep(1)
            else:
                if time()-sub_received_time > 5:
                    published = False
                    print("\ntimeout while waiting for message from mqtt broker, publish again...")
                    

def mqtt_isconnected():
    try:
        mqtt_pub.ping()
        mqtt_pub.ping()
    except:
        print("\nlost connection to mqtt broker...")
        return False
    else:
        return True    

        