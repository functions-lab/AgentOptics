from typing import Any, Optional, Dict, Union, Literal
import logging, sys, re, asyncio, os, subprocess
from mcp.server.fastmcp import FastMCP
from matplotlib import pyplot as plt
from pathlib import Path
import pandas as pd
from POD2000 import POD2000
from arduino_ctrl import ArduinoController
from control_single_beam_module import run_control_single_beam

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

def get_arduino():
    """Get or create Arduino controller instance"""
    global arduino_instance
    if arduino_instance is None:
        arduino_instance = ArduinoController(port="COM5", baudrate=115200)
    return arduino_instance

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

# ============================================================================
# Piezo Control Tools
# ============================================================================

@mcp.tool()
async def piezo_reset() -> str:
    """
    Perform hardware reset of the piezo DAC chip.
    
    This resets all 4 channels to their default state and clears any previous settings.
    Use this to recover from error states or initialize the DAC at startup.
    
    Returns:
      Confirmation message
    """
    try:
        arduino = get_arduino()
        arduino.piezo.reset_piezo()
        return "Piezo DAC reset completed successfully"
    except Exception as e:
        return f"Error resetting piezo DAC: {str(e)}"

@mcp.tool()
async def piezo_set_code(channel: int, code: int) -> str:
    """
    Set a single piezo channel to a raw 12-bit DAC code.
    
    Direct code control provides precise digital output without voltage conversion.
    Useful for calibration, testing, or when exact digital values are required.
    
    Args:
      channel: Channel number (1-4)
      code: DAC code (0-4095), automatically clamped to valid range if out of bounds
    
    Returns:
      Confirmation with channel number and actual code written (after clamping)
    """
    try:
        arduino = get_arduino()
        actual_code = arduino.piezo.send_piezo_code(channel, code)
        return f"Channel {channel} set to code {actual_code}"
    except Exception as e:
        return f"Error setting piezo code: {str(e)}"

@mcp.tool()
async def piezo_set_voltage(channel: int, voltage: float) -> str:
    """
    Set a single piezo channel to a specified voltage (0-5V).
    
    Voltage is converted to a 12-bit DAC code internally. The DAC reference voltage is 5.0V,
    so code 4095 = 5.0V, code 2048 ≈ 2.5V, etc. Input voltages are clamped to [0, 5.0]V.
    
    Args:
      channel: Channel number (1-4)
      voltage: Desired voltage (0.0-5.0V), automatically clamped if out of range
    
    Returns:
      Confirmation with channel, actual voltage set, and corresponding DAC code
    """
    try:
        arduino = get_arduino()
        code = arduino.piezo.send_piezo_voltage(channel, voltage)
        actual_voltage = (code / 4095) * arduino.piezo.vref
        return f"Channel {channel} set to {actual_voltage:.4f}V (code {code})"
    except Exception as e:
        return f"Error setting piezo voltage: {str(e)}"

# ============================================================================
# TTL Signal Tools
# ============================================================================

@mcp.tool()
async def ttl_read_active_beam() -> str:
    """
    Read which beam is currently active in the dual-beam optical system based on TTL signal state.
    
    The TTL input (Arduino pin D2) decodes the beam selector:
    - TTL HIGH (5V) = Beam 1 is active
    - TTL LOW (0V) = Beam 2 is active
    
    This is used in time-multiplexed dual-beam polarization control systems where two beams
    are alternated and controlled independently using the same hardware.
    
    Returns:
      "Active beam: Beam 1" or "Active beam: Beam 2"
    """
    try:
        arduino = get_arduino()
        beam_number = arduino.ttl.read_active_beam()
        return f"Active beam: Beam {beam_number}"
    except Exception as e:
        return f"Error reading TTL signal: {str(e)}"

# ============================================================================
# System Tools
# ============================================================================

@mcp.tool()
async def arduino_close() -> str:
    """
    Close the serial connection to the Arduino controller and release system resources.
    
    This terminates communication with the Arduino Mega and closes the COM port.
    Call this when finished with all measurements or before reconnecting.
    The connection will automatically reopen on the next command if needed.
    
    Returns:
      Confirmation message indicating connection status
    """
    global arduino_instance
    try:
        if arduino_instance is not None:
            arduino_instance.close()
            arduino_instance = None
            return "Successfully closed Arduino connection"
        else:
            return "Arduino connection already closed"
    except Exception as e:
        return f"Error closing Arduino connection: {str(e)}"

