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

#============================================================
# Global variables
#============================================================
global qos
global mqttClient
global stateTransitionMatrix
#global utcOffset


#============================================================
# MQTT Connection
#============================================================
qos = 0

try:
    mqttClient = mqttConnect()
except OSError as e:
    mqttReconnect()


#============================================================
# Real Time Clock & time sync with NTP server & UTC_OFFSET calculation
#============================================================
rtc = machine.RTC()
dateTime = rtc.datetime()

print("\nSyncing with NTP server")
ntptime.settime()
print("RTC datetime", rtc.datetime())

utcOffset = utcOffset()
actual_time = time.localtime(time.time() + utcOffset)
print("Actual time", actual_time)

#============================================================
# State Machine Matrix
#============================================================
print("\nOpening state transistionMatrix")
with open('stateTransitionMatrix.json') as f:
    stateMachineMatrix = json.loads(f.read())


#============================================================
# System stats
#============================================================
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


#============================================================
# Statemachine
#============================================================
stateMachine = StateMachine()

# States Logic Functions
def init_logic():
    # Referenced global variables
    
    if stateMachine.execute_once:
        # 
        print("\nMachine in init state")
        
        # Set all valves to default value
        for i in range(12):
            valve = "valve" + str(i) + "Position"
            requestedPosition = stateMachineMatrix["transition0"][valve]
            moveValve(requestedPosition, i)
            clearOutputs()
            # Publish to mqtt server
            topic = "OSVentilationPy/position/valve" + str(i)
            mqttPublish(mqttClient, str(requestedPosition) , topic, int(qos))
            time.sleep_ms(200)

    # Code that executes continously during state
    timeOfDay = evaluateDayOrNight()
    sleep(1)
    
    # Publish state of state machine
    state = "init"
    topic = "OSVentilationPy/operatingMode/state"
    mqttPublish(mqttClient, state, topic, int(qos))
    
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

    # Code that executes continously during state
    
    # Transition id 3 - day to night
    sleep(10)
    timeOfDay = evaluateDayOrNight()
    topic = "OSVentilationPy/operatingMode/time"
    mqttPublish(mqttClient, timeOfDay, topic, int(qos))
    time.sleep_ms(100)
    
    # Publish state of state machine
    state = "day"
    topic = "OSVentilationPy/operatingMode/state"
    mqttPublish(mqttClient, state, topic, int(qos))
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
            mqttPublish(mqttClient, str(measurement[key]), topic, int(qos))
            time.sleep_ms(200)
    
    # Read valve position of requested valve from file and publish valve positions to MQTT
    with open('valvePositions.json') as f:
        valvePositions = json.loads(f.read())    
    
    for i in range(12):
        topic = "OSVentilationPy/position/valve" + str(i)
        valvePosition = valvePositions[("valve" + str(i))]
        print("\nTopic is:", topic, "ValvePosition is:", valvePosition)
        mqttPublish(mqttClient, str(valvePosition), topic, int(qos))
        time.sleep_ms(200)
    
    f.close()
    
    # Conditions to make transition to other states
    if timeOfDay == "night" and SCD41Reading[2] <900:
        print("\nTime of day is:",timeOfDay, "CO2 is:",SCD41Reading[2], ", StateMachine transitions to night")
        stateMachine.force_transition_to(night)
    elif timeOfDay == "day" and SCD41Reading[2] >900:
        print("\nTime of day is:",timeOfDay, "CO2 is:",SCD41Reading[2], ", StateMachine transitions to highCO2Day")
        stateMachine.force_transition_to(highCO2Day)
    elif timeOfDay == "night" and SCD41Reading[2] >900:
        print("\nTime of day is:",timeOfDay, "CO2 is:",SCD41Reading[2], ", StateMachine transitions to highCO2Night")
        stateMachine.force_transition_to(highCO2Night)
    else:
        pass

