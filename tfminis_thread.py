import logging
import time

import numpy as np
import serial

from base_thread import BaseThread


class TfminisThread(BaseThread):
    def __init__(self, port='/dev/ttyS0', baud=115200, timeout=10.0):
        super(TfminisThread, self).__init__()
        self.serial_port = None
        self.reading = None
        self.timeout = timeout
        self.port = port
        self.baud = baud

    def read(self):
        return self.reading

    def run(self):
        logging.info(f'getting distance to vehicle from TFmini-S on port {self.port}')
        self.serial_port = serial.Serial(self.port, self.baud)
        if not self.serial_port.is_open:
            self.serial_port.open()
        super().run()

    def loop(self):
        try:
            count = self.serial_port.in_waiting
            if count > 8:
                recv = np.frombuffer(self.serial_port.read(9), dtype=np.uint8)
                self.serial_port.reset_input_buffer()
                if recv[0] == 89 and recv[1] == 89: # 0x59 is 'Y'
                    checksum = np.sum(recv[:8]) & 0xff
                    if checksum == recv[8]:
                        distance = recv[2] + recv[3] * 256
                        strength = recv[4] + recv[5] * 256
                        logging.debug(f'distance={distance} strength={strength}')
                        self.reading = { 'time': time.time(), 'distance':distance, 'strength':strength }
                    else:
                        logging.warning('Bad checksum from TFMini-S')
                        self.reading = None
                else:
                    self.reading = None
            else:
                if self.reading is not None and time.time() - self.reading['time'] > self.timeout:
                    self.reading = None
        except Exception as ex:
            logging.warning('Unable to read TFMini-S', traceback.format_exc())
            self.reading = None
              
    def shutdown(self):
        if self.serial_port is not None:
            self.serial_port.close()
        self.serial_port = None
        super().shutdown()
