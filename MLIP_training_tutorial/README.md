# Training Machine-learned interatomic potentials (MLIPs) from DFT Data

**Single Hg Adatom Adsorption on Monolayer Graphene**

This tutorial demonstrates how to train several machine-learned interatomic potentials (MLIPs) from DFT data. The workflow is laptop-friendly, but the full procedure may take several hours depending on the hardware and GPU availability.

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

## 4. Training MACE (/MACE_training)

### 4.1 Preparing the Training Data

We will use the ASE QE + DFT-D4 relaxation trajectories as MACE training data. Use the supplied `traj2xyz.py` script that uses ASE to export trajectories to extxyz format:

```
python traj2xyz.py DFT_calculations/atop/
```

Move the generated xyz files into a separate `training_dataset` directory under `/MACE_training`. Our training dataset contains the relaxation trajectories for all adsorption sites, as well as the pristine graphene. In this tutorial we reserve a fixed % of the training data for validation (`valid_fraction`). This split is random and the corresponding frames are not used for training. For reproducibility, MACE writes the indices of the validation frames used in each run to a separate file in the top directory. For a more finely tuned model, you can instead supply carefully generated validation frames via `valid_file` (with `valid_fraction: 0.0`), rather than relying on random sampling of the training data.

As per MACE recommended practice, the custom REF_energy, REF_forces, and REF_stress headers are used separately from the ASE default headers, which are redundant and not used in training.

### 4.2 Running MACE Training

Activate the training environment (either CPU or GPU).

```
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

### 4.3 Patience bug in MACE 0.3.17 

We found that patience does not terminate training: the log reaches "Stopping optimization after XYZ epochs without improvement" but the loop continues to max_num_epochs. Phase switching behaves correctly, but the termination does not occur as expected.

This is a known bug, confirmed in GitHub issue #1384: https://github.com/ACEsuit/mace/issues/1384

We expect this to be fixed in a future MACE release.

---

## 5. Training ALIGNN (/ALIGNN_training)

### 5.1 Preparing the Training Data

ALIGNN reads energies and forces from per-structure JSON files. Use the supplied `traj2json.py` script to export the ASE QE + DFT-D4 trajectories to the JARVIS Atoms format compatible with ALIGNN.

```
python traj2json.py DFT_calculations/atop/
```

Move the generated JSON files into a `training_dataset` directory under `/ALIGNN_training` as before. A fixed train/validation/test split is set in the config (`train_ratio`, `val_ratio`, `test_ratio`). Unlike MACE, ALIGNN does not write the validation indices to a separate file.

### 5.2 Running ALIGNN Training

Activate the ALIGNN environment (GPU):

```
source ~/alignn_cuda/bin/activate
```

Then launch training with the supplied `ALIGNN_launcher.py` script. 

```
python ALIGNN_launcher.py
```

The launcher performs three steps. First, it writes `config.json` with inputs. Second, it merges the per-site JSON files into a single `id_prop.json` and subtracts the isolated-atom reference energies (E0) to produce energy-per-atom targets. This E0 correction is done explicitly here because ALIGNN, unlike MACE, does not handle it internally. Finally, it invokes `train_alignn.py`.

---

## 6. Running calculations using the trained MLIPs

The ASE scripts used for Quantum ESPRESSO can be quickly adapted to run any MLIP by replacing the `Espresso` calculator with the corresponding ASE calculator and removing the QE-specific parameters. Load the newly generated models into the appropriate calculator and rerun the script to relax an Hg atom at the hollow and far positions, analogous to the Quantum ESPRESSO DFT calculations. 

```bash
python MACE_relaxation.py > MACE_hollow.out
```

Examples are provided in the subdirectories under the training directory, e.g. `/MACE_training/MACE_calculations.` As before, the adsorption energy is calculated as `E_ads = E_total − E_far` For the hollow position:

| Method | hollow (eV) | far (eV) | E_ads (eV) | d_eq, hollow (Å) |
|---|---|---|---|---|
| DFT | −15470.993331 | −15470.776218 | −0.217 | 3.348 |
| MACE | −15470.983697 | −15470.821109 | −0.163 | 3.343 |
| ALIGNN | -164.635507 | -164.452497 | -0.183 | 3.416 |

