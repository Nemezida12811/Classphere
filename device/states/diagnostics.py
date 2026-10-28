from states.state import AbstractState

from states.measurement import Measurement
from states.error import Error


class Diagnostics(AbstractState):
    def enter(self):
        print('>> Diagnostics State...')
    
    
    def exec(self):
        #
        self.device.change_state(Measurement(self.device))
        return
        #
        
        try:
            self.device.sensor.measure()
            
            if not (0 <= self.device.sensor.temperature() <= 50) or not (20 <= self.device.sensor.humidity() <= 90):
                self.device.change_state(Error(self.device))
                return
             
            #In progress
            if self.device.rtc is not None:
                dt = self.device.rtc.datetime()
                print("RTC datetime - ", dt)
            else:
                self.device.change_state(Error(self.device))
                return
            #
                
        except Exception:
            self.device.change_state(Error(self.device))
            return
        
        self.device.change_state(Measurement(self.device))
        
        
    def exit(self):
        print('>> Exit from Diagnostics state.')
