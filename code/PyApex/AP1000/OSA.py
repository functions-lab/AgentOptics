

from PyApex.Common import Send, Receive, ReceiveUntilChar


class OSA():

    def __init__(self, Equipment, SlotNumber=1, Simulation=False):
        '''
        Constructor of an OSA (Optical Spectrum Analyzer) equipment.
        The OSA is based on 2 AP1000 equipments:
            - 1 Polarimeter or 1 Power-Meter
            - 1 Single Filter or Dual Filters
        Equipement is the AP1000 class of the equipement
        Simulation is a boolean to indicate to the program if it has to run in simulation mode or not
        '''
        self.__Connexion = Equipment.Connexion
        self.__Simulation = Simulation
        self.__PowSlotNumber = SlotNumber
        self.__FilSlotNumber = -1
        self.__Polarimeter = False
        self.__YUnit = "dBm"
        self.__XUnit = "nm"
        self.__StartWavelength = 1530
        self.__StopWavelength = 1560
        self.__NbPoints = 400
        self.__ValidYUnits = ["dbm", "mw"]
        self.__ValidXUnits = ["nm", "ghz"]


    def __str__(self):
        '''
        Return the equipement name and the slot number when the 'print()' function is used
        '''
        String = ""
        if self.__Polarimeter:
            String += "Polarimeter "
        String += "O.S.A. based on slots " + str(self.__PowSlotNumber) + " and " + str(self.__FilSlotNumber)
          
        return String
    
    
    def SetPowerMeterSlotNumber(self, Slot):
        '''
        Sets the slot number of the Polarimeter or Power-Meter used for the O.S.A. module
        Slot is an integer representing the slot number
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE
        from PyApex.Errors import ApexError
        
        try:
            Slot = int(Slot)
        except:
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Slot")
        else:
            if not self.__Simulation:
                Command = "OSA[" + str(self.__PowSlotNumber).zfill(2) + "]:POWER" + \
                          str(Slot) + "\n"
                Send(self.__Connexion, Command)
            
            self.__PowSlotNumber = Slot
    
    
    def GetPowerMeterSlotNumber(self):
        '''
        Returns the slot number of the Polarimeter or Power-Meter module
        '''
        
        if not self.__Simulation:
            Command = "OSA[" + str(self.__PowSlotNumber).zfill(2) + "]:POWER?\n"
            Send(self.__Connexion, Command)
            self.__PowSlotNumber = int(Receive(self.__Connexion)[:-1])
        
        return self.__PowSlotNumber
    
    
    def SetFilterSlotNumber(self, Slot):
        '''
        Sets the slot number of the Filter used for the O.S.A. module
        Slot is an integer representing the slot number
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE
        from PyApex.Errors import ApexError
        
        try:
            Slot = int(Slot)
        except:
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Slot")
        else:
            if not self.__Simulation:
                Command = "OSA[" + str(self.__PowSlotNumber).zfill(2) + "]:FILTER" + \
                          str(Slot) + "\n"
                Send(self.__Connexion, Command)
            
            self.__FilSlotNumber = Slot
    
    
    def GetFilterSlotNumber(self):
        '''
        Returns the slot number of the Filter module
        '''
        
        if not self.__Simulation:
            Command = "OSA[" + str(self.__PowSlotNumber).zfill(2) + "]:FILTER?\n"
            Send(self.__Connexion, Command)
            self.__FilSlotNumber = int(Receive(self.__Connexion)[:-1])
        
        return self.__FilSlotNumber
    
    
    def SetXUnit(self, Unit):
        '''
        Set the x-axis unit of the OSA equipment
        Unit is a string which could be "nm" for wavelengths or "GHz" for Frequencies
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
                self.__XUnit = Unit


    def GetXUnit(self):
        '''
        Get the x-axis unit of the OSA equipment
        The return unit is a string
        '''
        return self.__XUnit
    
    
    def SetYUnit(self, Unit):
        '''
        Set the y-axis unit of the OSA equipment
        Unit is a string which could be "dBm" for logarithmic or "mW" for linear
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
                self.__YUnit = Unit
    
    
    def GetYUnit(self):
        '''
        Get the y-axis unit of the OSA equipment
        The return unit is a string
        '''
        return self.__YUnit
    
    
    def SetStartWavelength(self, Wavelength):
        '''
        Set the start wavelength of the OSA equipment
        Wavelength is expressed in nm
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE
        from PyApex.Errors import ApexError
        
        try:
            Wavelength = float(Wavelength)
        except:
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Wavelength")
        else:          
            if not self.__Simulation:
                Command = "OSA[" + str(self.__PowSlotNumber).zfill(2) + \
                          "]:STARTWL" + ("%4.3f" % Wavelength).zfill(8) + "\n"
                Send(self.__Connexion, Command)
            
            self.__StartWavelength = Wavelength
    
    
    def GetStartWavelength(self):
        '''
        Get the start wavelength of the OSA equipment
        The return wavelength is expressed in nm
        '''
        
        if not self.__Simulation:
            Command = "OSA[" + str(self.__PowSlotNumber).zfill(2) + "]:STARTWL?\n"
            Send(self.__Connexion, Command)
            self.__StartWavelength = float(Receive(self.__Connexion)[:-1])
        
        return self.__StartWavelength
    
    
    def SetStartFrequency(self, Frequency):
        '''
        Set the start frequency of the OSA equipment
        Frequency is expressed in GHz
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE
        from PyApex.Constantes import VACCUM_LIGHT_SPEED
        from PyApex.Errors import ApexError
        
        try:
            Frequency = float(Frequency)
        except:
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Frequency")
        else:              
            if Frequency > 0:
                self.SetStopWavelength(VACCUM_LIGHT_SPEED / Frequency)
    
    
    def GetStartFrequency(self):
        '''
        Get the start frequency of the POL equipment
        Frequency is expressed in GHz
        '''
        
        try:
            Wavelength = self.GetStopWavelength()
            return float(VACCUM_LIGHT_SPEED / Wavelength)
        except:
            return 0.0
    
    
    def SetStopWavelength(self, Wavelength):
        '''
        Set the stop wavelength of the OSA equipment
        Wavelength is expressed in nm
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE
        from PyApex.Errors import ApexError
        
        try:
            Wavelength = float(Wavelength)
        except:
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Wavelength")
        else:          
            if not self.__Simulation:
                Command = "OSA[" + str(self.__PowSlotNumber).zfill(2) + \
                          "]:STOPWL" + ("%4.3f" % Wavelength).zfill(8) + "\n"
                Send(self.__Connexion, Command)
            
            self.__StopWavelength = Wavelength
    
    
    def GetStopWavelength(self):
        '''
        Get the stop wavelength of the OSA equipment
        The return wavelength is expressed in nm
        '''
        
        if not self.__Simulation:
            Command = "OSA[" + str(self.__PowSlotNumber).zfill(2) + "]:STOPWL?\n"
            Send(self.__Connexion, Command)
            self.__StopWavelength = float(Receive(self.__Connexion)[:-1])
        
        return self.__StopWavelength
    
    
    def SetStopFrequency(self, Frequency):
        '''
        Set the stop frequency of the OSA equipment
        Frequency is expressed in GHz
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE
        from PyApex.Constantes import VACCUM_LIGHT_SPEED
        from PyApex.Errors import ApexError
        
        try:
            Frequency = float(Frequency)
        except:
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Frequency")
        else:              
            if Frequency > 0:
                self.SetStartWavelength(VACCUM_LIGHT_SPEED / Frequency)
    
    
    def GetStopFrequency(self):
        '''
        Get the stop frequency of the POL equipment
        Frequency is expressed in GHz
        '''
        
        try:
            Wavelength = self.GetStartWavelength()
            return float(VACCUM_LIGHT_SPEED / Wavelength)
        except:
            return 0.0
    
    
    def SetNbPoints(self, NbPoints):
        '''
        Set the number of points of the OSA equipment
        NbPoints is an integer
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE
        from PyApex.Errors import ApexError
        
        try:
            NbPoints = int(NbPoints)
        except:
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "NbPoints")
        else:
            if not self.__Simulation:
                Command = "OSA[" + str(self.__PowSlotNumber).zfill(2) + "]:NBPTS" + \
                          str(NbPoints) + "\n"
                Send(self.__Connexion, Command)
            
            self.__NbPoints = NbPoints
    
    
    def GetNbPoints(self):
        '''
        Returns the number of points of the OSA equipment
        '''
        
        if not self.__Simulation:
            Command = "OSA[" + str(self.__PowSlotNumber).zfill(2) + "]:NBPTS?\n"
            Send(self.__Connexion, Command)
            self.__NbPoints = int(Receive(self.__Connexion)[:-1])
        
        return self.__NbPoints
    
    
    def Run(self, Type = "single"):
        '''
        Run a single or repeat sweep in the OSA module
        Type is a string or an integer:
            - 1 or "single" : Run a single sweep (default)
            - 2 or "repeat" : Run a repeat sweep
        '''
        if isinstance(Type, str):
            if Type.lower() == "repeat":
                Type = 2                    
            else:
                Type = 1
        else:
            if Type not in [1, 2]:
                Type = 1
        
        if not self.__Simulation:
            Command = "OSA[" + str(self.__PowSlotNumber).zfill(2) + "]:SWEEP" + \
                      str(Type) + "\n"
            Send(self.__Connexion, Command)
    
    
    def Stop(self):
        '''
        Stop a sweep in the OSA module
        '''
        if not self.__Simulation:
            Command = "OSA[" + str(self.__PowSlotNumber).zfill(2) + "]:SWEEP0\n"
            Send(self.__Connexion, Command)
    
    
    def IsRunning(self):
        '''
        Returns the sweeping status of the OSA module
        If the OSA module is sweeping, returns True, False otherwise
        '''
        
        if not self.__Simulation:
            Command = "OSA[" + str(self.__PowSlotNumber).zfill(2) + "]:SWEEP?\n"
            Send(self.__Connexion, Command)
            IsRunning = int(Receive(self.__Connexion)[:-1])
        
        if IsRunning == 1:
            return True
        else:
            return False
    
    
    def GetData(self, DataX = "nm", DataY = "log"):
        '''
        Get the x or y data of the OSA module
        returns a 2D list [Y-axis Data, X-Axis Data]
        DataX is a string and can be:
            - "nm" for wavelength (default)
            - "GHz" for frequency
        DataY is a string and can be:
            - "log" for Logarithmic power in dBm (default)
            - "lin" for linear power in mW
            - "S1" for the stokes parameter S1
            - "S2" for the stokes parameter S2
            - "S3" for the stokes parameter S3
            - "DOP" for the degree of polarization DOP
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Constantes import APXXXX_ERROR_VARIABLE_NOT_DEFINED, Celerity
        from PyApex.Errors import ApexError
        from random import random
        
        try:
            DataX = str(DataX)
        except:
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "DataX")
        
        try:
            DataY = str(DataY)
        except:
            self.__Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "DataY")
        
        if DataX.lower() == "ghz":
            DataX = 1
        else:
            DataX = 0
        
        if DataY.lower() == "lin":
            DataY = 4
        elif DataY.lower() == "s1":
            DataY = 1
        elif DataY.lower() == "s2":
            DataY = 2
        elif DataY.lower() == "s3":
            DataY = 3
        elif DataY.lower() == "dop":
            DataY = 5
        else:
            DataY = 0
        
        if self.__Simulation:
            XString = ""
            YString = ""
            
            if DataX == 1:
                DeltaX = ((Celerity / self.__StartWavelength) - (Celerity / self.__StopWavelength)) / (self.__NbPoints)
            else:
                DeltaX = (self.__StopWavelength - self.__StartWavelength) / (self.__NbPoints)
            for i in range(self.__NbPoints):
                if DataX == 1:
                    XString += str((Celerity / self.__StopWavelength) + (i * DeltaX))
                else:
                    XString += str(self.__StartWavelength + (i * DeltaX))
                if i < self.__NbPoints - 1:
                    XString += ","
                    
            for i in range(self.__NbPoints):
                if DataY <= 1:
                    Value = random() * 70.0 - 60.0
                    if DataY == 1:
                        Value = 10.0**(Value / 10.0)
                elif DataY <= 4:
                    Value = random() * 2.0 - 1.0
                else:
                    Value = random()
                YString += "%.3f" %Value
                if i < self.__NbPoints - 1:
                    YString += ","
        else:
            Command = "OSA[" + str(self.__PowSlotNumber).zfill(2) + "]:DATAX" + str(DataX) + "\n"
            Send(self.__Connexion, Command)
            XString = ReceiveUntilChar(self.__Connexion)[:-1]
            
            Command = "OSA[" + str(self.__PowSlotNumber).zfill(2) + "]:DATAY" + str(DataY) + "\n"
            Send(self.__Connexion, Command)
            YString = ReceiveUntilChar(self.__Connexion)[:-1]
        
        XData = []
        YData = []
        for x in XString.split(','):
            try:
                XData.append(float(x))
            except:
                pass
        for y in YString.split(','):
            try:
                YData.append(float(y))
            except:
                pass
        
        return [YData, XData]
    
    
