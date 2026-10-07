
ASE tutorial
=============
**NOTE**

These tutorial is for **quick demonstrations of the workflow with bare bones scripts**.

ASE EMT supports Al, Cu, Ag, Au, Ni, Pd and Pt. The following elements are supported but **NOT well described by EMT, and the parameters are not for any serious use**: H, C, N, O

N2 molecule relaxation and Thermodynamics (/N2_EMT)
============

**python N2_relax.py**

Reads a N2 molecule in a periodic box (POSCAR format, can visualize in VESTA software (https://jp-minerals.org/vesta/en/), relaxes the atoms using the ASE default EMT calculator, and saves it.

**python Ideal_N2_EMT.py**

Runs a IdealGasThermo calculation at 298.15 K and 1 bar, and outputs (1) frequencies (2) ZPE , H, S, G

**NOTE: EMT for N is not well defined, and it cant replicate the standard data**

NIST standard data:

Frequency (harmonic): 2359 cm-1

Entropy (298.15K) 191.609 ± 0.004,  191.61 

https://webbook.nist.gov/cgi/cbook.cgi?ID=C7727379&Mask=1#Thermo-Gas 

https://cccbdb.nist.gov/exp2x.asp?casno=7727379


Pd adsorption on Au
=============

**python slab.py**

Generates a 4×4×4 Au slab with a Pd adatom adsorbed at the fcc hollow site and 10 Å of vacuum, using ASE fcc111 and add_adsorbate.

Install VESTA software (https://jp-minerals.org/vesta/en/) and open the generated file (in POSCAR format) to inspect it

**python relax_emt.py**

Runs an atomic relaxation using the ASE default EMT calculator with an force tolerance of 0.01 eV/Å, saves the relaxed structure. 

Open it in VESTA and compare with the starting structure.

**ase gui relax.traj**

Opens the saved ASE trajectory file relax.traj in the ASE GUI viewer so you can inspect each ionic relaxation frame.

**python thermodynamics.py**

Runs a HarmonicThermo calculation at 298.15 K, and outputs (1) frequencies (2) ZPE , F, U, S




