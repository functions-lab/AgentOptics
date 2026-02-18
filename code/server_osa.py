#!/usr/bin/env python3
from typing import Any, Optional, Dict, Union, Literal
from mcp.server.fastmcp import FastMCP
# from mcp.types import TableContent
import logging, sys, re, asyncio
from matplotlib import pyplot as plt
import subprocess
import pandas as pd
from pathlib import Path
import os, sys
import PyApex.AP2XXX as AP2XXX

logger = logging.getLogger(__name__)

osa_ipaddress = "YOUR_IP"

# Initialize FastMCP server
mcp = FastMCP("opticsMCP")

# Helper function
C_M_PER_S = 299_792_458.0  # exact, m/s

def nm_to_ghz(l_nm: float) -> float:
	return C_M_PER_S / (l_nm * 1e-9) / 1e9

def ghz_to_nm(f_ghz: float) -> float:
	return C_M_PER_S / (f_ghz * 1e9) * 1e9

# ============================================================================
# APEX OSA Tools
# ============================================================================
"""
	Get Apex OSA power measurement.
"""
@mcp.tool()
async def get_osa_power_measurement() -> str:
	"""Get Apex OSA (optical spectrum analyzer) power measurement.

	"""
	ipAddress = osa_ipaddress
	MyAP2XXX = AP2XXX(ipAddress, Simulation=False)
	logging.info("connected")

	ApexMode = {'Powermeter':3,"OSA":4}
	MyAP2XXX.ChangeMode(ApexMode['Powermeter'])
	logging.info("change mode")

	MyPowermeter = MyAP2XXX.Powermeter()
	power = MyPowermeter.GetPower()
	unit = MyPowermeter.GetUnit()

	logging.info(power)
	logging.info(unit)
	
	MyAP2XXX.Close()

	if not power:
		return "Unable to fetch OSA Power."

	format_str = f"""
		PowerValue: {power}
		Unit: {unit}
		"""
	return "\n---\n".join(format_str)


@mcp.tool()
async def get_osa_spectrum_measurement() -> dict:
	"""
		Run a **single** OSA sweep using the **current** configuration and return the spectrum.

		What this tool does
		-------------------
		- Connects to the OSA at `osa_ipaddress`.
		- Triggers one acquisition (`Run()`).
		- Retrieves the spectrum as **ASCII** arrays in **wavelength (nm)** and **power (dBm)**.
		- Returns data in a simple table-like JSON structure:
			{
			  "columns": ["Wavelength (nm)", "Power (dBm)"],
			  "rows":    [[x0, x1, ...], [y0, y1, ...]]
			}
		  where `rows[0]` are X values (nm) and `rows[1]` are Y values (dBm).
		- Closes the connection before returning.

		Output units & ordering
		-----------------------
		- X-axis is **wavelength in nm**.
		- Y-axis is **power in dBm** (log scale).
		- The underlying driver returns `[Y, X]`; this tool reorders to `[X, Y]` for clarity.

	"""
	ipAddress = osa_ipaddress
	MyAP2XXX = AP2XXX(ipAddress, Simulation=False)
	MyOSA = MyAP2XXX.OSA()

	Trace = MyOSA.Run()

	bASCII_data = True
	Data = [[], []]
	if Trace > 0:
		if bASCII_data == True:
			Data = MyOSA.GetData("nm", "log", Trace)
		else:
			Data = MyOSA.GetDataBin("nm", "log", Trace)

	MyAP2XXX.Close()

	columns = ["Wavelength (nm)", "Power (dBm)"]
	rows = [Data[1], Data[0]] if Trace > 0 else [[], []]

	if Trace > 0:
		plt.grid(True)
		plt.plot(Data[1], Data[0])
		plt.xlabel("Wavelength (nm)")
		plt.ylabel("Power (dBm)")
		# plt.show()
		plt.savefig("../figures/OSA_plot.png")
	else:
		print("No spectrum acquired")

	return {
		"columns": columns,
		"rows": rows
	}

