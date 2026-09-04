#!/usr/bin/env python
from ase import Atoms
from ase.calculators.espresso import Espresso, EspressoProfile
from dftd4.ase import DFTD4
from ase.io import read, write
from ase.optimize import BFGS
from ase.io.trajectory import Trajectory
#from ase.constraints import FixAtoms
from ase.calculators.mixing import SumCalculator
from dftd4.interface import DampingParam
from dftd4.parameters import get_damping_param
import os
import numpy as np
import sys
sys.stdout.flush()

# ==============================================
# ASE relax 
# ==============================================

# ==============================================
# 1. Quantum Espresso Input Parameters
# ==============================================
pseudopotentials = {
    'N': 'N.pbe-n-kjpaw_psl.1.0.0.UPF',
}

input_data = {
    'control': {
        'prefix': 'vibN',
        'outdir': './tmp',
        'verbosity': 'low',
        'tstress': True,
        'tprnfor': True,
        'disk_io': 'minimal'
    },
    'system': {
        'ecutwfc': 80,
        'ecutrho': 640,
        'occupations': 'smearing',
        'smearing': 'gauss',
        'degauss': 0.01,
        'ibrav': 0,
        'nat': 2,
        'ntyp': 1,
    },
    'electrons': {
        'mixing_beta': 0.2,
        'electron_maxstep': 100,
        'diagonalization': 'david',
        'diago_full_acc': True,
        'startingpot': 'atomic',
        'startingwfc': 'atomic+random',
        'conv_thr': 1.0e-9,
#       'diago_thr_init': 1.0e-6,
    }
}

# ==============================================
# 2. Atomic Structure 
# ==============================================
vasp_file = 'n.vasp'  

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

profile = EspressoProfile(
    command=pw_command,
    pseudo_dir='./'
)

qe_calc = Espresso(
    profile=profile,
    pseudopotentials=pseudopotentials,
    input_data=input_data,
    kpts=(1, 1, 1), 
#    koffset=(1, 1, 0) 
)

custom_params = {
    's6': 1.0, # Two-body dispersion scaling
    's9': 1.0, # Higher-order dispersion scaling 
    'alp': 16.0, # Damping attenuation steepness   
    's8': 0.95948085, # Three-body dispersion scaling
    'a1': 0.38574991, # Damping function parameter 1
    'a2': 4.80688534, # Damping function parameter 2
}
dftd4_calc = DFTD4(verbose=True, params_tweaks=custom_params)

combined_calc = SumCalculator([qe_calc, dftd4_calc])
atoms.calc = combined_calc

# ==============================================
# 5. Run atom relaxation
# ==============================================
print("Starting atom relaxation with QE+D4 forces via ASE...", flush=True)

print("\nPBE default DFT-D4 parameters :", get_damping_param("pbe"), flush=True)
print("Custom DFT-D4 parameters      :", custom_params, flush=True)

# Create trajectory file
traj = Trajectory('relaxation.traj', 'w', atoms)

# Define optimization (BFGS)
opt = BFGS(atoms, logfile='relaxation.log', trajectory=traj)

try:
    opt.run(fmax=0.001) # Convergence criterion: max force < 0.001 eV/Å
        
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