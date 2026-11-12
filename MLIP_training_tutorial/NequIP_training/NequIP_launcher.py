import os
import shutil
import subprocess
import sys
from pathlib import Path

# paths
BASE_DIR = Path(__file__).resolve().parent

root_dir   = BASE_DIR / "training_dataset"
merged_xyz = root_dir / "merged_for_nequip.xyz"
config     = BASE_DIR / "NequIP_config.yaml"
out_dir    = BASE_DIR / "NequIP_out"
log_file   = BASE_DIR / "NequIP_run.log"
project_dir = BASE_DIR

# for GPU, uncomment the "cuda" line below.
compile_targets = [
    ("cpu",  project_dir / "compiled_model_cpu.nequip.pt2"),
#    ("cuda", project_dir / "compiled_model_gpu.nequip.pt2"),
]

# cleanup
shutil.rmtree(BASE_DIR / "lightning_logs", ignore_errors=True)
shutil.rmtree(out_dir, ignore_errors=True)
for _, out_path in compile_targets:
    out_path.unlink(missing_ok=True)

# 1. merge per-site xyz files
with open(merged_xyz, "w") as fout:
    for f in sorted(root_dir.glob("*.xyz")):
        if f.name == merged_xyz.name:
            continue
        text = f.read_text()
        fout.write(text)
        if not text.endswith("\n"):
            fout.write("\n")
print(f"Merged xyz files -> {merged_xyz}")

# 2. launch NequIP training
cmd = [
    "nequip-train",
    "-cp", str(project_dir),
    "-cn", config.name,
    f"data.split_dataset.file_path={merged_xyz}",
    f"hydra.run.dir={out_dir}",
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

if proc.returncode != 0:
    sys.exit(proc.returncode)

# 4. compile the best checkpoint
search_roots = [out_dir, BASE_DIR / "lightning_logs"]
ckpts = []
for root in search_roots:
    ckpts.extend(root.glob("**/checkpoints/best.ckpt"))
ckpts = sorted(ckpts)
if not ckpts:
    sys.exit(f"ERROR: no best.ckpt found under {search_roots}. "
             f"Check the ModelCheckpoint config and {log_file}.")
best_ckpt = ckpts[0]
print(f"Found best checkpoint: {best_ckpt}")

for device, out_path in compile_targets:
    print(f"Compiling for {device}: {best_ckpt} -> {out_path}")
    rc = subprocess.run([
        "nequip-compile",
        str(best_ckpt),
        str(out_path),
        "--device", device,
        "--mode",   "aotinductor",
        "--target", "ase",
    ], env=env, cwd=BASE_DIR).returncode
    if rc != 0:
        sys.exit(f"Compilation for {device} failed with return code {rc}")

print("Compiled models:")
for device, out_path in compile_targets:
    print(f"  {device}: {out_path}")