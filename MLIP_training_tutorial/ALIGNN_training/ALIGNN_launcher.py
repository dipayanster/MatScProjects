import json
import os
import subprocess
import sys
from pathlib import Path

# paths
BASE_DIR = Path(__file__).resolve().parent

root_dir = BASE_DIR / "training_dataset"   # folder with per-site *.json
config   = BASE_DIR / "ALIGNN_config.json" # ALIGNN config (pre-written)
out_dir  = BASE_DIR / "ALIGNN_out"         # ALIGNN training output folder
log_file = BASE_DIR / "ALIGNN_run.log"     # stdout+stderr tee

# isolated-atom reference energies (eV), keyed by element symbol
# E0-subtraction done while merging
E0 = {
    "C":  -241.907386,
    "Hg": -10952.046782,
}

# 1. merge per-site JSONs
entries = []
for f in sorted(root_dir.glob("*.json")):
    if f.name == "id_prop.json":
        continue
    with open(f) as fh:
        for e in json.load(fh):
            els = e["atoms"]["elements"]
            n = len(els)
            e_ref = sum(E0[el] for el in els)
            e_total = e["energy_per_atom"] * n
            e["energy_per_atom"] = (e_total - e_ref) / n
            entries.append(e)
with open(root_dir / "id_prop.json", "w") as fh:
    json.dump(entries, fh, indent=2)
print(f"Merged {len(entries)} frames (E0-subtracted) -> {root_dir / 'id_prop.json'}")

# 2. launch ALIGNN training
cmd = [
    "train_alignn.py",
    "--root_dir", str(root_dir),
    "--config", str(config),
    "--output_dir", str(out_dir),
    "--target_key", "energy_per_atom",
    "--force_key", "forces",
    "--id_key", "jid",
]
print(f"Running: {' '.join(cmd)}")
print(f"Logging to: {log_file.resolve()}")

# 3. logging
env = os.environ.copy()
env["PYTHONUNBUFFERED"] = "1"

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