from time import sleep
from valveControl import *
from statemachine import *
from scd41 import SCD4X
from sensors import *
from mqtt import *
from timefunctions import *

import time
import gc
import _thread
import micropython
import os
import machine
import ntptime

#=========================================================================
# Global variables
#=========================================================================
global mqttClient
global stateTransitionMatrix
global remoteState

#=========================================================================
# Constants
#=========================================================================
CO2_MAX_LEVEL = 1000
CO2_MIN_LEVEL = 800
MQTT_QOS = 0
SUBSCRIBE_TOPIC = b"zigbee2mqtt/Reading light switch/action"

#=========================================================================
# MQTT Connection
#=========================================================================
try:
    mqttClient = mqttConnect()
except OSError as e:
    mqttReconnect()

# Call back function
def sub_cb(topic, msg):
    print((topic, msg))
    if msg == b'on':
        remoteState = "on"
    if msg == b'off':
        remoteState = "off"      
    else:
        remoteState = "undefined"
    return remoteState

# Subscribe to remote control status
mqttClient.set_callback(sub_cb)
mqttClient.subscribe(SUBSCRIBE_TOPIC)
print("Subscribed to:", SUBSCRIBE_TOPIC)

#=========================================================================
# Real Time Clock & time sync with NTP server & UTC_OFFSET calculation
#=========================================================================
rtc = machine.RTC()
dateTime = rtc.datetime()

print("\nSyncing with NTP server")
ntptime.settime()
print("RTC datetime", rtc.datetime())

utcOffset = utcOffset()
actual_time = time.localtime(time.time() + utcOffset)
print("Actual time", actual_time)

#=========================================================================
# State Machine Matrix
#=========================================================================
print("\nOpening state transistionMatrix")
with open('stateTransitionMatrix.json') as f:
    stateMachineMatrix = json.loads(f.read())

#=========================================================================
# System stats
#=========================================================================
def df():
  s = os.statvfs('//')
  return ('{0} MB'.format((s[0]*s[3])/1048576))

def free(full=False):
  gc.collect()
  F = gc.mem_free()
  A = gc.mem_alloc()
  T = F+A
  P = '{0:.2f}%'.format(F/T*100)
  if not full: return P
  else : return ('Total:{0} Free:{1} ({2})'.format(T,F,P))

def setValves():
    pass

#=========================================================================
# Statemachine
#=========================================================================
stateMachine = StateMachine()

# States Logic Functions
def init_logic():
    # Referenced global variables
    
    if stateMachine.execute_once:
        # 
        print("\nMachine in init state")
        
        # For this state valve positions have to change to default position. This is transition0
        #for i in range(12):
        #    valve = "valve" + str(i) + "Position"
        #    requestedPosition = stateMachineMatrix["transition0"][valve]
        #    moveValve(requestedPosition, i)
        #    clearOutputs()
            
            # Publish to mqtt server
        #    topic = "OSVentilationPy/position/valve" + str(i)
        #    mqttPublish(mqttClient, str(requestedPosition) , topic, int(MQTT_QOS))
        #    time.sleep_ms(200)
        
        # Set fan speed to low
        print("Fan speed is low")
        
        # Set remote to off
        remoteState = "off"
        mqttPublish(mqttClient, remoteState , SUBSCRIBE_TOPIC, int(MQTT_QOS))
        time.sleep_ms(200)

    # Code that executes continously during state
    timeOfDay = evaluateDayOrNight()
    sleep(1)
    
    # Publish state of state machine
    state = "init"
    topic = "OSVentilationPy/operatingMode/state"
    mqttPublish(mqttClient, state, topic, int(MQTT_QOS))
    
    # StateMachine can only transition to either "day" or "night" states
    if timeOfDay == "day":
        print("\nTime of day is:",timeOfDay, ", StateMachine transitions to day")
        stateMachine.force_transition_to(day)
    elif timeOfDay == "night":
        print("\nTime of day is:",timeOfDay, ", StateMachine transitions to night")
        stateMachine.force_transition_to(night)
    

