from states.state import AbstractState

from constants import SETTINGS_FILE, WIFI_FREQ

from states.sleep import Sleep
from states.error import Error
from states.publish_data import PublishData

import network
import machine
import ntptime
import socket
import time
import json

from helpers import validate_host_address, to_iso8601, create_topiс


class ConnectNetwork(AbstractState):
    def enter(self):
        machine.freq(WIFI_FREQ)
        self.device.wlan = network.WLAN(network.STA_IF)
        self.device.wlan.active(True)
        print('>> Connect Network State...')
    
    
    def exec(self):
        try:
            wifi_settings = self.device.config.get("wifi", {})
            ssid = wifi_settings.get("ssid")
            key = wifi_settings.get("password")
            print(ssid, key)
            ntp_host = self.device.config.get("ntp_host")
            
        except Exception:
            print('invalid')
            self.device.change_state(Error(self.device))
            return
       
        self.device.wdt.feed()
        #
#         self.device.change_state(Error(self.device))
#         return
        #
        
        if not self.device.wlan.isconnected():
            print('   Connecting to network...')
            self.device.wlan.connect(ssid, key)
            
            start = time.ticks_ms()
            while not self.device.wlan.isconnected():
                if time.ticks_diff(time.ticks_ms(), start) > 20000:
                    print("   Timeout")
                    self.device.change_state(Error(self.device))
                    return
                machine.idle()
                
        print('   Network config:', self.device.wlan.ipconfig('addr4'))
        self.device.wdt.feed()
        
        if not validate_host_address(ntp_host):
            print('   Invalid host')
            self.device.change_state(Error(self.device))
            return
        
        try:
            ntptime.host = ntp_host
            ntptime.settime()
            print("   Time NTP:", time.localtime())
            
#             tm = time.localtime()
#             self.device.rtc.datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5]))
#             print("   RTC updated:", self.device.rtc.datetime())
            
        except Exception:
            self.device.change_state(Error(self.device))
            return
        
        self.device.wdt.feed()
        #
        
        topic = create_topiс(self.device, "status")
        
        my_msg = json.dumps({"status": "offline"})
        self.device.mqtt.set_last_will(topic=topic, msg=my_msg, retain=True)
        
        try:
            self.device.mqtt.connect()
        except Exception:
            self.device.change_state(Error(self.device))
            return
        
        my_msg_online = {
            "status": "online",
            "ip": ip,
            "fw_version": sys.version,
            "uptime_ms": time.ticks_ms(),
            "device_id": self.device.device_id
        }

        try:
            self.device.client.publish(topic_status, ujson.dumps(my_msg_online), retain=True)
            print("   Published device status")
        except Exception:
            self.device.change_state(Error(self.device))
            return

        
        self.device.change_state(PublishData(self.device))
       
       
    def exit(self):
        print('>> Exit from Connect Network state.')

