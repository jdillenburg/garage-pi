# -*- coding: utf-8 -*
#
# garage.py
# Copyright (c) 2023 John Dillenburg (john@dillenburg.org)
#
# Monitors distance to car using TFMini-S and displays distance
#   from parking spot on a NeoPixel strip.  Also monitors
#   Wifi to look for the Car's wifi signal.
#
import json
import sys

import configargparse as cap
import gui
import logging
import os
from control_thread import ControlThread
from nicegui import app, ui
import io
import board


conf_files = ['/etc/garage.conf', os.path.expanduser('~/garage.conf')]
logging.info(f'loading config from {conf_files}')
p = cap.ArgumentParser(default_config_files=conf_files)
p.add_argument('-c', '--config', required=False, is_config_file=True, help='config file to load')
p.add_argument('--ssid', action='append', help='enable Wifi and scan for given ssid')
p.add_argument('--tfmini_port', action='store', help='TFmini-S port to use, defaults to /dev/ttyS0',
               default='/dev/ttyS0')
p.add_argument('--park_distance', action='store', default=94, type=int,
               help='set TFmini-S park_distance to given value in centimeters, defaults to 94 cm')
p.add_argument('--max_distance', action='store', default=390, type=int,
               help='set TFmini-S max_distance to given value in centimeters, defaults to 390 cm')
p.add_argument('--neopixel_pin', type=str, action='store', default='D21',
               help='Neopixel data line is connected to this pin, see Adafruit blinka library Board class')
p.add_argument('--num_pixels', type=int, action='store', help='number of NeoPixels, defaults to 60',
               default=60)
p.add_argument('--wlan', default='wlan0', help='wireless interface to use for ssid scanning, defaults to wlan0')
p.add_argument('--web_host', action='store', default='0.0.0.0',
               help='start web server and bind to given host')
p.add_argument('--storage_secret', type=str, action='store',
               help='secret key for browser based storage, default is `garage-pi-4-ever`, a value is '
                    'required to encrypt login)', default='garage-pi-4-ever')
p.add_argument('--door_status_pin', type=int, action='store', default=2,
               help='Door status pin, passed to gpiozero Button to monitor garage door open/close status, '
                    'defaults to 2')
p.add_argument('--door_control_pin', type=int, action='store', default=17,
               help='Door control pin, passed to gpiozero OutputDevice to trigger garage door open/close relay, '
                    'defaults to 17')
p.add_argument('--mqtt_server', action='store', help='FQDN of MQTT server to send status updates to')
p.add_argument('--mqtt_discovery_prefix', action='store', help='MQTT discovery_prefix portion of topic to publish '
                                                               'configuration and status to, defaults to homeassistant',
               default='homeassistant')
p.add_argument('--mqtt_device_id', action='store', help='MQTT device identifier to use in publications, '
                                                        'defaults to 01ad', default='01ad')
p.add_argument('--mqtt_device_name', action='store', help='MQTT device name to use in publications, '
                                                          'defaults to "Garage Door"', default='Garage Door')
p.add_argument('--mqtt_username', action='store', help='MQTT server username to login')
p.add_argument('--mqtt_password', action='store', help='MQTT server password to login')
p.add_argument('--passwords', action='store', default='passwords.json', help='passwords are loaded from this json file')
p.add_argument('--db_file', action='store', help='store persistent variables in this file, defaults to garage_vars',
               default='garage_vars')
p.add_argument('--auto_open_cool_down', type=int, action='store',
               help='amount of time in seconds to wait after car exits before considering opening the door, '
                    'defaults to 300 seconds',
               default=300)
p.add_argument('--door_movement_delay', type=int, action='store',
               help='how long to wait for door to open or close before considering it a failure when door_status_pin'
                    'does not change its reading, defaults to 10 seconds', default=10)
p.add_argument('--disable_tfmini', action='store_true', help='disables TFmini-S usage')
p.add_argument('--disable_wifi', action='store_true', help='disables Wifi usage')
p.add_argument('--disable_web', action='store_true', help='disables web interface')
p.add_argument('--disable_auto_open_via_wifi', action='store_true', help='disable auto open via Wifi')
p.add_argument('--disable_auto_close_via_wifi', action='store_true', help='disable auto close via Wifi')
p.add_argument('--disable_mqtt', action='store_true', help='disables MQTT integration')
p.add_argument('--autoremote_key', action='store', help='Tasker auto-remote key to send garage-opened and garage-closed messages to')


