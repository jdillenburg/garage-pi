import logging

import requests


class Autoremote:
    """Interacts with Tasker Autoremote to tell your phone the status of your garage door."""
    def __init__(self, key):
        self.key = key

    def send_opened(self):
        """Tell your phone the door was opened."""
        self.__send_message__('garage-opened')

    def send_closed(self):
        """Tell your phone the door was closed."""
        self.__send_message__('garage-closed')

    def __send_message__(self, msg):
        r = requests.get(f'https://autoremotejoaomgcd.appspot.com/sendmessage?key={self.key}&message={msg}')
        if r.status_code != 200:
            logging.error(f'unable to send {msg} message to Autoremote ' + r.text)
