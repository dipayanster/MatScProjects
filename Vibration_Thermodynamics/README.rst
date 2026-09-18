Script for calculating vibrational frequencies and thermodynamic properties
===========================================================
**1) Uses ASE vibrations, HarmonicThermo, IdealGasThermo, outputs (1) frequencies, (2) HarmonicThermo: ZPE , F, U, S, (3) IdealGasThermo: ZPE , H, S, G**

**2) No manual calculation. All calculations and unit conversions handled by ASE**

**3) Use vib_atom_index = None or vib_atom_index = [atom number (0 based index)] to vibrate all or specific atoms**

**4) Forces for each vibrations are saved under vib directory in json format**

N2 (/N2_ideal)
===========================================================
PAW-PBE+DFT-D4 (Suitable for running in personal laptops)
 
IdealGasThermo includes translational and rotational contributions rigorously

Atom relaxation (/N2_ideal/n2_atom_relax) followed by IdealGasThermo (ZPE , H, S, G) calculation 

Note: For a 2-atom system with geometry = 'linear', symmetrynumber = 2, and spin = 0.0, there are 3N = 6 total degrees of freedom, of which 3 are translations and 2 are rotations, leaving 3N − 3 − 2 = 1 true vibrational mode. ASE discards 5 lowest frequencies as translations and rotations, and only keeps the single real mode at 291.5 meV, giving ZPE = 0.5*291.5 meV in thermodynamics calculations. Hence vib.summary() and thermo.get_ZPE_correction() return different values of ZPE.

ΔH for Hg adatom adsorption on Au (111) surface (/Hg_on_Au)
===========================================================
PBE+SOC+DFT-D4 (This is a 'large' calculation, not suitable for personal laptops)

	Hg atom Total Energy (QE, no D4 for single atom): -4540.261001 eV (pre-calculated results in /Hg_on_Au/slab_atom)

	Au slab Total Energy (QE + D4):  -192938.444217 eV (pre-calculated results in /Hg_on_Au/slab_atom)

	Hg+Au Total Energy (QE + D4):  -197479.471488 eV

	DFT adsorption energy = -197479.471488 - (-192938.444217) - (-4540.261001) = -0.766 eV


@ Temperature: 298.15 K
 
	F   = -197479.617323 eV

	U   = -197479.394176 eV

	python -c "from ase.units import kB; print(298.15 * kB)" : 0.025692570400413117

**ΔH = H(S+A) - H(S) - H(A)**

**S = substrate, A = adsorbate**

**S+A (solid):**

  H(S+A) = U(S+A) + PV [ignore PV because solid]  
  
  H(S+A) = U(S+A) [directly from ASE]

**S (solid):**
  
  H(S) = U(S) + PV [ignore PV because solid]
  
  H(S) = U(S) = E_SCF(S) [slab is frozen]

**A (gas):** 

**(1) We can calculate it manually for mono-atomic systems**
  
  H(A) = U(A) + PV
  
  U(A) = E_SCF(A) + (3/2)k_BT [translational KE term]
  
  PV = k_BT  [ideal gas, 1 atom]
  
  H(A) = E_SCF(A) + (5/2)k_BT

**ΔH @ 298.15 K :** 

  = U(S+A) - E_SCF(S) - E_SCF(A) - (5/2)k_BT
  
  = (-197479.394176) - (-192938.444217) - (-4540.261001) - (5/2)*0.025692570400413117 = -0.753 eV

**(2) We can use ASE IdealGasThermo to get H of Hg atom directly (/Hg_on_Au/hg_ideal). This time we don't need to do the algebra manually.**

(For single atom we have turned off the DFT-D4 calculator as it adds very small amount of noise in total energy)

**ΔH @ 298.15 K :** 

  = U(S+A) - E_SCF(S) - H(A) [H from /Hg_on_Au/hg_ideal]

  = (-197479.394176) - (-192938.444217) - (-4540.196769) = -0.753 eV


ΔG for Hg adatom adsorption on Au (111) surface (/Hg_on_Au)
===========================================================
PBE+SOC+DFT-D4 (This is a 'large' calculation, not suitable for personal laptops)

**ΔG = G(S+A) - G(S) - G(A)**

**S = substrate, A = adsorbate**

**S+A (solid):**

  G(S+A) = F(S+A) + PV  [ignore PV because solid] 
  
  G(S+A) = F(S+A) [directly from ASE]
  
**S (solid):**

  G(S) = F(S) + PV [ignore PV because solid]

  G(S) = F(S) = E_SCF(S) [slab is frozen]

**A (gas):** 

**(1) Manual calculation:**

  G(A) = H(A) - TS(A)
	 
  But we derived above, H(A) = E_SCF(A) + (5/2)k_BT
	 
  G(A) = E_SCF(A) + (5/2)k_BT  - TS(A)

**ΔG @ 298.15 K:** 
  
  = F(S+A) - E_SCF(S) - E_SCF(A) - (5/2)k_BT  + TS(A) [S from /Hg_on_Au/hg_ideal]
  
  = -197479.617323 - (-192938.444217) - (-4540.261001) - (5/2)*0.025692570400413117 + (298.15*0.001812313)
				
  = -0.436 eV

**(2) We can use ASE IdealGasThermo to get G of Hg atom directly (G from /Hg_on_Au/hg_ideal). This time we don't need to do the algebra manually.**

**ΔG @ 298.15 K**
 
  = F(S+A) - E_SCF(S) - G(A)
  
  = -197479.617323 - (-192938.444217) - (-4540.737110) 
  
  = -0.436 eV