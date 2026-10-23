from states.state import AbstractState

import json
import utime
import neopixel
import network

from states.factory_reset import FactoryReset
from states.configuration import Configuration
# from states.diagnostics import Diagnostics

from machine import ADC, Pin
from led import LedRGB
from colors import Color
from helpers import read_settings, validate_settings
from dht import DHT11

from constants import BTN_PIN, BLUE_PIN, GREEN_PIN, RED_PIN, SHORT_PRESS_DURATION, LONG_PRESS_DURATION, LIGHT_SEN_PIN, DO_GAS_SEN_PIN, AO_GAS_SEN_PIN, AO_SOUND_SEN_PIN, DO_SOUND_SEN_PIN, DHT11_SEN_PIN, DEFAULT_SETTINGS


class Init(AbstractState):
    def enter(self):
        print('> Init State...')
    
    
    def exec(self):
        #init
        self.device.light = LedRGB(RED_PIN, GREEN_PIN, BLUE_PIN)
        self.device.light.set_color(Color.GREEN)
        
        self.device.button = Pin(BTN_PIN, Pin.IN, Pin.PULL_UP)
        
        self.device.sensor_light = ADC(Pin(LIGHT_SEN_PIN))
        
        self.device.sensor_gas_do = Pin(DO_GAS_SEN_PIN, Pin.IN)
        self.device.sensor_gas_ao = ADC(Pin(AO_GAS_SEN_PIN))
        
        self.device.sensor_sound_do = Pin(DO_SOUND_SEN_PIN, Pin.IN)
        self.device.sensor_sound_ao = ADC(Pin(AO_SOUND_SEN_PIN))
        
        self.device.sensor_dht11 = DHT11(Pin(DHT11_SEN_PIN))
        
        self.device.config = read_settings()
        
        
        #button timer
        short_press = False
        long_press = False
        
        if not self.device.button.value():
            start_time = utime.ticks_ms()
            
            while not self.device.button.value():
                holding_time = utime.ticks_ms() - start_time
                
                if not short_press and holding_time >= SHORT_PRESS_DURATION and holding_time < LONG_PRESS_DURATION:
                    short_press = True
                    self.device.light.set_color(Color.CYAN)
                
                if not long_press and holding_time >= LONG_PRESS_DURATION:
                    short_press = False
                    long_press = True
                    self.device.light.set_color(Color.ORANGE)
                    break
                    
                utime.sleep_ms(100)
              
              
        #checks
        if long_press:
            self.device.change_state(FactoryReset(self.device))
        elif short_press or not self.device.config or not validate_settings(self.device.config, DEFAULT_SETTINGS):
            self.device.config = DEFAULT_SETTINGS
            self.device.change_state(Configuration(self.device))
        else:
            print(">> diag")
#             self.device.change_state(Diagnostics(self.device))
    
    
    def exit(self):
        print('> Exit from Init state.')
    