def day_logic():
    # Referenced global variables
    
    if stateMachine.execute_once:
        print("Machine in day state")
        # Create empty dictionary
        sensorData = {}
        
        # For this state valve positions have to change to default position. This is transition0
        for i in range(12):
            valve = "valve" + str(i) + "Position"
            requestedPosition = stateMachineMatrix["transition0"][valve]
            moveValve(requestedPosition, i)
            clearOutputs()
            
            # Publish to mqtt server
            topic = "OSVentilationPy/position/valve" + str(i)
            mqttPublish(mqttClient, str(requestedPosition) , topic, int(MQTT_QOS))
            time.sleep_ms(200)
        
        # Set fan speed to medium
        print("Fan speed is medium")

    # Code that executes continously during state
    
    # Evaluate time and sensor data and publish to MQTT
    sleep(10)
    timeOfDay = evaluateDayOrNight()
    topic = "OSVentilationPy/operatingMode/time"
    mqttPublish(mqttClient, timeOfDay, topic, int(MQTT_QOS))
    time.sleep_ms(100)
    
    # Publish state of state machine
    state = "day"
    topic = "OSVentilationPy/operatingMode/state"
    mqttPublish(mqttClient, state, topic, int(MQTT_QOS))
    time.sleep_ms(100)
    
    #Read sensors, functions return array with readings
    SCD41Reading = readSCD41(scd41)
    DHT22Reading = readDHT22()

    # Dictionary with sensorData
    sensorData = { "SCD41": { "Temperature": SCD41Reading[0], "RelativeHumidity": SCD41Reading[1], "CO2": SCD41Reading[2]}, "DHT22": {"Temperature": DHT22Reading[0], "RelativeHumidity": DHT22Reading[1]}}
    
    # Iterate through nested dictionary sensorData and publish to MQTT
    for sensorType, measurement in sensorData.items():
        print("\nSensor:", sensorType)
        time.sleep_ms(200)
    
        for key in measurement:
            #print(key + ':', measurement[key])
            topic = "OSVentilationPy/" + sensorType + "/" + key 
            mqttPublish(mqttClient, str(measurement[key]), topic, int(MQTT_QOS))
            time.sleep_ms(200)
    
    # Read valve position of requested valve from file and publish valve positions to MQTT
    with open('valvePositions.json') as f:
        valvePositions = json.loads(f.read())    
    
    for i in range(12):
        topic = "OSVentilationPy/position/valve" + str(i)
        valvePosition = valvePositions[("valve" + str(i))]
        print("\nTopic is:", topic, "ValvePosition is:", valvePosition)
        mqttPublish(mqttClient, str(valvePosition), topic, int(MQTT_QOS))
        time.sleep_ms(200)
    
    f.close()
    
    # Check for status of remote control. The signal is maintained (so remains on when pressed 1 and off when 0)
    #while True:
    mqttClient.check_msg()
    print("\nremoteState is:", remoteState)
    
    # Evaluate conditions to make transition to other states
    if timeOfDay == "night" and SCD41Reading[2] < CO2_MAX_LEVEL:
        print("\nTime of day is:",timeOfDay, "CO2 is:",SCD41Reading[2], ", StateMachine transitions to night")
        stateMachine.force_transition_to(night)
    elif timeOfDay == "day" and SCD41Reading[2] > CO2_MAX_LEVEL:
        print("\nTime of day is:",timeOfDay, "CO2 is:",SCD41Reading[2], ", StateMachine transitions to highCO2Day")
        stateMachine.force_transition_to(highCO2Day)
    elif timeOfDay == "night" and SCD41Reading[2] > CO2_MAX_LEVEL:
        print("\nTime of day is:",timeOfDay, "CO2 is:",SCD41Reading[2], ", StateMachine transitions to highCO2Night")
        stateMachine.force_transition_to(highCO2Night)
    else:
        pass