@mcp.tool()
async def osa_set_units(x_unit: str = 'GHz', y_unit: str = 'lin') -> str:
	"""
	Set the OSA (optical spectrum analyzer) output units. Does not start a sweep.

	Args:
	  x_unit: "nm" for wavelength or "GHz" (dafault) for frequency (case-insensitive). 
	  y_unit: "log" for dBm or "lin" (default) for linear power in mW.

	Returns:
	  "x_unit=<val>, y_unit=<val>"
	"""
	ipAddress = osa_ipaddress
	MyAP2XXX = AP2XXX(ipAddress, Simulation=False)
	MyOSA = MyAP2XXX.OSA()
	MyOSA.SetScaleXUnit(x_unit)
	MyOSA.SetScaleYUnit(y_unit)
	MyAP2XXX.Close()
	return f"Successfully set x-axis unit to {x_unit} and y-axis scale to {y_unit}."

@mcp.tool()
async def osa_set_start_wavelength(start_nm: float) -> str:
	"""
	Set the OSA (optical spectrum analyzer) spectrum window START wavelength in nanometers. Does not start a sweep.

	Args:
	  start_nm: Start wavelength in nm.

	Returns:
	  "Successfully set start wavelength to <val> nm"
	"""
	ipAddress = osa_ipaddress
	MyAP2XXX = AP2XXX(ipAddress, Simulation=False)
	MyOSA = MyAP2XXX.OSA()
	MyOSA.SetStartWavelength(start_nm)
	applied = float(MyOSA.GetStartWavelength())
	MyAP2XXX.Close()
	return f"Successfully set start wavelength to {applied} nm"

@mcp.tool()
async def osa_get_start_wavelength() -> str:
	"""
	Get the OSA (optical spectrum analyzer) spectrum window START wavelength in nanometers.

	Returns:
	  "spectrum_window_start_wavelength=<value> nm"
	"""
	ipAddress = osa_ipaddress
	MyAP2XXX = AP2XXX(ipAddress, Simulation=False)
	MyOSA = MyAP2XXX.OSA()
	value = float(MyOSA.GetStartWavelength())
	MyAP2XXX.Close()
	return f"spectrum_window_start_wavelength={value} nm"

@mcp.tool()
async def osa_set_stop_wavelength(stop_nm: float) -> str:
	"""
	Set the OSA (optical spectrum analyzer) spectrum window STOP wavelength in nanometers. Does not start a sweep.

	Args:
	  stop_nm: Stop wavelength in nm.

	Returns:
	  "Successfully set stop wavelength to <val> nm"
	"""
	ipAddress = osa_ipaddress
	MyAP2XXX = AP2XXX(ipAddress, Simulation=False)
	MyOSA = MyAP2XXX.OSA()
	MyOSA.SetStopWavelength(stop_nm)
	applied = float(MyOSA.GetStopWavelength())
	MyAP2XXX.Close()
	return f"Successfully set stop wavelength to {applied} nm"

@mcp.tool()
async def osa_get_stop_wavelength() -> str:
	"""
	Get the OSA (optical spectrum analyzer) spectrum window STOP wavelength in nanometers.

	Returns:
	  "spectrum_window_stop_wavelength=<value> nm"
	"""
	ipAddress = osa_ipaddress
	MyAP2XXX = AP2XXX(ipAddress, Simulation=False)
	MyOSA = MyAP2XXX.OSA()
	value = float(MyOSA.GetStopWavelength())
	MyAP2XXX.Close()
	return f"spectrum_window_stop_wavelength={value} nm"

@mcp.tool()
async def osa_set_center(center_nm: float) -> str:
	"""
	Set the OSA (optical spectrum analyzer) spectrum CENTER wavelength in nanometers. Does not start a sweep.
	The instrument will recompute start/stop edges around the current span.

	Args:
	  center_nm: Center wavelength in nm.

	Returns:
	  "Successfully set center wavelength to <val> nm"
	"""
	ipAddress = osa_ipaddress
	MyAP2XXX = AP2XXX(ipAddress, Simulation=False)
	MyOSA = MyAP2XXX.OSA()
	MyOSA.SetCenter(center_nm)
	applied = float(MyOSA.GetCenter())
	MyAP2XXX.Close()
	return f"Successfully set center wavelength to {applied} nm"

@mcp.tool()
async def osa_get_center() -> str:
	"""
	Get the OSA (optical spectrum analyzer) spectrum CENTER wavelength in nanometers.

	Returns:
	  "spectrum_center_wavelength=<value> nm"
	"""
	ipAddress = osa_ipaddress
	MyAP2XXX = AP2XXX(ipAddress, Simulation=False)
	MyOSA = MyAP2XXX.OSA()
	value = float(MyOSA.GetCenter())
	MyAP2XXX.Close()
	return f"spectrum_center_wavelength={value} nm"

