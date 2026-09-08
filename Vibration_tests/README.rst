Updated script for vibration and thermodynamics calculations
===========================================================
1) Uses ASE vibrations and HarmonicThermo and prints frequencies, ZPE, F, U, S

2) NO manual calculation. All calculations and unite conversions handled by ASE

3) Use vib_atom_index = None or vib_atom_index = [atom number (0 based index)] to vibrate all or specific atoms

N2
===========================================================
Note: NO translational or rotational degrees of freedom


Au on Hg
===========================================================
Computation level PBE+SOC+DFT-D4

Hg atom Total Energy (QE+D4): -4540.261001 eV

Au slab Total Energy (QE + D4):  -192938.444217 eV

Hg+Au Total Energy (QE + D4):  -197479.471488 eV

DFT adsorption energy = -197479.471488 - (-192938.444217) - (-4540.261001) = -0.766 eV