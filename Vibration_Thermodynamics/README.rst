Script for calculating vibrational frequencies and thermodynamic properties
===========================================================
**1) Uses ASE vibrations, HarmonicThermo, IdealGasThermo, outputs (1) frequencies, (2) HarmonicThermo: ZPE , F, U, S, (3) IdealGasThermo: ZPE , H, S, G**

**2) No manual calculation. All calculations and unit conversions handled by ASE**

**3) Use vib_atom_index = None or vib_atom_index = [atom number (0 based index)] to vibrate all or specific atoms**

**4) Forces for each vibrations are saved under vib directory in json format**

N2
===========================================================
Note: No translational or rotational degrees of freedom in HarmonicThermo


Hg adatom adsorption on Au (111) surface (/Hg_on_Au)
===========================================================
Computation level PBE+SOC+DFT-D4 (This is a 'large' calculation, not suitable for personal laptops)

	Hg atom Total Energy (QE, no D4 for single atom): -4540.261001 eV (pre-calculated results in /Hg_on_Au/hg_ideal)

	Au slab Total Energy (QE + D4):  -192938.444217 eV (pre-calculated results in /Hg_on_Au/hg_ideal)

	Hg+Au Total Energy (QE + D4):  -197479.471488 eV

	DFT adsorption energy = -197479.471488 - (-192938.444217) - (-4540.261001) = -0.766 eV


@ Temperature: 298.15 K
 
	F   = -197479.617323 eV

	U   = -197479.394176 eV

	python -c "from ase.units import kB; print(298.15 * kB)" : 0.025692570400413117

**ΔH = H(S+A) - H(S) - H(A)**

**S = substrate, A = adsorbate**

**S+A (solid):**

  H(S+A) = U(S+A) + PV  [ignore PV because solid]  
  
  H(S+A) = U(S+A) [directly from ASE]

**S (solid):**
  
  H(S) = U(S) + PV  [ignore PV because solid]
  
  H(S) = U(S) = E_SCF(S)  [slab is frozen]

**A (gas):** 

(1) We can calculate it manually easily for mono-atomic systems
  
  H(A) = U(A) + PV
  
  U(A) = E_SCF(A) + (3/2)k_BT  [translational KE term]
  
  PV = k_BT  -> ideal gas, 1 atom
  
  H(A) = E_SCF(A) + (5/2)k_BT

**ΔH = U(S+A) - E_SCF(S) - E_SCF(A) - (5/2)k_BT**

ΔH @ 298.15 K = (-197479.394176) - (-192938.444217) - (-4540.261001) - (5/2)*0.025692570400413117 = -0.753 eV

(2) We can use ASE IdealGasThermo to get H of Hg directly (/Hg_on_Au/hg_ideal). This time don't need to do the algebra manually.

ΔH @ 298.15 K = U(S+A) - E_SCF(S) - H(A) = (-197479.394176) - (-192938.444217) - (-4540.196769) = -0.753 eV
