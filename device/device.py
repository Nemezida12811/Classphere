from states.state import AbstractState

from states.init import Init


class Device:
    def __init__(self):
        self.state: AbstractState = Init(self)
        self.config: dict = None
        self.wlan = None
        self.sensor_light = None
        self.sensor_gas_do = None
        self.sensor_gas_ao = None
        self.sensor_sound_do = None
        self.sensor_sound_ao = None
        self.sensor_dht11 = None
        self.button = None
        self.light = None
    
    def change_state(self, state: AbstractState):
        if state is not None:
            self.state = state
    
    def run(self):
        try:
            while True:
                state_sosud = self.state
                state_sosud.enter()
                state_sosud.exec()
                state_sosud.exit()
        except SystemExit:
            print('Sleeeep...')
