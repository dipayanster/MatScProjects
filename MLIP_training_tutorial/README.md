# Training Machine-learned interatomic potentials (MLIPs) from DFT Data

This tutorial demonstrates how to train several machine-learned interatomic potentials (MLIPs) using DFT data. We chose a suitably small Hg adatom adsorbed graphene system (fewer than 20 atoms) for this purpose. All models are built entirely from scratch — **no foundation models or pretrained components are used at any stage**. The workflow is laptop-friendly, but the full procedure may take several hours depending on the hardware and GPU availability.

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

| Site      | E_total (eV)    | E_far (eV)     | E_ads (eV) 			| E_ads (eV)*				| d_eq (Å) 			| d_eq (Å)* 			 |
|-----------|-----------------|----------------|----------------------	|--------------------------|--------------------|------------------------|
| atop      | -15470.986356   | -15470.776218  | -0.210               	| -0.178                   | 3.378              | 3.46                   |
| bridge    | -15470.986916   | -15470.776218  | -0.211               	| -0.180                   | 3.372              | 3.49                   |
| hollow    | -15470.993331   | -15470.776218  | -0.217               	| -0.186                   | 3.346              | 3.45                   |
| offcenter | -15470.988640   | -15470.776218  | -0.212               	| —                        | 3.363              | —                      |

**Note:** *Reference values are from Fenta et al. using all electron LAPW method in WIEN2k and PBE+DFT-D3. This work uses Quantum Espresso PBE+DFT-D4, so differences in absolute adsorption energy are expected. Consistently stronger binding in this work is reflected in the more negative adsorption energies and correspondingly shorter equilibrium distances, attributable to the DFT-D4 versus DFT-D3 dispersion correction. The site ordering (hollow most stable) remains consistent.

---

## 4. Training MLIPs (in separate directories, e.g. /MACE_training)

- We will use ASE-driven QE+DFT-D4 relaxation trajectories (`*.traj files`, you can visualize them with `ase gui *.traj`) as MLIP training data. Export them with the supplied conversion scripts — for example, `python traj2xyz.py DFT_calculations/atop/` exports extended XYZ format.
- Move the converted files (or directories e.g. DeePMD) into a `training_dataset` directory (or composition specific subdirectories e.g. DeePMD) under each training directory.
- The config files store all training input settings 
- Training can be launched immediately for some MLIPs, such as MACE, because it reads multiple training files directly from its config file, compiles the best model, and writes stdout logs automatically.
- For other MLIPs that don't automate these steps (e.g., those needing a single merged training file), we use a launcher script, so the workflow can be re-run with different training parameters by changing only the config files.
- A percentage of the data is held out for validation (and testing if needed), held-out frames are never used for training. A seed value can be set for reproducibility wherever the MLIP supports it.

Activate the required environment(s) 

```
source ~/mace_cuda/bin/activate
source ~/alignn_cuda/bin/activate
source ~/nequip_env/bin/activate
source ~/deepmd_env/bin/activate
```

On a GPU, you can monitor utilization with `nvidia-smi` or `watch -n 1 nvidia-smi`. 

Summary of procedures:

| MLIP   	| Conversion Script 		 		| Input File			| Launch Command/ Script                        | Generated Model                  			| ASE Calculator             	|
| :---------| :---------------------------------| :---------------------| :---------------------------------------------| :-----------------------------------------| :-----------------------------|
| MACE   	| `traj2xyz.py`	<br> (extended XYZ)	| `mace_config.yaml`    | `mace_run_train --config="mace_config.yaml"`  | `MACE_GrapheneHg_stagetwo.model` 			| `MACECalculator`				|
| ALIGNN-FF	| `traj2json.py` <br> (JSON)		| `ALIGNN_config.json`  | `python ALIGNN_launcher.py`                   | `ALIGNN_out` directory           			| `AlignnAtomwiseCalculator`	|
| NequIP 	| `traj2xyz.py`	<br> (extended XYZ)	| `NequIP_config.yaml`  | `python NequIP_launcher.py`					| `compiled_model_cpu.nequip.pt2` 			| `NequIPCalculator`			|
| Allegro  	| `traj2xyz.py` <br> (extended XYZ)	| `Allegro_config.yaml` | `python Allegro_launcher.py`					| `compiled_allegro_model_cpu.nequip.pt2` 	| `NequIPCalculator`			|
| DeePMD  	| `traj2npy.py` <br> (directories)	| `DeePMD_config.json`	| `python DeePMD_launcher.py`					| `final_model.pb` 							| `DP`							|

### Notes

- In extended XYZ files, custom `REF_energy`, `REF_forces`, and `REF_stress` headers are used. These are separate from the ASE default headers, which are redundant and not used in training.
- In MACE 0.3.17 patience does not terminate training. Phase switching works correctly, but termination does not occur (known bug, GitHub issue #1384: https://github.com/ACEsuit/mace/issues/1384). 
- Early stopping is not implemented in ALIGNN 2026.11.1's train.py — the n_early_stopping config field is inert
- For DeePMD, the conversion script generates a npy directory, each must be moved under `training_dataset/<composition>`. DeePMD does not shuffle or split frames into train and validation sets, so that has to be done manually. The CPU TensorFlow build does not auto-save the best checkpoint, so the launcher is set to freeze the last model.

---

## 5. Running calculations using the trained MLIPs

The ASE scripts used for Quantum ESPRESSO can be quickly adapted to run any MLIP by replacing the `Espresso` calculator with the corresponding ASE calculator and removing the QE-specific parameters. Load the newly generated models into the appropriate calculator and rerun the script to relax an Hg atom at the hollow and far positions, analogous to the Quantum ESPRESSO DFT calculations. 

```bash
python MACE_relaxation.py > MACE_hollow.out
```

Examples are provided in the subdirectories under the training directory, e.g. `/MACE_training/MACE_calculations.` As before, the adsorption energy is calculated as `E_ads = E_total − E_far` For the hollow position:

| Method 				| E_hollow (eV) 	| E_far (eV) 	| E_ads (eV)| d_eq @ hollow (Å) | Training Weights (force:energy)	|
|---					|---				|---			|---		|---				| ---								|
| WIEN2k, PBE+DFT-D3`*`	| —					| —				| −0.186 	| 3.450 			| —									|
| QE PBE + DFT-D4		| −15470.993331		| −15470.776218 | −0.217 	| 3.346 			| —									|
| MACE 					| −15470.983697 	| −15470.821109 | −0.163 	| 3.350 			| 100:1 → 100:10 (2 phase)			|
| ALIGNN-FF				| −164.606008 		| −164.397648 	| −0.208 	| 3.395 			| 100:10							|
| NequIP				| −15471.040401 	| −15470.864325 | −0.176 	| 3.345 			| 50:50								|
| Allegro				| −15470.997893 	| −15470.778992 | −0.219 	| 3.341 			| 50:50								|
| DeePMD				| −15470.990700 	| −15470.816395 | −0.174 	| 3.342 			| 1000:0.02 → 1:1 (2 phase)			|

### How to interpret this table: 

It is not a ranking of which MLIP performs best. Every model was trained on minimal configurations with limited data, and each could be improved with more data, larger models, opptimized training settings or longer training. The tutorial is meant to just demonstrate the workflows and show that even models trained with limited data can capture the atomic interactions.