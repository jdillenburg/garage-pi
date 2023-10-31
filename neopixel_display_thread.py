import logging

import board
import neopixel
import time
from base_thread import BaseThread


def mapval(x, in_min, in_max, out_min, out_max):
    small = min(in_min, in_max)
    large = max(in_min, in_max)
    if x < small:
        x = small
    elif x > large:
        x = large
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;


class NeoPixelDisplayThread(BaseThread):
    def __init__(self, color = (255, 255, 0), pin = board.D21, num_pixels = 60,
                 park_distance = 100, max_distance = 390):
        super(NeoPixelDisplayThread, self).__init__()
        self.pixels = neopixel.NeoPixel(pin, num_pixels, auto_write=False, brightness=0.6)
        self.pixels.fill((0,0,0))
        self.pixels.show()
        self.num_pixels = num_pixels
        self.color = color
        self.park_distance = park_distance
        self.backup_factor = 0.5
        self.max_distance = max_distance
        self.last_blink = int(time.time() * 1000)
        self.blink_is_on = False
        self.distance = 0
        self.speed = 0
        self.rate = 0
        self.parked = False

    def set_reading(self, distance, speed):
        self.distance = distance
        self.speed = speed
    
    def bullseye(self):
        pixel_count = int(mapval(self.distance, self.max_distance, self.park_distance, 0, self.num_pixels/2))
        logging.debug(f'distance={self.distance} max={self.max_distance} min={self.park_distance} pixel_count={pixel_count}')
        self.pixels.fill((0,0,0))
        for i in range(0, pixel_count):
            self.pixels[i] = self.color
            self.pixels[self.num_pixels - i - 1] = self.color
        self.pixels.show()
        
    def standby(self):
        self.pixels.fill((0,0,0))
        self.pixels[0] = self.color
        self.pixels[self.num_pixels-1] = self.color
        self.pixels.show()
        
    def loop(self):
        if abs(self.speed) < 2.0:
            self.standby()
            if self.park_distance >= self.distance >= self.park_distance * self.backup_factor:
                self.parked = True
            else:
                self.parked = True
        elif self.distance < self.park_distance * self.backup_factor:
            self.blink()
            self.parked = False
        elif self.distance > self.park_distance:
            self.bullseye()
            self.parked = False
        else:
            self.park_here()
            self.parked = True
        time.sleep(0.1)
            
    def blink(self):
        now = int(time.time() * 1000)
        if now > self.last_blink + 500:
            self.blink_is_on = not self.blink_is_on
            self.last_blink = now
        if self.blink_is_on:
            self.pixels.fill((255,0,0))
        else:
            self.pixels.fill((0,0,0))
        self.pixels.show()
        
    def park_here(self):
        self.pixels.fill((255,0,0))
        self.pixels.show()
        
    def shutdown(self):
        super().shutdown()
        self.pixels.fill((0,0,0))        
