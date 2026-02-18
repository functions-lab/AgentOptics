from PyApex.Common import Send, Receive


class Attenuator():

    def __init__(self, Equipment, SlotNumber=1, Simulation=False):
        '''
        Constructor of a ATT (Attenuator) equipment.
        Equipement is the AP1000 class of the equipement
        SlotNumber is the number of the slot used by the ATT
        Simulation is a boolean to indicate to the program if it has to run in simulation mode or not
        '''
        self.__Connexion = Equipment.Connexion
        self.__Simulation = Simulation
        self.__SlotNumber = SlotNumber
        self.__Unit = "dB"
        self.__Attenuation = 0
        self.__ValidUnits = ["db", "%"]


    def __str__(self):
        '''
        Return the equipement name and the slot number when the 'print()' function is used
        '''
        return "Optical Attenuator in slot " + str(self.__SlotNumber)


    def __ConvertForWriting(self, Attenuation):
        '''
        Internal use only
        Convert a dB attenuation in % or a % attenuation in dB
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_VALUE, APXXXX_ERROR_VARIABLE_NOT_DEFINED
        from PyApex.Errors import ApexError
        from math import log10 as log
        
        if self.__Unit.lower() == "db":
            return Attenuation
        elif self.__Unit.lower() == "%":
            try:
                log(Attenuation)
            except:
                self.__Connexion.close()
                raise ApexError(APXXXX_ERROR_ARGUMENT_VALUE, "Attenuation")
            else:
                return -10 * log(Attenuation/100)
        else:
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_VARIABLE_NOT_DEFINED, "self.__Unit")


    def __ConvertForReading(self, Attenuation):
        '''
        Internal use only
        Convert a dB attenuation in % or a % attenuation in dB
        '''
        from PyApex.Constantes import APXXXX_ERROR_VARIABLE_NOT_DEFINED
        from PyApex.Errors import ApexError
        
        if self.__Unit.lower() == "%":
            return 10**(- Attenuation / 10)
        elif self.__Unit.lower() == "db":
            return Attenuation
        else:
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_VARIABLE_NOT_DEFINED, "self.__Unit")
            
            
    def GetSlotNumber(self):
        '''
        Returns the slot number of the module
        '''
        
        return self.__SlotNumber
    
    
    def SetAttenuation(self, Attenuation, ChNumber=1):
        '''
        Set attenuation power of the ATT equipment
        Attenuation is expressed in the unit defined by the GetUnit() method
        ChNumber is the channel number : 1 (default) or 2
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Constantes import AP1000_ATT_ATTMIN, AP1000_ATT_ATTMAX, AP1000_ATT_CHNUMBER
        from PyApex.Errors import ApexError
        
        try:
            Attenuation = float(Attenuation)
        except:
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Attenuation")
        else:
            try:
                ChNumber = int(ChNumber)
            except:
                self.__Connexion.close()
                raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "ChNumber")
            else:
                
                Attenuation = self.__ConvertForWriting(Attenuation)
                if Attenuation < AP1000_ATT_ATTMIN:
                    Attenuation = AP1000_ATT_ATTMIN
                if Attenuation > AP1000_ATT_ATTMAX:
                    Attenuation = AP1000_ATT_ATTMAX
                if ChNumber > AP1000_ATT_CHNUMBER:
                    ChNumber = AP1000_ATT_CHNUMBER
                if ChNumber < 1:
                    ChNumber = 1
                
                if not self.__Simulation:
                    Command = "ATT[" + str(self.__SlotNumber).zfill(2) + "]:DB[" + \
                              str(ChNumber-1) +"]" + ("%.1f" % Attenuation) + "\n"
                    Send(self.__Connexion, Command)
                
                self.__Attenuation = Attenuation


    def GetAttenuation(self, ChNumber=1):
        '''
        Get attenuation of the ATT equipment
        The return attenuation is expressed in the unit defined by the GetUnit() method
        ChNumber is the channel number : 1 (default) or 2
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Constantes import AP1000_ATT_CHNUMBER, SimuATT_Attenuation
        from PyApex.Errors import ApexError
        
        try:
            ChNumber = int(ChNumber)
        except:
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "ChNumber")
        else:
            
            if ChNumber > AP1000_ATT_CHNUMBER:
                ChNumber = AP1000_ATT_CHNUMBER
            if ChNumber < 1:
                ChNumber = 1
            
            if not self.__Simulation:
                Command = "ATT[" + str(self.__SlotNumber).zfill(2) + "]:DB[" + \
                          str(ChNumber-1) + "]?\n"
                Send(self.__Connexion, Command)
                self.__Attenuation = self.__ConvertForReading(float(Receive(self.__Connexion)[:-1]))
            
            return self.__Attenuation


    def SetUnit(self, Unit):
        '''
        Set the attenuation unit of the ATT equipment
        Unit is a string which could be "dB" for logaritmic or "%" for linear power
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
        Get the attenuation unit of the ATT equipment
        Unit is a string which could be "dB" for logaritmic or "%" for linear power
        '''
        return self.__Unit
