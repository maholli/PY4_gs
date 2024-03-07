#!/usr/bin/python3

"""
Usage:
cd ~/PY4_gs/rx_only
# no argument causes the script to read from default pckts
python3 parse_prior_pckts.py

# with argument reads only the argument file
python3 parse_prior_pckts.py packet.bin
"""

import time, os, binascii, sys
from beacon_parse_json import parse_beacon # PY4 beacon data unpacking

prior_pckts = []

def get_default_packets():
    # packet log location
    PCKT_LOG = os.path.expanduser('~')+'/gs_pckts.txt'

    # read out gs_pckts file
    with open(PCKT_LOG,'r') as f:
        l=f.readline().strip()
        while l:
            try:
                p = eval(l)
                p = binascii.unhexlify(p[3])
                prior_pckts.append(p)
            except Exception as e:
                print(f'reading error: {e}')
            l=f.readline().strip()

# check if the script was started with an argument
if len(sys.argv) > 1:
    # read out argument file. assume tinygs format
    with open(sys.argv[1],'rb') as f:
        l=f.read()
    if b'\n' in l:
        lines = l.split(b'\n')
        for line in lines:
            if line and len(line)==120:
                prior_pckts.append(binascii.unhexlify(line))
    else:
        if len(l) == 120:
            prior_pckts.append(binascii.unhexlify(l))
        else:
            prior_pckts.append(l)
else:
    # read default pckt file
    get_default_packets()


# for each packet, try and parse it as a PY4 beacon and print the result
for pckt in prior_pckts:
    try:
        parsed_pckt = parse_beacon(pckt,debug=True)
        # delay a small moment for dramatic effect (not needed)
        # time.sleep(0.1)
    except Exception as e:
        print(f'parsing error: {e} {pckt}')

