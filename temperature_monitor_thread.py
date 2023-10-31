import os
import logging
import time
from base_thread import BaseThread


class TemperatureMonitorThread(BaseThread):
    """Uses the vcgencmd measure_temp to monitor the CPU temperature."""
    def __init__(self):
        super(TemperatureMonitorThread, self).__init__()
        self.temperature = 0.0

    def loop(self):
        t = os.popen("vcgencmd measure_temp").readline()
        self.temperature = float(t.replace("temp=","").replace("'C\n",""))
        logging.debug(f'temperature={self.temperature}')
        self.inform_listeners(self.temperature)
        time.sleep(5)
