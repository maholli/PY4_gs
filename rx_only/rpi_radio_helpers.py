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

spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

radio1=pycubed_rfm9x.RFM9x(spi, CS1, RESET1, 915.6, code_rate=8, baudrate=5_000_000)
radio1.dio0 = IRQ1
radio1.node = 0x49 # default GS ID
radio1.ack_delay= 0.2
radio1.ack_wait = 2
radio1.set_params(cfg['r1b']) # default CRC True, SF7, BW62500
radio1._write_u8(0x11,0b00110111) # IRQ RxTimeout,RxDone,TxDone
radio1.listen()

