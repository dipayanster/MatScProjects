import sys
from pathlib import Path
import numpy as np
from ase.io import Trajectory
import dpdata

# Globs the single *.traj inside the folder and writes a npy directory.
# Then copy the result into the training dataset, one subdirectory per composition.

folder    = Path(sys.argv[1])
traj_path = next(folder.glob("*.traj"))   # one traj per folder by convention

traj   = Trajectory(traj_path)
frames = list(traj)
if not frames:
    sys.exit(f"empty trajectory: {traj_path}")


symbols    = frames[0].get_chemical_symbols()
atom_names = sorted(set(symbols))                 
type_map   = {s: i for i, s in enumerate(atom_names)}
atom_numbs = [symbols.count(s) for s in atom_names]
atom_types = np.array([type_map[s] for s in symbols])

energies, forces, cells = [], [], []
for atoms in frames:
    energies.append(atoms.get_potential_energy())   # total energy (eV)
    forces.append(atoms.get_forces())               # eV/Å
    cells.append(atoms.get_cell()[:])               # Å

system = dpdata.LabeledSystem()
system.data = {
    "atom_names": atom_names,
    "atom_numbs": atom_numbs,
    "atom_types": atom_types,
    "orig":       np.zeros(3),
    "cells":      np.array(cells),
    "coords":     np.array([a.get_positions() for a in frames]),
    "energies":   np.array(energies),
    "forces":     np.array(forces),
}

out_dir = traj_path.with_suffix("")   
system.to("deepmd/npy", str(out_dir))
print(f"Wrote {len(frames)} frames to {out_dir}")