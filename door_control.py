from gpiozero import OutputDevice
import time
import logging

class DoorControl:
    """Simple class that encapsulates the pressing of the garage door control button.  Uses
    the gpiozero library to control a 5V rely on a GPIO pin of the raspberry pi (defaults to 17)."""
    
    def __init__(self, gpio_pin = 17):
        self.gpio_pin = gpio_pin
        self.output = OutputDevice(gpio_pin)
        self.listeners = list()
        self.last_pressed = 0
        
    def press(self):
        if time.time() - self.last_pressed > 1.0:
            logging.warning('triggering open/close button')
            self.last_pressed = time.time()
            self.output.on()
            time.sleep(0.1)
            self.output.off()
            for listener in self.listeners:
                listener(self)
        else:
            logging.warning('attempt to press control button too often is ignored')

    def close(self):
        self.output.close()