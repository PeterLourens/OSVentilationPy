# Functional Description Ventilation system

## Fan unit specification:
* Type: CVE ECO 2HE
* Version: 110-0031-001
* Article number: 545-5022
* Capacity: 417 m3/h
* Pressure: 150 Pa
* Nominal Power: 67.1 W
* Nominal Voltage: 230V-50Hz
* Nominal current: 0.5A
* Power factor: 0.58
* Weight: 3.5 kg

## Initial state

When the ventilation system starts, all valves should go to their default position and the fan at low (10%) speed. The default positions are:

| Valve number | Room | valve position [%] | flow [m3/h] | High valve position [%] |
| --- | ---| --- | --- | --- |
| 0 | HR Kap | 3 | 5 | 20 |
| 1 | Keuken | 3 | 5 | 20 |
| 2 | Toliet | 3 | 5 | 20 |
| 3 | | | | |
| 4 | | | | |
| 5 | Wasruimte | 3 | 5 | 20 |
| 6 | Badkamer | 100 | 60 | |
| 7 | | | | |
| 8 | Slaapkamer1 | 3 | 5 | 20 |
| 9 | Slaapkamer 2 | 3 | 5 | 20 |
| 10 | Slaapkamer 3 | 3 | 5 | 20 |
| 11 | Slaapkamer 4 | 3 | 5 | 20 |

Fan:
* Low: 20 -> 10% = 40 m3/h
* Medium: 120 -> 50% = 200 m3/h
* High: 220 -> 100% = 400 m3/h

## Operating

| Name | Flap position | ventilation | 
| --- | --- | --- |
| Bathroom | 100 | 60-75 |

### Ventilatiepatroon/etmaal

Normal ventilation pattern:
* Laagstand 8 uur (23:00u - 07:00u) 8 uur (23:00u - 07:00u)
* Middenstand 14 uur (07:00 - 23:00)
* Hoogstand 2 uur as required, e.g. cooking or shower

### Temperature control

No temperature control. Air is drawn in through the rosters in the windows which is an energy loss. 

### Humidity control

Humidity is measured with two sensors. Conditions:

* When both sensors indicate similar values (offset ?%) then the humidity cannot be influenced by the ventilation so no action is required.
* When bathroom1 humidity is higher than the general humidity in the house then shower is on. Actions:
    * Fanspeed should be increased to high. 
    * All valves remain in the same position (bathroom1 is and remains 100% open, all other unchanged).

### CO2 Control

CO2 is measured with one sensor in the suction tube of the fan so it measures for all rooms. Conditions and actions:

* When CO2 is high in daytime the ventilation should be increased. Actions:
    * Valves remain in same position 
    * fanspeed should be increased to high until CO2 level has decreased to XXX ppm.
* When CO2 is high during night time, the bedrooms should be ventilated more. Actions 
    * Open the valves to 100% of all bedrooms (not office). 
    * Fanspeed remains on low

		