def night_logic():
    # Referenced global variables
    
    if stateMachine.execute_once:
        print("Machine in night state")
        sensorData = {}
        
        # For this state valve positions have to change to default position. This is transition0
        for i in range(12):
            valve = "valve" + str(i) + "Position"
            requestedPosition = stateMachineMatrix["transition0"][valve]
            moveValve(requestedPosition, i)
            clearOutputs()
            
            # Publish to mqtt server
            topic = "OSVentilationPy/position/valve" + str(i)
            mqttPublish(mqttClient, str(requestedPosition) , topic, int(MQTT_QOS))
            time.sleep_ms(200)

        # Set fan speed low
        print("Fan speed is low")

    # Code that executes continously during state
    
    # Evaluate time and sensor data and publish to MQTT
    sleep(10)
    timeOfDay = evaluateDayOrNight()
    topic = "OSVentilationPy/operatingMode/time"
    mqttPublish(mqttClient, timeOfDay, topic, int(MQTT_QOS))
    time.sleep_ms(100)
    
    # Publish state of state machine
    state = "night"
    topic = "OSVentilationPy/operatingMode/state"
    mqttPublish(mqttClient, state, topic, int(MQTT_QOS))
    time.sleep_ms(100)
    
    #Read sensors, return array with readings
    SCD41Reading = readSCD41(scd41)
    DHT22Reading = readDHT22()

    # Dictionary sensorData
    sensorData = { "SCD41": { "Temperature": SCD41Reading[0], "RelativeHumidity": SCD41Reading[1], "CO2": SCD41Reading[2]}, "DHT22": {"Temperature": DHT22Reading[0], "RelativeHumidity": DHT22Reading[1]}}
    
    # Iterate through nested dictionary sensorData and publish to MQTT
    for sensorType, measurement in sensorData.items():
        print("\nSensor:", sensorType)
        time.sleep_ms(200)
    
        for key in measurement:
            #print(key + ':', measurement[key])
            topic = "OSVentilationPy/" + sensorType + "/" + key 
            mqttPublish(mqttClient, str(measurement[key]), topic, int(MQTT_QOS))
            time.sleep_ms(200)

    # Read valve position of requested valve from file and publish valve positions to MQTT
    with open('valvePositions.json') as f:
        valvePositions = json.loads(f.read())    
    
    for i in range(12):
        topic = "OSVentilationPy/position/valve" + str(i)
        valvePosition = valvePositions[("valve" + str(i))]
        print("\nTopic is:", topic, "ValvePosition is:", valvePosition)
        mqttPublish(mqttClient, str(valvePosition), topic, int(MQTT_QOS))
        time.sleep_ms(200)
    
    f.close()

    # Evaluate conditions to make transition to other states
    if timeOfDay == "day" and SCD41Reading[2] < CO2_MIN_LEVEL:
        print("\nTime of day is:",timeOfDay, "CO2 is:",SCD41Reading[2], ", StateMachine transitions to day")
        stateMachine.force_transition_to(day)
    elif timeOfDay == "day" and SCD41Reading[2] > CO2_MAX_LEVEL:
        print("\nTime of day is:",timeOfDay, "CO2 is:",SCD41Reading[2], ", StateMachine transitions to highCO2day state")
        stateMachine.force_transition_to(highCO2Day)
    elif timeOfDay == "night" and SCD41Reading[2] > CO2_MAX_LEVEL:
        print("\nTime of day is:",timeOfDay, "CO2 is:",SCD41Reading[2], ", StateMachine transitions to highCO2night state")
        stateMachine.force_transition_to(highCO2Night)
    else:
        pass

