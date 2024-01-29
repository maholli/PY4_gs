💡 PY4 is a joint CMU / NASA Ames Small Spacecraft Constellation.

General mission webpage TBD

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