def night_logic():
    # Referenced global variables
    
    if stateMachine.execute_once:
        print("Machine in night state")
        sensorData = {}

    # Code that executes continously during state
    
    # Transition id 4 - night to day
    sleep(10)
    timeOfDay = evaluateDayOrNight()
    topic = "OSVentilationPy/operatingMode/time"
    mqttPublish(mqttClient, timeOfDay, topic, int(qos))
    time.sleep_ms(100)
    
    # Publish state of state machine
    state = "night"
    topic = "OSVentilationPy/operatingMode/state"
    mqttPublish(mqttClient, state, topic, int(qos))
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
            mqttPublish(mqttClient, str(measurement[key]), topic, int(qos))
            time.sleep_ms(200)

    # Read valve position of requested valve from file and publish valve positions to MQTT
    with open('valvePositions.json') as f:
        valvePositions = json.loads(f.read())    
    
    for i in range(12):
        topic = "OSVentilationPy/position/valve" + str(i)
        valvePosition = valvePositions[("valve" + str(i))]
        print("\nTopic is:", topic, "ValvePosition is:", valvePosition)
        mqttPublish(mqttClient, str(valvePosition), topic, int(qos))
        time.sleep_ms(200)
    
    f.close()

    # Conditions to make transition to other states
    if timeOfDay == "day" and SCD41Reading[2] <900:
        print("\nTime of day is:",timeOfDay, "CO2 is:",SCD41Reading[2], ", StateMachine transitions to day")
        stateMachine.force_transition_to(day)
    elif timeOfDay == "day" and SCD41Reading[2] >900:
        print("\nTime of day is:",timeOfDay, "CO2 is:",SCD41Reading[2], ", StateMachine transitions to highCO2day state")
        stateMachine.force_transition_to(highCO2Day)
    elif timeOfDay == "night" and SCD41Reading[2] >900:
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
    
    # Code that executes continously during state
    sleep(10)
    timeOfDay = evaluateDayOrNight()
    topic = "OSVentilationPy/operatingMode/time"
    mqttPublish(mqttClient, timeOfDay, topic, int(qos))
    time.sleep_ms(100)
    
    # Publish state of state machine
    state = "highCO2Day"
    topic = "OSVentilationPy/operatingMode/state"
    mqttPublish(mqttClient, state, topic, int(qos))
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
            mqttPublish(mqttClient, str(measurement[key]), topic, int(qos))
            time.sleep_ms(200)

    # Read valve position of requested valve from file and publish valve positions to MQTT
    with open('valvePositions.json') as f:
        valvePositions = json.loads(f.read())    
    
    for i in range(12):
        topic = "OSVentilationPy/position/valve" + str(i)
        valvePosition = valvePositions[("valve" + str(i))]
        print("\nTopic is:", topic, "ValvePosition is:", valvePosition)
        mqttPublish(mqttClient, str(valvePosition), topic, int(qos))
        time.sleep_ms(200)
    
    f.close()
    
    # Conditions to make transition to other states
    if timeOfDay == "day" and SCD41Reading[2] <700:
        print("\nTime of day is:",timeOfDay, "CO2 is:",SCD41Reading[2], ", StateMachine transistions to day")
        stateMachine.force_transition_to(day)
    elif timeOfDay == "night" and SCD41Reading[2] >900:
        print("\nTime of day is:",timeOfDay, "CO2 is:",SCD41Reading[2], ", StateMachine transitions to highCO2Night")
        stateMachine.force_transition_to(highCO2Night)
    elif timeOfDay == "night" and SCD41Reading[2] <700:
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
        
    # Code that executes continously during state    
    sleep(10)
    timeOfDay = evaluateDayOrNight()
    topic = "OSVentilationPy/operatingMode/time"
    mqttPublish(mqttClient, timeOfDay, topic, int(qos))
    time.sleep_ms(100)
    
    # Publish state of state machine
    state = "highCO2Night"
    topic = "OSVentilationPy/operatingMode/state"
    mqttPublish(mqttClient, state, topic, int(qos))
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
            mqttPublish(mqttClient, str(measurement[key]), topic, int(qos))
            time.sleep_ms(200)

    # Read valve position of requested valve from file and publish valve positions to MQTT
    with open('valvePositions.json') as f:
        valvePositions = json.loads(f.read())    
    
    for i in range(12):
        topic = "OSVentilationPy/position/valve" + str(i)
        valvePosition = valvePositions[("valve" + str(i))]
        print("\nTopic is:", topic, "ValvePosition is:", valvePosition)
        mqttPublish(mqttClient, str(valvePosition), topic, int(qos))
        time.sleep_ms(200)
    
    f.close()    
        
    # Conditions to make transition to other states
    if timeOfDay == "day" and SCD41Reading[2] <700:
        print("\nTime of day is:",timeOfDay, "CO2 is:",SCD41Reading[2], ", StateMachine transitions to day state")
        stateMachine.force_transition_to(day)
    elif timeOfDay == "day" and SCD41Reading[2] >900:
        print("\nTime of day is:",timeOfDay, "CO2 is:",SCD41Reading[2], ", StateMachine transitions to highCO2Day")
        stateMachine.force_transition_to(highCO2Day)
    elif timeOfDay == "night" and SCD41Reading[2] <700:
        print("\nTime of day is:",timeOfDay, "CO2 is:",SCD41Reading[2], ", StateMachine transitions to highCO2Night")
        stateMachine.force_transition_to(night)
    else:
        pass    

# Add states to machine (Also create state objects)
init = stateMachine.add_state(init_logic)
day = stateMachine.add_state(day_logic)
night = stateMachine.add_state(night_logic)
higCO2Day = stateMachine.add_state(highCO2Day_logic)
higCO2Night = stateMachine.add_state(highCO2Night_logic)

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

# MQTT Connect
#mqttConnect()
#mqttPublish("3","OSVEntilationPy/SCD41/CO2",0)

# Move valve
#requestedPosition=4
#valveNumber=11
#moveValve(requestedPosition, valveNumber)

# Everything off after valve movement
#clearOutputs()

# Main Loop:
while True:
    stateMachine.run()




