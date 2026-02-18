#! /usr/bin/python3
# -*- coding: <utf-8> -*-

import usb.core

'''
struct AB3510_EmbeddedData
{
	// Board general data
	std::string Name;
	std::string FirmwareVersion;
	std::string HardwareVersion;
	std::string SerialNumber;
	std::string PartNumber;

	// Calibration data
	Calibration Channels[4];
};
'''

class AB3510():
    '''
    DESCRIPTION
        Elementary functions to communicate with Apex AB3510 board
        this version can :
            - Get a sample from the four channels
            - Get the temperature value
        this version cannot :
            - Get samples in streaming mode
    VERSION
        1.0
    '''

    def __init__(self, Simulation=False):
        '''
        Constructor of AB3510 equipment.
        Simulation is a boolean to indicate to the program if it has to run in simulation mode or not
        '''
        from PyApex.Constantes import ABXXXX_NO_EQUIPMENT_FOUND, AB3510_PTS_NB
        from PyApex.Errors import ApexError
        from sys import exit
        
        self.Simulation = Simulation
        self.Handle = 0
        self.Device = None
        
        self.InternalData = {}
        self.InternalData["sn"] = "XX-AB3510-XXXXXX"
        self.InternalData["firmware"] = "1.0"
        self.InternalData["hardware"] = "1.0"
        self.InternalData["ch0"] = {}
        self.InternalData["ch1"] = {}
        self.InternalData["ch2"] = {}
        self.InternalData["ch3"] = {}
        self.EEPromOK = False
        
        self.Channels = []
        for i in range(0, 4):
            EEPromCalib = []
            PowerCalib = []
            for k in range(AB3510_PTS_NB):
                EEPromCalib.append([0.0, 0])
            for k in range(0, 2**14):
                PowerCalib.append(0.0)
            self.Channels.append([PowerCalib, [1.0, 0.0], [1.0, 0.0]])
        
        Devices = self.Find()
        if len(Devices) == 0:
            raise ApexError(ABXXXX_NO_EQUIPMENT_FOUND, "AB3510")
            exit()
        if len(Devices) == 1: 
            self.Open()
        

    def Find(self):
        from PyApex.Constantes import AB3510_VID, AB3510_PID
        Devices = []
        if not self.Simulation:
            for dev in usb.core.find(find_all = True, idVendor = AB3510_VID, idProduct = AB3510_PID):
                Devices.append(dev)
        else:
            Devices.append("AB3510 USB Simulator Device")
        return Devices


    def Open(self, Handle=0):
        '''
        Opens a connexion with an AB3510 equipment.
        This method is called by the constructor of AB3510 class if only 1 board is present
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
                    raise ApexError(ABXXXX_NO_EQUIPMENT_FOUND, "AB3510")
                    exit()
                elif len(Devices) <= Handle:
                    raise ApexError(ABXXXX_ERROR_BAD_HANDLE, Handle)
                    exit()
                
                self.Device = Devices[Handle]
                self.Device.set_configuration()
                print("Connected successfully to the equipment")
            except:
                print("Cannot connect to the equipment")


    def Close(self):
        '''
        Close connexion with AB3510 equipment
        '''
        self.Device = None


    def GetID(self):
        '''
        Return values of VID and PID of AB3510 equipment
        '''
        from PyApex.Constantes import SIMU_AB3510_VID, SIMU_AB3510_PID
        
        if self.Simulation:
            return [SIMU_AB3510_VID, SIMU_AB3510_PID]
        else:
            return [self.Device.idVendor, self.Device.idProduct]


    def Reset(self):
        '''
        Reset AB3510 equipment
        '''
        from PyApex.Constantes import AB3510_VR_RESET_ALL, ABXXXX_EP0_WRITE_ERROR
        from PyApex.Errors import ApexError
        from sys import exit
        
        if not self.Simulation:
            try:
                self.Device.ctrl_transfer(0x40, AB3510_VR_RESET_ALL, 0, 0)
            except:
                raise ApexError(ABXXXX_EP0_WRITE_ERROR, AB3510_VR_RESET_ALL)
                exit()


    def GetTemperature(self):
        '''
        Get the temperature on AB3510 equipment in degree Celsius
        '''
        from PyApex.Constantes import AB3510_VR_GET_TEMPERATURE, ABXXXX_EP0_READ_ERROR, SIMU_AB3510_TEMPERATURE
        from PyApex.Errors import ApexError
        from random import randint
        from sys import exit

        if self.Simulation:
            return SIMU_AB3510_TEMPERATURE
        else:
            try:
                TempWord = self.Device.ctrl_transfer(0xC0, AB3510_VR_GET_TEMPERATURE, 0, 0, 2)
            except:
                raise ApexError(ABXXXX_EP0_READ_ERROR, AB3510_VR_GET_TEMPERATURE)
                exit()
            else:
                return ((TempWord[0] * 256 + TempWord[1]) / 16) * 0.0625


    def GetSample(self):
        '''
        Get one sample from the 4 channels of AB3510
        '''
        from PyApex.Constantes import AB3510_VR_GET_SAMPLE, ABXXXX_EP0_READ_ERROR
        from PyApex.Errors import ApexError
        from sys import exit

        Samples = []
        if self.Simulation:
            for i in range(0, 4):
                Samples.append(randint(0, 16383))
        else:
            try:
                SampleWord = self.Device.ctrl_transfer(0xC0, AB3510_VR_GET_SAMPLE, 0, 0, 8)
            except:
                raise ApexError(ABXXXX_EP0_READ_ERROR, AB3510_VR_GET_SAMPLE)
                exit()
            else:
                for i in range(0, 8, 2):
                    Samples.append(int((SampleWord[i] + (SampleWord[i + 1] * 256)) / 4))
        return Samples    


    def SetEEPromData(self, Data):
        '''
        Set Data into the EEPROM of AB3510
        Data is a bytes object to write into the EEProm
        '''
        from PyApex.Constantes import AB3510_VR_SET_EEPROM_PARAMETERS, ABXXXX_EP0_WRITE_ERROR,\
             APXXXX_ERROR_ARGUMENT_TYPE
        from PyApex.Errors import ApexError
        from sys import exit

        if not isinstance(Data, (bytes, bytearray)):
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Data")
            exit()
        
        if self.Simulation:
            return True
        else:
            if len(Data) <= 64:
                self.Device.ctrl_transfer(0x40, AB3510_VR_SET_EEPROM_PARAMETERS, len(Data), 0, Data)
            else:
                Length = len(Data)
                print("Send the first 64 bytes")
                self.Device.ctrl_transfer(0x40, AB3510_VR_SET_EEPROM_PARAMETERS, Length, 0, Data[0:64])
                Index = 64
                Length -= 64
                for i in range(int(Length / 64)):
                    print("Send the " + str(i) + "ieme 64 bytes")
                    self.Device.ctrl_transfer(0x40, 0, 0, 0, Data[Index:Index + 64])
                    Index += 64
                    Length -= 64
                if Length > 0:
                    print("Send the last " + str(Length) + " bytes")
                    self.Device.ctrl_transfer(0x40, 0, 0, 0, Data[Index:Index + Length + 1])
            try:
                len(Data)
            except:
                raise ApexError(ABXXXX_EP0_WRITE_ERROR, AB3510_VR_SET_EEPROM_PARAMETERS)
                return False
            else:
                return True


    def GetEEPromData(self, BytesNumber):
        '''
        Get Data from the EEPROM of AB3510
        BytesNumber is the number of bytes to read from the EEProm
        Returns an array of the data bytes
        '''
        from PyApex.Constantes import AB3510_VR_GET_EEPROM_PARAMETERS, ABXXXX_EP0_READ_ERROR,\
             APXXXX_ERROR_ARGUMENT_TYPE
        from PyApex.Errors import ApexError
        from sys import exit

        if not isinstance(BytesNumber, int):
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "BytesNumber")
            exit()
        
        if self.Simulation:
            return -1
        else:
            Data = self.Device.ctrl_transfer(0xC0, AB3510_VR_GET_EEPROM_PARAMETERS, BytesNumber, 0, BytesNumber)
            try:
                len(Data)
            except:
                raise ApexError(ABXXXX_EP0_READ_ERROR, AB3510_VR_GET_EEPROM_PARAMETERS)
                return -1
            else:
                return Data

    
    def EEPromData2Parameters(self):
        '''
        Reads the data from the EEProm and converts these data into python variables
        '''
        from PyApex.Constantes import AB3510_PTS_NB
        from struct import unpack, calcsize
        
        Data = self.GetEEPromData(3500)
        
        if Data == -1:
            return False
        
        self.InternalData["sn"] = ""
        for c in Data[:20]:
            if c != 0:
                self.InternalData["sn"] += chr(c)
        I0 = 20
        
        self.InternalData["firmware"] = ""
        for c in Data[I0:I0 + 7]:
            if c != 0:
                self.InternalData["firmware"] += chr(c)
        I0 += 7
        
        self.InternalData["hardware"] = ""
        for c in Data[I0:I0 + 7]:
            if c != 0:
                self.InternalData["hardware"] += chr(c)
        I0 += 7
        
        self.EEPromOK = "3510" in self.InternalData["sn"] and self.InternalData["firmware"] == "1.0"
        
        for n in range(4):
            ChKey = "ch" + str(n)
            
            self.InternalData[ChKey]["powers"] = []
            for i in range(AB3510_PTS_NB):
                Istart = I0 + i * calcsize('f')
                Istop = Istart + calcsize('f')
                self.InternalData[ChKey]["powers"].append(unpack('f', Data[Istart:Istop])[0])
            I0 = Istop
            
            self.InternalData[ChKey]["values"] = []
            for i in range(AB3510_PTS_NB):
                Istart = I0 + i * calcsize('h')
                Istop = Istart + calcsize('h')
                self.InternalData[ChKey]["values"].append(unpack('h', Data[Istart:Istop])[0])
            I0 = Istop
            
            self.InternalData[ChKey]["tempcoeff"] = []
            self.InternalData[ChKey]["tempcoeff"].append(unpack('f', Data[I0:I0 + calcsize('f')])[0])
            I0 += calcsize('f')
            self.InternalData[ChKey]["tempcoeff"].append(unpack('f', Data[I0:I0 + calcsize('f')])[0])
            I0 += calcsize('f')
            self.InternalData[ChKey]["wavecoeff"] = []
            self.InternalData[ChKey]["wavecoeff"].append(unpack('f', Data[I0:I0 + calcsize('f')])[0])
            I0 += calcsize('f')
            self.InternalData[ChKey]["wavecoeff"].append(unpack('f', Data[I0:I0 + calcsize('f')])[0])
            I0 += calcsize('f')
        
        return True
    
    
    def Parameters2EEPromData(self):
        '''
        Converts the python variables into binary data and writes these data to the EEProm
        '''
        from PyApex.Constantes import AB3510_PTS_NB
        from struct import pack, calcsize
        
        format = ""
        for i in range(20 + 6 + 6):
            format += 'c'
        for i in range(4):
            for k in range(AB3510_PTS_NB):
                format += 'fh'
            format += 'ffff'
        
        Data = bytearray(bytes(calcsize(format)))
        
        for i in range(20):
            try:
                Data[i] = (ord(self.InternalData["sn"][i]))
            except:
                pass
        I0 = 20
        
        for i in range(6):
            try:
                Data[I0 + i] = (ord(self.InternalData["firmware"][i]))
            except:
                pass
        I0 += 6
        
        for i in range(6):
            try:
                Data[I0 + i] = (ord(self.InternalData["hardware"][i]))
            except:
                pass
        I0 += 6
        
        for n in range(4):
            ChKey = "ch" + str(n)
            
            for i in range(AB3510_PTS_NB):
                Temp = pack('f', self.InternalData[ChKey]["powers"][i])
                for k in range(calcsize('f')):
                    Data[I0 + k] = Temp[k]
                I0 += calcsize('f')
            
            for i in range(AB3510_PTS_NB):
                Temp = pack('h', self.InternalData[ChKey]["values"][i])
                for k in range(calcsize('h')):
                    Data[I0 + k] = Temp[k]
                I0 += calcsize('h')
            
            Temp = pack('ff', self.InternalData[ChKey]["tempcoeff"][0], self.InternalData[ChKey]["tempcoeff"][1])
            for i in range(calcsize('ff')):
                Data[I0 + i] = Temp[i]    
            I0 += calcsize('ff')
            
            Temp = pack('ff', self.InternalData[ChKey]["wavecoeff"][0], self.InternalData[ChKey]["wavecoeff"][1])
            for i in range(calcsize('ff')):
                Data[I0 + i] = Temp[i]    
            I0 += calcsize('ff')
        
        return self.SetEEPromData(Data)

