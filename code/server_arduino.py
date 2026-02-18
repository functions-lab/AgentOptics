from typing import Any, Optional, Dict, Union, Literal
import logging, sys, re, asyncio, os, subprocess
from mcp.server.fastmcp import FastMCP
from matplotlib import pyplot as plt
from pathlib import Path
import pandas as pd
from arduino_ctrl import ArduinoController

logger = logging.getLogger(__name__)

pod_instance = None
arduino_instance = None

# Initialize FastMCP server
mcp = FastMCP("opticsMCP")

def get_arduino():
    """Get or create Arduino controller instance"""
    global arduino_instance
    if arduino_instance is None:
        arduino_instance = ArduinoController(port="COM5", baudrate=115200)
    return arduino_instance

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

if __name__ == "__main__":
	# Initialize and run the server
	mcp.run(transport='stdio')
