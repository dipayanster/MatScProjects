import os
import random
import shutil
import subprocess
import sys
from pathlib import Path

from ase.io import read, write

# Any .xyz file with only ONE frame is placed entirely in "train" or "val".
SINGLE_FRAME_SPLIT = "train"

# paths
BASE_DIR = Path(__file__).resolve().parent
root_dir = BASE_DIR / "training_dataset"
merged_xyz = root_dir / "merged_for_sevenn.xyz"
train_xyz = root_dir / "train_split.xyz"
val_xyz = root_dir / "val_split.xyz"
input_yaml = BASE_DIR / "SevenNet_config.yaml"
out_dir = BASE_DIR / "SevenNet_out"
log_file = BASE_DIR / "SevenNet_run.log"

# cleanup
shutil.rmtree(BASE_DIR / "sevenn_data", ignore_errors=True)
shutil.rmtree(out_dir, ignore_errors=True)
for f in [log_file, merged_xyz, train_xyz, val_xyz]:
    f.unlink(missing_ok=True)

# separate 1-frame .xyz files from multi-frame .xyz files
single_frames = []
multi_frames = []
skip_names = {merged_xyz.name, train_xyz.name, val_xyz.name}

for f in sorted(root_dir.glob("*.xyz")):
    if f.name in skip_names:
        continue
    frames = read(f, index=":")
    if len(frames) == 1:
        single_frames.extend(frames)
        print(f"Single-frame file '{f.name}' -> {SINGLE_FRAME_SPLIT}")
    else:
        multi_frames.extend(frames)

# write merged xyz for reference
write(merged_xyz, single_frames + multi_frames, format="extxyz")
print(f"Merged xyz -> {merged_xyz}")

# split multi-frame files into train / val (80/20, random)
random.seed(123)
random.shuffle(multi_frames)

split_idx = int(0.8 * len(multi_frames))
train_frames = multi_frames[:split_idx]
val_frames = multi_frames[split_idx:]

# route all 1-frame files according to SINGLE_FRAME_SPLIT
if SINGLE_FRAME_SPLIT == "train":
    train_frames = single_frames + train_frames
elif SINGLE_FRAME_SPLIT == "val":
    val_frames = single_frames + val_frames
else:
    raise ValueError(f"Invalid SINGLE_FRAME_SPLIT='{SINGLE_FRAME_SPLIT}'. Use 'train' or 'val'.")

write(train_xyz, train_frames, format="extxyz")
write(val_xyz, val_frames, format="extxyz")

print(f"Train: {len(train_frames)} frames -> {train_xyz}")
print(f"Val:   {len(val_frames)} frames -> {val_xyz}")

# launch SevenNet training
cmd_train = [
    "sevenn", "train",
    str(input_yaml),
    "-s",
]
print(f"Running: {' '.join(cmd_train)}")

# logging
env = os.environ.copy()
env["PYTHONUNBUFFERED"] = "1"

with open(log_file, "w", buffering=1) as log:
    proc = subprocess.Popen(
        cmd_train,
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

if proc.returncode != 0:
    sys.exit(proc.returncode)

print(f"Training complete. Log: {log_file.resolve()}")
