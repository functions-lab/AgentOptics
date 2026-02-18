from typing import Any, Optional, Dict, Union, Literal
import logging, sys, re, asyncio, os, subprocess
from mcp.server.fastmcp import FastMCP
from matplotlib import pyplot as plt
from pathlib import Path
import pandas as pd
from POD2000 import POD2000

logger = logging.getLogger(__name__)

pod_instance = None
arduino_instance = None

# Initialize FastMCP server
mcp = FastMCP("opticsMCP")


def get_pod():
    """Get or create POD2000 instance"""
    global pod_instance
    if pod_instance is None:
        pod_instance = POD2000()
        pod_instance.open()
    return pod_instance

# ============================================================================
# Luna POD2000 Polarimeter Tools
# ============================================================================
@mcp.tool()
async def pod_get_idn() -> str:
    """
    Get the POD2000 polarimeter identification string containing manufacturer, model, serial number, and firmware version.
    
    Returns:
      Device identification string in standard SCPI *IDN? format
    """
    try:
        pod = get_pod()
        idn = pod.idn()
        return f"POD2000 ID: {idn}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
async def pod_configure(
    wavelength_nm: float = 1060.0,
    gain: str = "AUTO",
    transfer: str = "MANUAL",
    power_unit: str = "UW"
) -> str:
    """
    Configure the POD2000 polarimeter measurement settings including wavelength, gain, transfer mode, and power unit.
    
    Args:
      wavelength_nm: Operating wavelength in nanometers (valid range: 1030-1090 nm). Must match the laser wavelength for accurate measurements.
      gain: Detector gain setting - GAIN1 (lowest) through GAIN5 (highest), UP/DOWN for incremental adjust, AUTO for automatic gain control, or OPTIMIZE for one-time optimization
      transfer: Data transfer mode - MANUAL (single measurement on command) or CONTINUOUS (continuous streaming)
      power_unit: Power measurement unit - UW (microwatts) or NW (nanowatts)
    
    Returns:
      Confirmation message with all applied settings and verified wavelength
    """
    try:
        pod = get_pod()
        pod.configure(wavelength_nm=wavelength_nm, gain=gain, transfer=transfer, power_unit=power_unit)
        wl_check = pod.get_wavelength()
        return f"POD2000 configured: {wavelength_nm} nm, gain={gain}, transfer={transfer}, unit={power_unit} (verified: {wl_check} nm)"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
async def pod_read_polarization() -> str:
    """
    Read the complete polarization state from POD2000 including degree of polarization, azimuth angle, and ellipticity angle.
    
    The measurement returns:
    - DOP (Degree of Polarization): 0.0 (unpolarized) to 1.0 (fully polarized)
    - Azimuth (psi): Orientation angle of polarization ellipse major axis, range -90 deg to +90 deg
    - Ellipticity (chi): Shape of polarization ellipse, range -45 deg (left circular) to +45 deg (right circular), 0 deg = linear
    
    Returns:
      Formatted string with DOP, azimuth angle in degrees, and ellipticity angle in degrees
    """
    try:
        pod = get_pod()
        dop, psi_deg, chi_deg = pod.read_pol()
        return f"DOP: {dop:.4f}, Azimuth: {psi_deg:.2f} deg, Ellipticity: {chi_deg:.2f} deg"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
async def pod_read_power() -> str:
    """
    Read the optical power measurement from POD2000 in the currently configured unit (microwatts or nanowatts).
    
    Power reading depends on:
    - Current gain setting (affects sensitivity and range)
    - Configured power unit (UW or NW)
    - Wavelength calibration setting
    
    Returns:
      Power value in the unit configured in the device (use pod_configure to set unit)
    """
    try:
        pod = get_pod()
        power = pod.read_power()
        return f"Power: {power:.3f}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
async def pod_read_stokes() -> str:
    """
    Read raw Stokes parameters (S0, S1, S2, S3) and power from POD2000.
    
    Stokes parameters represent the complete polarization state:
    - S0: Total intensity (always positive)
    - S1: Horizontal vs vertical linear polarization (+ = horizontal, - = vertical)
    - S2: +45 deg vs -45 deg linear polarization (+ = +45 deg, - = -45 deg)
    - S3: Right vs left circular polarization (+ = right circular, - = left circular)
    - Power: Same as pod_read_power(), in configured units
    
    The normalized Stokes vector (S1/S0, S2/S0, S3/S0) defines a point on the Poincaré sphere.
    DOP = sqrt(S1² + S2² + S3²) / S0
    
    Returns:
      All five raw measurement values (S0, S1, S2, S3, Power)
    """
    try:
        pod = get_pod()
        S0, S1, S2, S3, power = pod.read_raw5()
        return f"S0: {S0:.4f}, S1: {S1:.4f}, S2: {S2:.4f}, S3: {S3:.4f}, Power: {power:.3f}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
async def pod_set_wavelength(wavelength_nm: float) -> str:
    """
    Set only the POD2000 operating wavelength without changing other configuration settings.
    
    This is a quick configuration command that updates wavelength while preserving current gain, transfer mode, and power unit settings.
    The wavelength must match your laser source for accurate polarization measurements due to wavelength-dependent detector response.
    
    Args:
      wavelength_nm: Operating wavelength in nanometers (valid range: 1030-1090 nm)
    
    Returns:
      Confirmation message with the verified wavelength setting from the device
    """
    try:
        pod = get_pod()
        pod.scpi(f":CONF:WAVElength {wavelength_nm:.4f}", expect_reply=False)
        wl_check = pod.get_wavelength()
        return f"Wavelength set to {wl_check} nm"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
async def pod_close() -> str:
    """
    Close the USB connection to the POD2000 polarimeter and release system resources.
    
    This should be called when finished with measurements or before reconnecting to the device.
    The connection will automatically reopen on the next measurement command if needed.
    
    Returns:
      Confirmation message indicating connection status
    """
    global pod_instance
    try:
        if pod_instance is not None:
            pod_instance.close()
            pod_instance = None
            return "Successfully closed POD2000 connection"
        else:
            return "POD2000 connection already closed"
    except Exception as e:
        import traceback
        return f"Error closing POD2000: {str(e)}\n{traceback.format_exc()}"

if __name__ == "__main__":
	# Initialize and run the server
	mcp.run(transport='stdio')
