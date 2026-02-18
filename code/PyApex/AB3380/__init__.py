#! /usr/bin/python3
# -*- coding: <utf-8> -*-

import usb.core


class AB3380():
    '''
    DESCRIPTION
        Elementary functions to communicate with Apex AB3380 board via USB
    VERSION
        1.0
    '''

    def __init__(self, Simulation=False):
        '''
        Constructor of AB3380 equipment.
        Simulation is a boolean to indicate to the program if it has to run in simulation mode or not
        '''
        from PyApex.Constantes import ABXXXX_NO_EQUIPMENT_FOUND, AB3380_PTS_NB
        from PyApex.Errors import ApexError
        from sys import exit
        from math import fabs, sqrt
        
        self.Simulation = Simulation
        self.Handle = 0
        self.Device = None
        
        self.EEPromOK = False
        self.SerialNumber = "XX-3380-A-XXXXXX"     
        self.EEPromVersion = "0.0"
        
        self.WlTransistion = [1546.000, 1546.000]
        
        self.Wavelength = []
        self.DAC = [[], []]
        
        for i in range(AB3380_PTS_NB):
            self.Wavelength.append(1530.0 + (30.0 * i / AB3380_PTS_NB))
            self.DAC[0].append(sqrt(fabs(self.Wavelength[i] - self.WlTransistion[0])) * 15000)
            self.DAC[1].append(sqrt(fabs(self.Wavelength[i] - self.WlTransistion[1])) * 15000)
        
        Devices = self.Find()
        if len(Devices) == 0:
            raise ApexError(ABXXXX_NO_EQUIPMENT_FOUND, "AB3380")
            exit()
        if len(Devices) == 1: 
            self.Open()
        

    def Find(self):
        from PyApex.Constantes import AB3380_VID, AB3380_PID
        Devices = []
        if not self.Simulation:
            for dev in usb.core.find(find_all = True, idVendor = AB3380_VID, idProduct = AB3380_PID):
                Devices.append(dev)
        else:
            Devices.append("AB3380 USB Simulator Device")
        return Devices


    def Open(self, Handle=0):
        '''
        Opens a connexion with an AB3380 equipment.
        This method is called by the constructor of AB3380 class if only 1 board is present
        '''
        from PyApex.Constantes import ABXXXX_ERROR_BAD_HANDLE
        from PyApex.Errors import ApexError
        from sys import exit         
        
        if self.Simulation:
            print("Connected successfully to the equipment")
        else:
            try:
                Devices = self.Find()
                if len(Devices) == 0:
                    raise ApexError(ABXXXX_NO_EQUIPMENT_FOUND, "AB3380")
                    exit()
                elif len(Devices) <= Handle:
                    raise ApexError(ABXXXX_ERROR_BAD_HANDLE, Handle)
                    exit()
                
                self.Device = Devices[Handle]
                self.Device.set_configuration()
                print("Connected successfully to the equipment")
                self.EEPromData2Parameters()
            except:
                print("Cannot connect to the equipment")


    def Close(self):
        '''
        Close connexion with AB3380 equipment
        '''
        self.Device = None


    def GetID(self):
        '''
        Return values of VID and PID of AB3380 equipment
        '''
        from PyApex.Constantes import SIMU_AB3380_VID, SIMU_AB3380_PID
        
        if self.Simulation:
            return [SIMU_AB3380_VID, SIMU_AB3380_PID]
        else:
            return [self.Device.idVendor, self.Device.idProduct]


    def Reset(self):
        '''
        Reset AB3380 equipment
        '''
        from PyApex.Constantes import AB3380_VR_RESET_ALL, ABXXXX_EP0_WRITE_ERROR
        from PyApex.Errors import ApexError
        from sys import exit
        
        if not self.Simulation:
            try:
                self.Device.ctrl_transfer(0x40, AB3380_VR_RESET_ALL, 0, 0)
            except:
                raise ApexError(ABXXXX_EP0_WRITE_ERROR, AB3380_VR_RESET_ALL)
                exit()


    def SetVoltage(self, Voltage, Filter=1):
        '''
        Set the Voltage of one filter on AB3380
        Voltage is the binary value of the voltage (from 0 to 65535)
        Filter is the number of the filter 1 (default) or 2
        '''
        from PyApex.Constantes import AB3380_VR_SET_VOLTAGE1, AB3380_VR_SET_VOLTAGE2, ABXXXX_EP0_WRITE_ERROR
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Errors import ApexError
        from sys import exit

        if not isinstance(Voltage, (int, float)):
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Voltage")
            exit()

        if Voltage < 0 or Voltage > 65535:
            raise ApexError(APXXXX_ERROR_ARGUMENT_VALUE, "Voltage")
            exit()

        if not isinstance(Filter, (int, float)):
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Filter")
            exit()

        if Filter not in [1, 2]:
            raise ApexError(APXXXX_ERROR_ARGUMENT_VALUE, "Filter")
            exit()

        if not self.Simulation:
            try:
                if Filter == 2:
                    self.Device.ctrl_transfer(0x40, AB3380_VR_SET_VOLTAGE2, Voltage, 0)
                else:
                    self.Device.ctrl_transfer(0x40, AB3380_VR_SET_VOLTAGE1, Voltage, 0)
            except:
                raise ApexError(ABXXXX_EP0_WRITE_ERROR, AB3380_VR_SET_VOLTAGE1)
                exit()


    def SetSwitch(self, State, Filter=1):
        '''
        Set the Switch state of one filter on AB3380
        State is the binary state of the voltage ((0, 1) or (False, True))
        Filter is the number of the filter 1 (default) or 2
        '''
        from PyApex.Constantes import AB3380_VR_SET_SWITCH1, AB3380_VR_SET_SWITCH2, ABXXXX_EP0_WRITE_ERROR
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Errors import ApexError
        from sys import exit

        if not isinstance(State, (int, float, bool)):
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "State")
            exit()

        if int(State) not in [0, 1]:
            raise ApexError(APXXXX_ERROR_ARGUMENT_VALUE, "State")
            exit()

        if not isinstance(Filter, (int, float)):
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Filter")
            exit()

        if Filter not in [1, 2]:
            raise ApexError(APXXXX_ERROR_ARGUMENT_VALUE, "Filter")
            exit()

        if not self.Simulation:
            try:
                if Filter == 2:
                    self.Device.ctrl_transfer(0x40, AB3380_VR_SET_SWITCH2, State, 0)
                else:
                    self.Device.ctrl_transfer(0x40, AB3380_VR_SET_SWITCH1, State, 0)
            except:
                raise ApexError(ABXXXX_EP0_WRITE_ERROR, AB3380_VR_SET_SWITCH1)
                exit()  


    def SetEEPromData(self, Data):
        '''
        Set Data into the EEPROM of AB3380
        Data is a bytes object to write into the EEProm
        '''
        from PyApex.Constantes import AB3380_VR_SET_EEPROM_PARAMETERS, ABXXXX_EP0_WRITE_ERROR
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE
        from PyApex.Errors import ApexError
        from sys import exit

        if not isinstance(Data, bytes):
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Data")
            exit()
        
        if self.Simulation:
            return True
        else:
            self.Device.ctrl_transfer(0x40, AB3380_VR_SET_EEPROM_PARAMETERS, len(Data), 0, Data)
            try:
                len(Data)
            except:
                raise ApexError(ABXXXX_EP0_WRITE_ERROR, AB3380_VR_SET_EEPROM_PARAMETERS)
                return False
            else:
                return True


    def GetEEPromData(self, BytesNumber):
        '''
        Get Data from the EEPROM of AB3380
        BytesNumber is the number of bytes to read from the EEProm
        Returns an array of the data bytes
        '''
        from PyApex.Constantes import AB3380_VR_GET_EEPROM_PARAMETERS, ABXXXX_EP0_READ_ERROR
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE
        from PyApex.Errors import ApexError
        from sys import exit

        if not isinstance(BytesNumber, int):
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "BytesNumber")
            exit()
        
        if self.Simulation:
            return -1
        else:
            Data = self.Device.ctrl_transfer(0xC0, AB3380_VR_GET_EEPROM_PARAMETERS, BytesNumber, 0, BytesNumber)
            try:
                len(Data)
            except:
                raise ApexError(ABXXXX_EP0_READ_ERROR, AB3380_VR_GET_EEPROM_PARAMETERS)
                return -1
            else:
                return Data

    
    def EEPromData2Parameters(self):
        '''
        Reads the data from the EEProm and converts these data into python variables
        '''
        from PyApex.Constantes import AB3380_PTS_NB
        from struct import unpack, calcsize
        
        Data = self.GetEEPromData(1200)
        
        if Data == -1:
            return False
        
        self.SerialNumber = ""
        for c in Data[:19]:
            if c != 0:
                self.SerialNumber += chr(c)
        I0 = 20
        
        Temp = unpack('hh', Data[I0:I0 + calcsize('hh')])
        self.EEPromVersion = str(Temp[0]) + "." + str(Temp[1])
        I0 += calcsize('hh')
        
        self.EEPromOK = "3380" in self.SerialNumber and self.EEPromVersion == "0.0"
        
        self.WlTransistion[0] = unpack('f', Data[I0:I0 + calcsize('f')])[0] / 1000.0
        I0 += calcsize('f')
        self.WlTransistion[1] = unpack('f', Data[I0:I0 + calcsize('f')])[0] / 1000.0
        I0 += calcsize('f')
            
        self.Wavelength = []
        for i in range(AB3380_PTS_NB):
            Istart = I0 + i * calcsize('f')
            Istop = Istart + calcsize('f')
            self.Wavelength.append(unpack('f', Data[Istart:Istop])[0] / 1000.0)
        
        I0 = Istop
        self.DAC[0] = []
        for i in range(AB3380_PTS_NB):
            Istart = I0 + i * calcsize('f')
            Istop = Istart + calcsize('f')
            self.DAC[0].append(int(unpack('f', Data[Istart:Istop])[0]))   
        
        I0 = Istop
        self.DAC[1] = []
        for i in range(AB3380_PTS_NB):
            Istart = I0 + i * calcsize('f')
            Istop = Istart + calcsize('f')
            self.DAC[1].append(int(unpack('f', Data[Istart:Istop])[0]))
        
        return True
    
    
    def Parameters2EEPromData(self):
        '''
        Converts the python variables into binary data and writes these data to the EEProm
        '''
        from PyApex.Constantes import AB3380_PTS_NB
        from struct import pack, calcsize
        
        format = ""
        for i in range(20):
            format += 'c'
        format += 'hhff'
        for i in range(3):
            for k in range(AB3380_PTS_NB):
                format += 'f'
        
        Data = bytes(calcsize(format))
        
        for i in range(20):
            try:
                Data[i] = (ord(self.SerialNumber[i]))
            except:
                pass
        I0 = 20
        
        Temp = pack('hh', int(self.EEPromVersion[0]), int(self.EEPromVersion[2]))
        for i in range(calcsize('hh')):
            Data[I0 + i] = Temp[i]
        I0 += calcsize('hh')
        
        Temp = pack('ff', self.WlTransistion[0], self.WlTransistion[1])
        for i in range(calcsize('ff')):
            Data[I0 + i] = Temp[i]    
        I0 += calcsize('ff')
        
        for i in range(AB3380_PTS_NB):
            Temp = pack('f', self.Wavelength[i] * 1000.0)
            for k in range(calcsize('f')):
                Data[I0 + k] = Temp[k]
            I0 += calcsize('f')
        
        for i in range(AB3380_PTS_NB):
            Temp = pack('f', self.DAC[0][i])
            for k in range(calcsize('f')):
                Data[I0 + k] = Temp[k]
            I0 += calcsize('f')
        
        for i in range(AB3380_PTS_NB):
            Temp = pack('f', self.DAC[1][i])
            for k in range(calcsize('f')):
                Data[I0 + k] = Temp[k]
            I0 += calcsize('f')
        
        return self.SetEEPromData(Data)

    
    def SetWavelength(self, WavelengthOrder, Filter=1):
        '''
        Set the selected filter to the given wavelength
        WavelengthOrder is a float expressed in nm
        Filter is the number of the filter : 1 (default) or 2
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Errors import ApexError
        from sys import exit

        if not isinstance(WavelengthOrder, (int, float)):
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "WavelengthOrder")
            exit()

        if not isinstance(Filter, (int, float)):
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Filter")
            exit()

        if Filter not in [1, 2]:
            raise ApexError(APXXXX_ERROR_ARGUMENT_VALUE, "Filter")
            exit()
        
        if self.EEPromOK and not self.Simulation:
            Error = []
            for w in self.Wavelength:
                Error.append((w - WavelengthOrder)**2)
                
            Index = Error.index(min(Error))
            if self.Wavelength[Index] < WavelengthOrder:
                Index += 1
            
            if WavelengthOrder > self.WlTransistion[Filter - 1]:
                self.SetSwitch(True, Filter)
            else:
                self.SetSwitch(False, Filter)
            
            DWl = self.Wavelength[Index] - self.Wavelength[Index - 1]
            DB = self.DAC[Filter - 1][Index] - self.DAC[Filter - 1][Index - 1]
            C1 = DB / DWl
            C0 = self.DAC[Filter - 1][Index] - self.Wavelength[Index] * C1 
            self.SetVoltage(int(WavelengthOrder * C1 + C0), Filter)
    
            
            
            
            
            
            
            
            
            
            
            
            
            
            