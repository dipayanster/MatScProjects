# Training a MACE Potential from DFT Data

**Single Hg Adatom Adsorption on Monolayer Graphene**

This tutorial demonstrates how to train a MACE machine learning potential from DFT data. The workflow can be run on a laptop, but the full procedure may take several hours.

---

## 1. References (/references)

### Graphite structure

The graphite structure is taken from ICSD 193439:

https://www.ccdc.cam.ac.uk/structures/Search?Ccdcid=1702249

(B. Vadlamani, K. An, M. Jagannathan, K.S. Ravi Chandran, *Journal of the Electrochemical Society*, 2014, **161**, A1731, DOI: 10.1149/2.0951410jes)

### Reference DFT adsorption energies

Reference values for DFT adsorption energies are available in Table 1, A S Fenta et al 2020 J. Phys. Mater. 4 015002 (θ = 1/18, WIEN2k, LAPW method, PBE+DFT-D3)

---

## 2. DFT Calculations (/DFT_calculations)

**Level of theory:** QE PBE + DFT-D4, non-spin-polarized, PAW potentials.

### Preparing the graphene sheet

1. Save the graphite structure as a POSCAR from VESTA.
2. Delete one layer to obtain monolayer graphene.
3. Prepare a **3×3×1 unit cell** containing **18 C atoms** with a large vacuum slab.

