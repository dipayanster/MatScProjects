import json
import os
import subprocess
import sys
from pathlib import Path
from ase.io import read, write

BASE_DIR = Path(__file__).resolve().parent
traj_dir = BASE_DIR / "training_dataset"   # folder with *.xyz
config_file = BASE_DIR / "GAP_config.json"
log_file = BASE_DIR / "GAP_run.log"
merged_xyz = traj_dir / "merged_train.xyz"

# 1. Load configuration
with open(config_file) as f:
    cfg = json.load(f)

gap_cfg = cfg["gap_fit"]
key_cfg = cfg["keys"]
out_cfg = cfg["output"]

# 2. Glob and merge all source .xyz files into training_dataset/merged_train.xyz
xyz_files = sorted(f for f in traj_dir.glob("*.xyz") if f.name != merged_xyz.name)
if not xyz_files:
    sys.exit(f"No .xyz files found in {traj_dir}. Run traj2xyz.py first.")

frames = [atom for f in xyz_files for atom in read(f, index=":")]
merged_xyz.with_suffix(".xyz.idx").unlink(missing_ok=True)
write(merged_xyz, frames, format="extxyz")
print(f"Merged {len(frames)} frames from {len(xyz_files)} files -> {merged_xyz}")

# 3. Assemble gap_fit command (energy + forces only)
cmd = [
    "gap_fit",
    f"at_file={merged_xyz}",
    f"gap={gap_cfg['gap']}",
    f"default_sigma={gap_cfg['default_sigma']}",
    f"e0={gap_cfg['e0']}",
    f"energy_parameter_name={key_cfg['energy']}",
    f"force_parameter_name={key_cfg['forces']}",
    "virial_parameter_name=IGNORE_VIRIAL",
    "stress_parameter_name=IGNORE_STRESS",
    f"gp_file={out_cfg['gp_file']}",
]

print(f"Running: {' '.join(cmd)}")
print(f"Logging to: {log_file.resolve()}")

# 4. Execute with OpenMP multi-threading and log
env = os.environ.copy()
env["PYTHONUNBUFFERED"] = "1"
env.setdefault("OMP_NUM_THREADS", str(os.cpu_count() or 4))

with open(log_file, "w", buffering=1) as log:
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
        cwd=BASE_DIR,
    )
    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
        log.write(line)
    proc.wait()

sys.exit(proc.returncode)
