from PyApex.Common import Send, Receive


class ErbiumAmplifier():

    def __init__(self, Equipment, SlotNumber, Simulation=False):
        '''
        Constructor of a EFA (Erbium Amplifier) equipment.
        Equipement is the AP1000 class of the equipement
        SlotNumber is the number of the slot used by the EFA
        Simulation is a boolean to indicate to the program if it has to run in simulation mode or not
        '''
        self.__Connexion = Equipment.Connexion
        self.__Simulation = Simulation
        self.__SlotNumber = SlotNumber
        self.__Status = "OFF"
        self.__Type = self.GetType()
        self.__Unit = "dBm"
        self.__GainUnit = "dB"
        self.__Wavelength = 1550
        self.__Amplification = 0
        self.__IPump = 0
        self.__ValidUnits = ["dbm", "mw"]
        self.__ValidGainUnits = ["db", "%"]
        self.__Mode = 0
        self.__Setpoint = [0.0, 0.0]


    def __str__(self):
        '''
        Return the equipement name and the slot number when the 'print()' function is used
        '''
        return "Erbium Amplifier in slot " + str(self.__SlotNumber)
    
    
    def GetSlotNumber(self):
        '''
        Returns the slot number of the module
        '''
        
        return self.__SlotNumber
    
    
    def GetType(self, type="d"):
        '''
        Return the type of the EFA
        if type = 'd' (default), return a digit :
            - 0 for Booster
            - 1 for In-Line
            - 2 for Pre-Ampli
        if type = 'c', return the option character :
            - 'A' for Booster
            - 'B' for In-Line
            - 'C' for Pre-Ampli
        if type = 's', return a string :
            - "Booster" for Booster
            - "In-Line" for In-Line
            - "Pre-Amplifier" for Pre-Ampli
        '''
        from PyApex.Constantes import AP1000_ERROR_SLOT_TYPE_NOT_DEFINED
        from PyApex.Constantes import SimuEFA_SlotID
        from PyApex.Errors import ApexError
        import re
        
        if self.__Simulation:
            ID = SimuEFA_SlotID
        else:
            Command = "SLT[" + str(self.__SlotNumber).zfill(2) + "]:IDN?\n"
            Send(self.__Connexion, Command)
            ID = Receive(self.__Connexion)
        
        if re.findall("A", ID.split("/")[2].split("-")[2]) != []:
            if type.lower() == "c":
                return "A"
            elif type.lower() == "s":
                return "Booster"
            else:
                return 0
        elif re.findall("B", ID.split("/")[2].split("-")[2]) != []:
            if type.lower() == "c":
                return "B"
            elif type.lower() == "s":
                return "In-Line"
            else:
                return 1
        elif re.findall("C", ID.split("/")[2].split("-")[2]) != []:
            if type.lower() == "c":
                return "C"
            elif type.lower() == "s":
                return "Pre-Amplifier"
            else:
                return 2
        else:
            self.__Connexion.close()
            raise ApexError(AP1000_ERROR_SLOT_TYPE_NOT_DEFINED, self.__SlotNumber)


    def __ConvertForWriting(self, Value, Type = "power"):
        '''
        Internal use only
        Type is the type of value to convert:
        If Type is:
            - "power" or 1, the function converts a power in dBm
            - "gain" or 2, the function converts a gain in dB
        Value is the value to convert
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_VALUE, APXXXX_ERROR_VARIABLE_NOT_DEFINED
        from PyApex.Errors import ApexError
        from math import log10 as log
        
        Type = str(Type).lower()
        if Type == "gain" or Type == 2:
            Type = 2
        else:
            Type = 1
            
        if (self.__Unit.lower() == "dbm" and Type == 1) or (self.__GainUnit.lower() == "db" and Type == 2):
            return Value
        else:
            try:
                log(Value)
            except:
                self.__Connexion.close()
                raise ApexError(APXXXX_ERROR_ARGUMENT_VALUE, "Value")
            else:
                if Type == 2:
                    Value /= 100.0
                return 10.0 * log(Value/10.0)


    def __ConvertForReading(self, Value, Type = "power"):
        '''
        Internal use only
        Type is the type of value to convert:
        If Type is:
            - "power" or 1, the function converts a power in mW if needed
            - "gain" or 2, the function converts a gain in % if needed
        Value is the value to convert
        '''
        from PyApex.Constantes import APXXXX_ERROR_VARIABLE_NOT_DEFINED
        from PyApex.Errors import ApexError
        
        Type = str(Type).lower()
        if Type == "gain" or Type == 2:
            Type = 2
        else:
            Type = 1
        
        if (self.__Unit.lower() == "mw" and Type == 1) or (self.__GainUnit.lower() == "%" and Type == 2):
            Value = 10.0**(Value / 10.0)
            if Type == 2:
                Value *= 100.0
            return Value
        else:
            return Value


    def GetInVoltage(self):
        '''
        Get input binary voltage of the EFA equipment
        The return voltage is expressed in binary unit (V = 2.048 / 4096)
        !!! FOR CALIBRATION ONLY !!!
        '''
        from PyApex.Constantes import SimuEFA_InVoltage
        
        if self.__Simulation:
            InVoltage = SimuEFA_InVoltage
        else:
            Command = "AMP[" + str(self.__SlotNumber).zfill(2) + "]:POWERINVALUE\n"
            Send(self.__Connexion, Command)
            InVoltage = Receive(self.__Connexion)

        return int(InVoltage[:-1])


    def GetOutVoltage(self):
        '''
        Get output binary voltage of the EFA equipment
        The return voltage is expressed in binary unit (V = 2.048 / 4096)
        !!! FOR CALIBRATION ONLY !!!
        '''
        from PyApex.Constantes import SimuEFA_OutVoltage
        
        if self.__Simulation:
            OutVoltage = SimuEFA_OutVoltage
        else:
            Command = "AMP[" + str(self.__SlotNumber).zfill(2) + "]:POWEROUTVALUE\n"
            Send(self.__Connexion, Command)
            OutVoltage = Receive(self.__Connexion)
        
        return int(OutVoltage[:-1])
    
    
    def On(self):
        '''
        Switch on the pump laser of the EFA equipment
        Waits 0.2 second after switching on
        '''
        from time import sleep
        
        if not self.__Simulation:
            Command = "AMP[" + str(self.__SlotNumber).zfill(2) + "]:L1\n"
            Send(self.__Connexion, Command)
        self.__Status = "ON"
        sleep(0.2)

    
    def Off(self):
        '''
        Switch off the pump laser of the EFA equipment
        '''
        if not self.__Simulation:
            Command = "AMP[" + str(self.__SlotNumber).zfill(2) + "]:L0\n"
            Send(self.__Connexion, Command)
        self.__Status = "OFF"
        
        
    def GetStatus(self):
        '''
        Returns the status ("ON" or "OFF") of the TLS equipment
        '''
        return self.__Status
        

    def SetIPump(self, IPump):
        '''
        Set laser pump current of the EFA equipment
        IPump is expressed in mA
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Constantes import AP1000_EFA_IPMAX
        from PyApex.Errors import ApexError
        
        try:
            IPump = float(IPump)
        except:
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "IPump")
        else:
            if IPump > AP1000_EFA_IPMAX[self.__Type]:
                IPump = AP1000_EFA_IPMAX[self.__Type]
            if IPump < 0:
                IPump = 0
            
            if not self.__Simulation:
                Command = "AMP[" + str(self.__SlotNumber).zfill(2) + "]:PUMP" + \
                          ("%.1f" % IPump) + "\n"
                Send(self.__Connexion, Command)
            
            self.__IPump = IPump


    def GetInPower(self):
        '''
        Get input power of the EFA equipment
        The return power is expressed in the unit defined by the GetUnit() method
        '''
        from PyApex.Constantes import SimuEFA_InPower
        
        if self.__Simulation:
            Power = SimuEFA_InPower
        else:
            Command = "AMP[" + str(self.__SlotNumber).zfill(2) + "]:INDB?\n"
            Send(self.__Connexion, Command)
            Power = Receive(self.__Connexion)
        
        return float(Power[:-1])


    def GetOutPower(self):
        '''
        Get output power of the EFA equipment
        The return power is expressed in the unit defined by the GetUnit() method
        '''
        from PyApex.Constantes import SimuEFA_OutPower
        
        if self.__Simulation:
            Power = SimuEFA_OutPower
        else:
            Command = "AMP[" + str(self.__SlotNumber).zfill(2) + "]:OTDB?\n"
            Send(self.__Connexion, Command)
            Power = Receive(self.__Connexion)
        
        return float(Power[:-1])


    def SetUnit(self, Unit):
        '''
        Sets the power unit of the EFA equipment
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
        Gets power unit of the EFA equipment
        The return unit is a string
        '''
        return self.__Unit
        
        
    def SetUnitGain(self, Unit):
        '''
        Sets the gain unit of the EFA equipment
        Unit is a string which could be "dB" for logaritmic or "%" for linear gain
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE
        from PyApex.Errors import ApexError
        
        try:
            Unit = str(Unit)
        except:
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Unit")
        else:
            if Unit.lower() in self.__ValidGainUnits:
                self.__GainUnit = Unit

                
    def GetGainUnit(self):
        '''
        Gets gain unit of the EFA equipment
        The return unit is a string
        '''
        return self.__GainUnit
   

    def SetMode(self, Mode = 0, SetPoint = None):
        '''
        Sets the working mode of the EFA equipment
        Mode can be an integer or a string and represents the working mode
        of the EFA equipment
        If Mode is :
            - "manual" or 0, EFA is running in manual mode (default)
            - "power" or 1, EFA is running in constant output power mode
            - "gain" or 2, EFA is running in constant gain mode
        SetPoint represents the set point of the automatic mode.
        If no set point is given, the previous one is used.
        If Mode = "power", SetPoint is expressed in the unit defined by the GetUnit() method
        If Mode = "gain", SetPoint is expressed in the unit defined by the GetGainUnit() method
        If Mode = "manual", the SetPoint value has no effect
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE
        from PyApex.Errors import ApexError
        
        Command = "AMP[" + str(self.__SlotNumber).zfill(2) + "]:"
        if isinstance(Mode, str):
            if Mode.lower() == "power":
                Command += "AUTOPOWER"
                self.__Mode = 1
            elif Mode.lower() == "gain":
                Command += "AUTOGAIN"
                self.__Mode = 2
            else:
                Command += "MANUAL"
                self.__Mode = 0
        else:
            if Mode == 1:
                Command += "AUTOPOWER"
                self.__Mode = 1
            elif Mode == 2:
                Command += "AUTOGAIN"
                self.__Mode = 2
            else:
                Command += "MANUAL"
                self.__Mode = 0
                
        if SetPoint != None and self.__Mode != 0:
            if not isinstance(SetPoint, (int, float)):
                self.__Connexion.close()
                raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "SetPoint")
            else:
                self.__Setpoint[self.__Mode - 1] = self.__ConvertForWriting(SetPoint, self.__Mode)
        
        if self.__Mode == 1 or self.__Mode == 2:
            Command += ("%.1f" % self.__Setpoint[self.__Mode - 1])
        Command += "\n"
            
        if not self.__Simulation:
            Send(self.__Connexion, Command)
    
    
    def GetMode(self):
        '''
        Gets the working mode of the EFA equipment
        '''
        
        Command = "AMP[" + str(self.__SlotNumber).zfill(2) + "]:MODE?\n"
            
        if not self.__Simulation:
            Send(self.__Connexion, Command)
            Mode = Receive(self.__Connexion)
        
        try:
            Mode = int(Mode)
            self.__Mode = Mode
        except:
            pass
        
        if self.__Mode == -1:
            return "off"
        elif self.__Mode == 0:
            return "manual"
        elif self.__Mode == 1:
            return "constant power"
        elif self.__Mode == 2:
            return "constant gain"
        else:
            return "unknown mode"
    
    
    def SetPower(self, Power):
        '''
        Sets the power of the constant output power mode and sets the EFA equipment
        in the constant output power mode
        SetPoint is a value expressed in the unit defined by the GetUnit() method 
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE
        from PyApex.Errors import ApexError
        
        try:
            Power = float(Power)
        except:
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Power")
        else:
            self.__Setpoint[0] = self.__ConvertForWriting(Power, "power")
            
            
            Command = "AMP[" + str(self.__SlotNumber).zfill(2) + "]:"
            Command += "AUTOPOWER" + ("%.1f" % self.__Setpoint[0]) + "\n"
            
            if not self.__Simulation:
                Send(self.__Connexion, Command)
    
    
    def GetPower(self):
        '''
        Gets the set point power of the constant output power mode
        The value is expressed in the unit defined by the GetUnit() method
        
        '''
        Command = "AMP[" + str(self.__SlotNumber).zfill(2) + "]:AUTOPOWER?\n"
            
        if not self.__Simulation:
            Send(self.__Connexion, Command)
            Power = Receive(self.__Connexion)
            
            if "no set point" in str(Power).lower():
                return "no set point"
        
        try:
            Power = float(Power)
            self.__Setpoint[0] = Power
        except:
            pass
        
        return self.__ConvertForReading(self.__Setpoint[0], "power")
    
    
    def SetGain(self, Gain):
        '''
        Sets the gain of the constant gain mode and sets the EFA equipment
        in the constant gain mode
        SetPoint is a value expressed in the unit defined by the GetGainUnit() method 
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE
        from PyApex.Errors import ApexError
        
        try:
            Gain = float(Gain)
        except:
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Gain")
        else:
            self.__Setpoint[1] = self.__ConvertForWriting(Gain, "gain")
            
            
            Command = "AMP[" + str(self.__SlotNumber).zfill(2) + "]:"
            Command += "AUTOGAIN" + ("%.1f" % self.__Setpoint[1]) + "\n"
            
            if not self.__Simulation:
                Send(self.__Connexion, Command)
    
    
    def GetGain(self):
        '''
        Gets the set point gain of the constant gain mode
        The value is expressed in the unit defined by the GetGainUnit() method
        
        '''
        Command = "AMP[" + str(self.__SlotNumber).zfill(2) + "]:AUTOGAIN?\n"
            
        if not self.__Simulation:
            Send(self.__Connexion, Command)
            Gain = Receive(self.__Connexion)
            
            if "no set point" in str(Gain).lower():
                return "no set point"
        
        try:
            Gain = float(Gain)
            self.__Setpoint[1] = Gain
        except:
            pass
        
        return self.__ConvertForReading(self.__Setpoint[1], "gain")

