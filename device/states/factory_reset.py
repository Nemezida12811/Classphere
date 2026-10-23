from states.state import AbstractState

import machine
import os
import utime

from colors import Color
from constants import SETTINGS_FILE, SETTINGS


class FactoryReset(AbstractState):
    def enter(self):
        self.device.light.set_color(Color.ORANGE)
        print('> Factory Reset State...')
    
    
    def exec(self):
        if SETTINGS in os.listdir():
            os.remove(SETTINGS_FILE)
            print('>> Reset')

        
    def exit(self):
        print('> Exit from Factory Reset state.')
        utime.sleep(2)
        self.device.light.off()
        utime.sleep(1)
        machine.reset()
