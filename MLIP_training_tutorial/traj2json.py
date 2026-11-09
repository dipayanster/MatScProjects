import sys
import json
from pathlib import Path
from ase.io import Trajectory
from jarvis.core.atoms import ase_to_atoms

folder = Path(sys.argv[1])
traj_path = next(folder.glob('*.traj'))   # find the .traj file inside the folder

traj = Trajectory(traj_path)
out_entries = []

for idx, atoms in enumerate(traj):
    energy = atoms.get_potential_energy()
    forces = atoms.get_forces()
    stress = atoms.get_stress()

    atoms_dict = ase_to_atoms(atoms).to_dict()

    out_entries.append({
        "jid": f"{traj_path.stem}_{idx:04d}",
        "atoms": atoms_dict,
        "energy_per_atom": energy / len(atoms),
        "forces": forces.tolist(),
        "stress": stress.tolist(),
    })

json.dump(out_entries, open(traj_path.with_suffix(".json"), "w"), indent=2)
print(f"Wrote {len(out_entries)} frames to {traj_path.with_suffix('.json')}")