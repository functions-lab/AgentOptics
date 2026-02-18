

from PyApex.Common import Send, Receive


class DfbLaser():

    def __init__(self, Equipment, SlotNumber, Simulation=False):
        '''
        Constructor of a DFB (Distributed FeedBack Laser Source) equipment.
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
        Return the type of the DFB
        return 0 for a C band Laser
        return 2 for a L band Laser
        return 5 for a O band Laser
        '''
        from PyApex.Constantes import AP1000_ERROR_SLOT_TYPE_NOT_DEFINED
        from PyApex.Constantes import SimuDFB_SlotID, AP1000_DFB_CBAND, AP1000_DFB_LBAND, AP1000_DFB_OBAND
        from PyApex.Errors import ApexError
        import re
        
        if self.__Simulation:
            ID = SimuDFB_SlotID
        else:
            Command = "SLT[" + str(self.__SlotNumber).zfill(2) + "]:IDN?\n"
            Send(self.__Connexion, Command)
            ID = Receive(self.__Connexion)

        if re.findall(str(AP1000_DFB_CBAND), ID.split("/")[1]) != []:
            return 0
        elif re.findall(str(AP1000_DFB_LBAND), ID.split("/")[1]) != []:
            return 2
        elif re.findall(str(AP1000_DFB_OBAND), ID.split("/")[1]) != []:
            return 5
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
        Set output power of the DFB equipment
        Power is expressed in the unit defined by the GetUnit() method
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Constantes import AP1000_DFB_POWMIN, AP1000_DFB_POWMAX
        from PyApex.Errors import ApexError
        
        try:
            Power = float(Power)
        except:
            self.Off()
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Power")
        else:
            Power = self.__ConvertForWriting(Power)
            if Power < AP1000_DFB_POWMIN[self.__Type]:
                print("PyApex Warning. DFB Power is set to its minimum value: " + \
                      str(AP1000_DFB_POWMIN[self.__Type]) + " dBm !")
                Power = AP1000_DFB_POWMIN[self.__Type]
            elif Power > AP1000_DFB_POWMAX[self.__Type]:
                print("PyApex Warning. DFB Power is set to its maximum value: " + \
                      str(AP1000_DFB_POWMAX[self.__Type]) + " dBm !")
                Power = AP1000_DFB_POWMAX[self.__Type]
                
            if not self.__Simulation:
                Command = "DFB[" + str(self.__SlotNumber).zfill(2) + "]:TPDB" + \
                          ("%.1f" % Power) + "\n"
                Send(self.__Connexion, Command)
                
            self.__Power = Power


    def GetPower(self):
        '''
        Get output power of the DFB equipment
        The return power is expressed in the unit defined by the GetUnit() method
        '''
        
        if not self.__Simulation:
            Command = "DFB[" + str(self.__SlotNumber).zfill(2) + "]:TPDB?\n"
            Send(self.__Connexion, Command)
            Power = Receive(self.__Connexion)
            self.__Power = self.__ConvertForReading(float(Power[:-1]))
        
        return self.__Power


    def SetUnit(self, Unit):
        '''
        Set the power unit of the DFB equipment
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
        Get power unit of the DFB equipment
        The return unit is a string
        '''
        return self.__Unit


    def On(self):
        '''
        Activate the output power of DFB equipment
        Waits 0.2 second after switching on
        '''
        from time import sleep
        
        if not self.__Simulation:
            Command = "DFB[" + str(self.__SlotNumber).zfill(2) + "]:L1\n"
            Send(self.__Connexion, Command)
        self.__Status = "ON"
        sleep(0.2)


    def Off(self):
        '''
        Shut down the output power of the DFB equipment
        '''
        if not self.__Simulation:
            Command = "DFB[" + str(self.__SlotNumber).zfill(2) + "]:L0\n"
            Send(self.__Connexion, Command)
        self.__Status = "OFF"


    def GetStatus(self):
        '''
        Return the status ("ON" or "OFF") of the DFB equipment
        '''
        
        if not self.__Simulation:
            Command = "DFB[" + str(self.__SlotNumber).zfill(2) + "]:L?\n"
            Send(self.__Connexion, Command)
            StrStatus = Receive(self.__Connexion)[:-1]
        
            if StrStatus == "1":
                self.__Status = "ON"
            else:
                self.__Status = "OFF"
                
        return self.__Status


    def SetWavelength(self, Wavelength):
        '''
        Set wavelength of the DFB equipment
        Wavelength is expressed in nm
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Constantes import AP1000_DFB_WLMIN, AP1000_DFB_WLMAX
        from PyApex.Errors import ApexError
        
        try:
            Wavelength = float(Wavelength)
        except:
            self.Off()
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Wavelength")
        else:
            if Wavelength < AP1000_DFB_WLMIN[self.__Type]:
                print("PyApex Warning. DFB Wavelength is set to its minimum value: " + \
                      str(AP1000_DFB_WLMIN[self.__Type]) + " nm !")
                Wavelength = AP1000_DFB_WLMIN[self.__Type]
            if Wavelength > AP1000_DFB_WLMAX[self.__Type]:
                print("PyApex Warning. DFB Wavelength is set to its maximum value: " + \
                      str(AP1000_DFB_WLMAX[self.__Type]) + " nm !")
                Wavelength = AP1000_DFB_WLMAX[self.__Type]
            
            if not self.__Simulation:
                Command = "DFB[" + str(self.__SlotNumber).zfill(2) + "]:TWL" + \
                          ("%4.3f" % Wavelength).zfill(8) + "\n"
                Send(self.__Connexion, Command)
            
            self.__Wavelength = Wavelength


    def GetWavelength(self):
        '''
        Get wavelength of the DFB equipment
        The return wavelength is expressed in nm
        '''
        from PyApex.Constantes import AP1000_DFB_WLMIN, AP1000_DFB_WLMAX
        from random import random
        
        if not self.__Simulation:
            Command = "DFB[" + str(self.__SlotNumber).zfill(2) + "]:TWL?\n"
            Send(self.__Connexion, Command)
            self.__Wavelength = float(Receive(self.__Connexion)[:-1])
            
        return self.__Wavelength


    def SetFrequency(self, Frequency):
        '''
        Set frequency of the DFB equipment
        Frequency is expressed in GHz
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Constantes import VACCUM_LIGHT_SPEED, AP1000_DFB_FRMIN, AP1000_DFB_FRMAX
        from PyApex.Errors import ApexError
        
        try:
            Frequency = float(Frequency)
        except:
            self.Off()
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Frequency")
        else:
            if Frequency < AP1000_DFB_FRMIN[self.__Type]:
                print("PyApex Warning. DFB Frequency is set to its minimum value: " + \
                      str(AP1000_DFB_FRMIN[self.__Type]) + " nm !")
                Frequency = AP1000_DFB_FRMIN[self.__Type]
            if Frequency > AP1000_DFB_FRMAX[self.__Type]:
                print("PyApex Warning. DFB Frequency is set to its maximum value: " + \
                      str(AP1000_DFB_FRMAX[self.__Type]) + " nm !")
                Frequency = AP1000_DFB_FRMAX[self.__Type]
            
            self.SetWavelength(VACCUM_LIGHT_SPEED / Frequency)


    def GetFrequency(self):
        '''
        Get frequency of the DFB equipment
        The return frequency is expressed in GHz
        '''
        from PyApex.Constantes import VACCUM_LIGHT_SPEED
            
        Wavelength = self.GetWavelength()
        return VACCUM_LIGHT_SPEED / Wavelength
    
    
