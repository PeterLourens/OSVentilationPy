import time
import ntptime
import machine

def utcOffset():
    # Non leap years:
    # On day 90 day light saving starts at 02:00
    # On day 301 day light saving ends at 03:00

    # Leap years:
    # On day 91 day light saving starts at 02:00
    # On day 302 day light saving ends at 03:00

    # Check leap year
    # If year can be divided by 400 or by 4 and not divided by 100 it is a leap year
    #(year % 400 == 0) or ((year % 4 == 0) and (year % 100 != 0))
    
    rtc = machine.RTC()
    #dateTime = rtc.datetime()
    dateTime = time.localtime(time.time())
    
    if (dateTime[0] % 400 == 0) or (dateTime[0] % 4 == 0) or (dateTime[0] % 100 != 0):
        # Leap year
        print("\nLeap year")
        dstStartDate = 91
        dstEndDate = 301
    else:
        # Non Leap year
        print("\nNo leap year")
        dstStartDate = 90
        dstEndDate = 300
  
    if dateTime[7] >= dstStartDate and dateTime[3] >= 3 and dateTime[7] <= dstEndDate and dateTime[3] <= 2:
        # DST
        utcOffset = 2 * 3600
        print(dateTime)
        print("UTC offset is", utcOffset, "seconds")
        return utcOffset
    else:
        # No DST
        utcOffset = 1 * 3600
        print(dateTime)
        print("UTC offset is", utcOffset, "seconds")
        return utcOffset

def dayOfWeekToDay(dayOfWeek):
    # Array with names of the day. 1 is Monday, 6 is Sunday
    weekDays = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    return weekDays[int(dayOfWeek)]

def evaluateDayOrNight():
    # Update dateTime
    #dateTime = rtc.datetime()
    #utcOffset = utcOffset()
    dateTime = time.localtime(time.time() + utcOffset())
    
    # Get day of the week
    #dayOfWeek = dayOfWeekToDay(dateTime[6])
    
    # Logic to decide it is day or night time
    if dateTime[6] <= 4 and dateTime[3] >= 7 and dateTime[3] < 21: #Weekdays
        timeOfDay = "day"
        print("\ndateTime:",dateTime, ", Weekday and daytime")
    elif dateTime[6] > 4 and dateTime[3] >= 8 and dateTime[3] < 21: #Weekend
        timeOfDay = "day"
        print("\ndateTime:",dateTime, ", Weekend and daytime")
    else:
        timeOfDay = "night"
        print("\ndateTime:",dateTime, ", Night time")
    return timeOfDay

def valveCycleTimesDay():
    
    # Updat dateTime
    dateTime = time.localtime(time.time() + utcOffset())

    # Return True if valve cycle should start, otherwise return False
    if dateTime[3] == 10 and dateTime[4] < 30:
        print("valveCycleDay modus active")
        return True
    elif dateTime[3] == 10 and dateTime[4] >= 30:
        print("valveCycleDay modus not active")
        return False
    elif dateTime[3] == 12 and dateTime[4] < 30:
        print("valveCycleDay modus active")
        return True
    elif dateTime[3] == 12 and dateTime[4] >= 30:
        print("valveCycleDay modus not active")
        return False
    elif dateTime[3] == 14 and dateTime[4] < 30:
        print("valveCycleDay modus active")
        return True
    elif dateTime[3] == 14 and dateTime[4] >= 30:
        print("valveCycleDay modus not active")
        return False
    elif dateTime[3] == 16 and dateTime[4] < 30:
        print("valveCycleDay modus active")
        return True
    elif dateTime[3] == 16 and dateTime[4] >= 30:
        print("valveCycleDay modus not active")
        return False
    elif dateTime[3] == 18 and dateTime[4] > 10 and dateTime[4] < 40:
        print("valveCycleDay modus active")
        return True
    elif dateTime[3] == 18 and dateTime[4] >= 40:
        print("valveCycleDay modus not active")
        return False
    if dateTime[3] == 20 and dateTime[4] < 30:
        print("valveCycleDay modus active")
        return True
    if dateTime[3] == 20 and dateTime[4] >= 30:
        print("valveCycleDay modus not active")
        return False
    else:
        print("valveCycleDay modus not active")
        return False

def valveCycleTimesNight():
    
    # Updat dateTime
    dateTime = time.localtime(time.time() + utcOffset())

    # Return True if valve cycle should start, otherwise return False
    if dateTime[3] == 23 and dateTime[4] < 30:
        print("valveCycleNight modus active")
        return True
    elif dateTime[3] == 23 and dateTime[4] >= 30:
        print("valveCycleNight modus not active")
        return False
    elif dateTime[3] == 1 and dateTime[4] < 30:
        print("valveCycleNight modus active")
        return True
    elif dateTime[3] == 1 and dateTime[4] >= 30:
        print("valveCycleNight modus not active")
        return False
    elif dateTime[3] == 3 and dateTime[4] < 30:
        print("valveCycleNight modus active")
        return True
    elif dateTime[3] == 3 and dateTime[4] >= 30:
        print("valveCycleNight modus not active")
        return False
    elif dateTime[3] == 5 and dateTime[4] < 30:
        print("valveCycleNight modus active")
        return True
    elif dateTime[3] == 5 and dateTime[4] >= 30:
        print("valveCycleNight modus not active")
        return False
    else:
        print("valveCycleNight modus not active")
        return False


def cookingTimes():
    
    # Update dateTime
    dateTime = time.localtime(time.time() + utcOffset())

    # Return True if valve cycle should start, otherwise return False
    if dateTime[3] == 17 and dateTime[4] > 20:
        print("cooking modus active")
        return True
    elif dateTime[3] == 17 and dateTime[4] > 50:
        print("cooking modus not active")
        return False
    else:
        print("Cooking modus not active")
        return False


