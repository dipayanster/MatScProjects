# Example: vibrational properties of N2 molecule using EMT
from ase.io import read
from ase.calculators.emt import EMT
from ase.vibrations import Vibrations
from ase.thermochemistry import IdealGasThermo
import numpy as np

# Read the relaxed structure
atoms = read('relaxed_structure.vasp')

# Attach EMT calculator
atoms.calc = EMT()

# Get total energy
energy = atoms.get_potential_energy()
print('Total energy (eV):', energy)

# Run vibrations
vib = Vibrations(atoms, indices=None, name='vib', delta=0.01)
vib.run()
vib.summary()
vib_energies = vib.get_energies()

# Thermodynamics at STP 298.15 K and 1 bar (100000.0 Pa)
# ASE 3.28+ includes PBC check, used to work with periodic atom objects in 3.26
thermo_atoms = atoms.copy()
thermo_atoms.pbc = False 

thermo = IdealGasThermo(
    vib_energies=vib_energies,
    potentialenergy=energy,
    atoms=thermo_atoms,
    geometry='linear',
    symmetrynumber=2,
    spin=0.0,
    ignore_imag_modes=True
)

zpe = thermo.get_ZPE_correction()
H = thermo.get_enthalpy(298.15, verbose=False)
S = thermo.get_entropy(298.15, 100000.0, verbose=False)
G = thermo.get_gibbs_energy(298.15, 100000.0, verbose=False)

print('\nThermodynamics at 298.15 K')
print(f'  ZPE = {zpe:10.6f} eV')
print(f'  H   = {H:10.6f} eV')
print(f'  S   = {S:10.6e} eV/K')
print(f'  G   = {G:10.6f} eV')