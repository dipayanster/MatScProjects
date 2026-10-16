# MACE Training on ASE trajectory data

To Do: MACE read the stress, but it did not train on it. Include in the loss function. 

## Commands

```bash
source ~/mace-env/bin/activate
mace_run_train --config=mace_config.yaml
```

## Options Explained

### `name`
- Base name for the output directory and all generated model files.

### `train_file`
- Path to the training dataset.
- Must end in `.xyz` so ASE can detect the extended-XYZ format.

### `valid_fraction`
- Fraction of frames held out for validation during training.
- `0.1` reserves 10% of frames for validation.

### `E0s`
- Isolated-atom reference energies keyed by atomic number.

### `model`
- Architecture to train.

### `hidden_irreps`
- Model width and angular complexity.
- `64x0e + 64x1o` is a small model suited to tiny datasets; larger models overfit.

### `r_max`
- Cutoff radius in Å for message passing.
- Typical values are 4–6; `5.0` is a reasonable default.

### `batch_size`
- Number of frames processed per optimization step.
- Small values keep gradient updates frequent on tiny datasets.

### `max_num_epochs`
- Upper bound on the number of training epochs.
- `500` gives the model enough updates to converge on a small dataset.

### `forces_weight`
- Weight applied to the force loss.

### `energy_weight`
- Weight applied to the energy loss.

### `device`
- Compute device.
- Use `cpu` or `cuda` depending on your PyTorch and NVIDIA driver setup.

### `patience`
- Number of consecutive epochs without validation-loss improvement before early stopping triggers.
- `10` means training stops if the validation loss does not improve for 10 straight epochs.