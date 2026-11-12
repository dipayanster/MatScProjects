import os
import shutil
import subprocess
import sys
from pathlib import Path

# --- paths -------------------------------------------------------------------
root_dir = Path("training_dataset")
merged_xyz = root_dir / "merged_for_nequip.xyz"
config = "NequIP_config.yaml"
out_dir = Path("NequIP_out")
log_file = Path("NequIP_run.log")
best_ckpt = Path("lightning_logs/version_0/checkpoints/best.ckpt")
project_dir = Path(__file__).resolve().parent

# compile targets
# Each entry is (device, output_path).
# To also compile for GPU later, just uncomment the "cuda" line below.
compile_targets = [
    ("cpu",  project_dir / "compiled_model_cpu.nequip.pt2"),
#    ("cuda", project_dir / "compiled_model_gpu.nequip.pt2"),
]

# cleanup
shutil.rmtree("lightning_logs", ignore_errors=True)
shutil.rmtree(out_dir, ignore_errors=True)
for _, out_path in compile_targets:
    out_path.unlink(missing_ok=True)

# 1. merge per-site xyz files into one multi-frame extxyz
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
    "-cn", config,
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
    )
    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
        log.write(line)
    proc.wait()


if proc.returncode != 0:
    sys.exit(proc.returncode)

# 4. compile the best checkpoint
if not best_ckpt.exists():
    sys.exit(f"ERROR: ModelCheckpoint did not produce {best_ckpt}. "
             f"Check the ModelCheckpoint config and {log_file}.")
print(f"Best checkpoint: {best_ckpt}")

for device, out_path in compile_targets:
    print(f"Compiling for {device}: {best_ckpt} -> {out_path}")
    rc = subprocess.run([
        "nequip-compile",
        str(best_ckpt),
        str(out_path),
        "--device", device,
        "--mode",   "aotinductor",
        "--target", "ase",
    ], env=env).returncode
    if rc != 0:
        sys.exit(f"Compilation for {device} failed with return code {rc}")

print("Compiled models:")
for device, out_path in compile_targets:
    print(f"  {device}: {out_path}")