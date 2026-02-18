from Arduino import Arduino
import time
from typing import Optional, Dict, List

class ArduinoController:
    """
    Multi-function Arduino Mega controller that manages:
    - 4-channel piezo DAC control (20 pins)
    - TTL signals: beam switching + QKD protocol (3 pins total)
    """
    
    def __init__(self, port: str = "COM5", baudrate: int = 115200):
        """
        Initialize Arduino controller with all subsystems.
        
        Args:
            port: Serial port for Arduino connection
            baudrate: Serial communication speed
        """
        self.board = Arduino(baudrate, port=port)
        self.piezo = PiezoInterface(self.board)
        self.ttl = TTLInterface(self.board)
    
    def close(self):
        """Close the Arduino serial connection."""
        self.board.close()


class PiezoInterface:
    """
    Interface for 4-channel DAC control of piezoelectric actuators.
    Uses 20 Arduino pins for parallel DAC communication.
    """
    
    def __init__(self,
                 board: Arduino,
                 pins: Optional[Dict] = None,
                 vref: float = 5.0,
                 cs_pulse_s: float = 50e-9,
                 setup_s: float = 1e-9):
        """
        Initialize piezo DAC interface.
        
        Args:
            board: Arduino instance (shared with parent controller)
            pins: Pin mapping dict (uses defaults if None)
            vref: Reference voltage (maps 0..vref volts → 0..4095 code)
            cs_pulse_s: Chip select pulse width
            setup_s: Setup time before chip select
        """
        self.board = board
        self.pins = pins or {
            "RESET": 8,   # D8  -> RESET
            "RW":    6,   # D6  -> RW (LOW = write)
            "CS_N":  7,   # D7  -> /CS (active LOW)
            "A0":    4,   # D4  -> channel select bit 0
            "A1":    5,   # D5  -> channel select bit 1
            "DB":    [54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65],  # DB0..DB11 (LSB→MSB)
        }
        self.vref = float(vref)
        self.cs_pulse_s = float(cs_pulse_s)
        self.setup_s = float(setup_s)
        
        self._init_pins()
    
    def _init_pins(self):
        """Initialize all DAC control pins as outputs."""
        b, p = self.board, self.pins
        b.pinMode(p["RESET"], "OUTPUT")
        b.pinMode(p["RW"], "OUTPUT")
        b.pinMode(p["CS_N"], "OUTPUT")
        b.pinMode(p["A0"], "OUTPUT")
        b.pinMode(p["A1"], "OUTPUT")
        for pin in p["DB"]:
            b.pinMode(pin, "OUTPUT")
        
        # Set idle state
        b.digitalWrite(p["RW"], "HIGH")      # write mode ready
        b.digitalWrite(p["CS_N"], "HIGH")    # chip not selected
        b.digitalWrite(p["RESET"], "HIGH")   # not in reset
    
    def _set_bits(self, ch_idx_0_3: int, code_12: int, *, verbose: bool = False):
        """
        Set address and data lines for DAC write.
        
        Args:
            ch_idx_0_3: Channel index (0-3)
            code_12: 12-bit DAC code (0-4095)
            verbose: Print debug info if True
        """
        b, p = self.board, self.pins
        
        # Channel select A1:A0
        a0 = "HIGH" if (ch_idx_0_3 & 1) else "LOW"
        a1 = "HIGH" if ((ch_idx_0_3 >> 1) & 1) else "LOW"
        b.digitalWrite(p["A0"], a0)
        b.digitalWrite(p["A1"], a1)
        
        if verbose:
            print(f"ch_idx={ch_idx_0_3} A1({p['A1']})={a1} A0({p['A0']})={a0}  "
                  f"code_12=0x{code_12:03X} ({code_12:012b})")
        
        # Data bus DB0..DB11 (LSB..MSB)
        for i, pin in enumerate(p["DB"]):
            bit = (code_12 >> i) & 1
            level = "HIGH" if bit else "LOW"
            b.digitalWrite(pin, level)
            if verbose:
                print(f"DB{i}({pin})={level}")
    
    def _latch(self):
        """Pulse chip select to latch data into DAC."""
        b, p = self.board, self.pins
        b.digitalWrite(p["RW"], "LOW")       # enter write window
        time.sleep(self.setup_s)             # setup time
        b.digitalWrite(p["CS_N"], "LOW")     # activate chip select
        time.sleep(self.cs_pulse_s)          # latch pulse
        b.digitalWrite(p["CS_N"], "HIGH")    # deactivate
        b.digitalWrite(p["RW"], "HIGH")      # exit write window
    
    def reset_piezo(self):
        """Hardware reset of the DAC chip."""
        b, p = self.board, self.pins
        b.digitalWrite(p["RESET"], "LOW")
        time.sleep(0.01)  # 10ms reset pulse
        b.digitalWrite(p["RESET"], "HIGH")

    def send_piezo_code(self, channel_1_4: int, code_0_4095: int, *, verbose: bool = False) -> int:
        """Fast piezo write using single Arduino command"""
        if channel_1_4 not in (1, 2, 3, 4):
            raise ValueError("Channel must be 1-4")
        
        code = int(code_0_4095)
        code = max(0, min(4095, code))
        
        if verbose:
            print(f"ch={channel_1_4} code={code} (0x{code:03X}, {code:012b})")
        
        # Use fast command: @fpw%{channel}%{code}$!
        cmd_str = f"@fpw%{channel_1_4-1}%{code}$!"
        self.board.sr.write(str.encode(cmd_str))
        self.board.sr.flush()
        
        return code
    
    def send_piezo_voltage(self, channel_1_4: int, voltage_0_5: float) -> int:
        """
        Set piezo channel by voltage (0..vref).
        
        Args:
            channel_1_4: Channel number (1-4)
            voltage_0_5: Desired voltage (0-vref), will be clamped
        
        Returns:
            The 12-bit code written to the DAC
        """
        if channel_1_4 not in (1, 2, 3, 4):
            raise ValueError("Channel must be 1-4")
        
        v = float(max(0.0, min(self.vref, voltage_0_5)))
        code = int(round((v / self.vref) * 4095))
        return self.send_piezo_code(channel_1_4, code)
    
    def set_all_codes(self, codes: List[int], settle_s: float = 0.01):
        """
        Set all 4 channels to specified codes.
        
        Args:
            codes: List of 4 DAC codes [ch1, ch2, ch3, ch4]
            settle_s: Settling time after all channels are set
        """
        if len(codes) != 4:
            raise ValueError("codes must be a list of 4 values")
        
        for ch in range(4):
            self.send_piezo_code(ch + 1, int(codes[ch]))
        time.sleep(settle_s)


