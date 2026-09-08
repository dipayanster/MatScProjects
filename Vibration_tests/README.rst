Updated script for vibration and thermodynamics calculations
===========================================================
1) Uses ASE HarmonicThermo and prints frequencies, ZPE, F, U, S

2) NO manual calculation. All calculations and unite conversions handled by ASE

3) No translational or rotational degrees of freedom

4) Use vib_atom_index = None or vib_atom_index = [atom number (0 based index)] to vibrate all or specific atoms