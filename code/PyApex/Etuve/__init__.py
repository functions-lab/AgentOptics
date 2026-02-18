#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Etuve():
    '''
    This class allows to remote control the Thermal Etuve XU
    '''

    def __init__(self, ComPort=1, Simulation=False):
        '''
        Constructor of an Etuve equipment.
        ComPort is the COM port number (integer) of the Laser.
        Simulation is a boolean to indicate to the program if it has to run in simulation mode or not
        '''
        self.ComPort = ComPort
        self.Simulation = Simulation
        if self.Simulation:
            print("Connected successfully to the New Focus Tunable Laser")
        else:
            self.Connexion = self.Open()

        self.LastSend = 0
        self.Msg = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] 
        self.StatusIndex = 0
        self.Status = ["OFF", "ON"]


    def __str__(self):
        return "Thermal Etuve on " + str(self.ComPort)


    def Open(self):
        '''
        Open connexion with an Etuve XU equipment.
        This method is called by the constructor of Etuve class
        '''
        import serial, sys
        from PyApex.Constantes import ETUVE_BAUDRATE, ETUVE_NBITS, \
             ETUVE_STOPBIT, ETUVE_FLOWCONTROL
        
        try:
            Connexion = serial.Serial("COM" + str(self.ComPort), ETUVE_BAUDRATE)
        except:
            print("Cannot open connexion with the Etuve")
            sys.exit()
        else:
            print("Connected successfully to the Etuve")
            return Connexion


    def Close(self, Error=False):
        '''
        Close connexion to New Focus TLS equipment
        '''
        if not self.Simulation:
            self.Connexion.close()


    def Send(self, Command):
        '''
        Send a string Command to the Etuve (ending character must be \'\n')
        '''
        from PyApex.Constantes import ETUVE_ERROR_ARGUMENT_TYPE, ETUVE_ERROR_COMMUNICATION
        from PyApex.Errors import EtuveError
        
        if not isinstance(Command, str):
            self.Close(True)
            raise EtuveError(ETUVE_ERROR_ARGUMENT_TYPE, "Command")
        
        if not self.Simulation:
            self.Connexion.flush()
            try:
                self.Connexion.write(Command.encode())
            except:
                self.Close(True)
                raise EtuveError(ETUVE_ERROR_COMMUNICATION, "Command")


    def Receive(self, ByteNumber=56):
        '''
        Receive a string from the Etuve
        ByteNumber is an integer (default to 56) representing the number of bytes to receive
        '''
        from PyApex.Constantes import ETUVE_ERROR_ARGUMENT_TYPE, ETUVE_ERROR_BADCOMMAND
        from PyApex.Errors import EtuveError
        
        if not isinstance(ByteNumber, int):
            self.Close(True)
            raise EtuveError(ETUVE_ERROR_ARGUMENT_TYPE, "ByteNumber")
        
        if not self.Simulation:
            try:
                data = self.Connexion.read(size = ByteNumber)
            except:
                self.Close(True)
                raise EtuveError(ETUVE_ERROR_BADCOMMAND, "Last command")
            else:
                self.Msg = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                for i in range(0, len(data), 4):
                    if data[i] == 129:
                        if 0 <= data[i+1] <= 26:
                            self.Msg[int(data[i+1] / 2)] = data[i+2] + 256 * data[i+3]


    def GetActualTemp(self):
        from time import time
        if time() - self.LastSend > 10:
            self.Send('t')
            self.Receive()
            self.LastSend = time()
        return float(self.Msg[0] / 10.0)


    def GetConsigneTemp(self):
        from time import time
        if time() - self.LastSend > 10:
            self.Send('t')
            self.Receive()
            self.LastSend = time()
        return float(self.Msg[1] / 10.0)


    def SetConsigneTemp(self, Temperature):
        t = int(Temperature * 10)
        self.Connexion.write([b'\x81', b'\x02', t % 256, int(t / 256)])









