#! /usr/bin/python3
# -*- coding: <utf-8> -*-

import socket
from PyApex.Common import Send, Receive

class AP1000():
    '''
    DESCRIPTION
        Elementary functions to communicate with Apex AP1000 equipment
        this version can control :
            - AP331X (Power Meter Module)
            - AP3344 (Optical Switch Module)
            - AP335X (Tunable Laser Module)
            - AP336X (Attenuator Module)
            - AP337X (Amplifier Module)
            - AP338X (Optical Filter Module)
            - AP339X (DFB Laser Module)
    
    VERSION
        1.1
    
    CONTRIBUTORS
        Maxime FONTAINE
        Khalil KECHAOU
        Vincent PERNET
    '''

    def __init__(self, IPaddress, PortNumber=5900, Simulation=False):
        '''
        Constructor of AP1000 equipment.
        IPaddress is the IP address (string) of the equipment.
        PortNumber is by default 5900. It's an integer
        Simulation is a boolean to indicate to the program if it has to run in simulation mode or not
        '''
        self.__IPAddress = IPaddress
        self.__PortNumber = PortNumber
        self.__Simulation = Simulation
        self.__Connected = False
        self.Open()
        

    def Open(self):
        '''
        Open connexion to AP1000 equipment.
        This method is called by the constructor of AP1000 class
        '''
        self.Connexion = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
        self.Connexion.settimeout(10.0)
        
        if self.__Simulation:
            self.__Connected = True
            print("Connected successfully to the equipment")
        else:
            try:
                self.Connexion.connect((self.__IPAddress, self.__PortNumber))
                self.__Connected = True
                print("Connected successfully to the equipment")
            except:
                print("Cannot connect to the equipment")


    def Close(self):
        '''
        Close connexion to AP1000 equipment
        '''
        from PyApex.Constantes import APXXXX_ERROR_COMMUNICATION
        from PyApex.Errors import ApexError
        
        if self.__Simulation:
            self.__Connected = False
        else:
            try:
                self.Connexion.close()
                self.__Connected = False
            except:
                raise ApexError(APXXXX_ERROR_COMMUNICATION, self.Connexion.getsockname()[0])


    def IsConnected(self):
        '''
        Returns the status of the connection. True if an equipment
        is connected, False otherwise.
        '''
        return self.__Connected


    def SetTimeOut(self, TimeOut):
        '''
        Set the timeout of the Ethernet connection
        TimeOut is expressed in seconds
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE
        
        if not isinstance(TimeOut, (int, float)):
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "TimeOut")
        
        self.Connexion.settimeout(TimeOut)
    
    
    def GetTimeOut(self):
        '''
        Get the timeout of the Ethernet connection
        The returned value is expressed in seconds
        '''
        
        TimeOut = self.Connexion.gettimeout()
        return TimeOut


    def GetID(self):
        '''
        Return string ID of AP1000 equipment
        '''
        from PyApex.Constantes import SimuAP1000_ID
        
        if self.__Simulation:
            return SimuAP1000_ID
        else:
            Send(self.Connexion, "*IDN?\n")
            ID = Receive(self.Connexion)
            return ID


    def Reset(self):
        '''
        Reset AP1000 equipment
        '''
        if not self.__Simulation:
            Send(self.Connexion, "*RST\n")
    
    
    def DisplayScreen(self, Display):
        '''
        Displays or not the "Remote" window on the AP1000 equipment.
        Display is a boolean:
            - True: the window is displayed
            - False: the window is hidden
        '''
        
        if Display == False:
            Display = 0
        else:
            Display = 1
        
        if not self.__Simulation:
            Send(self.Connexion, "REMSCREEN" + str(Display) + "\n")


    def SlotUsed(self, SlotNumber):
        '''
        Return a boolean indicated if slot 'SlotNumber' is used by AP1000 equipment
            - if return True : Slot is used by a module
            - if return False : Slot is not used
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Constantes import AP1000_SLOT_MIN, AP1000_SLOT_MAX
        from PyApex.Constantes import SimuAP1000_SlotUsed
        from PyApex.Errors import ApexError
        
        if not isinstance(SlotNumber, int):
            self.Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "SlotNumber")
        if SlotNumber < AP1000_SLOT_MIN or SlotNumber > AP1000_SLOT_MAX:
            self.Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_VALUE, "SlotNumber")
        
        if self.__Simulation:
            ID = SimuAP1000_SlotUsed
        else:
            Command = "SLT[" + str(SlotNumber).zfill(2) + "]:EMPTY?\n"
            Send(self.Connexion, Command)
            ID = Receive(self.Connexion, 10)
            
        if ID[:-1] == "0":
            return False
        elif ID[:-1] == "1":
            return True


    def SlotID(self, SlotNumber, Force=False):
        '''
        Return a string ID of the module selected by 'SlotNumber'
        If Force is True, the function return an ID even if slot isn't used
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Constantes import AP1000_SLOT_MIN, AP1000_SLOT_MAX
        from PyApex.Constantes import SimuAP1000_SlotID
        from PyApex.Errors import ApexError
        
        if not isinstance(SlotNumber, int):
            self.Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "SlotNumber")
        if SlotNumber < AP1000_SLOT_MIN or SlotNumber > AP1000_SLOT_MAX:
            self.Connexion.close()
            raise ApexError(APXXXX_ERROR_ARGUMENT_VALUE, "SlotNumber")
        
        if self.__Simulation:
            ID = SimuAP1000_SlotID
        else:
            if Force:
                SlotUsed = True
            else:
                SlotUsed = self.SlotUsed(SlotNumber)
            if SlotUsed:
                Command = "SLT[" + str(SlotNumber).zfill(2) + "]:IDN?\n"
                Error = Send(self.Connexion, Command)
                ID = Receive(self.Connexion)
            else:
                return "Slot not used"
            
        return ID[:-1]


    def SlotSN(self, SlotNumber, Force=False):
        '''
        Return the Serial Number (integer) of the module in the slot 'SlotNumber'
        If Force is True, the function return a S/N even if slot isn't used 
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE, AP1000_ERROR_SLOT_NOT_DEFINED
        from PyApex.Constantes import AP1000_SLOT_MIN, AP1000_SLOT_MAX
        from PyApex.Constantes import SimuAP1000_SlotID
        from PyApex.Errors import ApexError
        import re
        
        if not isinstance(SlotNumber, int):
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "SlotNumber")
            sys.exit()
        if SlotNumber < AP1000_SLOT_MIN or SlotNumber > AP1000_SLOT_MAX:
            raise ApexError(APXXXX_ERROR_ARGUMENT_VALUE, "SlotNumber")
            sys.exit()

        if self.__Simulation:
            SN = SimuAP1000_SlotID
        else:
            SN = self.SlotID(SlotNumber, Force=Force)

        try:
            SN = SN.lower().split("/")[2].split("-")
            SN = SN[len(SN) - 1]
            SN = int(re.findall("\d+", SN)[0])
            return int(SN)
        except:
            print("PyApex Warning. Slot", SlotNumber, "not defined")
    

    def SlotType(self, SlotNumber, Type="string"):
        '''
        Return a description of the module in the slot 'SlotNumber'
        If Type = 'string' or 'str' or 's', the function returns a string (default)
        If Type = 'integer' or 'int' or 'i', the function returns the module number type
        '''
        from PyApex.Constantes import APXXXX_ERROR_ARGUMENT_TYPE, APXXXX_ERROR_ARGUMENT_VALUE
        from PyApex.Constantes import AP1000_SLOT_MIN, AP1000_SLOT_MAX
        from PyApex.Constantes import AP1000_ERROR_SLOT_NOT_DEFINED, SimuAP1000_SlotID, Modules
        from PyApex.Errors import ApexError
        from random import sample
        import re
        
        if not isinstance(SlotNumber, int):
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "SlotNumber")
            sys.exit()
        if SlotNumber < AP1000_SLOT_MIN or SlotNumber > AP1000_SLOT_MAX:
            raise ApexError(APXXXX_ERROR_ARGUMENT_VALUE, "SlotNumber")
            sys.exit()
        
        if not isinstance(Type, str):
            raise ApexError(APXXXX_ERROR_ARGUMENT_TYPE, "Type")
            sys.exit()
        
        Type = Type.lower()
        
        if self.__Simulation:
            ID = sample(list(Modules), 1)
            return Modules[ID[0]]
        else:
            if self.SlotUsed(SlotNumber):
                ID = self.SlotID(SlotNumber)
            else:
                return "Slot not used"
            
        try:
            ID = ID.lower().split("/")[1].split("-")[0]
            ID = int(re.findall("\d+", ID)[0])
            if Type == "integer" or Type == "int" or Type == "i":
                return ID
            else:
                return Modules[ID]
        except:
            print("PyApex Warning. Slot", SlotNumber, "not defined")


    def PowerMeter(self, SlotNumber, Force=False):
        '''
        Return a PowerMeter class for the module in the slot 'SlotNumber'
        if Force is True, a PowerMeter class is returned even if the module isn't a Power Meter
        '''
        from PyApex.Constantes import AP1000_ERROR_SLOT_NOT_GOOD_TYPE, AP1000_PWM_NAME
        from PyApex.Errors import ApexError
        from PyApex.AP1000.PowerMeter import PowerMeter
        
        if Force:
            return PowerMeter(self, SlotNumber, self.__Simulation)
        if self.__Simulation or self.SlotType(SlotNumber) == AP1000_PWM_NAME:
            return PowerMeter(self, SlotNumber, self.__Simulation)
        else:
            print("PyApex Warning. Wrong module")
            return None


    def Attenuator(self, SlotNumber, Force=False):
        '''
        Return an Attenuator class for the module in the slot 'SlotNumber'
        if Force is True, an Attenuator class is returned even if the module isn't an Attenuator
        '''
        from PyApex.Constantes import AP1000_ERROR_SLOT_NOT_GOOD_TYPE, AP1000_ATT_NAME
        from PyApex.Errors import ApexError
        from PyApex.AP1000.Attenuator import Attenuator
        
        if Force:
            return Attenuator(self, SlotNumber, self.__Simulation)
        if self.__Simulation or self.SlotType(SlotNumber) == AP1000_ATT_NAME:
            return Attenuator(self, SlotNumber, self.__Simulation)
        else:
            print("PyApex Warning. Wrong module")
            return None


    def TunableLaser(self, SlotNumber, Force=False):
        '''
        Return a TunableLaser class for the module in the slot 'SlotNumber'
        if Force is True, a TunableLaser class is returned even if the module isn't a Tunable Laser
        '''
        from PyApex.Constantes import AP1000_ERROR_SLOT_NOT_GOOD_TYPE, AP1000_TLS_CBAND_NAME, AP1000_TLS_LBAND_NAME
        from PyApex.Errors import ApexError
        from PyApex.AP1000.TunableLaser import TunableLaser
        
        if Force:
            return TunableLaser(self, SlotNumber, self.__Simulation)
        if self.__Simulation or self.SlotType(SlotNumber) == AP1000_TLS_CBAND_NAME \
           or self.SlotType(SlotNumber) == AP1000_TLS_LBAND_NAME:
            return TunableLaser(self, SlotNumber, self.__Simulation)
        else:
            print("PyApex Warning. Wrong module")
            return None


    def ErbiumAmplifier(self, SlotNumber, Force=False):
        '''
        Return an ErbiumAmplifier class for the module in the slot 'SlotNumber'
        if Force is True, an ErbiumAmplifier class is returned even if the module isn't an Erbium Amplifier
        '''
        from PyApex.Constantes import AP1000_ERROR_SLOT_NOT_GOOD_TYPE, AP1000_EFA_NAME 
        from PyApex.Errors import ApexError
        from PyApex.AP1000.ErbiumAmplifier import ErbiumAmplifier
        
        if Force:
            return ErbiumAmplifier(self, SlotNumber, self.__Simulation)
        if self.__Simulation or self.SlotType(SlotNumber) == AP1000_EFA_NAME:
            return ErbiumAmplifier(self, SlotNumber, self.__Simulation)
        else:
            print("PyApex Warning. Wrong module")
            return None


    def OpticalSwitch(self, SlotNumber, Force=False):
        '''
        Return an OpticalSwitch class for the module in the slot 'SlotNumber'
        if Force is True, an OpticalSwitch class is returned even if the module isn't an Optical Switch
        '''
        from PyApex.Constantes import AP1000_ERROR_SLOT_NOT_GOOD_TYPE, AP1000_OSW_NAME  
        from PyApex.Errors import ApexError
        from PyApex.AP1000.OpticalSwitch import OpticalSwitch
        
        if Force:
            return OpticalSwitch(self, SlotNumber, self.__Simulation)
        if self.__Simulation or self.SlotType(SlotNumber) == AP1000_OSW_NAME:
            return OpticalSwitch(self, SlotNumber, self.__Simulation)
        else:
            print("PyApex Warning. Wrong module")
            return None
    
    
    def OpticalFilter(self, SlotNumber, Force=False):
        '''
        Return an OpticalFilter class for the module in the slot 'SlotNumber'
        if Force is True, an OpticalFilter class is returned even if the module isn't an Optical Filter
        '''
        from PyApex.Constantes import AP1000_ERROR_SLOT_NOT_GOOD_TYPE, AP1000_FIL_NAME
        from PyApex.Errors import ApexError
        from PyApex.AP1000.Filter import Filter
        
        if Force:
            return Filter(self, SlotNumber, self.__Simulation)
        if self.__Simulation or self.SlotType(SlotNumber) == AP1000_FIL_NAME:
            return Filter(self, SlotNumber, self.__Simulation)
        else:
            print("PyApex Warning. Wrong module")
            return None
    
    
    def DfbLaser(self, SlotNumber, Force=False):
        '''
        Return a DfbLaser class for the module in the slot 'SlotNumber'
        if Force is True, a DfbLaser class is returned even if the module isn't a DFB Laser
        '''
        from PyApex.Constantes import AP1000_ERROR_SLOT_NOT_GOOD_TYPE, AP1000_DFB_CBAND_NAME, AP1000_DFB_LBAND_NAME, AP1000_DFB_OBAND_NAME
        from PyApex.Errors import ApexError
        from PyApex.AP1000.DfbLaser import DfbLaser
        
        if Force:
            return DfbLaser(self, SlotNumber, self.__Simulation)
        if self.__Simulation or self.SlotType(SlotNumber) == AP1000_DFB_CBAND_NAME \
           or self.SlotType(SlotNumber) == AP1000_DFB_LBAND_NAME or \
           self.SlotType(SlotNumber) == AP1000_DFB_OBAND_NAME:
            return DfbLaser(self, SlotNumber, self.__Simulation)
        else:
            print("PyApex Warning. Wrong module")
            return None
    
    
    def Polarimeter(self, SlotNumber, Force=False):
        '''
        Return a Polarimeter class for the module in the slot 'SlotNumber'
        if Force is True, a Polarimeter class is returned even if the module isn't a Polarimeter
        '''
        from PyApex.Constantes import AP1000_ERROR_SLOT_NOT_GOOD_TYPE, AP1000_POL_NAME
        from PyApex.Errors import ApexError
        from PyApex.AP1000.Polarimeter import Polarimeter
        
        if Force:
            return Polarimeter(self, SlotNumber, self.__Simulation)
        if self.__Simulation or self.SlotType(SlotNumber) == AP1000_POL_NAME:
            return Polarimeter(self, SlotNumber, self.__Simulation)
        else:
            print("PyApex Warning. Wrong module")
            return None
    
    
    def OSA(self, SlotNumber, Force=False):
        '''
        Return an OSA class for the OSA module
        SlotNumber is the slot of the polarimeter or the power-meter used for the OSA module
        if Force is True, an OSA class is returned even if the module isn't a Polarimeter or a Power-Meter
        '''
        from PyApex.Constantes import AP1000_ERROR_SLOT_NOT_GOOD_TYPE, AP1000_POL_NAME, AP1000_PWM_NAME
        from PyApex.Errors import ApexError
        from PyApex.AP1000.OSA import OSA
        
        if Force:
            return OSA(self, SlotNumber, self.__Simulation)
        if self.__Simulation or self.SlotType(SlotNumber) == AP1000_POL_NAME or self.SlotType(SlotNumber) == AP1000_PWM_NAME:
            return OSA(self, SlotNumber, self.__Simulation)
        else:
            print("PyApex Warning. Wrong module")
            return None
