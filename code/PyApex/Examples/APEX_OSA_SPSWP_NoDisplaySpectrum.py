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
    
  # start and stop wavelength 
bFullSpan = False
if bFullSpan:    
    wl_start = 1524.578 
    wl_stop = 1607.413 
    # Number of points and resolutions 
    NbPoints = int(5e6)
    Res_value = 0.04e-3

else:
    # wl_start = 1549.750 
    # wl_stop  =  1550.250 
    wl_start = 1549.000
    wl_stop  = 1551.000
    NbPoints = 14261
    Res_value = 1.12e-3
    
wl_center =  (wl_start+wl_stop)/2
wl_span = abs(wl_stop-wl_start)

# data acquisition: ASCII or Binary  
bASCII_data_acq = True  
# save and load files 
bload_mes = False
bSave_mes = False
bPlot_fig  = True

# Connection to your OSA *** SET THE GOOD IP ADDRESS 
MyAP2XXX = AP2XXX("192.168.1.35")

# tlsmode = MyAP2XXX.ListModes()
# print(tlsmode)
# MyTLS = MyAP2XXX.TLS() 
# MyTLS.SetUnit("dBm")
# MyTLS.On()
# MyTLS.SetPower(2.0)
# MyTLS.GetPower()
# MyTLS.SetWavelength(1550.000)
# MyTLS.GetWavelength()
MyOSA = MyAP2XXX.OSA()

#%% =============================================================================
#  Setting the parameters for Apex OSA and running the sweep 
# =============================================================================

#  Unit of XScale 
MyOSA.SetScaleXUnit("nm")
#  Unit of Yscal (default dBm)
# Defines the unit of the Y-Axis
MyOSA.SetScaleYUnit("log") 
MyOSA.SetStartWavelength(wl_start)
MyOSA.SetStopWavelength(wl_stop)
# MyOSA.SetSpan(3)
# MyOSA.SetCenter(1550.0)

# Set number of points 
MyOSA.DeactivateAutoNPoints() 
MyOSA.SetNPoints(NbPoints)

# MyOSA.SetNPoints(2000)
# Measurement resolution
MyOSA.SetXResolution(Res_value)
# MyOSA.SetXResolution(0.04*1e-3)
# MyOSA.SetXResolution(0.04*1e-3)
MyOSA.DeactivateAverageMode()

# MyOSA.SetSweepSpeed(50.0)
# WL calibration in order to capture the FP and Acetylen GAS signals  
# MyOSA.WavelengthCalib()

#%% =============================================================================
#  Running the single sweep 
# =============================================================================
#  freeze or blank the display
bFreezeDisplay = True
# number_sweep = int(6e3)
number_sweep = 2

if bFreezeDisplay == True:
    t0 = time.time()
    for i in range(number_sweep):    
        # We run a single
        # Trace = MyOSA.Run("single")
        # SPSWP4
        MyOSA.Run(4)        
        Data = MyOSA.GetDataBin("nm","log",1)
        plt.figure(i) 
        plt.grid(True) 
        plt.plot(Data[1], Data[0],label = 'ASCII') 
        plt.xlabel("Wavelength (nm)") 
        plt.ylabel("Power (dBm)") 
        # plt.legend("Measured data", loc='upper right')
        plt.legend()
        plt.show()
    t1 = time.time()
else:
    
    t0 = time.time()    
    for i in range(number_sweep):
        # We run a single
        Trace = MyOSA.Run("single")
        Data = MyOSA.GetDataBin("nm","log",1)
        plt.figure(i) 
        plt.grid(True) 
        plt.plot(Data[1], Data[0],label = 'ASCII') 
        plt.xlabel("Wavelength (nm)") 
        plt.ylabel("Power (dBm)") 
        # plt.legend("Measured data", loc='upper right')
        plt.legend()
        plt.show()
    t1 = time.time()

print("Time Total:", t1-t0,"sec")
print("Time Total:", (t1-t0)/3600,"hours")

# aaa
# if Trace > 0:
#  	#========================================================================= 
#     #  ASCII data transfer 
#     #=========================================================================
#     if bASCII_data_acq == True: 
#         t0_ASCII = time.time()
#         Data = MyOSA.GetData("nm","log",1)
#         # Data = MyOSA.GetData("nm","lin",1)
#         # Data = MyOSA.GetData("GHz","log",1)
#         # Data = MyOSA.GetData("GHz","lin",1)
#         t1_ASCII = time.time()
#         print("ASCII data Transfer Time Total :", t1_ASCII-t0_ASCII)
    
#         if bSave_mes== True:
#             # Save the ASCII data 
#             path = "D:/Work/Remote Control/Python/Test"
#             with open(path + '/' + 'res_' + str(Res_value) +'pm_'+ str(NbPoints) + 'Points_ASCII_' + '_Spectrum.txt', 'w') as f:
#                 f.write('nm' + '\t' + 'dBm' + '\n')
#                 for i in range(len(Data[1])):
#                     f.write(str(Data[1][i]) + "\t" + str(Data[0][i]) + '\n')
#                 f.close()
        
#         #  Display the sepctrum (figures)
#         # The spectrum is displayed
#         if bPlot_fig==True:     
#             if Trace > 0:
#                 plt.figure(1) 
#                 plt.grid(True) 
#                 plt.plot(Data[1], Data[0],label = 'ASCII') 
#                 plt.xlabel("Wavelength (nm)") 
#                 plt.ylabel("Power (dBm)") 
#                 # plt.legend("Measured data", loc='upper right')
#                 plt.legend()
#                 plt.show()
#             # del Data     
#     #========================================================================= 
#     #  Binary data transfer 
#     #========================================================================= 
#     else:
#         # Data = MyOSA.Get_xDataAscii_yDataBin("nm","log",1)
#         t0_BIN = time.time()
#         Data = MyOSA.GetDataBin("nm","log",1)
#         # Data = MyOSA.GetDataBin("nm","lin",1)
#         # Data = MyOSA.GetDataBin("ghz","log",1)
#         # Data = MyOSA.GetDataBin("ghz","lin",1)
#         t1_BIN = time.time()
#         print("Binary data Transfer Time Total :", t1_BIN-t0_BIN)
       
#         if bSave_mes == True: 
#             path = "D:/Work/Remote Control/Python/Test"    
#             with open(path + '/' + 'res_' + str(Res_value) +'pm_'+ str(NbPoints) + 'Points_Binary_' + '_Spectrum.txt', 'w') as f:
#                 f.write('nm' + '\t' + 'dBm' + '\n')
#                 for i in range(len(Data[1])):
#                     f.write(str(Data[1][i]) + "\t" + str(Data[0][i]) + '\n')
#                 f.close()
#         #  Display the sepctrum (figures)
#         # The spectrum is displayed
#         if bPlot_fig==True:                 
#             if Trace > 0:
#                 plt.figure(1) 
#                 plt.grid(True) 
#                 plt.plot(Data[1], Data[0],label = 'Binary') 
#                 plt.xlabel("Wavelength (nm)") 
#                 plt.ylabel("Power (dBm)") 
#                 # plt.legend("Measured data", loc='upper right')
#                 plt.legend()
#                 plt.show()
# # close connection
# # MyAP2XXX.Close()

# # #%% =============================================================================
# # #               Save the data and draw figure        
# # # =============================================================================
# # #save directly by python comman
# # #DataTran = np.transpose(np.sort(Data))
# # #MesData = np.transpose([DataTran[:,-1],DataTran[:,0]])
# # #MesData = np.transpose([np.sort(Data[1]),Data[0]])


