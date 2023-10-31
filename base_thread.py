from threading import Thread
import logging


class BaseThread(Thread):
    """All the threads that monitor the door open/close status, light up the NeoPixel strip, monitor the CPU temperature,
    and scan the Wifi inherit this base thread that allows for stopping the thread with a call to shutdown().
    Helper method allows for listeners (functions) to be added and informed of messages or changes by
    calling inform_listeners(message)."""
    def __init__(self, *args, **kwargs):
        super(BaseThread, self).__init__(daemon=True)
        self.running = False
        self.listeners = list()
        self.last_message = None

    def run(self) -> None:
        running = True
        while running:
            self.loop()

    def inform_listeners(self, message) -> None:
        if message == self.last_message:
            return
        self.last_message = message
        for listener in self.listeners:
            #logging.info(f'sending {message} to {type(listener)}')
            listener(message)

    def start(self) -> None:
        logging.info(f'{type(self)} started')
        super().start()

    def shutdown(self) -> None:
        self.running = False