class TTLInterface:
    """
    Interface for TTL signals.
    
    Pins:
    - BEAM_SWITCH (D2): Read which beam is active for dual-beam control
    - TTL_5 (D3): Bidirectional - typically input from DQC
    - TTL_14 (D9): Bidirectional - typically output to DQC
    
    All TTL pins support both read and write operations for flexibility.
    """
    
    def __init__(self, board: Arduino, pins: Optional[Dict] = None):
        """
        Initialize TTL interface.
        
        Args:
            board: Arduino instance (shared with parent controller)
            pins: Pin mapping dict (uses defaults if None)
        """
        self.board = board
        self.pins = pins or {
            "BEAM_SWITCH": 2,  # D2 (INT0) - Input: which beam is active
            "TTL_5":  3,       # D3 (INT1) - Input: from DQC
            "TTL_14": 9,       # D9 - Output: to DQC
        }
        self._init_pins()
    
    def _init_pins(self):
        """Initialize all TTL pins."""
        self.board.pinMode(self.pins["BEAM_SWITCH"], "INPUT")
        self.board.pinMode(self.pins["TTL_5"], "INPUT")
        self.board.pinMode(self.pins["TTL_14"], "OUTPUT")
        
        # Set TTL 14 to safe initial state (LOW)
        self.board.digitalWrite(self.pins["TTL_14"], "LOW")
    
    # ========================================================================
    # Dual-beam control
    # ========================================================================
    
    def read_active_beam(self) -> int:
        """
        Read which beam is currently active.
        
        Returns:
            1 if beam 1 is active (BEAM_SWITCH HIGH)
            2 if beam 2 is active (BEAM_SWITCH LOW)
        """
        state = self.board.digitalRead(self.pins["BEAM_SWITCH"])
        return 1 if state == 1 else 2
    
    # ========================================================================
    # TTL 14 - Bidirectional (output to DQC for detector state)
    # ========================================================================
    
    def set_ttl14(self, state: int):
        """
        Set TTL 14 output state.
        
        Args:
            state: 0 (LOW) or 1 (HIGH)
        """
        level = "HIGH" if state == 1 else "LOW"
        self.board.digitalWrite(self.pins["TTL_14"], level)
    
    def get_ttl14(self) -> int:
        """
        Read TTL 14 output state.
        
        Returns:
            0 (LOW) or 1 (HIGH)
        """
        return self.board.digitalRead(self.pins["TTL_14"])
    
    # ========================================================================
    # TTL 5 - Bidirectional (typically input from DQC for laser state)
    # ========================================================================
    
    def set_ttl5(self, state: int):
        """
        Set TTL 5 output state.
        
        Args:
            state: 0 (LOW) or 1 (HIGH)
        """
        level = "HIGH" if state == 1 else "LOW"
        self.board.digitalWrite(self.pins["TTL_5"], level)
    
    def get_ttl5(self) -> int:
        """
        Read TTL 5 input state.
        
        Returns:
            0 (LOW) or 1 (HIGH)
        """
        return self.board.digitalRead(self.pins["TTL_5"])