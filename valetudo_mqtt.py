import json
import os
import zlib

from dotenv import load_dotenv
from paho.mqtt import subscribe

load_dotenv()
MQTT_HOST = os.getenv('MQTT_HOST')
MQTT_USER = os.getenv('MQTT_USER')
MQTT_PASS = os.getenv('MQTT_PASS')

MAP_TOPIC = "valetudo/dreame/MapData/map-data"

if __name__ == '__main__':
    msg = subscribe.simple(MAP_TOPIC, hostname=MQTT_HOST, auth={"username": MQTT_USER, "password": MQTT_PASS})
    map_data = zlib.decompress(msg.payload)
    map_data = json.loads(map_data)
    # print(map_data)
    print(next(e for e in map_data['entities'] if e['type'] == 'robot_position')['points'])
    exit(0)
