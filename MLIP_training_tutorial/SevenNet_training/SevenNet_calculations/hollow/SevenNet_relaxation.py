#!/usr/bin/env python
from ase import Atoms
from ase.io import read, write
from ase.optimize import BFGS
from ase.io.trajectory import Trajectory
from sevenn.calculator import SevenNetCalculator
import os
import numpy as np
import sys

sys.stdout.flush()

# ==============================================
# 1. Atomic Structure
# ==============================================
vasp_file = 'hollow.vasp'

try:
    atoms = read(vasp_file, format='vasp')
    print(f"Successfully read {len(atoms)} atoms from {vasp_file}", flush=True)
except FileNotFoundError:
    print(f"Error: {vasp_file} not found!", flush=True)
    sys.exit(1)
except Exception as e:
    print(f"Error reading {vasp_file}: {e}", flush=True)
    sys.exit(1)

# ==============================================
# 2. Calculator Configuration (SevenNet)
# ==============================================
model_path = '../../checkpoint_best.pth'

sevennet_calc = SevenNetCalculator(model=model_path, device='cuda')
atoms.calc = sevennet_calc

# ==============================================
# 3. Atom Relaxation
# ==============================================
print("Starting atom relaxation with SevenNet forces via ASE...", flush=True)

# Create trajectory file
traj = Trajectory('hollow_SevenNet.traj', 'w', atoms)

# Define optimization (BFGS)
opt = BFGS(atoms, logfile='hollow_SevenNet.log', trajectory=traj)

try:
    # Run optimization
    opt.run(fmax=0.01)  # Convergence criterion

    # Calculate final energy
    total_energy = atoms.get_potential_energy()

    # Print final energy
    print("\n=== Final Relaxation Results ===", flush=True)
    print("\nEnergy Components:", flush=True)
    print(f"  SevenNet Total Energy:   {total_energy:>12.6f} eV", flush=True)

    # Get final forces from the optimizer's atoms (fail-safe with filters)
    forces = opt.atoms.get_forces()

    # Force analysis
    force_norms = np.linalg.norm(forces, axis=1)  # Euclidean norms
    max_force = np.max(force_norms)               # ASE-style max norm

    # Print results
    print("\nFinal forces", flush=True)
    print(f"  ASE-style max force (norm)    : {max_force:>8.6f} eV/Å", flush=True)

    # Save final structure
    write('relaxed_hollow_SevenNet.vasp', atoms, format='vasp', direct=False)
    print("\n=== Final structure saved to: 'relaxed_hollow_SevenNet.vasp' ===", flush=True)

except Exception as e:
    print(f"\nRelaxation failed: {str(e)}", flush=True)
finally:
    traj.close()
