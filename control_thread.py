import logging
import time
import shelve

import board
import numpy as np

from autoremote import Autoremote
from base_thread import BaseThread
from car_status import CarStatus
from home_assistant import HomeAssistant
from home_assistant_controllable import HomeAssistantControllable
from tfminis_thread import TfminisThread
from door_control import DoorControl
from door_status_thread import DoorStatusThread, DoorStatus
from neopixel_display_thread import NeoPixelDisplayThread
from temperature_monitor_thread import TemperatureMonitorThread
from wifi_scan_thread import WifiScanThread


class ControlThread(BaseThread, HomeAssistantControllable):
    """Represents one stall of a Garage with a double door."""
    def __init__(self, park_distance: int = 94,
                 max_distance: int = 390,
                 wlan_interface: str = 'wlan0',
                 ssids: [list] = None,
                 tfmini_port: str = '/dev/ttyS0',
                 tfmini_baud: int = 115200,
                 neopixel_pin = board.D21,
                 num_pixels: int = 60,
                 door_status_pin: int = 2,
                 door_control_pin: int = 17,
                 auto_open_via_wifi: bool = True,
                 auto_close_via_wifi: bool = False,
                 mqtt_server: str = 'homeassistant.local',
                 mqtt_discovery_prefix='homeassistant',
                 mqtt_device_id='01ad',
                 mqtt_device_name='Garage Door',
                 mqtt_username: str = None,
                 mqtt_password: str = None,
                 auto_open_cool_down: int = 300,
                 db_file: str = 'garage_vars',
                 door_movement_delay:int = 10,
                 autoremote_key: str = None):
        """Create a Garage Stall control thread with the given parameters for the sensors.

        Parameters
        ----------
        park_distance - int - distance car should park at, defaults to 94
        max_distance - int - maximum distance in centimeters for TFMiniS, defaults to 390 cm
        wlan_interface - str - wifi interface used to scan for Car wifi, defaults to 'wlan0'
        ssids - list(str) - Name of car wifis to look for, defaults to None
        tfmini_port - str - TFmini-S serial port connection, defaults to /dev/ttyS0, None disables
        tfmini_baud - int - TFmini-S baud rate, defaults to 115200
        neopixel_pin - str - board.Pin for neopixel display, defaults to board.D21
        num_pixels - int - number of neopixel pins to use, defaults to 60
        door_status_pin - int - GPIOzero pin number for monitoring garage door open/close status, defaults to 2
        door_control_pin - int - GPIOzero pin number for controlling garage door via relat, defaults to 17
        auto_open_via_wifi - bool - True to use Wifi detection to open door automatically (defaults to True)
        auto_close_via_wifi - bool - True to use Wifi detection to close door automatically (defaults to False)
        mqtt_server - str - MQTT server that will receive updates to current_distance, car_parked, etc., None disables
        mqtt_discovery_prefix - str - prefix for mqtt topic so that homeassistant can see it, defaults to 'homeassistant'
        mqtt_device_id - str - device identifier to use in publications to MQTT, defaults to '01ad'
        mqtt_device_name - str - device name to use in publications to MQTT, defaults to 'Garage Door'
        mqtt_username - str - username to login to MQTT server with, defaults to None meaning no user/password required
        mqtt_password - str - password needed to login to MQTT server, defaults to None meaning no password needed
        auto_open_cool_down - int - number of seconds to wait after exiting before auto-opening garage when Wifi is
            seen, defaults to 300 (5 minutes)
        db_file - str - name of file to use for storage of persistent variables last_found, last_not_found, etc,
            defaults to 'garage_vars' (.db is auto-appended)
        door_movement_delay - int - number of seconds to wait before considering open or close a failure if
            door_status_pin does not change, defaults to 10 seconds
        autoremote_key - str - Tasker autoremote key to send garage-opened and garage-closed messages to
        """
        super(ControlThread, self).__init__()
        self.max_distance = max_distance
        self.park_distance = park_distance
        if tfmini_port is not None:
            self.tfminis = TfminisThread(port=tfmini_port, baud=tfmini_baud)
        else:
            self.tfminis = None
            logging.info('TFmini-S disabled')
        self.wlan_interface = wlan_interface
        self.ssids = ssids
        self.display = NeoPixelDisplayThread(max_distance = max_distance, pin=neopixel_pin, num_pixels=num_pixels)
        self.door_status = DoorStatusThread(gpio_pin=door_status_pin, door_movement_delay=door_movement_delay)
        if autoremote_key is not None:
            self.autoremote = Autoremote(autoremote_key)
        else:
            self.autoremote = None
        self.control = DoorControl(gpio_pin=door_control_pin)
        if mqtt_server is not None:
            self.home_assistant = HomeAssistant(self,
                                                mqtt_server=mqtt_server,
                                                mqtt_discovery_prefix=mqtt_discovery_prefix,
                                                mqtt_device_id=mqtt_device_id,
                                                mqtt_device_name=mqtt_device_name,
                                                mqtt_username=mqtt_username,
                                                mqtt_password=mqtt_password
                                                )
        else:
            self.home_assistant = None
        # readings array will have time in column 0 and distance in column 1
        self.readings = np.zeros((0,2))
        self.readings_size_in_seconds = 5.0
        self.speed = 0.0
        if ssids is not None and self.wlan_interface is not None:
            self.wifi_scanner = WifiScanThread(self.ssids, self.wlan_interface)
        else:
            self.wifi_scanner = None
            logging.info('Wifi scanner disabled')
        self.current_distance = 0.0
        self.temperature_monitor = TemperatureMonitorThread()
        self.auto_open_via_wifi = auto_open_via_wifi
        self.auto_close_via_wifi = auto_close_via_wifi
        self.auto_open_cool_down = auto_open_cool_down # seconds
        self.db = shelve.open(db_file, writeback=True)
        if 'last_found' not in self.db:
            self.db['last_found'] = 0
            self.db['last_not_found'] = 0
            self.db['last_parked'] = 0
            self.db['last_exiting'] = 0
            self.db['last_entering'] = 0
            self.db['car_status'] = CarStatus.UNKNOWN
            self.db.sync()

    def loop(self):
        reading = self.tfminis.read() if self.tfminis is not None else None
        if reading is not None and reading['distance'] != 65535:
            self.current_distance = reading['distance']
            new_readings = np.append(self.readings,
                                     np.array([[time.time(), self.current_distance]]),
                                     axis=0)
            self.readings = truncate_time_series(
                new_readings,
                self.readings_size_in_seconds
            )
            self.speed = speed(self.readings)
            #self.publish('car_speed', f'{self.speed}')
            #logging.info(f"distance={reading['distance']} cm, speed={self.speed}")
            self.display.set_reading(self.current_distance, self.speed)
            self.inform_listeners(self.current_distance)
            #self.publish('current_distance', str(reading['distance']))
            if self.display.parked:
                self._parked()
        # The following auto-open/close logic only works if both tfmini and wifi are enabled
        if self.wifi_scanner is not None and self.tfminis is not None:
            if len(self.wifi_scanner.found()) > 0 and time.time() - self.db['last_not_found'] > 2.0: # secs
                # Car is in-range of Wifi for at least 2 seconds
                self.db['last_found'] = time.time()
                if self.display.parked:
                    self._parked()
                elif self.door_status.door_status == DoorStatus.OPEN:
                    if self.current_distance < self.max_distance:
                        if self.speed >= 2.0:
                            self.db['car_status'] = CarStatus.EXITING
                            self.publish_to_home_assistant()
                            #self.publish('car_status', self.db['car_status'].name)
                            self.db['last_exiting'] = time.time()
                        elif self.speed <= -2.0:
                            self.db['car_status'] = CarStatus.ENTERING
                            self.publish_to_home_assistant()
                            #self.publish('car_status', self.db['car_status'].name)
                            self.db['last_entering'] = time.time()
                elif self.door_status.door_status == DoorStatus.CLOSED:
                    # See the Wifi but the door is closed, maybe it just left or just arrived
                    if self.auto_open_via_wifi and time.time() - self.db['last_exiting'] > self.auto_open_cool_down:
                        self.open_garage('because Wifi is seen')
                self.db.sync()
            elif len(self.wifi_scanner.found()) == 0 and time.time() - self.db['last_found'] > 10.0 and \
                    not self.display.parked:
                # Car is out-of-range of Wifi for at least 10 seconds
                self.db['car_status'] = CarStatus.AWAY
                self.db['last_not_found'] = time.time()
                self.db.sync()
                self.publish_to_home_assistant()
                if self.auto_close_via_wifi and not self.display.parked and self.door_status == DoorStatus.OPEN:
                    self.close_garage('because Wifi not seen and car is not parked')
        time.sleep(0.1)

    def _parked(self):
        self.db['car_status'] = CarStatus.PARKED
        self.db['last_parked'] = time.time()
        self.db.sync()
        self.publish_to_home_assistant()

    def publish_to_home_assistant(self):
        if self.home_assistant is not None:
            self.home_assistant.publish(self.door_status.door_status, self.db['car_status'], self.display.park_distance)

    def set_park_distance(self, distance: float):
        if self.max_distance is None:
            logging.info(f'park_distance set to {distance}, ignoring because TFmini-S is disabled')
            return
        if distance < 0:
            distance = 0
            logging.warning(f'attempt to set distance to a value less than 0')
        elif distance > self.max_distance:
            distance = self.max_distance
            logging.warning(f'attempt to set distance to a value greater than {self.max_distance}')
        logging.info(f'park_distance set to {distance}, max is {self.max_distance}')
        self.display.park_distance = distance
        self.publish_to_home_assistant()

    def set_readings_size_in_seconds(self, size):
        logging.info(f'readings_size_in_seconds set to {size}')
        if size < 0:
            size = 0
            logging.warning(f'attempt to set readings_size_in_seconds to a value less than 0')
        elif size > 60:
            size = 60
            logging.warning(f'attempt to set readings_size_in_seconds to a value greater than 60')
        self.readings_size_in_seconds = size

    def close_garage(self, reason=''):
        if self.door_status.door_status == DoorStatus.OPEN:
            logging.info(f'closing garage {reason}')
            self.control.press()
            self.door_status.close_started()

    def open_garage(self, reason=''):
        if self.door_status.door_status == DoorStatus.CLOSED:
            logging.info(f'opening garage {reason}')
            self.control.press()
            self.door_status.open_started()

    def open_or_close(self, reason: str=''):
        if self.door_status.door_status == DoorStatus.OPEN:
            self.close_garage(reason)
        elif self.door_status.door_status == DoorStatus.CLOSED:
            self.open_garage(reason)

    def run(self):
        if self.wifi_scanner is not None:
            #self.wifi_scanner.listeners.append(lambda status: self.publish('wifi_found',
            #                                                               len(self.wifi_scanner.found())>0))
            self.wifi_scanner.start()
        if self.tfminis is not None:
            self.tfminis.start()
        self.display.start()
        #self.temperature_monitor.listeners.append(lambda status: self.publish('cpu_temp', f'{status}'))
        self.temperature_monitor.start()

        def door_status_publications(status: DoorStatus):
            self.publish_to_home_assistant()
            if self.autoremote:
                if status == DoorStatus.OPEN:
                    self.autoremote.send_opened()
                elif status == DoorStatus.CLOSED:
                    self.autoremote.send_closed()

        self.door_status.listeners.append(door_status_publications)
        self.door_status.start()
        super().run()

    def shutdown(self):
        super().shutdown()
        self.db.close()
        self.door_status.shutdown()
        self.temperature_monitor.shutdown()
        self.display.shutdown()
        if self.home_assistant is not None:
            self.home_assistant.shutdown()
        if self.tfminis is not None:
            self.tfminis.shutdown()
        if self.wifi_scanner is not None:
            self.wifi_scanner.shutdown()


