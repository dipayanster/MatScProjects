Example calculations for Thermoluminescence characteristics
===========================================================
**Replicate pristine BeO DOS and band structures as reported in Tsoutsoumanos et al., Physica B: Condensed Matter 697 (2025) 416700**

**These examples are suitable for running on personal laptops.** 

Resources
===========================================================
Python, numpy, ASE, Gnuplot, Quantum Espresso

Initial structure from P.J. Baldock, W.E. Spindler, T.W. Baker, Journal of Nuclear Materials, 1966, 19, 169, DOI: 10.1016/0022-3115(66)90107-3, ICSD 601160
https://www.ccdc.cam.ac.uk/structures/Search?Doi=https%3A%2F%2Fdoi.org%2F10.1016%2F0022-3115(66)90107-3&DatabaseToSearch=Published

Pseudo potentials form https://www.pseudo-dojo.org/
Norm Conserving (NC) Scalar Relativistic (SR) (ONCVPSP 0.5) PBE stringent

Note: Dispersion corrections not included in this example

1. Convergence test
===========================================================
ecutwfc CONVERGED at 125 Ry (ΔE < 0.01 meV/atom)

K-points CONVERGED at (10, 10, 5) (ΔE < 0.01 meV/atom) 

Note: NC Pseudo potentials require higher ecutwfc, but default ecutrho is adequate 


2. Cell relaxation
===========================================================

Constrained relaxation - relax lattice parameters, keep cell angles fixed

Note: Minor changes, a and b 2.71100 --> 2.71121, c 4.39400 --> 4.40132


3. DOS
===========================================================

Characteristic 7.5 eV gap is replicated. 

Note: aligning Fermi level to 0 put it in the middle of the gap and not on the top of valence band. However this is minor issue as alignment can be fixed manually/ also we can crosscheck with other pseudos 