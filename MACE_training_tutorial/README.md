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

Reference values for DFT adsorption energies are available in Table 1, A S Fenta et al 2020 J. Phys. Mater. 4 015002 (WIEN2k, LAPW method, PBE+DFT-D3)



---

## 2. DFT Calculations (In /DFT_calculations directory)

**Level of theory:** QE PBE + DFT-D4, non-spin-polarized, PAW potentials.

### Preparing the graphene sheet

1. Save the graphite structure as a POSCAR from VESTA.
2. Delete one layer to obtain monolayer graphene.
3. Prepare a **3×3×1 unit cell** containing **18 C atoms** with a large vacuum slab.

(Consult our video tutorials at https://indico.jinr.ru/category/912/ if you need more instructions)

### Constructing adsorbed structures

For the DFT calculations, place a single Hg atom in highly symmetric sites, e.g. **top**, **bridge**, **hollow**, etc. In addition, include an **off-center position between hollow and bridge**.

(Consult our video tutorials if you need more instructions on constructing adsorbed structures.)

### Relaxation runs

Relax a single Hg adatom on:

- **top** site
- **bridge** site
- **hollow** site
- **off-center** position (between hollow and bridge)

as well as the **pristine graphene sheet** (no adatom).

For example:

```bash
python atom_relaxation.py > atop.out
```

### Calculate the total energies of isolated C and Hg atoms for reference (E0s):

```bash
python energy.py > hg.out
```

---

## 3. Validation of DFT computed data

E_ads = E_total − E_graphene − E_Hg

E_Hg = −10952.046782 eV

E_graphene = −4518.682589 eV

| Site      | E_total (eV)    | E_graphene (eV) | E_Hg (eV)      | E_ads (eV) | E_ads (eV)* | d_eq (Å) | d_eq (Å)* |
|-----------|-----------------|-----------------|----------------|----------------------|--------------------------|--------------------|------------------------|
| atop      | −15470.986356   | −4518.682589    | −10952.046782  | −0.257               | −0.178                   | 3.376              | 3.46                   |
| bridge    | −15470.986916   | −4518.682589    | −10952.046782  | −0.258               | −0.180                   | 3.372              | 3.49                   |
| hollow    | −15470.993331   | −4518.682589    | −10952.046782  | −0.264               | −0.186                   | 3.346              | 3.45                   |
| offcenter | −15470.988640   | −4518.682589    | −10952.046782  | −0.259               | —                        | 3.363              | —                      |

**Note:** *Reference values are from Fenta et al. 2020 (θ = 1/18, WIEN2k PBE+DFT-D3). This work uses QE PBE+DFT-D4, so differences in absolute adsorption energy are expected. Consistently stronger binding in this work is reflected in the more negative adsorption energies and correspondingly shorter equilibrium distances, attributable to the DFT-D4 versus DFT-D3 dispersion correction. The site ordering (hollow most stable) remains consistent.

---

## 4. Training MACE

### 4.1 Preparing the Training Data

We will use the ASE QE + DFT-D4 relaxation trajectories as MACE training data. Use the supplied traj2extxyz.py script that uses ASE to export trajectories to extxyz format:

```bash
python traj2extxyz.py DFT_calculations/offcenter/
```

Then copy the generated xyz files into a separate dataset directory under the parent directory.

As per MACE recommended practice, the custom REF_energy, REF_forces, and REF_stress headers are used separately from the ASE default headers, which are redundant and not used in training.

### 4.2 Training Input File

Parameters for training are given in the input file mace_config.yaml:
	
**General inputs**

- name — run name
- valid_fraction — validation split fraction
- E0s — isolated-atom reference energies (eV)
- model — model architecture
- hidden_irreps — hidden feature channels
- r_max — radial cutoff (Å)
- batch_size — configurations per gradient update
- max_num_epochs — maximum training epochs
- patience — stops after this number of no improvement
- scheduler_patience — LR-scheduler patience
- forces_weight — forces loss weight
- energy_weight — energy loss weight
- device — compute device

**Dataset specific inputs**

- heads — all dataset-specific options go under this
- Dataset_details — custom name of the head; can be anything, only appears in logs and saved model metadata
- train_file — list of training files goes under this head
- energy_key — reference energy key, e.g. "REF_energy"
- forces_key — reference forces key, e.g. "REF_forces"

Training is performed for REF_energy and REF_forces. Stress is **ignored** for the current project since it involves atom relaxation only; it should be included if cell relaxation is done.

We use forces_weight: 100 and energy_weight: 1 because the energy is already close to convergence.

### 4.3 Running MACE Training

```bash
source ~/mace-env/bin/activate
mace_run_train --config="mace_config.yaml"
```
### 4.4 Early stopping bug in MACE 0.3.16 (CPU, non-distributed)

We found that patience does not terminate training: the log reaches "Stopping optimization after 30 epochs without improvement" but the loop continues to max_num_epochs. This is why our CPU run went the full 500 epochs despite converging around epoch 389.

This is a known bug, confirmed in GitHub issue #1384: https://github.com/ACEsuit/mace/issues/1384

Results are unaffected, and we expect this to be fixed in a future MACE release.

---

## 5. Running MACE calculations using the generated model (in /MACE_calculations directory)

We use the generated MACE_GrapheneHg.model for all calculations. 

As a test, we placed the Hg atom at an asymmetric position near the corner of a hexagon (MACE_calculations/asymmetric). The MACE calculation scripts can be prepared by adapting the earlier ASE scripts, simply replacing the Quantum ESPRESSO + DFT-D4 calculator with the trained MACE calculator.

```bash
 python3 mace_relaxation.py > mace_asymmetric.out
```

Upon relaxation with the newly trained MACE potential, the Hg atom slides toward the hollow site, converging to an equilibrium distance of 3.358 Å — closely matching the DFT value of 3.346 Å for the hollow site calculated above.

Next we calculate the total energy of the pristine graphene sheet and an isolated Hg atom again using the newly trained MACE potential

E_ads = E_total − E_graphene − E_Hg = (−15470.983323) − (−4518.901832) − (−10952.046782) = −0.035 eV

The calculated adsorption energy of −0.035 eV is significantly higher (less negative) than the DFT value of −0.264 eV at the hollow site from which this data was trained, indicating that the model requires more rigorous training. Some improvements to try if you have followed the tutorial this far:

- Add more pristine graphene frames to better constrain the graphene reference energy.

- Add a few Hg+graphene frames at large separation to teach the model the separated-limit energy.

- Use a separate valid_file with 15–20% of the data to better validate energy offsets.

