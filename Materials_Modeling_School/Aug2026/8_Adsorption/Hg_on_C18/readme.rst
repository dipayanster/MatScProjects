======
Hg@C18
======

python relaxation_Hg_C18.py

Successfully read 19 atoms from c18_hg.vasp

Starting atom relaxation by ASE

Final results
  Total Energy                  : -7481.346431 eV
  ASE-style max force (norm)    : 0.009006 eV/Å
  QE-style max force            : 0.009006 eV/Å
  Pressure                      : 3.795311 kbar

Final relaxed structure saved to: final_relaxed_structure.vasp

Relaxation complete

C18 slab
--------
python energy_c18.py
Successfully read 18 atoms from c18.vasp

Running SCF calculation...
  Total energy: -2947.320598 eV
  Fermi level: -1.698800 eV

Hg atom
-------
python energy_Hg.py
Successfully read 1 atoms from hg.vasp

Running SCF calculation...
  Total energy: -4533.787985 eV
  Fermi level: -2.274400 eV


Adsorption energy = E(Hg@C18)-E(C18)-H(Hg)=-7481.346431-(-2947.320598)-(-4533.787985)=-.237848 = -0.24 eV

GoogleAI:
Calculated (DFT with vdW corrections): -0.15 eV to -0.22 eV .
Experimental (Highly Oriented Pyrolytic Graphite / Graphene): -0.18  eV to -0.25 eV .

Challenge
---------
Calculate the adsorption energy of Hg on 3 different adsorption sites of the C18 slab: on-top, on-bridge, on-hollow.