options = p.parse_args()
if options.disable_tfmini:
    options.tfmini_port = None
if options.disable_wifi:
    options.wlan = None
auto_open_via_wifi = (not options.disable_wifi and not options.disable_auto_open_via_wifi and
                      options.ssid is not None and len(options.ssid) > 0)
auto_close_via_wifi = (not options.disable_wifi and not options.disable_auto_close_via_wifi and
                       options.ssid is not None and len(options.ssid) > 0)
if options.disable_mqtt:
    options.mqtt_server = None

with io.open(options.passwords, 'r') as fp:
    passwords = json.load(fp)

syslog_handler = logging.handlers.SysLogHandler(address='/dev/log')
stdout_handler = logging.StreamHandler(sys.stdout)
logging.basicConfig(format='[%(asctime)s %(filename)22s:%(lineno)3s - %(funcName)20s() ] %(message)s',
                    level=logging.INFO, handlers=[ syslog_handler, stdout_handler ], force=True)
logging.info('''
   _____                                   _____ _ 
  / ____|                                 |  __ (_)
 | |  __  __ _ _ __ __ _  __ _  ___ ______| |__) | 
 | | |_ |/ _` | '__/ _` |/ _` |/ _ \______|  ___/ |
 | |__| | (_| | | | (_| | (_| |  __/      | |   | |
  \_____|\__,_|_|  \__,_|\__, |\___|      |_|   |_|
                          __/ |                    
                         |___/                     
    Copyright (C) 2023  John Dillenburg (john@dillenburg.org)
    This program comes with ABSOLUTELY NO WARRANTY; for details see COPYING.
    This is free software, and you are welcome to redistribute it
    under certain conditions.''')

if auto_open_via_wifi:
    logging.info(f'*** Door will be opened based on seeing Wifi signal from {options.ssid}')
if auto_close_via_wifi:
    logging.info(f'*** Door will be closed based on not seeing Wifi signal from {options.ssid}')

garage = ControlThread(
    park_distance = options.park_distance,
    max_distance=options.max_distance,
    wlan_interface=options.wlan,
    ssids=options.ssid,
    tfmini_port=options.tfmini_port,
    neopixel_pin=getattr(board,options.neopixel_pin),
    num_pixels=options.num_pixels,
    door_status_pin=options.door_status_pin,
    door_control_pin=options.door_control_pin,
    auto_open_via_wifi=auto_open_via_wifi,
    auto_open_cool_down=options.auto_open_cool_down,
    auto_close_via_wifi=auto_close_via_wifi,
    db_file=options.db_file,
    door_movement_delay=options.door_movement_delay,
    mqtt_server=options.mqtt_server,
    mqtt_discovery_prefix=options.mqtt_discovery_prefix,
    mqtt_device_id=options.mqtt_device_id,
    mqtt_device_name=options.mqtt_device_name,
    mqtt_username=options.mqtt_username,
    mqtt_password=options.mqtt_password,
    autoremote_key=options.autoremote_key
)
logging.info('starting garage control thread')
garage.start()

def _run_system_command(command):
    logging.info(command)
    exit_value = os.popen(command)
    if exit_value is not None:
        logging.warning(f'unable to run {command}, exit from command was {exit_value}')

def shutdown():
    garage.shutdown()
    app.shutdown()
    _run_system_command('shutdown -h now')

def restart():
    garage.shutdown()
    logging.info('restarting')
    app.shutdown()
    _run_system_command('reboot -f')

if not options.disable_web:
    gui.create_pages(garage, passwords, shutdown, restart)
    app.add_static_files('/static', 'static')
    ui.run(title='Garage-Pi', host=options.web_host, reload=False, show=False,
           storage_secret=options.storage_secret, favicon='🚗')
else:
    try:
        logging.info('web interface disabled')
        garage.join()
    except KeyboardInterrupt:
        garage.shutdown()
