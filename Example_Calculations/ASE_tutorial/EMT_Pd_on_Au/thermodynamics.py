# Example: vibrational properties of Au(111) 4x4 slab with Hg adsorbate using EMT
from ase.io import read
from ase.calculators.emt import EMT
from ase.vibrations import Vibrations
from ase.thermochemistry import HarmonicThermo

# Read the relaxed structure
atoms = read('relaxed_structure.vasp')

# Attach EMT calculator
atoms.calc = EMT()

# Get total energy
energy = atoms.get_potential_energy()
print('Total energy (eV):', energy)

# Vibrating atom index (None or 0 based)
#vib_atom_index = [64]
vib_atom_index = None

# Run vibrations
vib = Vibrations(atoms, indices=vib_atom_index, name='vib')
vib.run()
vib.summary()

# Thermodynamics at 298.15 K
vib_energies = vib.get_energies()
thermo = HarmonicThermo(vib_energies=vib_energies,
                        potentialenergy=energy,
                        ignore_imag_modes=True)

zpe = thermo.get_ZPE_correction()
F = thermo.get_helmholtz_energy(298.15, verbose=False)
U = thermo.get_internal_energy(298.15, verbose=False)
S = thermo.get_entropy(298.15, verbose=False)

print('\nThermodynamics at 298.15 K')
print(f'  ZPE = {zpe:10.6f} eV')
print(f'  F   = {F:10.6f} eV')
print(f'  U   = {U:10.6f} eV')
print(f'  S   = {S:10.6e} eV/K')