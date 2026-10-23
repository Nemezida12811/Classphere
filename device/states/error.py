from states.state import AbstractState

from colors import Color, set_color
from constants import CPU_FREQ

from states.sleep import Sleep

import utime
import machine


class Error(AbstractState):
    def enter(self):
        machine.freq(CPU_FREQ)
        print('>> Error State...')
    
    
    def exec(self):       
        counter = 1
        
        while counter <= 10:
            if counter % 2 == 0:
                set_color(self.device.light, Color.OFF)
            else:
                set_color(self.device.light, Color.RED)
                print('>> Red')
            counter += 1
            utime.sleep(0.5)
             
        self.device.change_state(Sleep(self.device))
       
       
    def exit(self):
        print('>> Exit from Error state.')
