#!/usr/bin/python3

"""
Listen for PY4 packets, save locally, and send MQTT
    - fresh start will always listen for beacons with default PY4 lora params
    - Max (W5MAH) will automatically try and update lora params over MQTT for scheduled downlink
        - OR you can always update lora params yourself over MQTT. See example_mqtt_cmd.py
    - Make sure to set GROUND_STATION_ID below

For use on RPI or similar. Wifi required.

python external dependences:
pip install --upgrade paho-mqtt==1.6.1
pip install msgpack numpy
"""

# common python packages
import time, os, msgpack, struct, json
from binascii import hexlify,unhexlify
from pprint import pprint
import paho.mqtt.client as mqtt

# custom PY4 grounstand libs
from rpi_radio_helpers import radio1, cfg # radio setup and config
from beacon_parse_json import parse_beacon # PY4 beacon data unpacking

# manually hard-code the lora parameters (can still be updated over MQTT)
radio1.set_params((1,10,500000,1)) # recent file downlink settings
radio1.listen()

# Please update. Can be set to anything you want your ground station to be called. 
GROUND_STATION_ID = "" # Letters and numbers only. No spaces
if not GROUND_STATION_ID:
    print('Must provide a ground station ID')
    sys.exit()

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
    mqtt_msg=False
    try:
        mqtt_msg = json.loads(message.payload)
        print(f'mqtt msg: {mqtt_msg}')
    except Exception as e:
        print(f'MQTT Payload Error: {e}')
    if mqtt_msg:
        if not all([i in mqtt_msg for i in ('SF','BW','CR','LDRO')]):
            print('\tBAD mqtt cmd')
        else:
            radio_cmd = (mqtt_msg['CR'],mqtt_msg['SF'],mqtt_msg['BW'],mqtt_msg['LDRO'])
            radio1.set_params(radio_cmd)
            radio1.listen()
            print(f'\tRadio parameters updated. {mqtt_msg}')
            client.publish('ota/status', payload=f'{client.my_client_id} success')

# Setup MQTT client stuff
mqttc = mqtt.Client(client_id=GROUND_STATION_ID)
mqttc.my_client_id = GROUND_STATION_ID
print("Testing mqtt broker connection...")
mqttc.username_pw_set(username=py4_gs_config['mqtt_client_username'],password=py4_gs_config['mqtt_client_password'])
try:
    test_rc = mqttc.connect(host=py4_gs_config['mqtt_host'],port=py4_gs_config['mqtt_port'])
    mqttc.on_message = on_mqtt_message
    mqttc.subscribe(MQTT_CTRL_TOPIC)
    mqttc.loop_start()
    if test_rc != mqtt.MQTT_ERR_SUCCESS:
        print(f'\tERROR establishing test mqtt connection! {test_rc}')
    else:
        print(f'\tSuccess')
        # mqttc.disconnect()
except Exception as e:
    print(f'\tERROR establishing test mqtt connection! {e}')

def save_cache():
    print(f'save length: {len(packet_cache)}')
    while packet_cache:
        parsed_data={}
        pckt=packet_cache.pop(0)
        print(f'{pckt[1]} GS Time: {pckt[0]}, RSSI: {pckt[2]-137}')
        if PARSE_AND_PRINT_BEACONS and len(pckt[3])==60 and pckt[3][0]==0x49:
            try:
                if PARSE_AND_PRINT_BEACONS:
                    parsed_data=parse_beacon(pckt[3],debug=True)
                    # if parsed_data: pprint(parsed_data) # debug json
            except Exception as e:
                print(f'beacon parsing error? {e}')
        # write packet to file
        with open(PCKT_LOG,'a') as f:
            # (gs timestamp, pckt count, pckt rssi, beacon pckt)
            f.write(f'({pckt[0]}, {pckt[1]}, {pckt[2]-137}, {hexlify(pckt[3])})\r\n')
        # build mqtt payload
        mqtt_payload = {
            'gs_time':pckt[0],
            'pckt_cnt':pckt[1],
            'pckt_rssi':pckt[2]-137,
            # 'test':True, # manually let database know this is a test packet
            'pckt_hex':hexlify(pckt[3]).decode()
        }
        if not parsed_data:
            mqtt_payload['gs_downlink'] = True
        # queue mqtt payload to be sent
        mqtt_cache.append(msgpack.packb(mqtt_payload))

def mqtt_publish():
    cnt=0
    print(f'mqtt length: {len(mqtt_cache)}')
    while mqtt_cache:
        payload=mqtt_cache.pop(0)
        cnt+=1
        try:
            if not mqttc.is_connected():
                try: mqttc.loop_stop()
                except: pass
                mqttc.connect(host=py4_gs_config['mqtt_host'],port=py4_gs_config['mqtt_port'])
                mqttc.subscribe(MQTT_CTRL_TOPIC)
                mqttc.loop_start()
            result = mqttc.publish(MQTT_DATA_TOPIC, payload=payload)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f'mqtt pub success.')
            else:
                print(f'mqtt pub ERROR: {result.rc}')
                mqtt_cache.insert(0,payload)
                time.sleep(1)
        except Exception as e:
            print(f'MQTT ERROR: {e}')
            mqtt_cache.insert(0,payload)

packet_count = 0
timestamp=0
print('Listening for UHF packets...')
while True:
    if radio1.rx_done():
        radio1.rpi_rx_fast(packet_cache,timeout=40)
    elif packet_cache:
        save_cache()
    elif mqtt_cache:
        mqtt_publish()
