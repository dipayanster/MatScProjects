
ASE tutorial
=============
**python slab.py**

Generates a 4×4×4 Au slab with a Pd adatom adsorbed at the fcc hollow site and 10 Å of vacuum, using only default ASE commands.

Install VESTA software (https://jp-minerals.org/vesta/en/) and open the generated file (in POSCAR format) to inspect it

**python relax_emt.py**

Runs an atomic relaxation using the ASE default EMT calculator with an force tolerance of 0.01 eV/Å, saves the relaxed structure. 

Open it in VESTA and compare with the starting structure.

**ase gui relax.traj**

Opens the saved ASE trajectory file relax.traj in the ASE GUI viewer so you can inspect each ionic relaxation frame.

**python thermodynamics.py**

Calculate vibrational modes and Thermodynamics at 298.15 K


TASK
============

1) Calculate adsorption energy: E_total - E_slab - E_atom

2) Repeat the same for top, bridge and hcp hollow site adsorption