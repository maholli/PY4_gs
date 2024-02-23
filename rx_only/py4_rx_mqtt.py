#!/usr/bin/python3

"""
Listen for beacon packets, save locally, and send MQTT

For use on RPI or similar. Wifi required.

python external dependences:
pip install --upgrade paho-mqtt==1.6.1
pip install msgpack numpy
"""

# common python packages
import time, os, msgpack, struct
from binascii import hexlify,unhexlify
from pprint import pprint
import paho.mqtt.client as mqtt

# custom PY4 grounstand libs
from rpi_radio_helpers import radio1, cfg  # radio setup and config
from beacon_parse_json import parse_beacon # PY4 beacon data unpacking

# Please update. Can be set to anything you want your ground station to be called. 
GROUND_STATION_ID = "gs01" # Letters and numbers only. No spaces
# constants
PARSE_AND_PRINT_BEACONS = True
MQTT_DATA_TOPIC   = f"py4/{GROUND_STATION_ID}/pckts"

# load overly obscured MQTT credentials
with open('py4_gs_config.bin','rb') as f:
    l=f.read()
    py4_gs_config=eval(msgpack.unpackb(unhexlify(bytes(struct.unpack(f'>{int.from_bytes(l[:3],"big")}i',l[3:])))))

# local broker debug only
# py4_gs_config['mqtt_host'] = "10.0.0.155"

# Setup MQTT client stuff
mqttc = mqtt.Client(client_id=GROUND_STATION_ID)
print("Testing mqtt broker connection...")
mqttc.username_pw_set(username=py4_gs_config['mqtt_client_username'],password=py4_gs_config['mqtt_client_password'])
try:
    test_rc = mqttc.connect(host=py4_gs_config['mqtt_host'],port=py4_gs_config['mqtt_port'])
    if test_rc != mqtt.MQTT_ERR_SUCCESS:
        print(f'\tERROR establishing test mqtt connection! {test_rc}')
    else:
        print(f'\tSuccess')
        mqttc.disconnect()
except Exception as e:
    print(f'\tERROR establishing test mqtt connection! {e}')

# packet log location
PCKT_LOG = os.path.expanduser('~')+'/gs_pckts.txt'
packet_cache = []
mqtt_cache = []

def save_cache():
    # only one cached item per loop
    pckt=packet_cache.pop(0)
    print(f'{pckt[1]} GS Time: {pckt[0]}, RSSI: {pckt[2]-137}')
    try:
        if PARSE_AND_PRINT_BEACONS:
            parsed_data=parse_beacon(pckt[3],debug=True)
            # if parsed_data: pprint(parsed_data) # debug json
    except Exception as e:
        print(f'parsing error? {e}')
        parsed_data={}
    # write packet to file
    with open(PCKT_LOG,'a') as f:
        # (gs timestamp, pckt count, pckt rssi, beacon pckt)
        f.write(f'({pckt[0]}, {pckt[1]}, {pckt[2]-137}, {hexlify(pckt[3])})\r\n')
    # build mqtt payload
    mqtt_payload = {
        'gs_time':pckt[0],
        'pckt_cnt':pckt[1],
        'pckt_rssi':pckt[2]-137,
        'pckt_hex':hexlify(pckt[3]).decode()
    }
    # queue mqtt payload to be sent
    mqtt_cache.append(msgpack.packb(mqtt_payload))

def mqtt_publish():
    # only one cached item per loop
    payload=mqtt_cache.pop(0)
    try:
        mqttc.connect(host=py4_gs_config['mqtt_host'],port=py4_gs_config['mqtt_port'])
        result = mqttc.publish(MQTT_DATA_TOPIC, payload=payload)
        mqttc.loop()
        if result.rc != mqtt.MQTT_ERR_SUCCESS and mqttc.loop() != mqtt.MQTT_ERR_SUCCESS:
            print(f'PUB ERROR: {result.rc}')
            mqtt_cache.insert(0,payload)
        else:
            print(f'mqtt pub success.')
    except Exception as e:
        print(f'MQTT ERROR: {e}')
        mqtt_cache.insert(0,payload)

packet_count = 0
timestamp=0
print('Listening for UHF packets...')
while True:
    if radio1.rx_done():
        timestamp=time.time_ns()
        packet = radio1.receive(keep_listening=True,with_ack=False,with_header=True)
        if packet is not None:
            packet_count+=1
            packet_cache.append([timestamp,packet_count,radio1.last_rssi,packet])
    elif packet_cache:
        save_cache()
    elif mqtt_cache:
        mqtt_publish()
