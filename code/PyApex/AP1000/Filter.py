from PyApex.Common import Send, Receive


class Filter():

    def __init__(self, Equipment, SlotNumber=1, Simulation=False):
        '''
        Constructor of a FIL (Filter) equipment.
        Equipement is the AP1000 class of the equipement
        SlotNumber is the number of the slot used by the FIL
        Simulation is a boolean to indicate to the program if it has to run in simulation mode or not
        '''
        
        self.__Connexion = Equipment.Connexion
        self.__Simulation = Simulation
        self.__SlotNumber = SlotNumber
        self.__Unit = "nm"
        self.__Wavelength = 1550.0
        self.__ValidUnits = ["nm", "ghz"]


    def __str__(self):
        '''
        Return the equipement name and the slot number when the 'print()' function is used
        '''
        return "Optical Filter in slot " + str(self.__SlotNumber)
    
    
    def GetSlotNumber(self):
        '''
        Returns the slot number of the module
        '''
        
        return self.__SlotNumber
    
    
    def __Convert(self, Value):
        '''
        Internal use only
        Convert a wavelength (nm) in frequency (GHz) or a frequency (GHz) in wavelength (nm)
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_VALUE, APXXXX_ERROR_VARIABLE_NOT_DEFINED
        from PyApex.Constantes import Celerity
        from PyApex.Errors import ApexError
        
        return Celerity / Value


    def SetWavelength(self, Wavelength):
        '''
        Set Wavelength of the FIL equipment
        Wavelength is expressed in nm
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Constantes import AP1000_FIL_WLMIN, AP1000_FIL_WLMAX
        from PyApex.Errors import ApexError
        
        if not isinstance(Wavelength, (int, float)):
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Wavelength")
            sys.exit()
        
        [WavelengthMin, WavelengthMax] = self.GetWavelngthLimits()
        if(Wavelength < WavelengthMin or Wavelength > WavelengthMax):
            raise ApexError(APXXXX_ERROR_ARGUMENT_VALUE, "Wavelength")
            sys.exit()
            
        if not self.__Simulation:
            Command = "FLT[" + str(self.__SlotNumber).zfill(2) + "]:TWL" + \
                      ("%.2f" % Wavelength) + "\n"
            Send(self.__Connexion, Command)
        
        self.__Wavelength = Wavelength


    def GetWavelength(self):
        '''
        Get Wavelength of the FIL equipment
        Returns the wavelength in nm
        '''
                           
        if not self.__Simulation:
            Command = "FLT[" + str(self.__SlotNumber).zfill(2) + "]:TWL?\n"
            Send(self.__Connexion, Command)
            self.__Wavelength = float(Receive(self.__Connexion)[:-1])
        
        return self.__Wavelength
        

    def SetFrequency(self, Frequency):
        '''
        Set Frequency of the FIL equipment
        Frequency is expressed in GHz
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Errors import ApexError
        
        if not isinstance(Frequency, (int, float)):
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Frequency")
            sys.exit()
        
        [FrequencyMin, FrequencyMax] = self.GetFrequencyLimits()
        if(Frequency < FrequencyMin or Frequency > FrequencyMax):
            raise ApexError(APXXXX_ERROR_ARGUMENT_VALUE, "Frequency")
            sys.exit()
            
        if not self.__Simulation:
            Command = "FLT[" + str(self.__SlotNumber).zfill(2) + "]:TFR" + \
                      ("%.2f" % Frequency) + "\n"
            Send(self.__Connexion, Command)
        
        
        self.__Wavelength = self.__Convert(Frequency)


    def GetFrequency(self):
        '''
        Get Frequency of the FIL equipment
        Returns the Frequency in GHz
        '''
        
        if not self.__Simulation:
            Command = "FLT[" + str(self.__SlotNumber).zfill(2) + "]:TFR?\n"
            Send(self.__Connexion, Command)
            Frequency = float(Receive(self.__Connexion)[:-1])
            self.__Wavelength = self.__Convert(Frequency)
        
        return Frequency
    
    
    def GetWavelngthLimits(self):
        '''
        Get the wavelength limits (min and max) of the FIL equipment
        Returns the limits in nm in a list [min, max]
        '''
        from PyApex.Constantes import AP1000_FIL_WLMIN, AP1000_FIL_WLMAX
        from PyApex.Errors import ApexError
        
        if self.__Simulation:
            WavelengthMin = AP1000_FIL_WLMIN
            WavelengthMax = AP1000_FIL_WLMAX
        else:
            Command = "FLT[" + str(self.__SlotNumber).zfill(2) + "]:WLMIN?\n"
            Send(self.__Connexion, Command)
            WavelengthMin = float(Receive(self.__Connexion)[:-1])
            Command = "FLT[" + str(self.__SlotNumber).zfill(2) + "]:WLMAX?\n"
            Send(self.__Connexion, Command)
            WavelengthMax = float(Receive(self.__Connexion)[:-1])
        
        return [WavelengthMin, WavelengthMax]
        
        
    def GetFrequencyLimits(self):
        '''
        Get the frequency limits (min and max) of the FIL equipment
        Returns the limits in GHz in a list [min, max]
        '''
        from PyApex.Constantes import AP1000_FIL_FRMIN, AP1000_FIL_FRMAX
        from PyApex.Errors import ApexError
        
        if self.__Simulation:
            FrequencyMin = AP1000_FIL_FRMIN
            FrequencyMax = AP1000_FIL_FRMAX
        else:
            Command = "FLT[" + str(self.__SlotNumber).zfill(2) + "]:FRMIN?\n"
            Send(self.__Connexion, Command)
            FrequencyMin = float(Receive(self.__Connexion)[:-1])
            Command = "FLT[" + str(self.__SlotNumber).zfill(2) + "]:FRMAX?\n"
            Send(self.__Connexion, Command)
            FrequencyMax = float(Receive(self.__Connexion)[:-1])
        
        return [FrequencyMin, FrequencyMax]
        
        
    def SetStartWavelength(self, Wavelength):
        '''
        Set the start wavelength for a sweep
        Wavelength is expressed in nm
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Errors import ApexError
        
        if not isinstance(Wavelength, (int, float)):
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Wavelength")
            sys.exit()
        
        [WavelengthMin, WavelengthMax] = self.GetWavelngthLimits()
        if(Wavelength < WavelengthMin or Wavelength > WavelengthMax):
            raise ApexError(APXXXX_ERROR_ARGUMENT_VALUE, "Wavelength")
            sys.exit()
            
        if not self.__Simulation:
            Command = "FLT[" + str(self.__SlotNumber).zfill(2) + "]:TSTAWL" + \
                      ("%.2f" % Wavelength) + "\n"
            Send(self.__Connexion, Command)
    
    
    def GetStartWavelength(self):
        '''
        Get the start wavelength for a sweep
        Returns the wavelength in nm
        '''
        from PyApex.Constantes import AP1000_FIL_WLMIN
        
        if self.__Simulation:
            Wavelength = AP1000_FIL_WLMIN
        else:
            Command = "FLT[" + str(self.__SlotNumber).zfill(2) + "]:TSTAWL?\n"
            Send(self.__Connexion, Command)
            Wavelength = Receive(self.__Connexion)
        
        return float(Wavelength[:-1])
    
    
    def SetStopWavelength(self, Wavelength):
        '''
        Set the stop wavelength for a sweep
        Wavelength is expressed in nm
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Errors import ApexError
        
        if not isinstance(Wavelength, (int, float)):
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Wavelength")
            sys.exit()
        
        [WavelengthMin, WavelengthMax] = self.GetWavelngthLimits()
        if(Wavelength < WavelengthMin or Wavelength > WavelengthMax):
            raise ApexError(APXXXX_ERROR_ARGUMENT_VALUE, "Wavelength")
            sys.exit()
            
        if not self.__Simulation:
            Command = "FLT[" + str(self.__SlotNumber).zfill(2) + "]:TSTPWL" + \
                      ("%.2f" % Wavelength) + "\n"
            Send(self.__Connexion, Command)

    
    def GetStopWavelength(self):
        '''
        Get the stop wavelength for a sweep
        Returns the wavelength in nm
        '''
        from PyApex.Constantes import AP1000_FIL_WLMAX
        
        if self.__Simulation:
            Wavelength = AP1000_FIL_WLMAX
        else:
            Command = "FLT[" + str(self.__SlotNumber).zfill(2) + "]:TSTPWL?\n"
            Send(self.__Connexion, Command)
            Wavelength = Receive(self.__Connexion)
        
        return float(Wavelength[:-1])
    
    
    def SetSweepSpeed(self, SweepSpeed):
        '''
        Set the speed for a sweep
        SweepSpeed is expressed in nm/s
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Constantes import AP1000_FIL_SPEEDMIN, AP1000_FIL_SPEEDMAX
        from PyApex.Errors import ApexError
        
        if not isinstance(SweepSpeed, (int, float)):
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "SweepSpeed")
            sys.exit()
        
        if(SweepSpeed < AP1000_FIL_SPEEDMIN or SweepSpeed > AP1000_FIL_SPEEDMAX):
            raise ApexError(APXXXX_ERROR_ARGUMENT_VALUE, "SweepSpeed")
            sys.exit()
            
        if not self.__Simulation:
            Command = "FLT[" + str(self.__SlotNumber).zfill(2) + "]:TSWES" + \
                      ("%.2f" % SweepSpeed) + "\n"
            Send(self.__Connexion, Command)

    
    def GetSweepSpeed(self):
        '''
        Get the speed for a sweep
        Returns the speed in nm/s
        '''
        from PyApex.Constantes import AP1000_FIL_SPEEDMIN
        
        if self.__Simulation:
            Speed = AP1000_FIL_SPEEDMIN
        else:
            Command = "FLT[" + str(self.__SlotNumber).zfill(2) + "]:TSWES?\n"
            Send(self.__Connexion, Command)
            Speed = Receive(self.__Connexion)
        
        return float(Speed[:-1])
    
    
    def RunSweep(self, Type="single"):
        '''
        Run a sweep.
        If Type is
            - "single" or 0, a single sweep is running (default)
            - "repeat" or 1, a repeat sweep is running
        '''
        
        Command = "FLT[" + str(self.__SlotNumber).zfill(2) + "]:"
        
        if not self.__Simulation:
            if isinstance(Type, str):
                if Type.lower() == "repeat":
                    Command += "TRET\n"                    
                else:
                    Command += "TSGL\n"
            else:
                if Type == 1:
                    Command += "TRET\n"
                else:
                    Command += "TSGL\n"
            
            Send(self.__Connexion, Command)
    
    
    def StopSweep(self):
        '''
        Stop a sweep
        '''
        
        if not self.__Simulation:
            Command = "FLT[" + str(self.__SlotNumber).zfill(2) + "]:TSTO\n"
            Send(self.__Connexion, Command)
    
    
    def SetUnit(self, Unit):
        '''
        Set the unit of the FIL equipment
        Unit is a string which could be "nm" for wavelength or "GHz" for frequency
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE
        from PyApex.Errors import ApexError
        
        if not isinstance(Unit, str):
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Unit")
            sys.exit()
        
        if Unit.lower() in self.__ValidUnits:
            self.__Unit = Unit


    def GetUnit(self):
        '''
        Get the unit of the FIL equipment
        Unit is a string which could be "nm" for wavelength or "GHz" for frequency
        '''
        return self.__Unit
    
    
    def __SetVoltage(self, Voltage, Filter=1):
        '''
        Calibration use only
        Set Voltage of the FIL equipment (DAC binary value)
        Voltage is expressed in binary value (between 0 and 65535)
        Filter is the number of the filter 1 (default) or 2
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Errors import ApexError
        
        if not isinstance(Voltage, (int, float)):
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Voltage")
            sys.exit()
        
        if not isinstance(Filter, (int)):
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Filter")
            sys.exit()
        
        if(Voltage < 0 or Voltage > 65535):
            raise ApexError(APXXXX_ERROR_ARGUMENT_VALUE, "Voltage")
            sys.exit()
        
        if(Filter not in [1, 2]):
            raise ApexError(APXXXX_ERROR_ARGUMENT_VALUE, "Filter")
            sys.exit()
            
        if not self.__Simulation:
            Command = "FLT[" + str(self.__SlotNumber).zfill(2) + "]:SETV" + \
                      str(Filter) + str(Voltage) + "\n"
            Send(self.__Connexion, Command)
    
    
    def __SetSwitch(self, Value, Filter=1):
        '''
        Calibration use only
        Set connection of the switch in the FIL equipment
        Value is a binary value (True or False)
        Filter is the number of the filter 1 (default) or 2
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Errors import ApexError
        
        if not isinstance(Value, bool):
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Value")
            sys.exit()
        
        if not isinstance(Filter, (int)):
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Filter")
            sys.exit()
        
        if(Filter not in [1, 2]):
            raise ApexError(APXXXX_ERROR_ARGUMENT_VALUE, "Filter")
            sys.exit()
            
        if not self.__Simulation:
            Command = "FLT[" + str(self.__SlotNumber).zfill(2) + "]:SWITCH" + \
                      str(Filter) + str(int(Value)) + "\n"
            Send(self.__Connexion, Command)
        
