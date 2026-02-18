import serial
import time, sys, traceback
# sudo chmod a+rw /dev/ttyUSB1

'''
It is not reliable to use readInfo of the ARoF transmitter and receiver
Please reinitialize the object each time after set bias voltage
'''

'''
SETADD:X {CR,LF} X= 0,1,2,3,4,5,6,7,8, or 9; Sets the current address
(default = 0 for single unit)

READX {CR,LF} X = Current address, default 1; Reads the current
parameters of the LT-12-E-M device

READXC {CR,LF} X = Current address, default 1. Reads the laser diode
driving current setting.

SETXC:YYY {CR,LF} X = Current address, default 1; Y = Current in mA; Sets
the laser diode driving current setting. Max current indicated on test report.

READXB {CR, LF} X = Current address, default 1. Reads bias voltage

SETXB:YYY {CR,LF} X = Current address, default 1; Y = Bias voltage in V;
Sets bias voltage. Max bias voltage indicated on test report.
'''

class ARoF_transceiver():
    def __init__(self,port_num):
        self.port_num = port_num
        self.bias_vol_sleep_time = 5 # should not below this number by empirical
        self.infoReadingTime = 1
        self.arof = serial.Serial(self.port_num, baudrate=9600, timeout=1.0)

    def __del__(self):
        self.arof.close()
    
    def setAddr(self):
        self.arof.write(str.encode("SETADD 0\r\n"))
        rcv = self.arof.readline().decode()
        return rcv

    def readInfo(self):
        # not reliable
        # self.setAddr()
        # time.sleep(self.infoReadingTime)
        request = "READ0\r\n"
        self.arof.write(request.encode())
        time.sleep(self.infoReadingTime)
        rcv = self.arof.read(139).decode() # 138 is magic number
        return rcv
        
    def readOutputPower(self):
        print("Warning: transmitter power reading is not correct")
        info = self.readInfo()
        # input_power_line = info.split("\r\n")[-2]
        # input_power = input_power_line.split(":")[-1][:-4]
        # return float(input_power)
        splitedLines = [x for x in info.split("\r\n") if x]
        for line in splitedLines:
            if "Output" in line:
                try:
                    val_str = line.split(":")[-1].strip()     # "-2.97 dBm"
                    return float(val_str.split()[0])          # -2.97
                except Exception:
                    return line   
        # print(info)
        raise Exception("ARoF receiver Input power not found")

    def read_bias_vol(self):
        """
        READ0B — return the bias voltage (V) as a float.
        Example response: 'Bias is: -0.1'
        """
        self.arof.write(b"\r\nREAD0B\r\n") # SET0B:-1.10
        # rcv = self.arof.readline()
        # if len(rcv) <=0:
        #     print("unsuccess")
        # else:
        #     print(rcv.decode())
        #     return True # success
        rcv = self.arof.readline().decode(errors="ignore").strip()
        try:
            return float(rcv.split(":")[-1].strip())
        except Exception:
            raise Exception(f"Could not parse bias voltage from: {rcv!r}")
        
    def read_bias_cur(self):
        """
        READ0C — return the bias current (mA) as an integer.
        Example response: 'Current is: 099'
        """
        self.arof.write(b"\r\nREAD0C\r\n") # SET0B:-1.10
        # rcv = self.arof.readline()
        # if len(rcv) <=0:
        #     print("unsuccess")
        # else:
        #     print(rcv.decode())
        #     return True # success
        rcv = self.arof.readline().decode(errors="ignore").strip()
        # print(rcv)
        try:
            return int(rcv.split(":")[-1].strip())
        except Exception:
            raise Exception(f"Could not parse bias current from: {rcv!r}")

    # return true if set success
    # -2.5 <= bias <= +0.5
    def set_bias_vol(self,bias):
        """
        SET0B:<bias> — set bias voltage between -2.5 and 0.5 V.
        Example ack: 'Success Bias is: -0.1'
        """
        assert bias >=-2.5 and bias <= 0.5
        self.arof.write(f"\r\nSET0B:{bias}\r\n".encode())
        # rcv = self.arof.readline()
        rcv = self.arof.readline().decode(errors="ignore").strip()
        time.sleep(self.bias_vol_sleep_time)
        try:
            return float(rcv.split(":")[-1].strip())
        except Exception:
            return float(bias)

    # set bias current like 099, 050, etc...
    def set_bias_cur(self,bias):
        """
        SET0C:<YYY> — set bias current in mA.
        Example ack: 'Current is: 099'
        Accepts either a 3-digit string ('099') or an int (99).
        """
        bias_str = str(bias).zfill(3) if isinstance(bias, str) else f"{int(bias):03d}"
        self.arof.write(f"\r\nSET0C:{bias_str}\r\n".encode())
        # rcv = self.arof.readline()
        rcv = self.arof.readline().decode(errors="ignore").strip()
        # rcv = self.arof.read(50)
        try:
            return int(rcv.split(":")[-1].strip())
        except Exception:
            return int(bias_str)
        
class ARoF_reciever():
    def __init__(self,port_num):
        self.port_num = port_num
        self.infoReadingTime = 1
        self.arof = serial.Serial(self.port_num, baudrate=9600, timeout=3.0)

    def __del__(self):
        self.arof.close()

    def setAddr(self):
        self.arof.write(str.encode("SETADD 0\r\n"))
        # rcv = self.arof.readline()
        rcv = self.arof.readline().decode()
        return rcv

    def readInfo(self):
        # not reliable
        # self.setAddr()
        # time.sleep(self.infoReadingTime)
        request = "READ0\r\n"
        self.arof.write(request.encode())
        time.sleep(self.infoReadingTime)
        rcv = self.arof.read(120).decode()  # 120 is magic number
        return rcv
        
    def readInputPower(self):
        info = self.readInfo()
        # input_power_line = info.split("\r\n")[-2]
        splitedLines = info.split("\r\n")
        for line in splitedLines:
            if "Input" in line:
                try:
                    input_power = line.split(":")[-1][:-4]
                    return float(input_power)
                except:
                    print(line)
                    return line
        print(info)
        raise Exception("ARoF receiver Input power not found")

    def readTemperature(self):
        # never need temp ... 
        pass

# test_code
if False:
    arof_address = "/dev/ttyUSB1"
    # arof_address = "COM3"
    arof = ARoF_transceiver(arof_address)
    print("\nRead info: ", arof.readInfo())
    print("\nRead power: ", arof.readOutputPower())
    # print("\nset bias voltage: ", arof.set_bias_vol(-0.90))
    print("\nread bias voltage: ", arof.read_bias_vol())
    # print("\nset bias current: ", arof.set_bias_cur("099"))
    print("\nread bias current: ",arof.read_bias_cur())
    
if False:
    arof_address = "/dev/ttyUSB0"
    arof = ARoF_reciever(arof_address)
    print(arof.readInfo())
    print(arof.readInputPower())
    # print(input_power)