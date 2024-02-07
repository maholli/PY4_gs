import struct, time
from collections import OrderedDict
try:
    import numpy as np
    from pprint import pprint
except:
    import ulab.numpy as np

sats = OrderedDict({
    0x49:'GS',
    0x4A:'Leo',
    0x4B:'Don',
    0x4C:'Raph',
    0x4D:'Mike'
    })
POWER_CONFIG = ('RF','SKY','SAMD','IRI','NOVA','RPI')
raw = bytearray(56)
view=memoryview(raw)

DSENSERES=25e-6 # 25uV resolution
SENSERES=0.02
MAG_SCALAR = (1/16) * 1e-6 # T
GYR_SCALAR = 1/65.6        # deg/s
# sat_X =  imu_Y, sat_Y = -imu_X, sat_Z = -imu_Z
R_sat_imu = np.array(
    (
        [0.0, 1.0, 0.0],
        [-1.0, 0.0, 0.0],
        [0.0, 0.0, -1.0],
    )
)

def calc_lux(raw_bytes):
    fractional_result=int.from_bytes(raw_bytes,'big')
    lux = 0.01 * (fractional_result&-61441) * 2 ** ((fractional_result & 61440) >> 12)
    return lux

def parse_beacon(beacon,debug=False):
    if beacon[0] in sats:
        view[:]=beacon[4:]
        pwr_cfg = "".join(reversed(f'{view[9]:08b}'))
        pwr_cfg = [int(i) for i in pwr_cfg]
        parsed_beacon_data = {
            'sat_id'            :beacon[1],
            'pckt_crc'          :view[-1],
            'boot_cnt'          :view[0],
            'sc_err_cnt'        :view[1],
            'vlowb_cnt'         :view[3],
            'detumbling_f'      :bool(view[4]>>2&1),
            'lowbtout_f'        :bool(view[4]>>3&1),
            'tumbling_f'        :bool(view[4]>>4&1),
            'shutdown_f'        :bool(view[4]>>5&1),
            'deploy_f'          :bool(view[4]>>6&1),
            'deploy_wait'       :bool(view[4]>>7&1),
            'rpi_status'        :view[4]&3,
            'sc_time'           :int.from_bytes(view[5:9],"big"), # sec
            'pwr_rf'            :pwr_cfg[0],
            'pwr_sky'           :pwr_cfg[1],
            'pwr_SAMD'          :pwr_cfg[2],
            'pwr_iri'           :pwr_cfg[3],
            'pwr_nova'          :pwr_cfg[4],
            'pwr_rpi'           :pwr_cfg[5],
            'vbatt'             :view[10]/10, # V
            'ichrg'             :view[11]*4,  # mA
            'idraw'             :(((view[12]<<8)|view[13])>>4)*DSENSERES/SENSERES, # A
            'radio_rsps'        :list(view[14:19]), # [0x49,0x4A,0x4B,0x4C,0x4D]
            'uhf_err_cnt'       :view[2],
            'sc_last_rssi'      :view[19]-137,
            }
        # rotating dataset
        if view[20] == 0xA8:
            _ecef = struct.unpack('<ddd',view[29:53])
            parsed_beacon_data.update({
            # gps dataset
            'time_stat'         :view[21],
            'gps_week'          :int.from_bytes(view[22:24],"little"),
            'gps_time'          :int.from_bytes(view[24:28],"little")/1000, # sec
            'pos_stat'          :view[28],
            'ecef_x'            :_ecef[0], # meters
            'ecef_y'            :_ecef[1], # meters
            'ecef_z'            :_ecef[2], # meters
            'sv_in_sol'         :view[53],
            'sd_rpi_files'      :view[54],
            })
        elif view[20] == b'R'[0]:
            _imu_mag = np.frombuffer(view[25:31], dtype='int16') * MAG_SCALAR
            _imu_gyr = np.frombuffer(view[31:37], dtype='int16') * GYR_SCALAR
            # rotate to spacecraft frame
            _imu_mag = np.dot(R_sat_imu,_imu_mag)
            _imu_gyr = np.dot(R_sat_imu,_imu_gyr)
            _sun_lux = np.frombuffer(view[37:49],dtype='>u2')
            _sun_lux = 0.01 * (_sun_lux&-61441) * 2 ** ((_sun_lux & 61440) >> 12)
            _which_rad = f'{"rad_r1" if any(view[52:55]) else "rad_r2"}'
            _rt=0
            if _which_rad == "rad_r1":
                _rt=(int.from_bytes(view[52:55],"big")*1.49012e-07*1000)
                _rt=(-1*((129.00-_rt)*0.403)+25)
            else: _rt = 0
            parsed_beacon_data.update({
            # rad dataset
            'rng_file_cnt'      :int.from_bytes(view[21:23],"big"),
            'rad_file_cnt'      :int.from_bytes(view[23:25],"big"),
            'mag_x'             :_imu_mag[0],
            'mag_y'             :_imu_mag[1],
            'mag_z'             :_imu_mag[2],
            'gyr_x'             :_imu_gyr[0],
            'gyr_y'             :_imu_gyr[1],
            'gyr_z'             :_imu_gyr[2],
            'sun_xp'            :_sun_lux[0],
            'sun_yp'            :_sun_lux[1],
            'sun_zp'            :_sun_lux[2],
            'sun_xn'            :_sun_lux[3],
            'sun_yn'            :_sun_lux[4],
            'sun_zn'            :_sun_lux[5],
            _which_rad          :(2.5-(int.from_bytes(view[49:52],"big")*1.49012e-07)), # V
            'rad_t'             :_rt, # deg C
            })
        # print(f'heard from {sats[beacon[1]]}:\n\t Packet: {bytes(view)}\n')
        # pprint(parsed_beacon_data)
        pd = parsed_beacon_data
        if debug:
            _crc=0
            for i in range(len(view)-1): _crc^=view[i]
            print(f'{"-"*20} {sats[beacon[1]]} {pd["sat_id"]} {hex(beacon[1])} {"-"*20}')
            print(f'{"Packet CRC":>23}: {bool(_crc==view[-1])} {hex(_crc)} {hex(view[-1])}')
            print(f'{"Boot Count":>23}: {view[0]} {pd["boot_cnt"]}')
            print(f'{"Error Count":>23}: {view[1]} {pd["sc_err_cnt"]}')
            print(f'{"Vlowb Count":>23}: {view[3]} {pd["vlowb_cnt"]}')
            print(f'{"NVM Flags":>23}: {view[4]}')
            print(f'{"":>18} └── Tumbling: {bool(view[4]>>4&1)} {pd["tumbling_f"]}, Detumbling: {bool(view[4]>>2&1)} {pd["detumbling_f"]}')
            print(f'{"":>18} └── Low Bat Timeout: {bool(view[4]>>3&1)} {pd["lowbtout_f"]}, Shutdown: {bool(view[4]>>5&1)} {pd["shutdown_f"]}')
            print(f'{"":>18} └── Deploy Wait: {bool(view[4]>>7&1)} {pd["deploy_wait"]}, Deploy Flag: {bool(view[4]>>6&1)} {pd["deploy_f"]}')
            print(f'{"":>18} └── RPI Status: {view[4]&3} {pd["rpi_status"]}')
            print(f'{"SC Time":>23}: {int.from_bytes(view[5:9],"big")} {pd["sc_time"]}')
            print(f'{"Power Config":>23}:')
            _pwrs = (pd["pwr_rf"],pd["pwr_sky"],pd["pwr_SAMD"],pd["pwr_iri"],pd["pwr_nova"],pd["pwr_rpi"])
            for i,j in enumerate("".join(reversed(f'{view[9]:08b}'))):
                if i>5: pass
                else: print(f'{"":>18} └── {POWER_CONFIG[i]:>4}: {j} {_pwrs[i]}')
            print(f'{"Vbatt":>23}: {view[10]/10:.1f}V {pd["vbatt"]}')
            print(f'{"Charge Current":>23}: {view[11]*4}mA {pd["ichrg"]}')
            _i = ((view[12]<<8) | view[13]) >> 4 # reduce from 16 bits to 12
            _i = _i * DSENSERES / SENSERES
            print(f'{"Current Draw":>23}: {_i}A {pd["idraw"]}')
            print(f'{"Radio Responses":>23}:')
            for i,j in enumerate(sats):
                print(f'{"":>18} └── [{hex(j)} {sats[j]:>4}] {view[14:19][i]} {pd["radio_rsps"][i]}')
            print(f'{"UHF CRC Error Count":>23}: {view[2]} {pd["uhf_err_cnt"]}')
            print(f'{"Last UHF RSSI":>23}: {view[19]-137}dBm {pd["sc_last_rssi"]}')
            # -------- rotating dataset ---------
            if view[20] == 0xA8:
                print(f'{"GPS dataset":>23}')
                _ecef = struct.unpack('<ddd',view[29:53])
                print(f'{"":>18} └── time status {view[21]} {pd["time_stat"]}')
                print(f'{"":>18} └── gps week {int.from_bytes(view[22:24],"little")} {pd["gps_week"]}')
                print(f'{"":>18} └── time of week (s) {int.from_bytes(view[24:28],"little")/1000} {pd["gps_time"]}')
                print(f'{"":>18} └── pos sol status {view[28]} {pd["pos_stat"]}')
                print(f'{"":>18} └── ECEF-X {_ecef[0]}m {pd["ecef_x"]}')
                print(f'{"":>18} └── ECEF-Y {_ecef[1]}m {pd["ecef_y"]}')
                print(f'{"":>18} └── ECEF-Z {_ecef[2]}m {pd["ecef_z"]}')
                print(f'{"":>18} └── SVs in sol {view[53]} {pd["sv_in_sol"]}')
                print(f'{"SD RPI Files":>23}: {view[54]} {pd["sd_rpi_files"]}')

            elif view[20] == b'R'[0]:
                print(f'{"IMU/SUN/RAD dataset":>23}')
                # File Counts
                print(f'{"":>18} └── Range File #: {int.from_bytes(view[21:23],"big")} {pd["rng_file_cnt"]}')
                print(f'{"":>18} └──   Rad File #: {int.from_bytes(view[23:25],"big")} {pd["rad_file_cnt"]}')

                # IMU
                print(f'{"IMU DATA":>23}')
                raw_mag  = struct.unpack('<hhh',view[25:31])   # (x,y,z)
                raw_mag = tuple(x * MAG_SCALAR for x in raw_mag)
                raw_gyro = struct.unpack('<hhh',view[31:37]) # (x,y,z)
                raw_gyro = tuple(x * GYR_SCALAR for x in raw_gyro)
                print(f'{"":>18} └──  IMU MAG: {raw_mag} {(pd["mag_x"],pd["mag_y"],pd["mag_z"])}')
                print(f'{"":>18} └── IMU GYRO: {raw_gyro} {(pd["gyr_x"],pd["gyr_z"],pd["gyr_z"])}')

                # SUN
                print(f'{"SUN DATA":>23}')
                _suns = (pd["sun_xp"],pd["sun_yp"],pd["sun_zp"],pd["sun_xn"],pd["sun_yn"],pd["sun_zn"])
                for i,j in enumerate(('+X','+Y','+Z','-X','-Y','-Z')):
                    pos = 37+(i*2)
                    print(f'{"":>18} └── [{j}] [{pos}:{pos+2}]: {calc_lux(view[pos:pos+2])} {_suns[i]}')

                # RAD
                print(f'{"RAD DATA":>23}')
                _which_rad = f'{"R1" if any(view[52:55]) else "R2"}'
                print(f'{"":>18} └── {_which_rad}: {(2.5-(int.from_bytes(view[49:52],"big")*1.49012e-07))} {pd["rad_r1" if _which_rad == "R1" else "rad_r2"]}')
                if _which_rad == "R1":
                    _rt=(int.from_bytes(view[52:55],"big")*1.49012e-07*1000)
                    print(f'{"":>18} └── T: {(-1*((129.00-_rt)*0.403)+25)} {pd["rad_t"]}')
            print()
        return parsed_beacon_data

# parse_beacon(a)