def highCO2Day_logic():
    # Referenced global variables
    
    if stateMachine.execute_once:
        print("Machine in high CO2 day state")
        # Create empty dictionary
        sensorData = {}
        
        # No need to change valve positions because they are set already correctly at init state
        
        # Set fan speed to high
        print("Fan speed is high")
    
    # Code that executes continously during state
    
    # Evaluate time and sensor data and publish to MQTT
    sleep(10)
    timeOfDay = evaluateDayOrNight()
    topic = "OSVentilationPy/operatingMode/time"
    mqttPublish(mqttClient, timeOfDay, topic, int(MQTT_QOS))
    time.sleep_ms(100)
    
    # Publish state of state machine
    state = "highCO2Day"
    topic = "OSVentilationPy/operatingMode/state"
    mqttPublish(mqttClient, state, topic, int(MQTT_QOS))
    time.sleep_ms(100)
    
    #Read sensors, return array with readings
    SCD41Reading = readSCD41(scd41)
    DHT22Reading = readDHT22()

    # Dictionary sensorData
    sensorData = { "SCD41": { "Temperature": SCD41Reading[0], "RelativeHumidity": SCD41Reading[1], "CO2": SCD41Reading[2]}, "DHT22": {"Temperature": DHT22Reading[0], "RelativeHumidity": DHT22Reading[1]}}
    
    # Iterate through nested dictionary sensorData and publish to MQTT
    for sensorType, measurement in sensorData.items():
        print("\nSensor:", sensorType)
        time.sleep_ms(200)
    
        for key in measurement:
            #print(key + ':', measurement[key])
            topic = "OSVentilationPy/" + sensorType + "/" + key 
            mqttPublish(mqttClient, str(measurement[key]), topic, int(MQTT_QOS))
            time.sleep_ms(200)

    # Read valve position of requested valve from file and publish valve positions to MQTT
    with open('valvePositions.json') as f:
        valvePositions = json.loads(f.read())    
    
    for i in range(12):
        topic = "OSVentilationPy/position/valve" + str(i)
        valvePosition = valvePositions[("valve" + str(i))]
        print("\nTopic is:", topic, "ValvePosition is:", valvePosition)
        mqttPublish(mqttClient, str(valvePosition), topic, int(MQTT_QOS))
        time.sleep_ms(200)
    
    f.close()
    
    # Evaluate conditions to make transition to other states
    if timeOfDay == "day" and SCD41Reading[2] < CO2_MIN_LEVEL:
        print("\nTime of day is:",timeOfDay, "CO2 is:",SCD41Reading[2], ", StateMachine transistions to day")
        stateMachine.force_transition_to(day)
    elif timeOfDay == "night" and SCD41Reading[2] > CO2_MAX_LEVEL:
        print("\nTime of day is:",timeOfDay, "CO2 is:",SCD41Reading[2], ", StateMachine transitions to highCO2Night")
        stateMachine.force_transition_to(highCO2Night)
    elif timeOfDay == "night" and SCD41Reading[2] < CO2_MIN_LEVEL:
        print("\nTime of day is:",timeOfDay, "CO2 is:",SCD41Reading[2], ", StateMachine transitions to night")
        stateMachine.force_transition_to(night)
    else:
        pass
    
    
