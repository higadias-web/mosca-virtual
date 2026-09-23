"""Roda a bateria de benchmarks da Fase 0 nos perfis de energia do KDE.

Cada medição roda num subprocesso próprio (RAM de pico isolada). Antes e depois de
cada uma, registra a frequência e a temperatura da CPU e o SwapFree.
Saída: bench/results/<tag>.jsonl

Uso:
  uv run python bench/run_all.py --profiles balanced performance --tag short
  uv run python bench/run_all.py --throttle-min 12 --profiles balanced performance
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "bench" / "results"
PP = ["org.freedesktop.UPower.PowerProfiles", "/org/freedesktop/UPower/PowerProfiles",
      "org.freedesktop.UPower.PowerProfiles", "ActiveProfile"]
ENV = dict(os.environ, MUJOCO_GL="egl", PYOPENGL_PLATFORM="egl")


def set_profile(p):
    subprocess.run(["busctl", "set-property", *PP, "s", p], check=True)
    time.sleep(5)


def sysinfo():
    def rd(path):
        try:
            return Path(path).read_text().strip()
        except OSError:
            return None
    freqs = [int(rd(f"/sys/devices/system/cpu/cpu{i}/cpufreq/scaling_cur_freq") or 0)
             for i in range(os.cpu_count())]
    temps = []
    for z in Path("/sys/class/hwmon").glob("hwmon*"):
        if rd(z / "name") == "coretemp":
            temps = [int(rd(t)) / 1000 for t in z.glob("temp*_input")]
    mem = dict(l.split(":") for l in Path("/proc/meminfo").read_text().splitlines())
    return dict(
        profile=subprocess.run(["busctl", "get-property", *PP], capture_output=True,
                               text=True).stdout.split()[-1].strip('"'),
        ac=rd("/sys/class/power_supply/AC/online"),
        no_turbo=rd("/sys/devices/system/cpu/intel_pstate/no_turbo"),
        freq_p_mhz=max(freqs[:4]) / 1000, freq_e_mhz=max(freqs[4:]) / 1000,
        temp_max_c=max(temps) if temps else None,
        swap_free_kb=int(mem["SwapFree"].split()[0]),
        mem_avail_kb=int(mem["MemAvailable"].split()[0]),
    )


def run(cmd, tag, out):
    pre = sysinfo()
    t = time.perf_counter()
    r = subprocess.run([sys.executable, *cmd], capture_output=True, text=True, env=ENV, cwd=ROOT)
    wall = time.perf_counter() - t
    post = sysinfo()
    line = next((l for l in reversed(r.stdout.splitlines()) if l.startswith("{")), None)
    rec = dict(cmd=" ".join(cmd), tag=tag, ok=r.returncode == 0 and line is not None,
               result=json.loads(line) if line else None, proc_wall_s=wall, pre=pre, post=post,
               swapped=post["swap_free_kb"] < pre["swap_free_kb"],
               stderr_tail=r.stderr[-800:] if r.returncode else "")
    out.write(json.dumps(rec) + "\n")
    out.flush()
    res = rec["result"] or {}
    print(f"[{pre['profile']}] {' '.join(cmd[1:]):60s} -> "
          f"{res.get('wall_per_sim_s', float('nan')):.3f} s/s, "
          f"RSS {res.get('peak_rss_mb', float('nan')):.0f} MB, swap={rec['swapped']}", flush=True)
    return rec


SHORT = [
    ["bench/bench_brain.py", "--engine", "numba-active", "--sim-ms", "2000"],
    ["bench/bench_brain.py", "--engine", "numba", "--sim-ms", "1000"],
    ["bench/bench_brain.py", "--engine", "numba-f32", "--sim-ms", "1000"],
    ["bench/bench_brain.py", "--engine", "numba-par", "--threads", "2", "--sim-ms", "1000"],
    ["bench/bench_brain.py", "--engine", "numpy", "--sim-ms", "500"],
    ["bench/bench_brain.py", "--engine", "torch", "--sim-ms", "500"],
    ["bench/bench_brain.py", "--engine", "torch", "--threads", "2", "--sim-ms", "500"],
    ["bench/bench_brain.py", "--engine", "brian2-runtime", "--sim-ms", "1000"],
    ["bench/bench_brain.py", "--engine", "brian2-cpp", "--sim-ms", "1000"],
    ["bench/bench_brain.py", "--engine", "brian2-cpp", "--threads", "2", "--sim-ms", "1000"],
    ["bench/bench_flygym.py", "--sim-s", "2"],
    ["bench/bench_flygym.py", "--sim-s", "1", "--vision-hz", "500"],
    ["bench/bench_flygym.py", "--sim-s", "1", "--vision-hz", "100"],
    ["bench/bench_worm.py", "--sim-s", "2", "--n-worms", "1"],
    ["bench/bench_worm.py", "--sim-s", "2", "--n-worms", "2"],
    ["bench/bench_full.py", "--sim-s", "2"],
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profiles", nargs="+", default=["balanced", "performance"])
    ap.add_argument("--tag", default="short")
    ap.add_argument("--throttle-min", type=float, default=0)
    args = ap.parse_args()
    RES.mkdir(parents=True, exist_ok=True)
    original = sysinfo()["profile"]
    try:
        with open(RES / f"{args.tag}.jsonl", "a") as out:
            for p in args.profiles:
                set_profile(p)
                if args.throttle_min:
                    # execução contínua: cenário completo em blocos de 20 s simulados
                    t_end = time.time() + 60 * args.throttle_min
                    i = 0
                    while time.time() < t_end:
                        run(["bench/bench_full.py", "--sim-s", "20"], f"throttle-{p}-{i}", out)
                        i += 1
                    time.sleep(120)  # esfria entre perfis
                else:
                    for cmd in SHORT:
                        run(cmd, f"{args.tag}-{p}", out)
    finally:
        set_profile(original)


if __name__ == "__main__":
    main()
