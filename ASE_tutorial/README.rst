
ASE tutorial
=============
**python slab.py**

Generates a 4×4×4 Au slab with a Pd adatom adsorbed at the fcc hollow site and 10 Å of vacuum, using only default ASE commands.

Install vesta (https://jp-minerals.org/vesta/en/) to open the generated file (in POSCAR format) and inspect it

**python relax_emt.py**

Runs an atomic relaxation using the ASE default EMT calculator with an fmax tolerance of 0.01 eV/Å, saves the relaxed structure. 

Opens it in VESTA to compare with the starting structure.

**ase gui relax.traj**

Opens the saved ASE trajectory file relax.traj in the ASE GUI viewer so you can inspect each ionic relaxation frame.