@mcp.tool()
async def osa_set_span(span_nm: float) -> str:
	"""
	Set the OSA (optical spectrum analyzer) spectrum SPAN in nanometers. Does not start a sweep.
	The instrument will recompute start/stop edges around the current center.

	Args:
	  span_nm: Total span in nm.

	Returns:
	  "Successfully set span to <val> nm"
	"""
	ipAddress = osa_ipaddress
	MyAP2XXX = AP2XXX(ipAddress, Simulation=False)
	MyOSA = MyAP2XXX.OSA()
	MyOSA.SetSpan(span_nm)
	applied = float(MyOSA.GetSpan())
	MyAP2XXX.Close()
	return f"Successfully set span to {applied} nm"

@mcp.tool()
async def osa_get_span() -> str:
	"""
	Get the OSA (optical spectrum analyzer) spectrum SPAN in nanometers.

	Returns:
	  "spectrum_span=<value> nm"
	"""
	ipAddress = osa_ipaddress
	MyAP2XXX = AP2XXX(ipAddress, Simulation=False)
	MyOSA = MyAP2XXX.OSA()
	value = float(MyOSA.GetSpan())
	MyAP2XXX.Close()
	return f"spectrum_span={value} nm"

@mcp.tool()
async def osa_get_settings() -> dict:
	"""
		Get Apex OSA (Optical Spectrum Analyzer) key acquisition settings.

		Units & fields
		--------------
		- All wavelength-related values are returned in **nanometers (nm)**.
		- The number of points is returned as an **integer**.
		- Returned fields:
			{
			  "start_nm":  float,   # window start wavelength (nm)
			  "stop_nm":   float,   # window stop wavelength (nm)
			  "center_nm": float,   # center wavelength (nm)
			  "span_nm":   float,   # total span (nm)
			  "npoints":   int      # sample points configured (auto or manual)
			}

	"""
	ipAddress = osa_ipaddress
	MyAP2XXX = AP2XXX(ipAddress, Simulation=False)
	MyOSA = MyAP2XXX.OSA()

	center_nm = float(MyOSA.GetCenter())
	start_nm = float(MyOSA.GetStartWavelength())
	stop_nm  = float(MyOSA.GetStopWavelength())
	span_nm  = float(MyOSA.GetSpan())
	npoints  = int(MyOSA.GetNPoints())

	MyAP2XXX.Close()

	return {
		"start_nm": start_nm,
		"stop_nm": stop_nm,
		"center_nm": center_nm,
		"span_nm": span_nm,
		"npoints": npoints
	}


@mcp.tool()
async def osa_set_x_resolution(resolution: float) -> str:
	"""
	Set the OSA (optical spectrum analyzer) X-axis measurement resolution.
	Resolution is expressed in the current X unit (as set by SetScaleXUnit). Does not start a sweep.

	Args:
	  resolution: X-axis resolution value, in the current X unit.

	Returns:
	  "Successfully set x_resolution to <val>"
	"""
	ipAddress = osa_ipaddress
	MyAP2XXX = AP2XXX(ipAddress, Simulation=False)
	MyOSA = MyAP2XXX.OSA()
	MyOSA.SetXResolution(resolution)
	applied = float(MyOSA.GetXResolution())
	MyAP2XXX.Close()
	return f"Successfully set x_resolution to {applied}"


@mcp.tool()
async def osa_get_x_resolution() -> str:
	"""
	Get the OSA (optical spectrum analyzer) X-axis measurement resolution.
	Resolution is expressed in the current X unit (as set by SetScaleXUnit).

	Returns:
	  "x_resolution=<value>"
	"""
	ipAddress = osa_ipaddress
	MyAP2XXX = AP2XXX(ipAddress, Simulation=False)
	MyOSA = MyAP2XXX.OSA()
	value = float(MyOSA.GetXResolution())
	MyAP2XXX.Close()
	return f"x_resolution={value}"