# ============================================================================
# Polarization Stabilization Tools
# ============================================================================

@mcp.tool()
async def polarization_stabilize(
    target_azimuth_deg: float,
    target_ellipticity_deg: float,
    wavelength_nm: float = 1060.0,
    stop_threshold_deg: float = 0.5,
    max_rounds: int = 400,
    settle_time_sec: float = 0.01,
    init_code: int = 2048,
    log_filepath: str = "./polarization_control_mcp_2.csv",
    reset_log: bool = True
) -> dict:
    """
    Run single-beam polarization stabilization using piezo feedback control.
    
    This implements a multi-stage gradient descent algorithm that adjusts 4 piezo
    voltages to minimize angular distance from target polarization state.
    
    Algorithm: Uses coarse-to-fine step sizes (256->128->64->32->8->2 DAC codes).
    For each round, tests +/- steps on each of 4 channels, moves to better position
    if improvement found, automatically reduces step size as error decreases.
    
    All measurement data is saved to CSV for later plotting/analysis.
    
    Args:
      target_azimuth_deg: Target azimuth angle psi in degrees, range [-90, +90]
      target_ellipticity_deg: Target ellipticity angle chi in degrees, range [-45, +45]
      wavelength_nm: POD2000 wavelength setting in nm (range: 1030-1090). Default 1060.0
      stop_threshold_deg: Convergence threshold (angular error in degrees). Default 0.5 deg
      max_rounds: Maximum optimization rounds. Default 400
      settle_time_sec: Piezo settling time after voltage change. Default 0.01s
      init_code: Initial DAC code for all channels (0-4095). Default 2048
      log_filepath: CSV file path to log all measurements. Default "./polarization_control_mcp.csv"
      reset_log: If True, delete existing log file before starting. Default True
    
    Returns:
      dict: {
        "status": "converged" | "max_rounds_reached",
        "converged": bool,
        "final_error_deg": float,
        "final_dop": float,
        "final_azimuth_deg": float,
        "final_ellipticity_deg": float,
        "final_piezo_codes": [int, int, int, int],
        "rounds_executed": int,
        "log_file": str
      }
    
    CSV columns saved:
      time, target_dop, target_psi, target_chi, curr_dop, curr_psi, curr_chi,
      distance, step_codes, c1, c2, c3, c4
    
    Example:
      # Stabilize to linear horizontal (Az=0 deg, Ell=0 deg)
      result = await polarization_stabilize(0.0, 0.0)
      
      # Stabilize at 1090nm wavelength
      result = await polarization_stabilize(0.0, -45.0, wavelength_nm=1090.0)
    """
    try:
        arduino = get_arduino()
        pod = get_pod()
        
        # Configure POD with specified wavelength
        pod.configure(wavelength_nm=wavelength_nm, gain="AUTO", transfer="MANUAL", power_unit="UW")
        
        # Run control algorithm
        result = await asyncio.to_thread(
            run_control_single_beam,
            arduino,
            pod,
            (target_azimuth_deg, target_ellipticity_deg),
            steps_codes=(256, 128, 64, 32, 8, 2),
            thresh=(40.0, 25.0, 15.0, 5.0, 2.0, 0.5),
            stop_threshold=stop_threshold_deg,
            settle_s=settle_time_sec,
            init_code=init_code,
            min_code=0,
            max_code=4095,
            max_rounds=max_rounds,
            log_path=log_filepath,
            reset_log=reset_log,
        )
        
        # Format return value
        converged = result["converged"]
        final_pol = result["final_pol"]
        
        return {
            "status": "converged" if converged else "max_rounds_reached",
            "converged": converged,
            "final_error_deg": float(result["final_distance_deg"]),
            "final_dop": float(final_pol[0]),
            "final_azimuth_deg": float(final_pol[1]),
            "final_ellipticity_deg": float(final_pol[2]),
            "final_piezo_codes": [int(c) for c in result["final_codes"]],
            "log_file": log_filepath
        }
        
    except Exception as e:
        import traceback
        logger.exception("Polarization stabilization failed")
        return {
            "status": "error",
            "converged": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

if __name__ == "__main__":
	# Initialize and run the server
	mcp.run(transport='stdio')
