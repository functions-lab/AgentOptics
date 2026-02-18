from __future__ import annotations
import math, time, csv
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional, Dict

import pandas as pd
import matplotlib.pyplot as plt

def _iclamp(v: int, lo: int, hi: int) -> int:
    return lo if v < lo else hi if v > hi else v

def _set_all_codes(piezo, codes: List[int], settle_s: float) -> None:
    t0 = time.perf_counter()
    for ch in range(4):
        piezo.send_piezo_code(ch + 1, _iclamp(int(codes[ch]), 0, 4095))
    time.sleep(settle_s)
    dt = time.perf_counter() - t0
    print(f"    [TIMING] _set_all_codes: {dt*1000:.1f} ms (settle={settle_s*1000:.1f} ms)")

def _set_one_code(piezo, channel, code, settle_s):
    t0 = time.perf_counter()
    piezo.send_piezo_code(channel, _iclamp(int(code), 0, 4095))
    time.sleep(settle_s)
    dt = time.perf_counter() - t0
    print(f"    [TIMING] _set_one_code ch={channel}: {dt*1000:.1f} ms (settle={settle_s*1000:.1f} ms)")

def _dist_ang(target_angles, meas):
    def angdiff_deg(a, b, period=180.0):
        d = (a - b) % period
        return d - period if d > period/2 else d
    if len(target_angles) == 3:
        _, tp, tc = target_angles
    else:
        tp, tc = target_angles
    _, mp, mc = meas
    dpsi = angdiff_deg(mp, tp, 180.0)
    dchi = angdiff_deg(mc, tc, 180.0)
    return math.hypot(dpsi, dchi)

def _ensure_csv(path: Path) -> None:
    with path.open("w", newline="") as f:
        csv.writer(f).writerow([
            "event", "channel",
            "time",
            "target_dop","target_psi","target_chi",
            "curr_dop","curr_psi","curr_chi",
            "distance","step_codes","c1","c2","c3","c4",
            "read_latency_us",
        ])

def _append_csv(path: Path,
                event: str,
                channel: int,
                target: Tuple[float, float, float],
                current: Tuple[float, float, float],
                distance: float,
                step_codes: int,
                codes: List[int],
                read_latency_us: float = float("nan"), 
                ) -> None:
    with path.open("a", newline="") as f:
        csv.writer(f).writerow([
            event, int(channel),
            datetime.now().isoformat(timespec="microseconds"),
            f"{target[0]:.6f}", f"{target[1]:.3f}", f"{target[2]:.3f}",
            f"{current[0]:.6f}", f"{current[1]:.3f}", f"{current[2]:.3f}",
            f"{distance:.6f}", int(step_codes),
            int(codes[0]), int(codes[1]), int(codes[2]), int(codes[3]),
            f"{read_latency_us:.1f}",
        ])

