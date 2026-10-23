from states.state import AbstractState

from constants import CPU_FREQ
from colors import Color, set_color
from helpers import wakeup

import sys
import machine


class Sleep(AbstractState):
    def enter(self):
        machine.freq(CPU_FREQ)
        set_color(self.device.light, Color.OFF)
        self.device.button.irq(trigger=machine.Pin.IRQ_FALLING, handler=wakeup)
        print('>> Sleep State...')
    
    
    def exec(self):
        
        if self.device.mqtt:
            if self.device.wlan.isconnected():
                self.device.mqtt.disconnect()
        
        if self.device.wlan:
            self.device.wlan.active(False)
            
        machine.lightsleep(self.config.get("measurement_interval"))
            
        sys.exit(0)
        
        
    def exit(self):
        print('>> Exit from Sleep state.')
