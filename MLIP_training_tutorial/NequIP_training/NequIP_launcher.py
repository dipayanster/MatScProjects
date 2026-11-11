import os
import shutil
import subprocess
import sys
from pathlib import Path

root_dir = Path("training_dataset")
merged_xyz = root_dir / "merged_for_nequip.xyz"
config = "NequIP_config.yaml"
out_dir = "NequIP_out"
log_file = Path("NequIP_run.log")

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

# wipe previous Lightning checkpoints so only THIS run's are found later
shutil.rmtree("lightning_logs", ignore_errors=True)

# 2. launch NequIP training
config_dir = Path(__file__).resolve().parent
cmd = [
    "nequip-train",
    "-cp", str(config_dir),
    "-cn", config,
    f"data.split_dataset.file_path={merged_xyz}",
    f"hydra.run.dir={out_dir}",
]
print(f"Running: {' '.join(cmd)}")
print(f"Logging to: {log_file.resolve()}")

# 3. stream stdout+stderr to terminal and log file
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

# 4. compile the checkpoint from this run
# (because for some reason NequIP doesn't do it automatically)
ckpt_path = max(
    Path("lightning_logs").glob("version_*/checkpoints/*.ckpt"),
    key=lambda p: p.stat().st_mtime,
)

project_dir = Path(__file__).resolve().parent
cpu_compiled_path = project_dir / "compiled_model_cpu.nequip.pt2"
#gpu_compiled_path = project_dir / "compiled_model_gpu.nequip.pt2"

compile_targets = [
    ("cpu", cpu_compiled_path),
#    ("cuda", gpu_compiled_path),
]

for device, out_path in compile_targets:
    print(f"Compiling for {device}: {ckpt_path} -> {out_path}")
    rc = subprocess.run([
        "nequip-compile",
        str(ckpt_path),
        str(out_path),
        "--device", device,
        "--mode",   "aotinductor",
        "--target", "ase",
    ], env=env).returncode
    if rc != 0:
        print(f"Compilation for {device} failed with return code {rc}")
        sys.exit(rc)

print("Compiled models:")
print(f"  CPU: {cpu_compiled_path}")
#print(f"  GPU: {gpu_compiled_path}")