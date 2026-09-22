=========================
Adsorption on the surface
=========================

Adsorption of H atom on a piece of graphene (C8).

Initial structures are read from vasp geometry files. 
The H atom is placed into a middle of  cubic box.

step 1
~~~~~~
relaxation.py - optimizes the H@C8 geometry

step 2
~~~~~~
energy_h.py - computes the energy of H atom

step 3 
~~~~~~
energy_c.py - computes the energy of C8 surface

Binding energy = E(C8) + E(H) - E(H@C8) =  -1303.645828 -12.559508 -( -1319.069236) eV
Binding energy = 2.8639 eV 

Google AI: 
The binding energy of a single Hydrogen (H) atom on pristine graphene is approximately 0.67 to 1.0 eV (chemisorption).
Binding Energy: Typically 0.67–1.0 eV, with some studies reporting up to ~1.9 eV.

Challenge
---------
Modify the Python script to perform the relaxation of the C8 slab and calculate the new adsorption energy.

Likewise, increase the ecutwfc parameter to see if this improves the binding energy of H on C8.

Note: if you would enlarge the slab (increasing the number of graphene C atoms), 
it would become computationally very demanding, thus not suitable for running on your personal computer.
