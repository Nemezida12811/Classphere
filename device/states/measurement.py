from states.state import AbstractState

from states.connect_network import ConnectNetwork
from states.error import Error

from constants import MEASUREMENT_FILE

import json


class Measurement(AbstractState):
    def enter(self):
        print('>> Measurement State...')
    
    
    def exec(self):
        try:
            
            #
            self.device.change_state(ConnectNetwork(self.device))
            return
            #
            
            measure_data = self.device.sensor.measure()
            
            if os.path.exists(MEASUREMENT_FILE):
                with open(MEASUREMENT_FILE, 'r') as file:
                    try:
                        data = json.load(file)
                    except json.JSONDecodeError:
                        data = []
            else:
                data = []
                
            data.append(measure_data)
            
            with open(MEASUREMENT_FILE, 'w') as file:
                json.dump(data, file)
            
            print('>> Data added.')
            self.device.change_state(ConnectingWiFi(self.device))    
            
        except Exception:
            self.device.change_state(Error(self.device))
            return
        
        
    def exit(self):
        print('>> Exit from Measurement state.')