@mcp.tool()
async def osa_set_y_resolution(resolution: float) -> str:
	"""
	Set the OSA (optical spectrum analyzer) Y-axis resolution (power per division).
	Resolution is expressed in the current Y unit (as set by SetScaleYUnit). Does not start a sweep.

	Args:
	  resolution: Y-axis power-per-division value, in the current Y unit.

	Returns:
	  "Successfully set y_resolution to <val>"
	"""
	ipAddress = osa_ipaddress
	MyAP2XXX = AP2XXX(ipAddress, Simulation=False)
	MyOSA = MyAP2XXX.OSA()
	MyOSA.SetYResolution(resolution)
	applied = float(MyOSA.GetYResolution())
	MyAP2XXX.Close()
	return f"Successfully set y_resolution to {applied}"


@mcp.tool()
async def osa_get_y_resolution() -> str:
	"""
	Get the OSA (optical spectrum analyzer) Y-axis resolution (power per division).
	Resolution is expressed in the current Y unit (as set by SetScaleYUnit).

	Returns:
	  "y_resolution=<value>"
	"""
	ipAddress = osa_ipaddress
	MyAP2XXX = AP2XXX(ipAddress, Simulation=False)
	MyOSA = MyAP2XXX.OSA()
	value = float(MyOSA.GetYResolution())
	MyAP2XXX.Close()
	return f"y_resolution={value}"


@mcp.tool()
async def osa_set_npoints(npoints: int) -> str:
	"""
	Set the OSA (optical spectrum analyzer) number of points for measurement.
	Does not start a sweep.

	Args:
	  npoints: Total number of sample points.

	Returns:
	  "Successfully set npoints to <val>"
	"""
	ipAddress = osa_ipaddress
	MyAP2XXX = AP2XXX(ipAddress, Simulation=False)
	MyOSA = MyAP2XXX.OSA()
	MyOSA.SetNPoints(npoints)
	applied = int(MyOSA.GetNPoints())
	MyAP2XXX.Close()
	return f"Successfully set npoints to {applied}"


@mcp.tool()
async def osa_get_npoints() -> str:
	"""
	Get the OSA (optical spectrum analyzer) number of points configured for measurement.

	Returns:
	  "npoints=<value>"
	"""
	ipAddress = osa_ipaddress
	MyAP2XXX = AP2XXX(ipAddress, Simulation=False)
	MyOSA = MyAP2XXX.OSA()
	value = int(MyOSA.GetNPoints())
	MyAP2XXX.Close()
	return f"npoints={value}"

@mcp.tool()
async def osa_set_start_freq_ghz(start_ghz: float) -> str:
	"""
	Set the OSA (optical spectrum analyzer) spectrum window START frequency in gigahertz. Does not start a sweep.

	Args:
	  start_ghz: Start frequency in GHz.

	Returns:
	  "Successfully set start frequency to <val> GHz"
	"""
	ipAddress = osa_ipaddress
	MyAP2XXX = AP2XXX(ipAddress, Simulation=False)
	MyOSA = MyAP2XXX.OSA()
	MyOSA.SetStartWavelength(ghz_to_nm(start_ghz))
	applied_nm = float(MyOSA.GetStartWavelength())
	MyAP2XXX.Close()
	return f"Successfully set start frequency to {nm_to_ghz(applied_nm):.3f} GHz"

@mcp.tool()
async def osa_get_start_freq_ghz() -> str:
	"""
	Get the OSA (optical spectrum analyzer) spectrum window START frequency in gigahertz.

	Returns:
	  "spectrum_window_start_frequency=<value> GHz"
	"""
	ipAddress = osa_ipaddress
	MyAP2XXX = AP2XXX(ipAddress, Simulation=False)
	MyOSA = MyAP2XXX.OSA()
	value_nm = float(MyOSA.GetStartWavelength())
	MyAP2XXX.Close()
	return f"spectrum_window_start_frequency={nm_to_ghz(value_nm):.3f} GHz"

@mcp.tool()
async def osa_set_stop_freq_ghz(stop_ghz: float) -> str:
	"""
	Set the OSA (optical spectrum analyzer) spectrum window STOP frequency in gigahertz. Does not start a sweep.

	Args:
	  stop_ghz: Stop frequency in GHz.

	Returns:
	  "Successfully set stop frequency to <val> GHz"
	"""
	ipAddress = osa_ipaddress
	MyAP2XXX = AP2XXX(ipAddress, Simulation=False)
	MyOSA = MyAP2XXX.OSA()
	MyOSA.SetStopWavelength(ghz_to_nm(stop_ghz))
	applied_nm = float(MyOSA.GetStopWavelength())
	MyAP2XXX.Close()
	return f"Successfully set stop frequency to {nm_to_ghz(applied_nm):.3f} GHz"

