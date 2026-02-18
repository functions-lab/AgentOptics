# pod2000.py
import time
import math
import usb.core
import usb.util
import usb.backend.libusb1

class POD2000:
    def __init__(
        self,
        dll_path=r"YOUR_PATH",
        vid=0x0E33,
        pid=0xC001,
        iface=(0, 0),                 # (interface_number, alt_setting)
        timeout_ms=1000,
        pkt_size=512,
        mapped_mode="STOKES",         # "STOKES" or "DIRECT"
    ):
        self.vid = vid
        self.pid = pid
        self.ifnum, self.alt = iface
        self.timeout = timeout_ms
        self.pkt_size = pkt_size
        self.mapped_mode = mapped_mode.upper()

        # backend (Windows: pin to DLL; set to None to rely on PATH)
        self.backend = usb.backend.libusb1.get_backend(find_library=lambda _: dll_path) if dll_path else None

        self.dev = None
        self.cfg = None
        self.intf = None
        self.ep_out = None  # 0x01
        self.ep_in  = None  # 0x81

    # --- open / close ---
    def open(self):
        self.dev = usb.core.find(idVendor=self.vid, idProduct=self.pid, backend=self.backend)
        if self.dev is None:
            raise RuntimeError("POD2000 not found")

        try:
            self.dev.set_configuration()
        except usb.core.USBError:
            pass

        self.cfg = self.dev.get_active_configuration()
        self.intf = self.cfg[(self.ifnum, self.alt)]

        # fixed endpoints to match your existing script
        self.ep_out = usb.util.find_descriptor(self.intf, bEndpointAddress=0x01)
        self.ep_in  = usb.util.find_descriptor(self.intf, bEndpointAddress=0x81)
        if self.ep_out is None or self.ep_in is None:
            raise RuntimeError("Bulk endpoints 0x01/0x81 not found")

    def close(self):
        try:
            if self.dev is not None:
                usb.util.dispose_resources(self.dev)
        finally:
            self.dev = self.cfg = self.intf = self.ep_out = self.ep_in = None

    # --- SCPI helpers ---
    def scpi(self, cmd: str, expect_reply=True):
        if not (self.ep_out and self.ep_in):
            raise RuntimeError("Device not open")
        self.ep_out.write((cmd + "\n").encode("ascii"), timeout=self.timeout)
        if expect_reply:
            data = self.ep_in.read(self.pkt_size, timeout=self.timeout).tobytes()
            return data.decode("ascii", errors="ignore").strip()
        return None

    def idn(self) -> str:
        return self.scpi("*IDN?") or ""
    
    def get_wavelength(self) -> str:
        return self.scpi(":CONFigure:WAVElength?") or ""

    def configure(self, *, wavelength_nm=1060.0, gain="AUTO", transfer="MANUAL", power_unit="UW"):
        # normalize
        t = str(transfer).strip().upper()
        g = str(gain).strip().upper()
        u = str(power_unit).strip().upper()

        #  validation
        if t not in {"MANUAL", "CONTINUOUS"}:
            raise ValueError("transfer must be MANUAL or CONTINUOUS")
        try:
            w = float(wavelength_nm)
        except Exception:
            raise ValueError("wavelength_nm must be a number")
        if not (1030.0 <= w <= 1090.0): 
            raise ValueError("wavelength_nm out of reasonable range (1200–1700 nm)")
        allowed_gain = {"GAIN1","GAIN2","GAIN3","GAIN4","GAIN5","UP","DOWN","AUTO","OPTIMIZE"}
        if g not in allowed_gain:
            raise ValueError("gain must be one of GAIN1..GAIN5, UP, DOWN, AUTO, OPTIMIZE")
        if u not in {"UW","NW"}:
            raise ValueError("power_unit must be UW or NW")

        self.scpi(f":CONF:TRANSfer {'MANual' if t=='MANUAL' else 'CONTinuous'}", expect_reply=False)
        self.scpi(f":CONF:WAVElength {w:.4f}", expect_reply=False)
        self.scpi(f":CONF:GAIN {'OPTImize' if g=='OPTIMIZE' else g}", expect_reply=False)
        self.scpi(f":UNIT:POWer {u}", expect_reply=False)
        time.sleep(0.1)

    # --- reading ---
    @staticmethod
    def _parse_read_value(raw: str):
        if raw is None:
            raise ValueError("Empty reply")
        # print(raw)
        s = raw.strip().strip('"').strip("'")
        parts = [p.strip() for p in s.split(",")]
        if len(parts) != 5:
            raise ValueError(f"Expected 5 values, got {len(parts)}: {parts}")
        try:
            v1, v2, v3, v4, v5 = (float(p) for p in parts)
        except ValueError as e:
            raise ValueError(f"Non-numeric field in reply: {parts}") from e
        return v1, v2, v3, v4, v5

    def read_raw5(self):
        raw = self.scpi(":READ:VALue?")
        return self._parse_read_value(raw)

    def read_pol(self):
        S0, S1, S2, S3, _power = self.read_raw5()

        EPS = 1e-12
        S0c = S0 if abs(S0) > EPS else EPS

        # Sphere-normalized Stokes and DOP (per manual Appendix A)
        Snorm = (S1*S1 + S2*S2 + S3*S3) ** 0.5
        if Snorm < EPS:
            # Undefined azimuth/ellipticity if no polarized component
            return 0.0, 0.0, 0.0

        s1, s2, s3 = S1 / Snorm, S2 / Snorm, S3 / Snorm
        dop = Snorm / S0c

        # Azimuth psi and ellipticity angle chi (in radians)
        psi_rad = 0.5 * math.atan2(s2, s1)   # uses normalized s1,s2
        # s3c = -1.0 if s3 < -1.0 else (1.0 if s3 > 1.0 else s3)
        # chi_rad = 0.5 * math.asin(s3c)       # uses normalized s3
        chi_rad = 0.5 * math.atan2(s3, (s1*s1 + s2*s2) ** 0.5)

        # Convert to degrees; wrap psi into (-90, 90]
        psi_deg = math.degrees(psi_rad)
        if psi_deg <= -90.0:
            psi_deg += 180.0
        if psi_deg > 90.0:
            psi_deg -= 180.0

        chi_deg = math.degrees(chi_rad)
        return dop, psi_deg, chi_deg

    def read_power(self):
        _S0, _S1, _S2, _S3, power = self.read_raw5()
        power_f = float(power)
        return power_f

