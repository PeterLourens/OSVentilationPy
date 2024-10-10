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
qos = 1

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
        print("\nMachine in init state")
        # Set all valves to default value
        setposition = stateMachineMatrix["transition1"]["valve1Position"]
        print(setposition)

    # Code that executes continously during state
    timeOfDay = evaluateDayOrNight()
    sleep(1)
    
    # Publish state of state machine
    state = "init"
    topic = "OSVentilationPy/operatingMode/state"
    mqttPublish(mqttClient, state, topic, int(qos))
    
    if timeOfDay == "day":
        stateMachine.force_transition_to(day)
    elif timeOfDay == "night":
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
    
    # Publish state of state machine
    state = "day"
    topic = "OSVentilationPy/operatingMode/state"
    mqttPublish(mqttClient, state, topic, int(qos))
    
    #Read sensors, return array with readings
    SCD41Reading = readSCD41(scd41)
    DHT22Reading = readDHT22()

    # Dictionary sensorData
    sensorData = { "SCD41": { "Temperature": SCD41Reading[0], "RelativeHumidity": SCD41Reading[1], "CO2": SCD41Reading[2]}, "DHT22": {"Temperature": DHT22Reading[0], "RelativeHumidity": DHT22Reading[1]}}
    
    # Iterate through nested dictionary sensorData and publish to MQTT
    for sensorType, measurement in sensorData.items():
        print("\nSensor:", sensorType)
    
        for key in measurement:
            #print(key + ':', measurement[key])
            topic = "OSVentilationPy/" + sensorType + "/" + key 
            mqttPublish(mqttClient, str(measurement[key]), topic, int(qos))
    
    if timeOfDay == "night":
        stateMachine.force_transition_to(night)

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
    
    # Publish state of state machine
    state = "night"
    topic = "OSVentilationPy/operatingMode/state"
    mqttPublish(mqttClient, state, topic, int(qos))
    
    #Read sensors, return array with readings
    SCD41Reading = readSCD41(scd41)
    DHT22Reading = readDHT22()

    # Dictionary sensorData
    sensorData = { "SCD41": { "Temperature": SCD41Reading[0], "RelativeHumidity": SCD41Reading[1], "CO2": SCD41Reading[2]}, "DHT22": {"Temperature": DHT22Reading[0], "RelativeHumidity": DHT22Reading[1]}}
    
    # Iterate through nested dictionary sensorData and publish to MQTT
    for sensorType, measurement in sensorData.items():
        print("\nSensor:", sensorType)
    
        for key in measurement:
            #print(key + ':', measurement[key])
            topic = "OSVentilationPy/" + sensorType + "/" + key 
            mqttPublish(mqttClient, str(measurement[key]), topic, int(qos))
    
    if timeOfDay == "day":
        stateMachine.force_transition_to(day)

# Add states to machine (Also create state objects)
init = stateMachine.add_state(init_logic)
day = stateMachine.add_state(day_logic)
night = stateMachine.add_state(night_logic)


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




