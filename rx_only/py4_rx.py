#!/usr/bin/python3

"""
Listen for beacon packets and save locally.

For use on RPI or similar.

python external dependences:
pip install msgpack numpy
"""

# common python packages
import time, os, msgpack, struct
from binascii import hexlify,unhexlify
from pprint import pprint

# custom PY4 grounstand libs
from rpi_radio_helpers import radio1, cfg  # radio setup and config
from beacon_parse_json import parse_beacon # PY4 beacon data unpacking

# constants
PARSE_AND_PRINT_BEACONS = True

# packet log location
PCKT_LOG = os.path.expanduser('~')+'/gs_pckts.txt'
packet_cache = []

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
