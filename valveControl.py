import time
import json
import uos
from sr74hc595_bitbang import SR74HC595_BITBANG
from machine import Pin, SoftI2C

# Pins for first string of 3 74HC595 ICs
ser1 = Pin(14, Pin.OUT)
rclk1 = Pin(12, Pin.OUT)
srclk1 = Pin(13, Pin.OUT)

# Pins for second string of 3 74HC595 ICs
ser2 = Pin(27, Pin.OUT)
rclk2 = Pin(25, Pin.OUT)
srclk2 = Pin(26, Pin.OUT)

sr1 = SR74HC595_BITBANG(ser1, srclk1, rclk1)
sr2 = SR74HC595_BITBANG(ser2, srclk2, rclk2)

def moveValve(requestedPosition, valveNumber):
    
    # Print input variables
    print("\nRequested position is: ", requestedPosition)
    print("Valve number: ", valveNumber)
    
    # Read valve position of requested valve from file
    with open('valvePositions.json') as f:
        data = json.loads(f.read())
    print("\nCurrent valve positions:", data)
    
    # Compile valve number from string valve and input valveNumber into function
    valve = "valve" + str(valveNumber)
    
    # Get current position from data from file
    currentPosition=int(data[valve])
    print("Current position for",valve,"from file is",currentPosition)
    
    # Each valve can move from position 0 (fully closed) to 24 (fully open).
    # The requested position is the absolute value of the new position.
    # Based on current position and requested position change this function will decide in which.
    # direction to move and how many steps.

    # Check if requestedPosition is not out of bounds
    if requestedPosition > 24:
        requestedPosition = 24
    elif requestedPosition < 0:
        requestedPosition = 0
    else:
        pass
    
    # Logics to decide which direction to move and how many steps
    if requestedPosition < currentPosition:
        # Means valve needs to close
        direction = "close"
        valvePositionMove = currentPosition - requestedPosition
        print("Valve will move", valvePositionMove, "positions", "in direction", direction)
        newPosition = requestedPosition
    elif requestedPosition > currentPosition:
        # Means valve needs to open further
        direction = "open"
        valvePositionMove = requestedPosition - currentPosition
        print("Valve will move", valvePositionMove, "positions", "in direction", direction)
        newPosition = requestedPosition
    else:
        # Current position is the same requestedPosition so nothing to do
        valvePositionMove = 0
        newPosition = requestedPosition
    
    # Switching pattern for the first 4 bits
    pattern= [0b00000101,0b00001001,0b00001010,0b00000110]
    
    # Create array for output pattern
    output = [ [0]*4 for i in range(4)]
    
    # One complete rotation requires 24 cycles through the pattern
    CyclesPerRotation = 24
    
    # For valves 0 - 5 use the pins ser1, srclk1, rclk1, for valves 6 - 11 use ser2, srclk2, rclk2
    if valveNumber < 6:
        sr = SR74HC595_BITBANG(ser1, srclk1, rclk1)
    else:
        sr = SR74HC595_BITBANG(ser2, srclk2, rclk2)

    # Assign correct pattern to valvenumber
    if valveNumber == 0 or valveNumber == 6:
        for i in range(4):
            output[0][i] = pattern[i] <<4
            output[1][i] = 0
            output[2][i] = 0
    elif valveNumber == 1 or valveNumber == 7:
        for i in range(4):
            output[0][i] = pattern[i]    #Shift pattern 4 bits 
            output[1][i] = 0
            output[2][i] = 0
    elif valveNumber == 2 or valveNumber == 8:
        for i in range(4):
            output[0][i] = 0
            output[1][i] = pattern[i] <<4
            output[2][i] = 0
    elif valveNumber == 3 or valveNumber == 9:
        for i in range(4):
            output[0][i] = 0
            output[1][i] = pattern[i]
            output[2][i] = 0
    elif valveNumber == 4 or valveNumber == 10:
        for i in range(4):
            output[0][i] = 0
            output[1][i] = 0
            output[2][i] = pattern[i] <<4
    elif valveNumber == 5 or valveNumber == 11:
        for i in range(4):
            output[0][i] = 0
            output[1][i] = 0
            output[2][i] = pattern[i]
    else:
        pass

    #print output pattern
    #print("\n",output)

    #Write output sequence based on direction
    if valvePositionMove != 0:    # No need to do anything no move of valve is required
        if direction == "close":
            for j in range(int(valvePositionMove) * CyclesPerRotation):
                for i in range(0,4,1):
                    sr.latch()
                    sr.bits(output[2][i], 8)
                    sr.bits(output[1][i], 8)
                    sr.bits(output[0][i], 8)
                    time.sleep_ms(5)    # 5ms delay (200Hz switching time) for one step of the valve 
        elif direction == "open":
            for j in range(int(valvePositionMove) * CyclesPerRotation):
                for i in range(3,-1,-1):
                    sr.latch()
                    sr.bits(output[2][i], 8)
                    sr.bits(output[1][i], 8)
                    sr.bits(output[0][i], 8)
                    time.sleep_ms(5)
        else:
            print("Incorrection direction given, use either 0 (open) or 1 (close)")
    else:
        print("Valve move is 0")

    # Now write new position to of valve to json file. Data from the file before move is still available in variable data
    data[valve] = newPosition
    print("New valve positions:", data)
    
    # Write data to json file
    with open('valvePositions.json','w') as f:
        json.dump(data, f)

def clearOutputs():
    sr1.latch()
    sr1.bits(0b00000000, 8)
    sr1.bits(0b00000000, 8)
    sr1.bits(0b00000000, 8)
    sr1.latch()
    
    sr2.latch()
    sr2.bits(0b00000000, 8)
    sr2.bits(0b00000000, 8)
    sr2.bits(0b00000000, 8)
    sr2.latch()

def defaultValvePositions():

    defaultValvePositions = {
        'valve0': '4',
        'valve1': '4',
        'valve2': '4',
        'valve3': '0',
        'valve4': '0',
        'valve5': '4',
        'valve6': '24',
        'valve7': '0',
        'valve8': '4',
        'valve9': '4',
        'valve10': '4',
        'valve11': '4'
    }
    with open('valvePositions.json','w') as f:
        json.dump(defaultValvePositions, f)

def checkValvePositionFile():
    # Check is valvePositions.json exists and if not write the default positions
    filename="valvePositions.json"
    if filename in uos.listdir():
        print("\nValve status file found.")
        if uos.stat(filename)[6] < 100:
            print("\nValve status file found, but too small. Creating new default file")
            defaultValvePositions()
        else:
            print("Everything ok with valve status file")
    else:
        print("\nValve status file not found. Creating new default one")
        defaultValvePositions()


