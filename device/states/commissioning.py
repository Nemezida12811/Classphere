from states.state import AbstractState

import states.configuration

from helpers import validate_host_address


class Commissioning(AbstractState):
    def enter(self):
        self.device.wlan = network.WLAN(network.STA_IF)
        print('>> Commissioning State...')
    
    
    def exec(self):

        self.device.wlan.active(True)

        ssid = self.device.config.get("wifi")
        password = self.device.config.get("password")

        if not ssid:
            print("   SSID not configured")
            self.device.change_state(Configuration(self.device))
            return

        print("   Connecting to Wi-Fi SSID: {ssid}")
        self.device.wlan.connect(ssid, password)

        if not self.device.wlan.isconnected():    
            start = time.ticks_ms()
            while not self.device.wlan.isconnected():
                if time.ticks_diff(time.ticks_ms(), start) > 20000:
                    print("   Timeout")
                    self.device.change_state(Configuration(self.device))
                    return
                machine.idle()
                
        print('   Network config:', self.device.wlan.ipconfig('addr4'))


        mqtt_config = self.device.config.get("mqtt")
        
        department = mqtt_config.get("department")
        room = mqtt_config.get("room")
        type = "Sensor"
        id = mqtt_config.get("id")
        
        topic = f"{department}/{room}/{type}/{id}/status"
        
        my_msg = json.dumps({"status": "offline"})
        self.device.mqtt.set_last_will(topic=topic, msg=my_msg, retain=True)
        
        try:
            self.device.mqtt.connect()
        except Exception:
            self.device.change_state(Configuration(self.device))
            return
        
        
        ntp_host = self.device.config.get("ntp_host")
        if not validate_host_address(ntp_host):
            print('   Invalid host')
            self.device.change_state(Configuration(self.device))
            return
        
        try:
            ntptime.host = ntp_host
            ntptime.settime()
            print("   Time NTP:", time.localtime())
            
#             tm = time.localtime()
#             self.device.rtc.datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5]))
#             print("   RTC updated:", self.device.rtc.datetime())
            
        except Exception:
            self.device.change_state(Configuration(self.device))
            return

        machine.reset()
     
    
    def exit(self):
        print('>> Exit from Commissioning state.')
        