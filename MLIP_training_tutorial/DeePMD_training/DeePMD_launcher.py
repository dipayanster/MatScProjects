import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import dpdata

# Each subdirectory of training_dataset/ is one composition group. All DeepMD systems inside it are merged. Merging enforces matching atom names and counts, so mixed compositions fail loudly. (The directory name can be anything.) The template config has no data paths; a runtime config with generated paths is written under dpdata/ each run. dpdata/ is wiped and rebuilt every run

# Paths
BASE_DIR = Path(__file__).resolve().parent
root_dir = BASE_DIR / "training_dataset"
template_config = BASE_DIR / "DeePMD_config.json"
data_dir = BASE_DIR / "dpdata"
runtime_config = data_dir / "runtime_config.json"
log_file = BASE_DIR / "deepmd_run.log"
frozen_model = BASE_DIR / "final_model.pb"

VAL_FRAC = 0.1
SEED     = 123

# A composition group with only ONE frame is placed entirely in "train" or "val".
SINGLE_FRAME_SPLIT = "train"

if SINGLE_FRAME_SPLIT not in ("train", "val"):
    sys.exit(f"SINGLE_FRAME_SPLIT must be 'train' or 'val', got {SINGLE_FRAME_SPLIT!r}")

# Discover composition groups
comp_dirs = sorted([p for p in root_dir.iterdir() if p.is_dir()])
if not comp_dirs:
    sys.exit(f"no composition folders under {root_dir}")

print(f"Found {len(comp_dirs)} composition group(s):")
for d in comp_dirs:
    print(f"  {d.name}")

# Merge and split each composition group (DeepMD does not do this internally).
# Wipe dpdata/ first so only fresh output remains.
if data_dir.exists():
    shutil.rmtree(data_dir)

split_dirs = {"train": data_dir / "train", "val": data_dir / "val"}
for d in split_dirs.values():
    d.mkdir(parents=True)

np.random.seed(SEED)

for comp_dir in comp_dirs:
    comp = comp_dir.name
    print(f"\n[{comp}]")

    sys_paths = sorted([
        p for p in comp_dir.rglob("*")
        if p.is_dir() and (p / "type_map.raw").exists()
    ])
    if not sys_paths:
        print(f"  [skip] no systems found under {comp_dir}")
        continue

    loaded = []
    for sp in sys_paths:
        s = dpdata.LabeledSystem(str(sp), fmt="deepmd/npy")
        loaded.append(s)
        print(f"  {sp.relative_to(comp_dir)}: {s.get_nframes()} frames")

    merged = loaded[0]
    for system in loaded[1:]:
        merged.append(system)
    n = merged.get_nframes()
    print(f"  merged: {n} frames")

    if n == 1:
        # Single-frame group: route the whole frame to SINGLE_FRAME_SPLIT.
        if SINGLE_FRAME_SPLIT == "train":
            train, val = merged, None
        else:
            train, val = None, merged
        print(f"  single frame -> {SINGLE_FRAME_SPLIT}")
    else:
        idx = np.arange(n)
        np.random.shuffle(idx)
        n_val = max(1, int(n * VAL_FRAC))
        n_val = min(n_val, n - 1)   # always leave at least one frame for training
        train = merged.sub_system(idx[n_val:])
        val   = merged.sub_system(idx[:n_val])

    if train is not None:
        train.to("deepmd/npy", str(split_dirs["train"] / comp))
    if val is not None:
        val.to("deepmd/npy", str(split_dirs["val"] / comp))

    parts = []
    if train is not None:
        parts.append(f"train: {train.get_nframes()}")
    if val is not None:
        parts.append(f"val: {val.get_nframes()}")
    print("  " + ", ".join(parts))

# Collect written systems and build the runtime config.
train_systems = sorted(
    f"./dpdata/train/{p.name}" for p in split_dirs["train"].iterdir() if p.is_dir()
)
val_systems = sorted(
    f"./dpdata/val/{p.name}" for p in split_dirs["val"].iterdir() if p.is_dir()
)

print("\nTrain systems:")
for s in train_systems:
    print(f"  {s}")
print("Val systems:")
for s in val_systems:
    print(f"  {s}")

with open(template_config) as f:
    config = json.load(f)

config["training"]["training_data"]["systems"] = train_systems
config["training"]["validation_data"]["systems"] = val_systems

# Write fresh runtime config under dpdata/ (overwrites any stale copy).
with open(runtime_config, "w") as f:
    json.dump(config, f, indent=2)
print(f"\nRuntime config written: {runtime_config}")

# Run DeePMD training with the runtime config.
cmd = ["dp", "--tf", "train", str(runtime_config)]
print(f"\nRunning: {' '.join(cmd)}")
print(f"Logging to: {log_file.resolve()}")

env = os.environ.copy()
env["PYTHONUNBUFFERED"] = "1"

# Stream log to console and file
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

# Check training exit code before freezing
if proc.returncode != 0:
    print(f"\nTraining failed with exit code {proc.returncode}; skipping freeze.")
    sys.exit(proc.returncode)

# Freeze the final model
print(f"\nFreezing final model -> {frozen_model}")
freeze_cmd = ["dp", "--tf", "freeze", "-o", str(frozen_model)]
with open(log_file, "a", buffering=1) as log:
    freeze_proc = subprocess.Popen(
        freeze_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
        cwd=BASE_DIR,
    )
    for line in freeze_proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
        log.write(line)
    freeze_proc.wait()

if freeze_proc.returncode != 0:
    print(f"\nFreeze failed with exit code {freeze_proc.returncode}.")
    sys.exit(freeze_proc.returncode)

print(f"\nDone. Final model written to: {frozen_model}")
sys.exit(0)