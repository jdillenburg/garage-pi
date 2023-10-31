# Garage-Pi
**by John Dillenburg (john@dillenburg.org)**

This project turns a Raspberry-Pi (3, 4, or Zero-2W) into a Garage helper with features including:
* Open/Close garage door using 5V relay
* Determine Open/Close status via contact switch
* TFmini-S and Neopixel integration to display distance from car to front of garage
* Home Assistant integration via MQTT 
  * Garage door device is auto-configured
  * Status of door (open/closed) and car (parked/not parked)
  * Open/close the garage door
  * Configure park distance
  * Tasker/AutoRemote integration (garage-pi pushes open/close status to AutoRemote)
* NiceGUI website
  * HTTPS and password protected
  * Open/close garage door
  * Graphs of car distance and CPU temperature
  * Scan to see if your car emits Wifi signal
  * Status of sensors
  * API end points for open/close status and control
* Option to auto-open and close based on detecting car's WiFi signal
## Screenshots
Here are some obligatory screenshots, so you can figure out if this is what you want or not.
### Home Assistant
![Home Assistant](readme_assets/Screenshot_HA.png)
### Built-In Web Site
![Web site homepage](readme_assets/Screenshot_Home.png)
![Graphs](readme_assets/Screenshot_Graphs.png)
![WiFi](readme_assets/Screenshot_Wifi.png)
## Demo
Screenshots not enough? This video shows how Garage-Pi displays the Neopixel strip of lights as a car approaches its parking distance from the front of the garage.
[![Garage-Pi Demo](readme_assets/demo.png)](readme_assets/demo.mp4 "Video")
## Installation
Garage-Pi requires some assembly and soldering skills in addition to software installation.  Here is a list of equipment that was used in my installation.
### Hardware Assembly
#### Parts List
1. Raspberry Pi Zero 2W (other Raspberry Pi models will work but the Zero 2W seems to be able to withstand garage environments the best)
1. 5V Relay Module (to trigger the opener)
1. TFmini-S Distance Sensor (to sense the vehicle distance)
1. NeoPixel 5V LED Strip with 60 pixels
1. 2 Amp AC to 5V DC Power Supply
1. Small 5V DC Fan
1. Case to install everything in (I used a leftover packaging box)
1. Solderable breadboard
#### Circuit Diagram
![Circuit Diagram](readme_assets/circuit/Sketch_bb.png)
#### Assembled Circuit
![Assembled Circuit](readme_assets/Garage-Pi%20Assembled.jpg)
# Acknowledgements
This system was inspired by [ResinChem Tech's](https://www.youtube.com/@ResinChemTech) "[A New Parking Assistant using ESP8266 and WS2812b LEDs](https://www.youtube.com/watch?v=HqqlY4_3kQ8)" video on YouTube.  It is an excellent system and video so I encourage you to go watch it.  His system displays the LEDs the same
way as Garage-Pi and has Home Assistant integration as well.  There is no Door or WiFi Sensors and no Door Open/Close Control, however.
