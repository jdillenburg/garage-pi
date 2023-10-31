from enum import Enum
from gpiozero import Button
import time
from base_thread import BaseThread
import logging


class DoorStatus(Enum):
    UNKNOWN = 0
    OPENING = 1
    OPEN = 2
    CLOSING = 3
    CLOSED = 4
    

class DoorStatusThread(BaseThread):
    """Uses the gpiozero library to check the status of a pulled up GPIO pin (2 by default).  Reports
    the status as the garage door open/close status to listeners.
    """
    def __init__(self, gpio_pin = 2, door_movement_delay : int = 10.0, opening_delay : int = 1.5):
        """Initialize DoorStatusThread object.

        Parameters
        ----------
        door_movement_delay (int) - delay in seconds from control press until door is fully opened or closed, defaults to
           10 seconds
        opening_delay (int) - delay in seconds from control press until door starts to open, defaults to 1.5 seconds
        """
        super(DoorStatusThread, self).__init__()
        self.gpio_pin = gpio_pin
        self.button = Button(gpio_pin)
        self.door_status = DoorStatus.UNKNOWN
        self.open_started_time = time.time()
        self.close_started_time = time.time()
        self.close_failed = False
        self.open_failed = False
        self.door_movement_delay = door_movement_delay # seconds
        self.opening_delay = opening_delay
        self.last_close_failed = 0
        self.last_open_failed = 0
        
    def loop(self):
        open_status = self.is_open()
        #logging.info(f'open_status is {open_status}, door_status is {self.door_status}')
        if open_status:
            # door is OPEN
            if self.door_status == DoorStatus.CLOSED:
                self.door_status = DoorStatus.OPENING
                self.open_started_time = time.time()
                self.inform_listeners(self.door_status)
            elif (self.door_status == DoorStatus.OPENING and
                  time.time() - self.open_started_time > self.door_movement_delay):
                self.door_status = DoorStatus.OPEN
                self.open_failed = False
                self.inform_listeners(self.door_status)
            elif (self.door_status == DoorStatus.CLOSING and
                  time.time() - self.close_started_time > self.door_movement_delay):
                self.door_status = DoorStatus.OPEN
                self.close_failed = True
                self.last_close_failed = time.time()
                self.inform_listeners(self.door_status)
            elif self.door_status == DoorStatus.UNKNOWN:
                self.door_status = DoorStatus.OPEN
                self.inform_listeners(self.door_status)
        else:
            # door is CLOSED
            if (self.door_status == DoorStatus.OPENING and
                  time.time() - self.open_started_time > self.door_movement_delay):
                self.door_status = DoorStatus.CLOSED
                self.open_failed = True
                self.last_open_failed = time.time()
                self.inform_listeners(self.door_status)
            elif (self.door_status == DoorStatus.OPENING and
                    time.time() - self.open_started_time < self.opening_delay):
                # wait for at least opening_delay seconds before setting status to back to CLOSED
                pass
            elif self.door_status != DoorStatus.CLOSED:
                self.door_status = DoorStatus.CLOSED
                self.close_failed = False
                self.inform_listeners(self.door_status)
        time.sleep(1.0)

    def close_started(self):
        self.door_status = DoorStatus.CLOSING
        self.close_started_time = time.time()
        self.inform_listeners(self.door_status)

    def open_started(self):
        self.door_status = DoorStatus.OPENING
        self.open_started_time = time.time()
        self.inform_listeners(self.door_status)

    def is_open(self):
        # contact is closed when door is closed, so we're open when button is not pressed
        return not self.button.is_pressed

    def run(self):
        logging.info(f'monitoring door status using GPIO pin {self.gpio_pin}')
        # send an initial message since loop() may not send one if nothing changes
        if self.is_open():
            self.door_status = DoorStatus.OPEN
        else:
            self.door_status = DoorStatus.CLOSED
        self.inform_listeners(self.door_status)
        super().run()

    def shutdown(self):
        super().shutdown()
        self.button.close()
     