from states.state import AbstractState

import network
import utime
import machine

# from states.commissioning import Commissioning

from colors import Color
from constants import SSID, PASSWORD
from web.server import start_webserver


class Configuration(AbstractState):
    def enter(self):
        self.device.light.set_color(Color.CYAN)
        self.device.wlan = network.WLAN(network.AP_IF)
        print('> Configuration State...')
    
    
    def exec(self):
        self.device.wlan.active(True)
        self.device.wlan.config(essid=SSID, password=PASSWORD)

        print(">> AP IP:", self.device.wlan.ifconfig()[0])

        while True:
            clients = self.device.wlan.status('stations')
            print(">> Clients:", clients)
            if clients:
                break
            utime.sleep(3)
        
        try:
            start_webserver(self.device)
        except Exception:
            self.device.wlan.active(False)
            print("Error with start webserver")
        
        self.device.wlan.active(False)
        utime.sleep_ms(5000)
        machine.reset()
#         self.device.change_state(Commissioning(self.device))
    
    
    def exit(self):
        print('> Exit from Configuration state.')
