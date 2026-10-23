# helpers.py
import json
import time
import socket

from machine import reset

from constants import SETTINGS_FILE, DEFAULT_SETTINGS, TEMP_METRIC, TEMP_IMPERIAL, TEMP_STANDARD


def read_settings() -> dict:
    try:
        with open(SETTINGS_FILE, 'r') as file:
            return json.load(file)
    except OSError:
        print('ERROR: Settings file not found')
        
        
def save_settings(data):
    with open(SETTINGS_FILE, 'w') as file:
        json.dump(data, file)
        

def validate_settings(variable, inspector):
    for key, val in inspector.items():
        if key not in variable:
            return False

        if isinstance(val, dict):
            if not isinstance(variable[key], dict):
                return False

            if not validate_settings(variable[key], val):
                return False
    
    return True
        
        
def convert_temp(value: float, units: str) -> float:
    if units == TEMP_METRIC:
        return value

    if units == TEMP_IMPERIAL:
        return value * 9/5 + 32

    if units == TEMP_STANDARD:
        return value + 273.15

    raise SettingsError(f'Invalid unit "{units}"')


def validate_host_address(host) -> bool:
    try:
        socket.getaddrinfo(host, 123)
        return True
    except OSError:
        return False


def to_iso8601(ts: int = None) -> str:  #TODO
    dt = gmtime(ts)
    return f'{dt[0]:04}-{dt[1]:02}-{dt[2]:02}T{dt[3]:02}:{dt[4]:02}:{dt[5]:02}Z'


def wakeup():
    print('Waking up!')


def create_topiс(device, mode) -> str:
    mqtt_config = device.config.get("mqtt")
        
    department = mqtt_config.get("department")
    room = mqtt_config.get("room")
    type = "Sensor"
    id = mqtt_config.get("id")
    
    return f"{department}/{room}/{type}/{id}/{mode}"

    
def mqtt_callback(self, topic, msg):
        print("   MQTT message received:\n      Topic: {topic}\n      Message: {msg}")
        try:
            data = json.loads(msg)
            if "update" in data:
                print("   OTA update requested!")
                
                
                
            elif "command" in data:
                print("   Received command: {data['command']}")
            else:
                print("   Unknown message type.")
        except Exception:
            print("   Error parsing message:")
