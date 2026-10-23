#pin config
BTN_PIN = 0
BLUE_PIN  = 6
GREEN_PIN = 8
RED_PIN = 9
LIGHT_SEN_PIN = 26
DO_GAS_SEN_PIN = 1
AO_GAS_SEN_PIN = 27
AO_SOUND_SEN_PIN = 28
DO_SOUND_SEN_PIN = 15
DHT11_SEN_PIN = 2

DS3231_ADDR = 0x68

#press time
SHORT_PRESS_DURATION = 3000
LONG_PRESS_DURATION = 6000

#units
TEMP_METRIC = 'metric'
TEMP_IMPERIAL = 'imperial'
TEMP_STANDARD = 'standard'

#access point
SSID = "Inspector-comforT"
PASSWORD = "NADteam100"

#settings config
SETTINGS = "settings.json"
SETTINGS_FILE = '/settings.json'
MEASUREMENT_FILE = '/measurement.json'
DEFAULT_SETTINGS = {
    "user": {
        "login": "admin",
        "password": "4444",
    },
    "units": TEMP_STANDARD,
    "wifi": {
        "ssid": "",
        "password": "",   
    },
    "ntp_host": "pool.ntp.org",
    "mqtt": {
        "server": "",
        "port": 8883,
        "user": "",
        "password": "",
        "ssl": True,
        "cert": "",
    },
    "department": "",
    "room": "",
    "id": "",
    "measurement_interval" : 10000
}
