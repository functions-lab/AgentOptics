

from PyApex.Common import Send, Receive


class TunableLaser():

    def __init__(self, Equipment, SlotNumber, Simulation=False):
        '''
        Constructor of a TLS (Tunable Laser Source) equipment.
        Equipement is the AP1000 class of the equipement
        SlotNumber is the number of the slot used by the TLS
        Simulation is a boolean to indicate to the program if it has to run in simulation mode or not
        '''
        self.__Connexion = Equipment.Connexion
        self.__SlotNumber = SlotNumber
        self.__Simulation = Simulation
        self.__Type = self.GetType()
        self.__Unit = "dBm"
        self.__Wavelength = 1550
        self.__Power = 0
        self.__Status = "OFF"
        self.__ValidUnits = ["dbm", "mw"]


    def __str__(self):
        '''
        Return the equipement name and the slot number when the 'print()' function is used
        '''
        return "Tunable Laser in slot " + str(self.__SlotNumber)
    
    
    def GetSlotNumber(self):
        '''
        Returns the slot number of the module
        '''
        
        return self.__SlotNumber
    
    
    def GetType(self):
        '''
        Return the type of the TLS
        return 0 for a C band Laser
        return 2 for a L band Laser
        '''
        from PyApex.Constantes import AP1000_ERROR_SLOT_TYPE_NOT_DEFINED
        from PyApex.Constantes import SimuTLS_SlotID, AP1000_TLS_CBAND, AP1000_TLS_LBAND
        from PyApex.Errors import ApexError
        import re
        
        if self.__Simulation:
            ID = SimuTLS_SlotID
        else:
            Command = "SLT[" + str(self.__SlotNumber).zfill(2) + "]:IDN?\n"
            Send(self.__Connexion, Command)
            ID = Receive(self.__Connexion)

        if re.findall(str(AP1000_TLS_CBAND), ID.split("/")[1]) != []:
            return 0
        elif re.findall(str(AP1000_TLS_LBAND), ID.split("/")[1]) != []:
            return 2
        else:
            self.Off()
            self.__Connexion.close()
            raise ApexError(AP1000_ERROR_SLOT_TYPE_NOT_DEFINED, self.__SlotNumber)
            
    
    def __ConvertForWriting(self, Power):
        '''
        Internal use only
        Convert a dBm power in mW or a mW power in dBm
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_VALUE, APXXXX_ERROR_VARIABLE_NOT_DEFINED
        from PyApex.Errors import ApexError
        from math import log10 as log
        
        if self.__Unit.lower() == "dbm":
            return Power
        elif self.__Unit.lower() == "mw":
            try:
                log(Power)
            except:
                self.Off()
                self.__Connexion.close()
                raise ApexError(APXXXX_ERROR_ARGUMENT_VALUE, "Power")
            else:
                return -10 * log(Power/100)
        else:
            self.Off()
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_VARIABLE_NOT_DEFINED, "self.__Unit")


    def __ConvertForReading(self, Power):
        '''
        Internal use only
        Convert a dBm power in mW or a mW power in dBm
        '''
        from PyApex.Constantes import APXXXX_ERROR_VARIABLE_NOT_DEFINED
        from PyApex.Errors import ApexError
        
        if self.__Unit.lower() == "mw":
            return 10**(Power / 10)
        elif self.__Unit.lower() == "dbm":
            return Power
        else:
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_VARIABLE_NOT_DEFINED, "self.__Unit")


    def SetPower(self, Power):
        '''
        Set output power of the TLS equipment
        Power is expressed in the unit defined by the GetUnit() method
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Constantes import AP1000_TLS_POWMIN, AP1000_TLS_POWMAX
        from PyApex.Errors import ApexError
        
        try:
            Power = float(Power)
        except:
            self.Off()
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Power")
        else:
            Power = self.__ConvertForWriting(Power)
            if Power < AP1000_TLS_POWMIN[self.__Type]:
                print("PyApex Warning. TLS Power is set to its minimum value: " + \
                      str(AP1000_TLS_POWMIN[self.__Type]) + " dBm !")
                Power = AP1000_TLS_POWMIN[self.__Type]
            elif Power > AP1000_TLS_POWMAX[self.__Type]:
                print("PyApex Warning. TLS Power is set to its maximum value: " + \
                      str(AP1000_TLS_POWMIN[self.__Type]) + " dBm !")
                Power = AP1000_TLS_POWMAX[self.__Type]
                
            if not self.__Simulation:
                Command = "TLS[" + str(self.__SlotNumber).zfill(2) + "]:TPDB" + \
                          ("%.1f" % Power) + "\n"
                Send(self.__Connexion, Command)
            
            self.__Power = Power


    def GetPower(self):
        '''
        Get output power of the TLS equipment
        The return power is expressed in the unit defined by the GetUnit() method
        '''
        
        if not self.__Simulation:
            Command = "TLS[" + str(self.__SlotNumber).zfill(2) + "]:TPDB?\n"
            Send(self.__Connexion, Command)
            self.__Power = self.__ConvertForReading(float(Receive(self.__Connexion)[:-1]))
        
        return self.__Power


    def SetUnit(self, Unit):
        '''
        Set the power unit of the TLS equipment
        Unit is a string which could be "dBm" for logaritmic or "mW" for linear power
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE
        from PyApex.Errors import ApexError
        
        try:
            Unit = str(Unit)
        except:
            self.Off()
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Unit")
        else:
            if Unit.lower() in self.__ValidUnits:
                self.__Unit = Unit


    def GetUnit(self):
        '''
        Get power unit of the TLS equipment
        The return unit is a string
        '''
        return self.__Unit


    def On(self):
        '''
        Activate the output power of TLS equipment
        Waits 0.2 second after switching on
        '''
        from time import sleep
        
        if not self.__Simulation:
            Command = "TLS[" + str(self.__SlotNumber).zfill(2) + "]:L1\n"
            Send(self.__Connexion, Command)
        self.__Status = "ON"
        sleep(0.2)


    def Off(self):
        '''
        Shut down the output power of the TLS equipment
        '''
        if not self.__Simulation:
            Command = "TLS[" + str(self.__SlotNumber).zfill(2) + "]:L0\n"
            Send(self.__Connexion, Command)
        self.__Status = "OFF"


    def GetStatus(self):
        '''
        Return the status ("ON" or "OFF") of the TLS equipment
        '''
        return self.__Status


    def SetWavelength(self, Wavelength):
        '''
        Set wavelength of the TLS equipment
        Wavelength is expressed in nm
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Constantes import AP1000_TLS_WLMIN, AP1000_TLS_WLMAX
        from PyApex.Errors import ApexError
        
        try:
            Wavelength = float(Wavelength)
        except:
            self.Off()
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Wavelength")
        else:
            if Wavelength < AP1000_TLS_WLMIN[self.__Type]:
                print("PyApex Warning. TLS Wavelength is set to its minimum value: " + \
                      str(AP1000_TLS_WLMIN[self.__Type]) + " nm !")
                Wavelength = AP1000_TLS_WLMIN[self.__Type]
            if Wavelength > AP1000_TLS_WLMAX[self.__Type]:
                print("PyApex Warning. TLS Wavelength is set to its maximum value: " + \
                      str(AP1000_TLS_WLMAX[self.__Type]) + " nm !")
                Wavelength = AP1000_TLS_WLMAX[self.__Type]
            
            if not self.__Simulation:
                Command = "TLS[" + str(self.__SlotNumber).zfill(2) + "]:TWL" + \
                          ("%4.3f" % Wavelength).zfill(8) + "\n"
                Send(self.__Connexion, Command)
            
            self.__Wavelength = Wavelength


    def GetWavelength(self):
        '''
        Get wavelength of the TLS equipment
        The return wavelength is expressed in nm
        '''
        
        if not self.__Simulation:
            Command = "TLS[" + str(self.__SlotNumber).zfill(2) + "]:TWL?\n"
            Send(self.__Connexion, Command)
            self.__Wavelength = float(Receive(self.__Connexion)[:-1])
            
        return self.__Wavelength


    def SetFrequency(self, Frequency):
        '''
        Set frequency of the TLS equipment
        Frequency is expressed in GHz
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Constantes import VACCUM_LIGHT_SPEED, AP1000_TLS_WLMAX
        from PyApex.Errors import ApexError
        
        try:
            Frequency = float(Frequency)
        except:
            self.Off()
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Frequency")
        else:
            if Frequency > 0:
                self.SetWavelength(VACCUM_LIGHT_SPEED / Frequency)
            else:
                print("PyApex Warning. TLS Frequency is set to its minimum value: " + \
                      str(AP1000_TLS_WLMAX[self.__Type] / VACCUM_LIGHT_SPEED) + " GHz !")
                self.SetWavelength(AP1000_TLS_WLMAX[self.__Type])


    def GetFrequency(self):
        '''
        Get frequency of the TLS equipment
        The return frequency is expressed in GHz
        '''
        from PyApex.Constantes import VACCUM_LIGHT_SPEED
            
        Wavelength = self.GetWavelength()
        return VACCUM_LIGHT_SPEED / Wavelength
    
    
    def SetSOACurrent(self, Current):
        '''
        !!! FOR TLS CALIBRATION ONLY !!!
        Set the SOA current. 'Current' is a 16-bits binary value 
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Constantes import AP1000_TLS_SOAMIN, AP1000_TLS_SOAMAX
        from PyApex.Errors import ApexError
        
        if not isinstance(Current, (float, int)):
            self.Off()
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Current")
            
        if Current < AP1000_TLS_SOAMIN or Current > AP1000_TLS_SOAMAX:
            self.Off()
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_VALUE, "Current")
            
        if not self.__Simulation:
            Command = "TLS[" + str(self.__SlotNumber).zfill(2) + "]:SETSOAVALUE" + str(Current) + "\n"
            Send(self.__Connexion, Command)
            
        self.__SOACurrent = Current
        
        
    def GetSOALimit(self):
        '''
        !!! FOR TLS CALIBRATION ONLY !!!
        Get the SOA Degrade status. Returns True if the SOA is out
        of bounds, False otherwise
        '''
        from PyApex.Errors import ApexError
            
        if not self.__Simulation:
            Command = "TLS[" + str(self.__SlotNumber).zfill(2) + "]:TLIMIT?\n"
            Send(self.__Connexion, Command)
            Limit = bool(int(Receive(self.__Connexion)[:-1]))
        else:
            Limit = False
        
        return Limit
    
    
    def SetDiodeTemp(self, DiodeNumber, Temperature, SweepSpeed, SOAComp):
        '''
        !!! FOR TLS CALIBRATION ONLY !!!
        Select the laser diode 'DiodeNumber' (between 1 and 12)
        Set the temperature of the diode. 'Temperature' is a 16-bits binary value
        Set the temperature tuning speed
        Set the SOA compensation value
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Constantes import AP1000_TLS_TMIN, AP1000_TLS_TMAX
        from PyApex.Errors import ApexError

        if not isinstance(DiodeNumber, int):
            self.Off()
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "DiodeNumber")
        
        if not isinstance(Temperature, (float, int)):
            self.Off()
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Temperature")
        
        if DiodeNumber < 1 or DiodeNumber > 12:
            self.Off()
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_VALUE, "DiodeNumber")
        
        if Temperature < AP1000_TLS_TMIN or Temperature > AP1000_TLS_TMAX:
            self.Off()
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_VALUE, "Temperature")
            
        if not self.__Simulation:
            Command = "TLS[" + str(self.__SlotNumber).zfill(2) + "]:SETTARGETPARAM" + str(DiodeNumber) + ";" + str(Temperature) + ";"+ str(SweepSpeed) + ";" + str(SOAComp) + "\n"
            Send(self.__Connexion, Command)
            
        self.__DiodeNumber = DiodeNumber
        self.__DiodeTemp = Temperature
        self.__SweepSpeed = SweepSpeed
        self.__SOAComp = SOAComp
