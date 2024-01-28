# Receiving & decoding PY4 beacon packets

Each of the four PY4 spacecraft transmit a LoRa modulated beacon packet every 30 seconds.

Beacon modulation parameters

|     LoRa Parameter        |   Value       |
|:----------------------:   |:---------:    |
|              Frequency    | 915.6 MHz     |
|       Spreading Factor    | SF            |
|              Bandwidth    | 62.5 kHz      |
|            Coding Rate    | 4 (CR4/8)     |
|                    CRC    | True          |
|        Preamble Length    | 8 Bytes       |
|       Explicit Header?    | True          |
| Low Datarate Optimize?    | True          |

## Hardware

Any one of the following will work.

|                Hardware                   | PY4_gs Status     |
|:--------------------------------------:   |:-------------:    |
| RPI 3/4/5 Zero2 + Adafruit LoRa Bonnet    |       ✅          |
|            PyCubed Mainboard              |      TBD          |
|     Adafruit Feather + FeatherWing        |      TBD          |