def highCO2Night_logic():
    # Referenced global variables
    
    if stateMachine.execute_once:
        print("Machine in high CO2 night state")
        # Create empty dictionary
        sensorData = {}
        
        # For this state valve positions have to change. This is transition9
        for i in range(12):
            valve = "valve" + str(i) + "Position"
            requestedPosition = stateMachineMatrix["transition9"][valve]
            moveValve(requestedPosition, i)
            clearOutputs()
            
            # Publish to mqtt server
            topic = "OSVentilationPy/position/valve" + str(i)
            mqttPublish(mqttClient, str(requestedPosition) , topic, int(MQTT_QOS))
            time.sleep_ms(200)
        
        # Set fan speed to low
        print("Fan speed is low")
        
    # Code that executes continously during state
    
    # Evaluate time and sensor data and publish to MQTT
    sleep(10)
    timeOfDay = evaluateDayOrNight()
    topic = "OSVentilationPy/operatingMode/time"
    mqttPublish(mqttClient, timeOfDay, topic, int(MQTT_QOS))
    time.sleep_ms(100)
    
    # Publish state of state machine
    state = "highCO2Night"
    topic = "OSVentilationPy/operatingMode/state"
    mqttPublish(mqttClient, state, topic, int(MQTT_QOS))
    time.sleep_ms(100)
    
    #Read sensors, return array with readings
    SCD41Reading = readSCD41(scd41)
    DHT22Reading = readDHT22()

    # Dictionary sensorData
    sensorData = { "SCD41": { "Temperature": SCD41Reading[0], "RelativeHumidity": SCD41Reading[1], "CO2": SCD41Reading[2]}, "DHT22": {"Temperature": DHT22Reading[0], "RelativeHumidity": DHT22Reading[1]}}
    
    # Iterate through nested dictionary sensorData and publish to MQTT
    for sensorType, measurement in sensorData.items():
        print("\nSensor:", sensorType)
        time.sleep_ms(200)
    
        for key in measurement:
            #print(key + ':', measurement[key])
            topic = "OSVentilationPy/" + sensorType + "/" + key 
            mqttPublish(mqttClient, str(measurement[key]), topic, int(MQTT_QOS))
            time.sleep_ms(200)

    # Read valve position of requested valve from file and publish valve positions to MQTT
    with open('valvePositions.json') as f:
        valvePositions = json.loads(f.read())    
    
    for i in range(12):
        topic = "OSVentilationPy/position/valve" + str(i)
        valvePosition = valvePositions[("valve" + str(i))]
        print("\nTopic is:", topic, "ValvePosition is:", valvePosition)
        mqttPublish(mqttClient, str(valvePosition), topic, int(MQTT_QOS))
        time.sleep_ms(200)
    
    f.close()
        
    # Evaluate conditions to make transition to other states
    if timeOfDay == "day" and SCD41Reading[2] < CO2_MIN_LEVEL:
        print("\nTime of day is:",timeOfDay, "CO2 is:",SCD41Reading[2], ", StateMachine transitions to day state")
        stateMachine.force_transition_to(day)
    elif timeOfDay == "day" and SCD41Reading[2] > CO2_MAX_LEVEL:
        print("\nTime of day is:",timeOfDay, "CO2 is:",SCD41Reading[2], ", StateMachine transitions to highCO2Day")
        stateMachine.force_transition_to(highCO2Day)
    elif timeOfDay == "night" and SCD41Reading[2] < CO2_MIN_LEVEL:
        print("\nTime of day is:",timeOfDay, "CO2 is:",SCD41Reading[2], ", StateMachine transitions to highCO2Night")
        stateMachine.force_transition_to(night)
    else:
        pass    

