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
(Note: Links marked "Amazon" are Affiliate links and will earn money for me.)

| Item                                   | Price   | Buy Link                                                                                                                                                                                                                                                                                                                                                                                   |
|----------------------------------------|---------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Raspberry Pi Zero 2W                   | $15.00  | [SparkFun](https://www.sparkfun.com/products/18713?src=raspberrypi)                                                                                                                                                                                                                                                                                                                        |
| Raspberry Pi Zero 2W Case              | $9.89   | [Amazon](https://www.amazon.com/gp/product/B075FLGWJL/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&amp;th=1&_encoding=UTF8&tag=amazonjohn07f-20&linkCode=ur2&linkId=694770aff795ccdb015d84dc21b93e9d&camp=1789&creative=9325)                                                                                                                                                                 |
| 5V Relay Module 8-pack                 | $11.99  | [Amazon](https://www.amazon.com/gp/product/B09G6H7JDT/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&amp;psc=1&_encoding=UTF8&tag=amazonjohn07f-20&linkCode=ur2&linkId=a56ce9dcd27e755bd94e1f00805aefb0&camp=1789&creative=9325)                                                                                                                                                                |
| TFmini-S                               | $47.85  | [Amazon](https://www.amazon.com/gp/product/B09WDWFW21/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&amp;psc=1&_encoding=UTF8&tag=amazonjohn07f-20&linkCode=ur2&linkId=7362245319d2cd58e64a60fba5464729&camp=1789&creative=9325)                                                                                                                                                                |
| 12V DC Fan 2-pack                      | $13.98  | [Amazon](https://www.amazon.com/ANVISION-Bearing-Brushless-Cooling-YDM4010B12/dp/B0711FVD48/ref=sr_1_4?crid=3NAYFNGPGZ72U&amp;keywords=small%252B12v%252Bdc%252Bfan&amp;qid=1698788735&amp;sprefix=small%252B12v%252Bdc%252Bfan%252B%252Caps%252C103&amp;sr=8-4&amp;th=1&_encoding=UTF8&tag=amazonjohn07f-20&linkCode=ur2&linkId=29cbc948cbb01b8f02c3846da9a491dc&camp=1789&creative=9325) |
| NeoPixel 5V LED Strip                  | $20.99  | [Amazon](https://www.amazon.com/gp/product/B09MVZ5DZM/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&amp;th=1&_encoding=UTF8&tag=amazonjohn07f-20&linkCode=ur2&linkId=59b0ec4ec9f23567de283beb54ad7a95&camp=1789&creative=9325)                                                                                                                                                                 |
| 5V 5A Power Supply                     | $15.99  | [Amazon](https://www.amazon.com/gp/product/B08744HPRN/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&amp;th=1&_encoding=UTF8&tag=amazonjohn07f-20&linkCode=ur2&linkId=294d1459a701c9db4e703a09ed8680e0&camp=1789&creative=9325)                                                                                                                                                                 |            
| Case (I used a leftover packaging box) | Free?   |                                                                                                                                                                                                                                                                                                                                                                                            |
| Solderable breadboard 5-pack           | $11.99  | [Amazon](https://www.amazon.com/gp/product/B07HNKJNK3/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&amp;psc=1&_encoding=UTF8&tag=amazonjohn07f-20&linkCode=ur2&linkId=c71241a09ce8fa4c9c3acf3a2e233c89&camp=1789&creative=9325)                                                                                                                                                                |
| Jumper wires                           | $9.29   | [Amazon](https://www.amazon.com/gp/product/B077X99KX1/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&amp;psc=1&_encoding=UTF8&tag=amazonjohn07f-20&linkCode=ur2&linkId=97a3ab5ea609179bb98116fad01dc373&camp=1789&creative=9325)                                                                                                                                                                | 
| TOTAL                                  | $129.90 |                                                                                                                                                                                                                                                                                                                                                                                            | 

Note that some of the above items come in packs so you will have leftover DC relays, a fan, and solderable breadboards.  The total
reflects the per-item cost and not the price.
#### Circuit Diagram
![Circuit Diagram](readme_assets/circuit/Sketch_bb.png)
#### Assembled Circuit
![Assembled Circuit](readme_assets/Garage-Pi%20Assembled.jpg)
# Acknowledgements
This system was inspired by [ResinChem Tech's](https://www.youtube.com/@ResinChemTech) "[A New Parking Assistant using ESP8266 and WS2812b LEDs](https://www.youtube.com/watch?v=HqqlY4_3kQ8)" video on YouTube.  It is an excellent system and video so I encourage you to go watch it.  His system displays the LEDs the same
way as Garage-Pi and has Home Assistant integration as well.  There is no Door or WiFi Sensors and no Door Open/Close Control, however.
