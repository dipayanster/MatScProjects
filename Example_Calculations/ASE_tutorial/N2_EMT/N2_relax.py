# Example: structure optimization of N2 molecule using EMT
from ase.io import read, write
from ase.optimize import BFGS
from ase.calculators.emt import EMT

# Read the structure
atoms = read('N2.vasp')

# Attach EMT calculator
atoms.calc = EMT()

# Relax all atoms with BFGS, save trajectory
opt = BFGS(atoms, trajectory='relax.traj', logfile='relax.log')
opt.run(fmax=0.0001)

# Print final energy
print('Final energy (eV):', atoms.get_potential_energy())

# Save final structure as VASP POSCAR (Cartesian, no sorting)
write('relaxed_structure.vasp', atoms, format='vasp', direct=False)