(Consult our video tutorials at https://indico.jinr.ru/category/912/ if you need more instructions)

### Constructing adsorbed structures

For the DFT calculations, place a single Hg atom on highly symmetric sites, e.g. **top**, **bridge**, **hollow**, etc. In addition, we include an **off-center position between hollow and bridge**. We also include two reference configurations to sample the separation limit between Hg and graphene: an **intermediate** frame starting with Hg 5 Å above the hollow site, and a **far** frame starting with Hg 7.5 Å above the graphene sheet. You are encouraged to add more adsorption configurations — in general, more training data leads to a better model.

### Relaxation runs

Relax a single Hg adatom on each of the adsorbed configurations created above, as well as on the pristine graphene sheet (no adatom).

For example:

```
python atom_relaxation.py > atop.out
```

### Calculate the total energies of isolated C and Hg atoms for reference (E0s):

```
python energy.py > hg.out
```

---

## 3. Validation of DFT computed data

Following Fenta et al., the adsorption energy is evaluated as E_ads = E_total − E_far, where E_far is the energy when the Hg atom is placed 7.5 Å from the graphene sheet.

E_far = -15470.776218 eV

| Site      | E_total (eV)    | E_far (eV)     | E_ads (eV) | E_ads (eV)* | d_eq (Å) | d_eq (Å)* |
|-----------|-----------------|----------------|----------------------|--------------------------|--------------------|------------------------|
| atop      | -15470.986356   | -15470.776218  | -0.210               | -0.178                   | 3.378              | 3.46                   |
| bridge    | -15470.986916   | -15470.776218  | -0.211               | -0.180                   | 3.369              | 3.49                   |
| hollow    | -15470.993331   | -15470.776218  | -0.217               | -0.186                   | 3.348              | 3.45                   |
| offcenter | -15470.988640   | -15470.776218  | -0.212               | —                        | 3.359              | —                      |

**Note:** *Reference values are from Fenta et al. using all electron LAPW method in WIEN2k and PBE+DFT-D3. This work uses Quantum Espresso PBE+DFT-D4, so differences in absolute adsorption energy are expected. Consistently stronger binding in this work is reflected in the more negative adsorption energies and correspondingly shorter equilibrium distances, attributable to the DFT-D4 versus DFT-D3 dispersion correction. The site ordering (hollow most stable) remains consistent.

---

## 4. Training MACE

### 4.1 Preparing the Training Data

We will use the ASE QE + DFT-D4 relaxation trajectories as MACE training data. Use the supplied traj2extxyz.py script that uses ASE to export trajectories to extxyz format:

```
python traj2extxyz.py DFT_calculations/offcenter/
```

Copy the generated xyz files into a separate `training_dataset` directory under the parent directory. Our training dataset contains the relaxation trajectories for all adsorption sites, as well as the pristine graphene.

In this tutorial we reserve a fixed % of the training data for validation (`valid_fraction`). This split is random and the corresponding frames are not used for training. For reproducibility, MACE writes the indices of the validation frames used in each run to a separate file in the top directory. For a more finely tuned model, you can instead supply carefully generated validation frames via `valid_file` (with `valid_fraction: 0.0`), rather than relying on random sampling of the training data.

As per MACE recommended practice, the custom REF_energy, REF_forces, and REF_stress headers are used separately from the ASE default headers, which are redundant and not used in training.

### 4.2 Training Input File

Parameters for training are given in the input file mace_config.yaml:

**Run identity**

- `name` — run name
- `model` — model architecture

**Compute device**

- `device` — compute device ('cuda' for GPU, 'cpu' for CPU-only nodes)

**Isolated-atom reference energies (eV)**

- `E0s` — isolated-atom reference energies (eV), with atomic number. must be calculated with same settings as the training data.

**Model settings**

- `r_max` — radial cutoff (Å), larger value used in this example to capture the effects of vdW forces
- `interaction_first` — mention explicitly to avoid silent-rewrite warning
- `hidden_irreps` — model size
- `num_interactions` — model size, number of message-passing layers

**Validation settings**

- `valid_fraction` — validation split fraction (random % of training data or use `valid_file`)

**Training schedule**

- `batch_size` — configurations per gradient update
- `max_num_epochs` — maximum training epochs
- `patience` — stops after this number of epochs without improvement
- `scheduler_patience` — LR-scheduler patience (keep below `patience`)

**Training weights (Phase 1)**

- `forces_weight` — Phase 1 forces loss weight
- `energy_weight` — Phase 1 energy loss weight

**Training weights (Phase 2)**

- `swa` — enable two-phase Stochastic Weight Averaging
- `start_swa` — epoch at which Phase 2 begins
- `swa_forces_weight` — Phase 2 forces loss weight
- `swa_energy_weight` — Phase 2 energy loss weight

**Dataset details**

- `heads` — all dataset-specific options go under this
- `Dataset_details` — custom name of the head; can be anything, only appears in logs and saved model metadata
- `train_file` — list of training files goes under this head
- `valid_file` — list of validation files goes under this head
- `energy_key` — reference energy key, e.g. "REF_energy"
- `forces_key` — reference forces key, e.g. "REF_forces"

### 4.3 Running MACE Training

Activate the training environment (either CPU or GPU).

```
source ~/mace-env/bin/activate
source ~/mace_cuda/bin/activate
```

If you are using, GPU, you can monitor GPU utilization during training by:

```
nvidia-smi
watch -n 1 nvidia-smi
```

Then start training:

```
mace_run_train --config="mace_config.yaml"
```

### 4.4 Patience bug in MACE 0.3.17 

We found that patience does not terminate training: the log reaches "Stopping optimization after XYZ epochs without improvement" but the loop continues to max_num_epochs. Phase switching behaves correctly, but the termination does not occur as expected.

This is a known bug, confirmed in GitHub issue #1384: https://github.com/ACEsuit/mace/issues/1384

We expect this to be fixed in a future MACE release.

---

## 5. Running MACE calculations using the generated model (in /MACE_calculations directory)

The ASE scripts used for Quantum ESPRESSO can be quickly adapted to run MACE by replacing the `Espresso` calculator with the `MACECalculator` and removing the QE-specific parameters. We use the newly trained `MACE_GrapheneHg_stagetwo.model` to relax an Hg atom at the **hollow** and **far** positions, analogous to the Quantum ESPRESSO DFT calculations. The Stage One model MACE_GrapheneHg.model is kept only as reference and not used.

```bash
python mace_relaxation.py > mace_hollow.out
```

As before, the adsorption energy is calculated as:

E_ads = E_total − E_far

For the hollow position:

E_ads = −15470.983697 − (−15470.821109) = −0.163 eV

The MACE-predicted adsorption energy is in reasonable agreement with the DFT results — for example, E_ads is −0.163 eV in MACE vs −0.217 eV in DFT, and the equilibrium height d_eq for the hollow site is 3.343 Å in MACE vs 3.348 Å in DFT — but even better agreement could be obtained with more extensive training.