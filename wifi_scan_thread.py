import time

import wifi.exceptions
from wifi import Cell
import logging
from base_thread import BaseThread


class WifiScanThread(BaseThread):
    """Thread that uses the Wifi library to scan for Wifi networks and notify listeners if
    networks are found."""
    
    def __init__(self, ssids: dict[str,str], interface: str='wlan0'):
        """Scan for ssids that are the keys in the ssids dictionary.

        Parameters
        ----------
        ssid - dict[str,str] - dict of ssid to password mappings
        interface - str - interface to use for scanning, defaults to 'wlan0'
        """
        super(WifiScanThread, self).__init__()
        self.ssids = ssids
        self.interface = interface
        self.cells = None

    def loop(self) -> None:
        try:
            self.cells = list(Cell.all(self.interface))
            self.inform_listeners(self.cells)
            #logging.info(f'Wifi networks found {[cell.ssid for cell in self.cells]}')
        except wifi.exceptions.InterfaceError:
            logging.info('WiFi busy - scan skipped')
        time.sleep(1.0)

    def found(self) -> list[str]:
        """Checks to see if one of the given ssids is in the list of Wifi networks found.

        Returns
        -------
        list of ssids found, empty if nothing was found
        """
        if self.cells is None:
            return []
        return [cell for cell in self.cells if (cell.ssid in self.ssids)]

    def run(self) -> None:
        logging.info(f'scanning wifi {self.interface} for {self.ssids}')
        super().run()
