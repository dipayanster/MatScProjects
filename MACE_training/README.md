# MACE Training — Au–Fl System

Train a MACE potential on a QE+D4 relaxation trajectory of a 48-atom Au slab with one Flerovium (Fl) adsorbate.

## Commands

```bash
cd ~
source mace-env/bin/activate
mace_run_train --config=mace_config.yaml
```

## Config (`mace_config.yaml`)

```yaml
name: MACE_AuFl
train_file: train.xyz
valid_fraction: 0.1
E0s: '{79: -4019.5509211875, 114: -5240.211831}'
model: MACE
hidden_irreps: '64x0e + 64x1o'
r_max: 5.0
batch_size: 5
max_num_epochs: 20
forces_weight: 100
energy_weight: 1
device: cpu
energy_key: "energy"
forces_key: "forces"
```

## Options Explained

### `name`
- Base name for the output directory and all generated model files.
- Example: `MACE_AuFl` produces `MACE_AuFl/`, `MACE_AuFl.model`, and log files.

### `train_file`
- Path to the training dataset.
- Must end in `.xyz` so ASE can detect the extended-XYZ format; a `.txt` extension will raise `UnknownFileTypeError`.

### `valid_fraction`
- Fraction of frames held out for validation during training.
- Example: `0.1` reserves 10% of frames for validation.

### `E0s`
- Isolated-atom reference energies keyed by atomic number.
- `79` = Au, `114` = Fl; the Au value here is the 48-atom cell energy divided by 48.

### `model`
- Architecture to train.
- `MACE` is the standard equivariant message-passing model and the correct choice here.

### `hidden_irreps`
- Model width and angular complexity.
- `64x0e + 64x1o` is a small model suited to tiny datasets; larger models overfit 23 frames.

### `r_max`
- Cutoff radius in Å for message passing.
- Typical values are 4–6; `5.0` is a reasonable default.

### `batch_size`
- Number of frames processed per optimization step.
- Small values keep gradient updates frequent on tiny datasets.

### `max_num_epochs`
- Upper bound on the number of training epochs.
- Training may stop earlier if validation loss plateaus.

### `forces_weight`
- Weight applied to the force loss.
- Kept high because this trajectory is nearly converged and forces carry most of the signal.

### `energy_weight`
- Weight applied to the energy loss.
- Kept low relative to forces because total energy varies by only ~0.006 eV across the dataset.

### `device`
- Compute device.
- Use `cpu` or `cuda` depending on your PyTorch and NVIDIA driver setup.

### `energy_key`
- Name of the energy field in the XYZ header.
- Set to `"energy"` for ASE-written files; MACE's internal default is `REF_energy`.

### `forces_key`
- Name of the forces field in the XYZ header.
- Set to `"forces"` for ASE-written files; MACE's internal default is `REF_forces`.