def manualHighSpeed_logic():
    # Referenced global variables
    
    if stateMachine.execute_once:
        print("Machine in manual high speed state")
        # Create empty dictionary
        sensorData = {}
        
        # For this state valve positions have to change to default position. This is transition0
        for i in range(12):
            valve = "valve" + str(i) + "Position"
            requestedPosition = stateMachineMatrix["transition0"][valve]
            moveValve(requestedPosition, i)
            clearOutputs()
            
            # Publish to mqtt server
            topic = "OSVentilationPy/position/valve" + str(i)
            mqttPublish(mqttClient, str(requestedPosition) , topic, int(MQTT_QOS))
            time.sleep_ms(200)
        
        # Set fan speed to low
        print("Fan speed is high")
        
        # Set remote to off
        remoteState = "off"
        mqttPublish(mqttClient, remoteState , SUBSCRIBE_TOPIC, int(MQTT_QOS))
        time.sleep_ms(200)
        
    # Code that executes continously during state
    
    # Evaluate time and sensor data and publish to MQTT
    sleep(10)
    remoteState = "on"
    timeOfDay = evaluateDayOrNight()
    topic = "OSVentilationPy/operatingMode/time"
    mqttPublish(mqttClient, timeOfDay, topic, int(MQTT_QOS))
    time.sleep_ms(100)
    
    # Publish state of state machine
    state = "manualHighSpeed"
    topic = "OSVentilationPy/operatingMode/state"
    mqttPublish(mqttClient, state, topic, int(MQTT_QOS))
    time.sleep_ms(100)
    
    #Read sensors, return array with readings
    SCD41Reading = readSCD41(scd41)
    DHT22Reading = readDHT22()

    # Dictionary sensorData
    sensorData = { "SCD41": { "Temperature": SCD41Reading[0], "RelativeHumidity": SCD41Reading[1], "CO2": SCD41Reading[2]}, "DHT22": {"Temperature": DHT22Reading[0], "RelativeHumidity": DHT22Reading[1]}}
    
    # Iterate through nested dictionary sensorData and publish to MQTT
    for sensorType, measurement in sensorData.items():
        print("\nSensor:", sensorType)
        time.sleep_ms(200)
    
        for key in measurement:
            #print(key + ':', measurement[key])
            topic = "OSVentilationPy/" + sensorType + "/" + key 
            mqttPublish(mqttClient, str(measurement[key]), topic, int(MQTT_QOS))
            time.sleep_ms(200)

    # Read valve position of requested valve from file and publish valve positions to MQTT
    with open('valvePositions.json') as f:
        valvePositions = json.loads(f.read())    
    
    for i in range(12):
        topic = "OSVentilationPy/position/valve" + str(i)
        valvePosition = valvePositions[("valve" + str(i))]
        print("\nTopic is:", topic, "ValvePosition is:", valvePosition)
        mqttPublish(mqttClient, str(valvePosition), topic, int(MQTT_QOS))
        time.sleep_ms(200)
    
    f.close()
        
    # Evaluate conditions to make transition to other states
    if timeOfDay == "day" and SCD41Reading[2] > CO2_MAX_LEVEL:
        print("\nTime of day is:",timeOfDay, "CO2 is:",SCD41Reading[2], ", StateMachine transitions to highCO2Day state")
        stateMachine.force_transition_to(highCO2Day)
    elif timeOfDay == "night" and SCD41Reading[2] > CO2_MAX_LEVEL:
        print("\nTime of day is:",timeOfDay, "CO2 is:",SCD41Reading[2], ", StateMachine transitions to highCO2Night state")
        stateMachine.force_transition_to(highCO2Night)
    elif timeOfDay == "night" and SCD41Reading[2] < CO2_MIN_LEVEL:
        print("\nTime of day is:",timeOfDay, "CO2 is:",SCD41Reading[2], ", StateMachine transitions to night state")
        stateMachine.force_transition_to(night)    
    elif remoteState == "off" and SCD41Reading[2] < CO2_MIN_LEVEL:
        print("\nTime of day is:",timeOfDay, "CO2 is:",SCD41Reading[2], ", StateMachine transitions to night state")
        stateMachine.force_transition_to(day)
    else:
        pass

# Add states to machine (Also create state objects)
init = stateMachine.add_state(init_logic)
day = stateMachine.add_state(day_logic)
night = stateMachine.add_state(night_logic)
highCO2Day = stateMachine.add_state(highCO2Day_logic)
highCO2Night = stateMachine.add_state(highCO2Night_logic)
manualHighSpeed = stateMachine.add_state(manualHighSpeed_logic)

# ===========================================================================================
# Main program
# ===========================================================================================

# Systems stats
disk = df()
mem = free()

print("\nDisk usage: ",disk)
print("Memory free: ", mem)

# Check if valvePosition file is present an correct
checkValvePositionFile()

# All outputs off when starting
clearOutputs()

# Init SCD41 sensor
#global scd41
scd41=initSCD41()
print("\nInit SCD41 sensor complete")

#print(datetime)
dateTime = time.localtime(time.time() + utcOffset)
print("\nCurrent date is:",dateTime[0],"/",dateTime[1],"/",dateTime[2])
print("Current time is:",dateTime[3],":",dateTime[4],":",dateTime[5])
print("Today is",dayOfWeekToDay(dateTime[6]))

# Move valve
#requestedPosition=4
#valveNumber=11
#moveValve(requestedPosition, valveNumber)

# Everything off after valve movement
#clearOutputs()

# Main Loop:
while True:
    stateMachine.run()




