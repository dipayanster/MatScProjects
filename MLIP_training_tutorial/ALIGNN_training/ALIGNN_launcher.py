import json
import os
import subprocess
import sys
from pathlib import Path

root_dir = Path("training_dataset")   # folder with per-site *.json
config   = "config.json"              # generated ALIGNN config
out_dir  = "ALIGNN_out"               # ALIGNN training output folder
log_file = Path("ALIGNN_run.log")     # stdout+stderr tee

# isolated-atom reference energies (eV), keyed by element symbol
E0 = {
    "C":  -241.907386,
    "Hg": -10952.046782,
}

# 1. ALIGNN config
alignn_config = {
    "version": "1123",
    "random_seed": 123,
    "dataset": "user_data",
    "target": "energy_per_atom",
    "model": {
        "name": "alignn_atomwise_pure",
        "alignn_layers": 2,
        "gcn_layers": 2,
        "atom_input_features": 92,
        "edge_input_features": 80,
        "triplet_input_features": 40,
        "embedding_features": 64,
        "hidden_features": 64,
        "output_features": 1,
        "calculate_gradient": True,
        "graphwise_weight": 10.0,    # energy weight
        "gradwise_weight": 100.0,    # force weight
        "stresswise_weight": 0.0,
    },
    "neighbor_strategy": "pure_torch",
    "optimizer": "adamw",
    "learning_rate": 0.001,
    "weight_decay": 0.00001,
    "batch_size": 16,
    "epochs": 500,
    "scheduler": "onecycle",
    "train_ratio": 0.7,
    "val_ratio": 0.2,
    "test_ratio": 0.1,
    "keep_data_order": True,
    "n_early_stopping": 50,
}
with open(config, "w") as fh:
    json.dump(alignn_config, fh, indent=2)
print(f"Wrote ALIGNN config -> {config}")

# 2. merge per-site JSONs, subtract E0, write id_prop.json
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

# 3. launch ALIGNN training
cmd = [
    "train_alignn.py",
    "--root_dir", str(root_dir),
    "--config", config,
    "--output_dir", out_dir,
    "--target_key", "energy_per_atom",
    "--force_key", "forces",
    "--id_key", "jid",
]
print(f"Running: {' '.join(cmd)}")
print(f"Logging to: {log_file.resolve()}")

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
        sys.stdout.write(line)  # terminal
        sys.stdout.flush()      # flush immediately
        log.write(line)         # log file
    proc.wait()

sys.exit(proc.returncode)