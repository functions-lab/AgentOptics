# Import the AP2XXX class from the Apex Driver
from PyApex import AP2XXX
# Import pyplot for displaying the data
from matplotlib import pyplot as plt
# import scipy as sp
# import numpy as np
# import struct
# import os
# from decimal import *
# c = 299792458 # Speed of light
import time
# import re

#%% =============================================================================
#  The parameters for Apex OSA
# =============================================================================
c = 299792458 # Speed of light

# Connection to your OSA *** SET THE GOOD IP ADDRESS 
selPC = 3
if selPC==0:
    #  My PC
    MyAP2XXX = AP2XXX("192.168.1.54")
    MyTLS = MyAP2XXX.APEXTLS()  # for Apex TLS
elif (selPC == 1):
    #  Apex Laser 
    MyAP2XXX = AP2XXX("192.168.1.52")
    MyTLS = MyAP2XXX.APEXTLS()  # for Apex TLS
elif (selPC == 2):
    # NEWFOCUS Laser
    MyAP2XXX = AP2XXX("192.168.1.48")
    tlsmode = MyAP2XXX.ListModes()
    print(tlsmode)
    MyTLS = MyAP2XXX.TLS()  # for NEWFOCUS in APChart_v2
    MyTLS.SetUnit("dBm")
else:
    # FILTEL Laser
    MyAP2XXX = AP2XXX("192.168.1.69")
    tlsmode = MyAP2XXX.ListModes()
    print(tlsmode)
    MyTLS = MyAP2XXX.TLS()  # for NEWFOCUS in APChart_v2
    MyTLS.SetUnit("dBm")
        

#  Laser ON/OF
MyTLS.On()
# MyTLS.Off()

status = MyTLS.GetStatus()
print("Laser status =", status)

# ----------------------------------------------------------------------------
#  Select Unit for WL and Power 
# ----------------------------------------------------------------------------
'''
selUnit = 
    0: (dBm , nm)
    1: (dBm, GHz)
    2: (mW, nm)
    3: (mW, GHz)
'''
selUnit = 0
#  boolean variables: 
# set unit for static WL: 0 for nm; 1 for GHz
bSetWL = 0   # set o for nm; 1 for GHz

bSelStatic = 0 # 0 for static mode; 1 for sweep mode 
bSelSweepMode = 1     # 0 for continuous mode; 1 for step mode 
# ----------------------------------------------------------------------------
if selUnit ==0:
    # Set Power Unit 
    MyTLS.SetPRWUnit(0)    # dBm 
    # MyTLS.SetPRWUnit(1)  # mW
    print("Power Unit =", MyTLS.GetPRWUnit())

    # Set WL Unit
    MyTLS.SetWLUnit(0)     # nm 
    # MyTLS.SetWLUnit(1)   # GHz
    print("Power Unit =", MyTLS.GetWLUnit())
elif selUnit ==1:
    # Set Power Unit 
    MyTLS.SetPRWUnit(0)    # dBm 
    # MyTLS.SetPRWUnit(1)  # mW
    print("Power Unit =", MyTLS.GetPRWUnit())

    # Set WL Unit
    # MyTLS.SetWLUnit(0)     # nm 
    MyTLS.SetWLUnit(1)   # GHz
    print("Power Unit =", MyTLS.GetWLUnit())
elif selUnit ==2:
    # Set Power Unit 
    # MyTLS.SetPRWUnit(0)    # dBm 
    MyTLS.SetPRWUnit(1)  # mW
    print("Power Unit =", MyTLS.GetPRWUnit())

    # Set WL Unit
    MyTLS.SetWLUnit(0)     # nm 
    # MyTLS.SetWLUnit(1)   # GHz
    print("Power Unit =", MyTLS.GetWLUnit())
else: 
    # Set Power Unit 
    # MyTLS.SetPRWUnit(0)    # dBm 
    MyTLS.SetPRWUnit(1)  # mW
    print("Power Unit =", MyTLS.GetPRWUnit())

    # Set WL Unit
    MyTLS.SetWLUnit(0)     # nm 
    # MyTLS.SetWLUnit(1)   # GHz
    print("Power Unit =", MyTLS.GetWLUnit())
    
# ----------------------------------------------------------------------------
#  Static Mode  
# ----------------------------------------------------------------------------
if bSelStatic == 0:
    MyTLS.SetLaserStatic()
    
    # Static Wavelength   
    if bSetWL ==0:
        # static WL 
        MyTLS.SetWavelength(1575.000)
        time.sleep(0.150)
        dWL = MyTLS.GetWavelength()
        time.sleep(0.150)
        print("Get Static WL =", dWL)
    else: 
        # static WL 
        MyTLS.SetFrequency(190345.264)
        time.sleep(0.150)
        dWL = MyTLS.GetFrequency()
        time.sleep(0.150)
        print("Get Static Freq =", dWL)
    
    # Static Power
    MyTLS.SetPower(5.00)
    time.sleep(0.150)
    dPow = MyTLS.GetPower()
    time.sleep(0.150)
    print("Get Static Power =", dPow)
else: 
    
    MyTLS.SetStartWL(1545.000)
    start_wl = MyTLS.GetStartWL()
    print("start WL =", start_wl)
    
    MyTLS.SetStopWL(1650.000)
    stop_wl = MyTLS.GetStopWL()
    print("stop WL =", stop_wl)
    if bSelSweepMode ==0:
        #-------------------------------------------------------------------------
        #  Continuous sweep mode 
        #-------------------------------------------------------------------------
        MyTLS.SetLaserSweep(0)      # continuous mode
        # Set Laser Speed 
        MyTLS.SetLaserSpeed(20.0)   # nm/s
        Speed = MyTLS.GetLaserSpeed()
        print("Laser Speed =", Speed)     
        
        # Set Cont. Power
        MyTLS.SetContPower(5.0)   # nm/s
        ContPower = MyTLS.GetContPower()
        print("Laser Speed =", ContPower)  
    else:
        #-------------------------------------------------------------------------
        #  Step sweep mode 
        #-------------------------------------------------------------------------
        MyTLS.SetLaserSweep(1)    # Mode 1: Step sweep mode 
        
        # Set and Get Step Delay  
        MyTLS.SeStepDealy(0.1)    # Step delay = 0.1 s
        StepDelay = MyTLS.GetStepDelay()
        print("Step Delay =", StepDelay)     
        
        # Set and Get Step Delay 
        MyTLS.SeStepNum(20)
        StepNum = MyTLS.GetStepNum()
        print("Step Delay =", StepNum)     
        
    
    # Runing one sweep 
    # MyTLS.Run(0)
    MyTLS.Run(1)
    # MyTLS.Stop()

#-------------------------------------------------------------------------    
# Close the connection 
# MyAP2XXX.Close()
  
 
# Sweep mode 
# MyTLS.SetLaserSweep(0)    # Mode 0: Continuous sweep mode  
# MyTLS.SetLaserSweep(1)    # Mode 1: Step sweep mode 



# MyTLS.SetPower(2.0)
# MyTLS.GetPower()
# MyTLS.SetWavelength(1550.000)
# MyTLS.GetWavelength()
# MyOSA = MyAP2XXX.OSA()


#%% =============================================================================
#               Save the data and draw figure        
# =============================================================================
#save directly by python comman
#DataTran = np.transpose(np.sort(Data))
#MesData = np.transpose([DataTran[:,-1],DataTran[:,0]])
#MesData = np.transpose([np.sort(Data[1]),Data[0]])


