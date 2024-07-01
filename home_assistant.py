import logging
from typing import Callable

from paho import mqtt
from paho.mqtt.client import MQTTMessage, MQTT_ERR_SUCCESS, Client

from car_status import CarStatus
from door_status_thread import DoorStatus
from home_assistant_controllable import HomeAssistantControllable


class HomeAssistant:
    """Encapsulates the garage door's interactions with Home Assistant in one location."""
    def __init__(self,
                 garage: HomeAssistantControllable,
                 mqtt_server: str = 'homeassistant.local',
                 mqtt_discovery_prefix='homeassistant',
                 mqtt_device_id='01ad',
                 mqtt_device_name='Garage Door',
                 mqtt_username: str = None,
                 mqtt_password: str = None,
                 max_distance: float = 390,
                 on_connect : Callable = None):
        """
        Parameters
        ----------
        garage - HomeAssistantControllable - the set_park_distance() and open_or_close() methods will be called by Home Assistant
        mqtt_server - str - MQTT server that will receive updates to current_distance, car_parked, etc., None disables
        mqtt_discovery_prefix - str - prefix for mqtt topic so that homeassistant can see it, defaults to 'homeassistant'
        mqtt_device_id - str - device identifier to use in publications to MQTT, defaults to '01ad'
        mqtt_device_name - str - device name to use in publications to MQTT, defaults to 'Garage Door'
        mqtt_username - str - username to login to MQTT server with, defaults to None meaning no user/password required
        mqtt_password - str - password needed to login to MQTT server, defaults to None meaning no password needed
        max_distance - int - maximum distance in centimeters for TFMiniS, defaults to 390 cm
        on_connect - Callable - this function is called after successfully connecting to Home Assistant server
        """
        self.garage = garage
        self.on_connect = on_connect
        if mqtt_server is not None:
            self.mqtt_server = mqtt_server
            self.mqtt_discovery_prefix = mqtt_discovery_prefix
            self.mqtt_device_id = mqtt_device_id
            self.mqtt_device_name = mqtt_device_name
            self.max_distance = max_distance
            self.mqtt_client = Client(client_id="garage-pi", userdata=self)
            if mqtt_username is not None and mqtt_password is not None:
                self.mqtt_client.username_pw_set(mqtt_username, password=mqtt_password)
            self.mqtt_client.on_message = self._on_mqtt_message
            self.mqtt_client.on_connect = self._on_mqtt_connect
            try:
                self.mqtt_client.connect(mqtt_server)
                self.mqtt_client.loop_start()
            except IOError as error:
                logging.warning(f'unable to connect to MQTT at {mqtt_server}, MQTT disabled', error)
                self.mqtt_client = None
        else:
            self.mqtt_client = None
        # Store command topics for later use in _on_mqtt_connect and _on_mqtt_message
        self.garage_button_command_topic = f'{self.mqtt_discovery_prefix}/button/garage_door/commands'
        self.park_distance_command_topic = f'{self.mqtt_discovery_prefix}/number/garage_park_distance/set'


    def publish(self, door_status: DoorStatus, car_status: CarStatus, park_distance: float):
        """Sends the current status of this garage device to home assistant."""
        if self.mqtt_client is not None:
            self.mqtt_client.publish(f'{self.mqtt_discovery_prefix}/cover/garage_door/state',
                                     door_status.ha_status(), retain=True)
            self.mqtt_client.publish(f'{self.mqtt_discovery_prefix}/binary_sensor/car_presence/state',
                                     'ON' if car_status == CarStatus.PARKED else 'OFF', retain=True)
            if park_distance is not None:
                self.mqtt_client.publish(f'{self.mqtt_discovery_prefix}/number/garage_park_distance/state',
                                         str(park_distance), retain=True)

    def _on_mqtt_connect(self, client: Client, userdata, flags, rc):
        """This is called after connecting with homeassistant MQTT.  It configures the entities that are used
        for communicating with home assistant."""
        #         mqtt_discovery_prefix - str - prefix for mqtt topic so that homeassistant can see it, defaults to 'homeassistant'
        #         mqtt_device_id - str - device identifier to use in publications to MQTT, defaults to '01ad'
        #         mqtt_device_name - str - device name to use in publications to MQTT, defaults to 'Garage Door'
        client.publish(f'{self.mqtt_discovery_prefix}/cover/garage_door/config',
                       f'{{ '
                       f'  "uniq_id": "mqtt_cover.garage_door",'
                       f'  "name": "Garage Door", '
                       f'  "device_class": "garage", '
                       f'  "state_topic": "{self.mqtt_discovery_prefix}/cover/garage_door/state",'
                       f'  "unique_id": "garagedoor{self.mqtt_device_id}",'
                       f'  "device": {{ '
                       f'    "identifiers" : ["{self.mqtt_device_id}"], '
                       f'    "name": "{self.mqtt_device_name}" '
                       f'  }}'
                       f'}}')
        client.publish(f'{self.mqtt_discovery_prefix}/binary_sensor/car_presence/config',
                       f'{{ '
                       f'  "uniq_id": "mqtt_binary_sensor.garage_car_presence",'
                       f'  "name": "Car Presence", '
                       f'  "device_class": "presence", '
                       f'  "state_topic": "{self.mqtt_discovery_prefix}/binary_sensor/car_presence/state",'
                       f'  "unique_id": "carpresence{self.mqtt_device_id}",'
                       f'  "device": {{ '
                       f'    "identifiers" : ["{self.mqtt_device_id}"], '
                       f'    "name": "{self.mqtt_device_name}" '
                       f'  }}'
                       f'}}')
        client.publish(f'{self.mqtt_discovery_prefix}/button/garage_door/config',
                       f'{{ '
                       f'  "uniq_id": "mqtt_button.garage_button",'
                       f'  "name": "Garage Button", '
                       f'  "command_topic": "{self.garage_button_command_topic}",'
                       f'  "unique_id": "garagebutton{self.mqtt_device_id}",'
                       f'  "device": {{ '
                       f'    "identifiers" : ["{self.mqtt_device_id}"], '
                       f'    "name": "{self.mqtt_device_name}" '
                       f'  }}'
                       f'}}')
        client.publish(f'{self.mqtt_discovery_prefix}/number/garage_park_distance/config',
                       f'{{ '
                       f'  "uniq_id": "mqtt_binary_sensor.garage_park_distance",'
                       f'  "name": "Car Park Distance", '
                       f'  "command_topic": "{self.park_distance_command_topic}",'
                       f'  "device_class": "distance", '
                       f'  "state_topic": "{self.mqtt_discovery_prefix}/number/garage_park_distance/state",'
                       f'  "unique_id": "parkdistance{self.mqtt_device_id}",'
                       f'  "min": 0.0,'
                       f'  "max": {self.max_distance},'
                       f'  "step": 1.0,'
                       f'  "retain": "true",'
                       f'  "unit_of_measurement": "cm",'
                       f'  "device": {{ '
                       f'    "identifiers" : ["{self.mqtt_device_id}"], '
                       f'    "name": "{self.mqtt_device_name}" '
                       f'  }}'
                       f'}}')
        if self.on_connect is not None:
            self.on_connect()
        result, _ = client.subscribe(f'{self.garage_button_command_topic}', qos=0)
        if result != MQTT_ERR_SUCCESS:
            logging.error(f'unable to subscribe to MQTT at {self.mqtt_server} topic {self.garage_button_command_topic}')
        else:
            logging.info(f'connected to MQTT at {self.mqtt_server}')
        result, _ = client.subscribe(f'{self.park_distance_command_topic}', qos=0)
        if result != MQTT_ERR_SUCCESS:
            logging.error(f'unable to subscribe to MQTT at {self.mqtt_server} topic {self.park_distance_command_topic}')
        else:
            logging.info(f'connected to MQTT at {self.mqtt_server}')

    def _on_mqtt_message(self, _, userdata, message: MQTTMessage):
        """Home Assistant sent us a command or setting."""
        command = message.payload.decode('ascii')
        logging.info(f'{message.topic} {command}')
        if message.topic == f'{self.garage_button_command_topic}' and command == 'PRESS':
            self.garage.open_or_close(reason='home assistant button pressed')
        elif message.topic == f'{self.park_distance_command_topic}':
            self.garage.set_park_distance(float(command))

    def shutdown(self):
        if self.mqtt_client is not None:
            self.mqtt_client.loop_stop()