@mcp.tool()
async def osa_get_stop_freq_ghz() -> str:
	"""
	Get the OSA (optical spectrum analyzer) spectrum window STOP frequency in gigahertz.

	Returns:
	  "spectrum_window_stop_frequency=<value> GHz"
	"""
	ipAddress = osa_ipaddress
	MyAP2XXX = AP2XXX(ipAddress, Simulation=False)
	MyOSA = MyAP2XXX.OSA()
	value_nm = float(MyOSA.GetStopWavelength())
	MyAP2XXX.Close()
	return f"spectrum_window_stop_frequency={nm_to_ghz(value_nm):.3f} GHz"

@mcp.tool()
async def osa_set_center_freq_ghz(center_ghz: float) -> str:
	"""
	Set the OSA (optical spectrum analyzer) spectrum CENTER frequency in gigahertz. Does not start a sweep.
	The instrument will recompute start/stop edges around the current span.

	Args:
	  center_ghz: Center frequency in GHz.

	Returns:
	  "Successfully set center frequency to <val> GHz"
	"""
	ipAddress = osa_ipaddress
	MyAP2XXX = AP2XXX(ipAddress, Simulation=False)
	MyOSA = MyAP2XXX.OSA()
	MyOSA.SetCenter(ghz_to_nm(center_ghz))
	applied_nm = float(MyOSA.GetCenter())
	MyAP2XXX.Close()
	return f"Successfully set center frequency to {nm_to_ghz(applied_nm):.3f} GHz"

@mcp.tool()
async def osa_get_center_freq_ghz() -> str:
	"""
	Get the OSA (optical spectrum analyzer) spectrum CENTER frequency in gigahertz.

	Returns:
	  "spectrum_center_frequency=<value> GHz"
	"""
	ipAddress = osa_ipaddress
	MyAP2XXX = AP2XXX(ipAddress, Simulation=False)
	MyOSA = MyAP2XXX.OSA()
	value_nm = float(MyOSA.GetCenter())
	MyAP2XXX.Close()
	return f"spectrum_center_frequency={nm_to_ghz(value_nm):.3f} GHz"

@mcp.tool()
async def osa_set_span_freq_ghz(span_ghz: float) -> str:
	"""
	Set the OSA (optical spectrum analyzer) spectrum SPAN in gigahertz. Does not start a sweep.
	The instrument will recompute start/stop edges around the current center.

	Args:
	  span_ghz: Total span in GHz.

	Returns:
	  "Successfully set span to <val> GHz"
	"""
	ipAddress = osa_ipaddress
	MyAP2XXX = AP2XXX(ipAddress, Simulation=False)
	MyOSA = MyAP2XXX.OSA()

	center_nm = float(MyOSA.GetCenter())
	center_ghz = nm_to_ghz(center_nm)
	f_start = center_ghz - span_ghz / 2.0
	f_stop  = center_ghz + span_ghz / 2.0

	MyOSA.SetStartWavelength(ghz_to_nm(f_start))
	MyOSA.SetStopWavelength(ghz_to_nm(f_stop))

	applied_start_ghz = nm_to_ghz(float(MyOSA.GetStartWavelength()))
	applied_stop_ghz  = nm_to_ghz(float(MyOSA.GetStopWavelength()))
	applied_span = abs(applied_stop_ghz - applied_start_ghz)
	MyAP2XXX.Close()
	return f"Successfully set span to {applied_span:.3f} GHz"

@mcp.tool()
async def osa_get_span_freq_ghz() -> str:
	"""
	Get the OSA (optical spectrum analyzer) spectrum SPAN in gigahertz.

	Returns:
	  "spectrum_span=<value> GHz"
	"""
	ipAddress = osa_ipaddress
	MyAP2XXX = AP2XXX(ipAddress, Simulation=False)
	MyOSA = MyAP2XXX.OSA()
	f_start = nm_to_ghz(float(MyOSA.GetStartWavelength()))
	f_stop  = nm_to_ghz(float(MyOSA.GetStopWavelength()))
	MyAP2XXX.Close()
	return f"spectrum_span={abs(f_stop - f_start):.3f} GHz"

######################## main ########################
if __name__ == "__main__":
	# Initialize and run the server
	mcp.run(transport='stdio')