def truncate_time_series(arr: np.ndarray, seconds: float) -> np.ndarray:
    # Start time for data slice
    start_time = time.time() - seconds
    # Select rows where timestamp is greater than or equal to start time
    truncated = arr[arr[:, 0] >= start_time]
    return truncated


def speed(arr: np.ndarray, period: float = 2.0) -> float:
    """Compute and return average speed in centimeters per second over the last period seconds.

    Parameters
    ----------
    arr - np.ndarray (float) - array of times and positions from TFmini-S
    period - float - how many seconds of data to use in computing average speed

    Returns
    -------
    speed in cm/s or -999 if not enough data
    """
    truncated = truncate_time_series(arr, period)
    if truncated.shape[0] < 2:
        return -999.0
    positions = truncated[:, 1]
    times = truncated[:, 0]
    v, _ = np.polyfit(times, positions, 1)
    #logging.info(f'n={n} delta_p={positions[n-1]-positions[0]} delta_t={times[n-1]-times[0]}')
    return v


def acceleration(arr: np.ndarray) -> float:
    if arr.shape[0] < 2:
        return 0.0
    positions = arr[:, 1]
    times = arr[:, 0]
    delta_positions = np.diff(positions)
    delta_times = np.diff(times)
    delta_times = np.where(delta_times == 0, np.inf, delta_times)
    velocities = delta_positions / delta_times
    times = times[1:]
    a, _ = np.polyfit(times, velocities, 1)
    return a

