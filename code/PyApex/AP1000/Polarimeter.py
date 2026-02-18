

from PyApex.Common import Send, Receive


class Polarimeter():

    def __init__(self, Equipment, SlotNumber=1, Simulation=False):
        '''
        Constructor of a POL (Polarimeter) equipment.
        Equipement is the AP1000 class of the equipement
        SlotNumber is the number of the slot used by the POL
        Simulation is a boolean to indicate to the program if it has to run in simulation mode or not
        '''
        self.__Connexion = Equipment.Connexion
        self.__Simulation = Simulation
        self.__SlotNumber = SlotNumber
        self.__Unit = "dBm"
        self.__Wavelength = 1550
        self.__AcqTime = 100
        self.__ValidUnits = ["dbm", "mw"]


    def __str__(self):
        '''
        Return the equipement name and the slot number when the 'print()' function is used
        '''
        return "Polarimeter in slot " + str(self.__SlotNumber)
    
    
    def GetSlotNumber(self):
        '''
        Returns the slot number of the module
        '''
        
        return self.__SlotNumber


    def SetAcquisitionTime(self, AcqTime):
        '''
        Set the acquisition time of the POL equipment
        AcqTime is expressed in ms
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Constantes import AP1000_POL_ACQMIN, AP1000_POL_ACQMAX
        from PyApex.Errors import ApexError
        
        try:
            AcqTime = float(AcqTime)
        except:
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "AcqTime")
        else:
            if AcqTime < AP1000_POL_ACQMIN:
                print("PyApex Warning. POL Acquisition time is set to its minimum value: " + \
                      str(AP1000_POL_ACQMIN) + " ms !")
                AcqTime = AP1000_POL_ACQMIN
            if AcqTime > AP1000_POL_ACQMAX:
                print("PyApex Warning. PWM Average time is set to its maximum value: " + \
                      str(AP1000_POL_ACQMAX) + " ms !")
                AcqTime = AP1000_POL_ACQMAX
            
            if not self.__Simulation:
                Command = "POL[" + str(self.__SlotNumber).zfill(2) + "]:ACQTIME" + \
                          str(AcqTime) + "\n"
                Send(self.__Connexion, Command)
            
            self.__AcqTime = AcqTime


    def GetAcquisitionTime(self):
        '''
        Get the acquisition time of the POL equipment
        AcqTime is expressed in ms
        '''
        
        if not self.__Simulation:
            Command = "POL[" + str(self.__SlotNumber).zfill(2) + "]:ACQTIME?\n"
            Send(self.__Connexion, Command)
            self.__AcqTime = float(Receive(self.__Connexion)[:-1])
            
        return self.__AcqTime


    def SetUnit(self, Unit):
        '''
        Set the power unit of the POL equipment
        Unit is a string which could be "dBm" for logaritmic or "mW" for linear power
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE
        from PyApex.Errors import ApexError
        
        try:
            Unit = str(Unit)
        except:
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Unit")
        else:
            if Unit.lower() in self.__ValidUnits:
                self.__Unit = Unit


    def GetUnit(self):
        '''
        Get power unit of the POL equipment
        The return unit is a string
        '''
        return self.__Unit


    def SetWavelength(self, Wavelength):
        '''
        Set wavelength of the POL equipment
        Wavelength is expressed in nm
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Constantes import AP1000_POL_WLMIN, AP1000_POL_WLMAX
        from PyApex.Errors import ApexError
        
        try:
            Wavelength = float(Wavelength)
        except:
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Wavelength")
        else:
            if Wavelength < AP1000_POL_WLMIN:
                print("PyApex Warning. PWM Wavelength is set to its minimum value: " + \
                      str(AP1000_POL_WLMIN) + " nm !")
                Wavelength = AP1000_POL_WLMIN
            if Wavelength > AP1000_POL_WLMAX:
                print("PyApex Warning. PWM Wavelength is set to its maximum value: " + \
                      str(AP1000_POL_WLMAX) + " nm !")
                Wavelength = AP1000_POL_WLMAX
            
            if not self.__Simulation:
                Command = "POL[" + str(self.__SlotNumber).zfill(2) + \
                          "]:WL" + ("%4.3f" % Wavelength).zfill(8) + "\n"
                Send(self.__Connexion, Command)
            
            self.__Wavelength = Wavelength


    def GetWavelength(self):
        '''
        Get wavelength of the POL equipment
        The return wavelength is expressed in nm
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Errors import ApexError
        
        if not self.__Simulation:
            Command = "POL[" + str(self.__SlotNumber).zfill(2) + "]:WL?\n"
            Send(self.__Connexion, Command)
            self.__Wavelength = float(Receive(self.__Connexion)[:-1])
        
        return self.__Wavelength


    def SetFrequency(self, Frequency):
        '''
        Set frequency of the POL equipment
        Frequency is expressed in GHz
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Constantes import VACCUM_LIGHT_SPEED, AP1000_POL_WLMAX
        from PyApex.Errors import ApexError
        
        try:
            Frequency = float(Frequency)
        except:
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Frequency")
        else:              
            if Frequency > 0:
                self.SetWavelength(VACCUM_LIGHT_SPEED / Frequency)
            else:
                print("PyApex Warning. POL Frequency is set to its minimum value: " + \
                      str(AP1000_PWM_WLMAX / VACCUM_LIGHT_SPEED) + " GHz !")
                self.SetWavelength(AP1000_PWM_WLMAX)


    def GetFrequency(self):
        '''
        Get frequency of the POL equipment
        Frequency is expressed in GHz
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Constantes import VACCUM_LIGHT_SPEED
        from PyApex.Errors import ApexError
        
        try:
            Wavelength = self.GetWavelength(ChNumber)
            return float(VACCUM_LIGHT_SPEED / Wavelength)
        except:
            return 0.0


    def GetPower(self):
        '''
        Get the total power of the POL equipment
        The return power is expressed in the unit defined by the GetUnit() method
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Constantes import APXXXX_ERROR_VARIABLE_NOT_DEFINED
        from PyApex.Errors import ApexError
        from random import random
            
        if self.__Simulation:
            Power = random() * 70.0 - 60.0
            if self.__Unit.lower() == "mw":
                Power = 10.0**(Power / 10.0)
        else:
            if self.__Unit.lower() == "dbm":
                Command = "POL[" + str(self.__SlotNumber).zfill(2) + "]:DBM?\n"
            elif self.__Unit.lower() == "mw":
                Command = "POL[" + str(self.__SlotNumber).zfill(2) + "]:MW?\n"
            else:
                self.__Connexion.close()
                raise ApexError(APXXXX_ERROR_VARIABLE_NOT_DEFINED, "self.__Unit")
            
            Send(self.__Connexion, Command)
            Power = Receive(self.__Connexion)
            
            try:
                Power = float(Power[:-1])
            except:
                Power = float("NAN")
        
        return Power
    
    
    def GetSOP(self):
        '''
        Get a measured SOP by the POL equipment
        The returned SOP is expressed in nominal values and separated by space
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Constantes import APXXXX_ERROR_VARIABLE_NOT_DEFINED
        from PyApex.Errors import ApexError
        from random import random
            
        if self.__Simulation:
            SOP = []
            for i in range(4):
                SOP.append(random() * 2.0 - 1.0)
        else:
            Command = "POL[" + str(self.__SlotNumber).zfill(2) + "]:SOP?\n"           
            Send(self.__Connexion, Command)
            VALstr = Receive(self.__Connexion)
            VALstr = VALstr[:-1].split(" ")
            
            SOP = []
            for v in VALstr:
                try:
                    SOP.append(float(v))
                except:
                    SOP.append(float("NAN"))
        
        return SOP
    
    
    def GetBoardID(self):
        '''
        !!! FOR CALIBRATION ONLY !!!
        Get the AB3510 board ID in a list with the following elements:
            - The Serial Number of the board
            - The Firmware version
            - The EEPROM version
        '''
        
        if self.__Simulation:
            ID = []
            ID.append("XX-AB3510-XXXXXX")
            ID.append("1.0")
            ID.append("1.0")
        else:
            Command = "POL[" + str(self.__SlotNumber).zfill(2) + "]:BOARDID?\n"
            Send(self.__Connexion, Command)
            IDstr = Receive(self.__Connexion)
            
            ID = IDstr[:-1].split(" ")
        
        return ID
    
    
    def GetRawValues(self):
        '''
        !!! FOR CALIBRATION ONLY !!!
        Get the raw values of the 4 detectors of the POL equipment
        '''
        from random import randint
        
        if self.__Simulation:
            Raw = []
            for i in range(4):
                Raw.append(randint(0, 16384))
        else:
            Command = "POL[" + str(self.__SlotNumber).zfill(2) + "]:RAW4?\n"
            Send(self.__Connexion, Command)
            VALstr = Receive(self.__Connexion)
            VALstr = VALstr[:-1].split(" ")
            
            Raw = []
            for v in VALstr:
                try:
                    Raw.append(int(v))
                except:
                    Raw.append(float("NAN"))
        
        return Raw
    
    
    def GetPowerValues(self):
        '''
        !!! FOR CALIBRATION ONLY !!!
        Get the Power values (in dBm) of the 4 detectors of the POL equipment
        '''
        from random import random
        
        if self.__Simulation:
            Pow = []
            for i in range(4):
                Pow.append(random() * 70.0 - 60.0)
        else:
            Command = "POL[" + str(self.__SlotNumber).zfill(2) + "]:POW4?\n"
            Send(self.__Connexion, Command)
            VALstr = Receive(self.__Connexion)
            VALstr = VALstr[:-1].split(" ")
            
            Pow = []
            for v in VALstr:
                try:
                    Pow.append(float(v))
                except:
                    Pow.append(float("NAN"))
        
        return Pow
    
    
    def GetTemperature(self):
        '''
        !!! FOR CALIBRATION ONLY !!!
        Get the temperature (in °C) of the POL equipment
        '''
        from random import random
        
        if self.__Simulation:
            Temp = random() * 40.0 + 10.0
        else:
            Command = "POL[" + str(self.__SlotNumber).zfill(2) + "]:TEMP?\n"
            Send(self.__Connexion, Command)
            Temp = Receive(self.__Connexion)[:-1]

            try:
                Temp = float(Temp)
            except:
                Temp = float("NAN")
        
        return Temp
