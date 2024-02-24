PY4 is a joint CMU / NASA Ames Small Spacecraft Constellation.

General mission webpage: to be announced

> [!TIP]
> You can manually parse PY4 beacons with this simple web app: https://maholli.github.io/PY4_gs/

| Sat ID     	| Name 	| Space-Track Name 	|
|:------------:	|:------:	|:------------------:	|
| 0x4A  (74) 	| Leo  	| PY4-1            	|
| 0x4B (75)  	| Don  	| PY4-2            	|
| 0x4C (76)  	| Raph 	| PY4-3            	|
| 0x4D (77)  	| Mike 	| PY4-4            	|

----

# Receiving & decoding PY4 beacon packets

Each of the four PY4 spacecraft transmit a LoRa modulated beacon packet every 30 seconds.

PY4 Beacon modulation parameters

|     LoRa Parameter        |   Value       |
|:----------------------:   |:---------:    |
|       Center Frequency    | 915.6 MHz     |
|       Spreading Factor    | 7             |
|              Bandwidth    | 62.5 kHz      |
|            Coding Rate    | 4 (CR4/8)     |
|                    CRC    | True          |
|        Preamble Length    | 8 Bytes       |
|       Explicit Header?    | True          |
| Low Datarate Optimize?    | True          |

### Hardware

This repo supports only RPI-based stations for now.

|                Hardware                   | PY4_gs Status                                              |
|:--------------------------------------:   |:-------------:    |
| RPI 3/4/5 Zero2 + [Adafruit LoRa Bonnet](https://www.adafruit.com/product/4074)    |       ✅          |
|            PyCubed Mainboard                                                       |      TBD          |
|     Adafruit Feather + FeatherWing                                                 |      TBD          |

### Python Dependencies

General python packages
```bash
# uncomment below if you have trouble with pip. Adjust python version accordingly.
# sudo rm /usr/lib/python3.12/EXTERNALLY-MANAGED
pip3 install msgpack paho-mqtt numpy
```

Setting up CircuitPython (if not done already)
```bash
sudo apt update && sudo apt upgrade -y
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y python3-pip ; sudo apt install --upgrade python3-setuptools
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0
sudo raspi-config nonint do_serial_hw 0
sudo raspi-config nonint do_ssh 0
sudo raspi-config nonint do_camera 0
sudo raspi-config nonint disable_raspi_config_at_boot 0
sudo apt-get install -y i2c-tools libgpiod-dev python3-libgpiod
pip3 install --upgrade RPi.GPIO ; pip3 install --upgrade adafruit-blinka
```

# RX Operation
There are two options for RX operation:
1. [py4_rx.py](./rx_only/py4_rx.py) logs all packets to a file.
2. [py4_rx_mqtt.py](./rx_only/py4_rx_mqtt.py) logs all packets to a file + attempts to send each packet to the PY4 mqtt server.

If your groundstation has internet access, please consider running py4_rx_mqtt.py (no additional setup required) to help us keep track of beacon packets over time. A public grafana dashboard will be available to view historic data.

Default radio config is an unmodified [Adafruit LoRa Bonnet](https://www.adafruit.com/product/4074) connected to the RPI. See [rpi_radio_helpers.py](./rx_only/rpi_radio_helpers.py) to adjust pin assignments or LoRa parameters.

To start the script:
```bash
cd PY_gs/rx_only && python3 py4_rx_mqtt.py
```

By default, the ground station will parse and print a formatted version of each beacon. To disable this, comment out the `PARSE_AND_PRINT_BEACONS` line of the respective script.

## Testing your RX station
It can be helpful to test your RX ground station without relying on a satellite pass. Below is a 60-byte packet exactly as it would be stored in the radio's FIFO buffer upon successful beacon reception. 

```python
# python bytes format
b'IL\x00\x00\x05\x00\x00\x00\x808mI\xf3\x11R\x00\n@\t\x00\x00\x00\xb1\x00R\x01\xa4\x00\x01\t\x00Q\xfe\xb5\xfe\xdd\xff\x02\x00\x1f\x00\x18\xc6\x00x\x00H\x01\x98\x04\x13\x0e\xd8\x00\x00\x00\x00\x00\x00I'
```
If you transmit the above packet from a second rfm9x radio setup while your RX station is running, you should see a parsed beacon message output in the terminal of your RX station running the python script.

NOTE: if you're using a CircuitPython library (pycubed_rfm9x.py, adafruit_rfm9x.py, etc...) to transmit the dummy packet, the library automatically inserts a 4-byte RadioHead header to the front of the data payload. Therefore, to transmit the above 60-byte payload you will need to trim the first 4 bytes off the dummy packet as well as set the `destination` and `node` bytes of the radio object as shown below. RadioHead header format: `[TO] [FROM] [MSG ID] [FLAGS]` (`[MSG ID]` and `[FLAGS]` will always be 0 in a beacon packet)

```python
#!/usr/bin/python3

import time,busio,board
from digitalio import DigitalInOut, Pull
import pycubed_rfm9x

# radio1 - STOCK ADAFRUIT BONNET https://www.adafruit.com/product/4074
CS1    = DigitalInOut(board.CE1)
RESET1 = DigitalInOut(board.D25)
IRQ1   = DigitalInOut(board.D22)

# set pins before radio init
CS1.switch_to_output(value=True)
RESET1.switch_to_output(value=True)
IRQ1.pull=Pull.DOWN

cfg = {
    'r1b':(1,7,62500,1),  # default radio1 beacon config (CRC,SF,BW,LDRO) symb=2ms
}

# dummy 60-byte beacon packet to send
dummy_packet = b'IL\x00\x00\x05\x00\x00\x00\x808mI\xf3\x11R\x00\n@\t\x00\x00\x00\xb1\x00R\x01\xa4\x00\x01\t\x00Q\xfe\xb5\xfe\xdd\xff\x02\x00\x1f\x00\x18\xc6\x00x\x00H\x01\x98\x04\x13\x0e\xd8\x00\x00\x00\x00\x00\x00I'

spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
radio1=pycubed_rfm9x.RFM9x(spi, CS1, RESET1, 915.6, code_rate=8, baudrate=5_000_000)
radio1.dio0 = IRQ1
radio1.node = dummy_packet[1]
radio1.ack_delay= 0.2
radio1.ack_wait = 2
radio1.set_params(cfg['r1b']) # default CRC True, SF7, BW62500
radio1._write_u8(0x11,0b00110111) # IRQ RxTimeout,RxDone,TxDone
radio1.listen()

# set the node id to the one used in the packet
# set the destination byte and transmit the packet
radio1.send(dummy_packet[4:],
    # set the 4-byte RadioHead header from the first four bytes of the dummy packet
    destination=dummy_packet[0],node=dummy_packet[1],identifier=dummy_packet[2],flags=dummy_packet[3],
    keep_listening=True)

```

