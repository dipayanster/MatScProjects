import sys
from pathlib import Path
from ase.io import Trajectory, write
from ase.calculators.singlepoint import SinglePointCalculator

folder = Path(sys.argv[1])

traj_path = next(folder.glob('*.traj'))
traj = Trajectory(traj_path)
out_frames = []

for atoms in traj:
    energy = atoms.get_potential_energy()
    forces = atoms.get_forces()
    stress = atoms.get_stress()

    atoms_copy = atoms.copy()
    calc = SinglePointCalculator(atoms_copy, energy=energy, forces=forces, stress=stress)
    atoms_copy.calc = calc

    atoms_copy.info['REF_energy'] = energy
    atoms_copy.new_array('REF_forces', forces)
    atoms_copy.info['REF_stress'] = stress

    out_frames.append(atoms_copy)

write(folder / traj_path.with_suffix('.xyz').name, out_frames, format='extxyz')