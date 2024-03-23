#!/usr/bin/python3

"""
EXAMPLE AND TESTING ONLY
    - Max (W5MAH) will update lora params automatically for a scheduled downlink attempt.

This script allows you to update the lora params of a currently running py4_downlink_mqtt.py instance.
Change the GROUND_STATION_ID and lora_settings values below and run the script.

For use on RPI or similar. Wifi required.

python external dependences:
pip install --upgrade paho-mqtt==1.6.1
pip install msgpack numpy
"""

# common python packages
import time, os, msgpack, struct, sys, json
from binascii import hexlify,unhexlify
import paho.mqtt.client as mqtt

# Must be the same value as you set in py4_downlink_mqtt.py
GROUND_STATION_ID = ""
if not GROUND_STATION_ID:
    print('Must provide your ground station ID')
    sys.exit()

"""
Define the settings we want to change.
These are the only configurable options at the moment.
TODO: allow center frequency to be changed
"""
lora_settings = {
    "SF":9,
    "BW":500000,
    "CR":8,
    "LDRO":1
}


# constants
PARSE_AND_PRINT_BEACONS = True
MQTT_DATA_TOPIC   = f"py4/{GROUND_STATION_ID}/pckts"
MQTT_CTRL_TOPIC   = f'ota/{GROUND_STATION_ID}/cmd'

# packet log location
PCKT_LOG = os.path.expanduser('~')+'/gs_pckts.txt'
packet_cache = []
mqtt_cache = []

# load overly obscured MQTT credentials
with open('py4_gs_config.bin','rb') as f:
    l=f.read()
    py4_gs_config=eval(msgpack.unpackb(unhexlify(bytes(struct.unpack(f'>{int.from_bytes(l[:3],"big")}i',l[3:])))))

# local broker debug only
# py4_gs_config['mqtt_host'] = "10.0.0.155"

# Create MQTT message callback
def on_mqtt_message(client, userdata, message):
    print(f'MQTT STATUS MSG: {message.payload}')

# Setup MQTT client stuff
mqttc = mqtt.Client(client_id="mqtt_cmd")
mqttc.username_pw_set(username=py4_gs_config['mqtt_client_username'],password=py4_gs_config['mqtt_client_password'])
mqttc.connect(host=py4_gs_config['mqtt_host'],port=py4_gs_config['mqtt_port'])
mqttc.on_message = on_mqtt_message
mqttc.subscribe('ota/status')
mqttc.loop_start()

mqttc.publish(MQTT_CTRL_TOPIC, payload=json.dumps(lora_settings))

# wait to see if we get a response
time.sleep(10)

mqttc.loop_stop()
mqttc.disconnect()
