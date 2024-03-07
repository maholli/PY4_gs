#!/usr/bin/python3

"""
Usage:
cd ~/PY4_gs/rx_only
python3 parse_prior_pckts.py
"""

import time, os, binascii
from beacon_parse_json import parse_beacon # PY4 beacon data unpacking

# packet log location
PCKT_LOG = os.path.expanduser('~')+'/gs_pckts.txt'

# read out gs_pckts file and
prior_pckts = []
with open(PCKT_LOG,'r') as f:
    l=f.readline().strip()
    while l:
        try:
            prior_pckts.append(eval(l))
        except Exception as e:
            print(f'reading error: {e}')
        l=f.readline().strip()

# for each packet, try and parse it as a PY4 beacon and print the result
for pckt in prior_pckts:
    try:
        beacon = pckt[3]
        parsed_pckt = parse_beacon(binascii.unhexlify(beacon),debug=True)
        # delay a small moment for dramatic effect (not needed)
        # time.sleep(0.1)
    except Exception as e:
        print(f'parsing error: {e}')

