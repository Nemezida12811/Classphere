from states.state import AbstractState

from models.payload import Payload #TODO

from states.ota import OTA

import datetime
import json
from helpers import create_topiс


class PublishData(AbstractState):
    def enter(self):
        print('>> Connect Publish Data State...')
    
    
    def exec(self):
        units = self.device.config.get("units")
        humidity = None
        topic = create_topiс(self.device, "data")
        
        
        now_iso = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        
        metrics = [
            {
                "dt": now_iso,
                "name": "temperature",
                "value": 0, #TODO
                "units": units
            },
            {
                "dt": now_iso,
                "name": "humidity",
                "value": 0, #TODO 
                "units": "%"
            }
        ]

        payload = Payload(
            dt = now_iso,
            metrics = metrics
        )

        
        json_payload = json.dumps(payload.__dict__)
        
        self.device.mqtt.publish(topic, json_payload)
        
        self.device.change_state(OTA(self.device))
       
       
    def exit(self):
        print('>> Exit from Publish Data state.')
