#!/usr/bin/env python
from ase import Atoms
from ase.calculators.espresso import Espresso, EspressoProfile
from ase.io import read, write
from ase.optimize import BFGS
import numpy as np
import sys
from ase.filters import UnitCellFilter 
sys.stdout.flush()

# ==============================================
# ASE full relaxation (unitcell + atom) 
# ==============================================

# ==============================================
# 1. Quantum Espresso Input Parameters
# ==============================================
pseudopotentials = {
    'Be': 'Be.upf',
    'O': 'O.upf',
}

input_data = {
    'control': {
        'prefix': 'BeO',
        'outdir': './tmp',
        'verbosity': 'low',
        'disk_io': 'minimal',
        'tstress': True,
        'tprnfor': True
    },
    'system': {
        'ecutwfc': 125,
        'occupations': 'smearing',
        'smearing': 'gauss',
        'degauss': 0.01,
        'ibrav': 0,
        'nat': 4,
        'ntyp': 2
    },
    'electrons': {
        'mixing_beta': 0.2,
        'electron_maxstep': 100,
        'diagonalization': 'david',
        'diago_full_acc': True,
        'startingpot': 'atomic',
        'startingwfc': 'atomic+random',
        'conv_thr': 1.0e-10
    }
}

# ==============================================
# 2. Atomic Structure 
# ==============================================
vasp_file = '1739328.vasp' 

try:
    atoms = read(vasp_file, format='vasp')
    print(f"Successfully read {len(atoms)} atoms from {vasp_file}")
except FileNotFoundError:
    print(f"Error: {vasp_file} not found!")
    sys.exit(1)
except Exception as e:
    print(f"Error reading {vasp_file}: {e}")
    sys.exit(1)

# ==============================================
# 3. Calculator Configuration
# ==============================================
# Set QE bin directory 
qe_bin = "/home/dsen/work/bin/qe-7.4.1/bin"

# Job commands
pw_command = f'mpirun -np 8 {qe_bin}/pw.x'

pw_profile = EspressoProfile(
    command=pw_command,
    pseudo_dir='./'
)

calc = Espresso(
    profile=pw_profile,
    pseudopotentials=pseudopotentials,
    input_data=input_data,
    kpts=(10,10,5)  # Fixed k-points
)

atoms.calc = calc

# ==============================================
# 4. Cell Relaxation
# ==============================================
print("\nStarting cell relaxation by ASE", flush=True)

# Define the constraint mask: [xx, yy, zz, yz, xz, xy]
mask = [True, True, True,  # Relax xx (a), yy (b); zz (c)
        False, False, False]  # Fix all angles (no distortion)

# Setup full cell relaxation
ucf = UnitCellFilter(atoms, mask=mask)

# Create a trajectory file to store relaxation steps
from ase.io.trajectory import Trajectory
traj = Trajectory('relaxation.traj', 'w', atoms)

# Pass the Trajectory object to BFGS 
opt = BFGS(ucf, trajectory=traj, logfile='relaxation.log')

try:
    opt.run(fmax=0.01) # Convergence criterion: max force < 0.01 eV/Å
        
    # Get final results
    final_energy = atoms.get_potential_energy()
    forces = opt.atoms.get_forces()
    qe_style_forces = atoms.get_forces() 
    stress = atoms.get_stress()
     
    # Analysis
    force_norms = np.linalg.norm(forces, axis=1)  # Euclidean norms
    max_force = np.max(force_norms)               # ASE-style max norm
    max_qe_force = np.max(np.abs(qe_style_forces)) # Max component across all atoms/directions
    pressure = -np.sum(stress[:3]) * 1602.1766208 / 3

    # Print results
    print("\nFinal results", flush=True)    
    print(f"  Total Energy                  : {final_energy:>12.6f} eV", flush=True)
    print(f"  ASE-style max force (norm)    : {max_force:>8.6f} eV/Å", flush=True)
    print(f"  QE-style max force            : {max_qe_force:>8.6f} eV/Å", flush=True)
    print(f"  Pressure                      : {pressure:>8.6f} kbar", flush=True)

    # Save final structure
    write('final_relaxed_structure.vasp', atoms, format='vasp', direct=False)
    print("\nFinal relaxed structure saved to: final_relaxed_structure.vasp", flush=True)

except Exception as e:
    print(f"\nRelaxation failed: {str(e)}", flush=True)
    print("Check output files for error details", flush=True)
finally:
    traj.close()
    print("\nRelaxation complete", flush=True)