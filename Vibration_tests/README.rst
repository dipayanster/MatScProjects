Updated script for vibration and thermodynamics calculations
===========================================================
**1) Uses ASE vibrations and HarmonicThermo, outputs frequencies, ZPE, F, U, S**

**2) No manual calculation. All calculations and unit conversions handled by ASE**

**3) Use vib_atom_index = None or vib_atom_index = [atom number (0 based index)] to vibrate all or specific atoms**

**4) Forces for each vibrations are saved under vib directory in json format**

N2
===========================================================
Note: No translational or rotational degrees of freedom in HarmonicThermo


Au on Hg
===========================================================
Computation level PBE+SOC+DFT-D4

Hg atom Total Energy (QE, no D4 for single atom): -4540.261001 eV

Au slab Total Energy (QE + D4):  -192938.444217 eV

Hg+Au Total Energy (QE + D4):  -197479.471488 eV

DFT adsorption energy = -197479.471488 - (-192938.444217) - (-4540.261001) = -0.766 eV


Temperature: 298.15 K
 
F   = -197479.617323 eV

U   = -197479.394176 eV

python -c "from ase.units import kB; print(298.15 * kB)"
0.025692570400413117
  
Delta_G = F - E_slab - E_atom - k_B*T = -197479.617323 - (-192938.444217) - (-4540.261001) - 0.025692570400413117 = -0.938 eV

Delta_H = U - E_slab - E_atom - k_B*T = -197479.394176 - (-192938.444217) - (-4540.261001) - 0.025692570400413117 = -0.715 eV
