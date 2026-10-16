from ase.io import Trajectory, write
from ase.calculators.singlepoint import SinglePointCalculator

traj = Trajectory('relaxation.traj')  # your ASE trajectory file
out_frames = []

for atoms in traj:
    # Extract energy, forces, and stress from calculator
    energy = atoms.get_potential_energy()
    forces = atoms.get_forces()
    try:
        stress = atoms.get_stress()  # optional
    except Exception:
        stress = None

    # Create a copy and attach SinglePointCalculator
    atoms_copy = atoms.copy()
    calc = SinglePointCalculator(atoms_copy, energy=energy, forces=forces, stress=stress)
    atoms_copy.calc = calc
    out_frames.append(atoms_copy)

# Write to extxyz, MACE can read directly
write('train.xyz', out_frames, format='extxyz')