def run_control_single_beam(
    arduino,
    pod,
    target,
    *,
    steps_codes=(256, 128, 32, 8, 2), 
    thresh=(30.0, 15.0, 5.0, 2.0, 0.5),
    stop_threshold=0.5,
    settle_s=0.01,
    init_code=2048,
    min_code=0,
    max_code=4095,
    max_rounds=400,
    log_path: Optional[str] = None,
    reset_log: bool = True,
    verbose_timing: bool = False,
) -> Dict[str, object]:
    
    if len(steps_codes) != len(thresh):
        raise ValueError("steps_codes and thresh must have the same length")

    if len(target) == 2:
        tp, tc = map(float, target)
        td = float("nan")
        target_full = (td, tp, tc)
    elif len(target) == 3:
        td, tp, tc = map(float, target)
        target_full = (td, tp, tc)
    else:
        raise ValueError("Invalid target format.")

    piezo = arduino.piezo

    stored = [_iclamp(init_code, min_code, max_code)] * 4
    _set_all_codes(piezo, stored, settle_s)

    csv_path = Path(log_path) if log_path else None

    def log(event, channel, pol, dist, latency_us):
        if csv_path:
            _append_csv(csv_path, event, channel,
                        target_full, pol, dist, step_now, stored,
                        read_latency_us=latency_us)

    if csv_path:
        if reset_log and csv_path.exists():
            csv_path.unlink()
        _ensure_csv(csv_path)
        t0 = time.perf_counter()
        p0 = pod.read_pol()
        dt_init = (time.perf_counter() - t0) * 1e6
        _append_csv(csv_path, "init", 0, target_full, p0, _dist_ang(target_full, p0), 0, stored,
                    read_latency_us=dt_init)

    step_idx = 0
    for rnd in range(1, max_rounds + 1):
        round_t0 = time.perf_counter()
        step_now = int(steps_codes[step_idx])

        t0 = time.perf_counter()
        baseline_pol = pod.read_pol()
        dt_baseline = (time.perf_counter() - t0) * 1e6
        baseline_err = _dist_ang(target_full, baseline_pol)
        if verbose_timing:
            print(f"  [TIMING] Baseline read: {dt_baseline:.1f} us")
        log("baseline", 0, baseline_pol, baseline_err, dt_baseline)

        t0_sweep = time.perf_counter()
        for ch in range(4):
            if verbose_timing:
                print(f"  [Ch {ch+1}]")

            plus = stored[:]
            plus[ch] = _iclamp(plus[ch] + step_now, min_code, max_code)
            _set_one_code(piezo, ch+1, plus[ch], settle_s)

            t0 = time.perf_counter()
            pol_plus = pod.read_pol()
            dt_read = (time.perf_counter() - t0) * 1e6
            if verbose_timing:
                print(f"    [TIMING] Read (+): {dt_read:.1f} us")
            d_plus = _dist_ang(target_full, pol_plus)
            log("probe_plus", ch+1, pol_plus, d_plus, dt_read)

            minus = stored[:]
            minus[ch] = _iclamp(minus[ch] - step_now, min_code, max_code)
            _set_one_code(piezo, ch+1, minus[ch], settle_s)

            t0 = time.perf_counter()
            pol_minus = pod.read_pol()
            dt_read = (time.perf_counter() - t0) * 1e6
            if verbose_timing:
                print(f"    [TIMING] Read (-): {dt_read:.1f} us")
            d_minus = _dist_ang(target_full, pol_minus)
            log("probe_minus", ch+1, pol_minus, d_minus, dt_read)

            _set_all_codes(piezo, stored, settle_s)

            if d_plus < baseline_err:
                stored[ch] = plus[ch]
                _set_one_code(piezo, ch+1, stored[ch], settle_s)
                t0 = time.perf_counter()
                baseline_pol = pod.read_pol()
                dt_read = (time.perf_counter() - t0) * 1e6
                if verbose_timing:
                    print(f"    [TIMING] Read (update+): {dt_read:.1f} us")
                baseline_err = _dist_ang(target_full, baseline_pol)
                log("accept_plus", ch+1, baseline_pol, baseline_err, dt_read)
            elif d_minus < baseline_err:
                stored[ch] = minus[ch]
                _set_one_code(piezo, ch+1, stored[ch], settle_s)
                t0 = time.perf_counter()
                baseline_pol = pod.read_pol()
                dt_read = (time.perf_counter() - t0) * 1e6
                if verbose_timing:
                    print(f"    [TIMING] Read (update-): {dt_read:.1f} us")
                baseline_err = _dist_ang(target_full, baseline_pol)
                log("accept_minus", ch+1, baseline_pol, baseline_err, dt_read)

        dt_sweep = (time.perf_counter() - t0_sweep) * 1e6
        if verbose_timing:
            print(f"  [TIMING] Total 4-channel sweep: {dt_sweep:.1f} us")

        _set_all_codes(piezo, stored, settle_s)
        t0 = time.perf_counter()
        pol_after = pod.read_pol()
        dt_eval = (time.perf_counter() - t0) * 1e6
        err_after = _dist_ang(target_full, pol_after)
        if verbose_timing:
            print(f"  [TIMING] Final eval read: {dt_eval:.1f} us")

        dt_round = (time.perf_counter() - round_t0) * 1e6
        print(
            f"[round {rnd:03d}] step={step_now}"
            f" | target=(DoP N/A, {target_full[1]:.3f}, {target_full[2]:.3f})"
            f" | current=({pol_after[0]:.6f}, {pol_after[1]:.3f}, {pol_after[2]:.3f})"
            f" | ang_err_deg={err_after:.6f}"
            f" | codes={stored}"
            f" | ROUND TIME: {dt_round:.0f} us"
        )
        log("round_eval", 0, pol_after, err_after, dt_eval)

        if err_after < stop_threshold:
            return {"converged": True,
                    "final_distance_deg": err_after,
                    "final_pol": pol_after,
                    "final_codes": stored[:]}

        if err_after < thresh[step_idx] and step_idx < len(steps_codes) - 1:
            step_idx += 1

    final_pol = pod.read_pol()
    return {"converged": False,
            "final_distance_deg": _dist_ang(target_full, final_pol),
            "final_pol": final_pol,
            "final_codes": stored[:]}

def plot_time_vs_polarization(csv_path: str,
    *,
    title_prefix: str = "Polarization vs Time",
    save_dir: Optional[str] = None,
    show: bool = True
) -> Dict[str, Tuple[plt.Figure, plt.Axes]]:

    df = pd.read_csv(csv_path)
    df["_t"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(subset=["_t"]).reset_index(drop=True)
    x_sec = (df["_t"] - df["_t"].iloc[0]).dt.total_seconds()

    target_azimuth = float(df["target_psi"].iloc[0])
    target_ellipticity = float(df["target_chi"].iloc[0])
    curr_azimuth = df["curr_psi"].copy()
    curr_ellipticity = df["curr_chi"].copy()

    def wrap_to_near(series, ref):
        d = (series - ref) % 180
        d[d > 90] -= 180
        return ref + d

    curr_azimuth = wrap_to_near(curr_azimuth, target_azimuth)
    curr_ellipticity = wrap_to_near(curr_ellipticity, target_ellipticity)

    if save_dir:
        Path(save_dir).mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(x_sec, [target_azimuth]*len(x_sec), linestyle="--", linewidth=1.0, label="Target Azimuth (deg)")
    ax.plot(x_sec, [target_ellipticity]*len(x_sec), linestyle="--", linewidth=1.0, label="Target Ellipticity (deg)")
    ax.plot(x_sec, curr_azimuth, linewidth=1.5, label="Current Azimuth (deg)")
    ax.plot(x_sec, curr_ellipticity, linewidth=1.5, label="Current Ellipticity (deg)")

    ax.set_title(f"{title_prefix} — Azimuth & Ellipticity")
    ax.set_xlabel("Elapsed Time (s)")
    ax.set_ylabel("Degrees")
    ax.legend()
    ax.grid(True, linestyle="--", linewidth=0.6)
    fig.tight_layout()

    if save_dir:
        fig.savefig(Path(save_dir) / "azimuth_ellipticity_time.png", dpi=150)
    if show:
        plt.show()

    return {"azimuth_ellipticity": (fig, ax)}