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
from ARoF_transceiver import *

logger = logging.getLogger(__name__)

arof_address = "YOUR_ADDR"

# Initialize FastMCP server
mcp = FastMCP("opticsMCP")

# Helper function
C_M_PER_S = 299_792_458.0  # exact, m/s

def nm_to_ghz(l_nm: float) -> float:
	return C_M_PER_S / (l_nm * 1e-9) / 1e9

def ghz_to_nm(f_ghz: float) -> float:
	return C_M_PER_S / (f_ghz * 1e9) * 1e9

# ============================================================================
# ARoF Tools
# ============================================================================
@mcp.tool()
async def arof_tx_read_info() -> str:
	"""
	Read raw ARoF transmitter (Tx) info (READ0) from the ARoF device.

	Returns:
	  Raw multi-line string from the device.
	"""
	tx = ARoF_transceiver(arof_address)
	s = tx.readInfo()
	tx.arof.close()
	return s

@mcp.tool()
async def arof_tx_read_output_power() -> str:
	"""
	Read ARoF transmitter (Tx) output power parsed from READ0.

	Returns:
	  "output_power=<value> dBm"
	"""
	tx = ARoF_transceiver(arof_address)
	val = tx.readOutputPower()  # float dBm
	tx.arof.close()
	return f"output_power={val} dBm"


@mcp.tool()
async def arof_tx_get_bias_voltage() -> str:
	"""
	Read ARoF transmitter (Tx) bias voltage (READ0B).

	Returns:
	  "bias_voltage=<value> V"
	"""
	tx = ARoF_transceiver(arof_address)
	val = tx.read_bias_vol()  # float V
	tx.arof.close()
	return f"bias_voltage={val} V"

@mcp.tool()
async def arof_tx_get_bias_current() -> str:
	"""
	Read ARoF transmitter (Tx) bias current (READ0C).

	Returns:
	  "bias_current=<value> mA"
	"""
	tx = ARoF_transceiver(arof_address)
	val = tx.read_bias_cur()  # int mA
	tx.arof.close()
	return f"bias_current={val} mA"


@mcp.tool()
async def arof_tx_set_bias_voltage(bias_v: float) -> str:
	"""
	Set ARoF transmitter (Tx) bias voltage (SET0B:<bias>) and return applied value.

	Args:
	  bias_v: Target bias voltage in volts.

	Returns:
	  "bias_voltage=<value> V"
	"""
	tx = ARoF_transceiver(arof_address)
	applied = tx.set_bias_vol(bias_v)  # float V (parsed from ack)
	tx.arof.close()
	return f"bias_voltage={applied} V"

@mcp.tool()
async def arof_tx_set_bias_current(bias_mA: int) -> str:
	"""
	Set ARoF transmitter (Tx) bias current (SET0C:<YYY>) and return applied value.

	Args:
	  bias_mA: Target current in mA (integer).

	Returns:
	  "bias_current=<value> mA"
	"""
	tx = ARoF_transceiver(arof_address)
	applied = tx.set_bias_cur(bias_mA)  # int mA (parsed from ack)
	tx.arof.close()
	return f"bias_current={applied} mA"

######################## main ########################
if __name__ == "__main__":
	# Initialize and run the server
	mcp.run(transport='stdio')
