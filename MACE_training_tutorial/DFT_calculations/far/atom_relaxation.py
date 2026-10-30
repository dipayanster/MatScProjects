#!/usr/bin/env python
from ase import Atoms
from ase.calculators.espresso import Espresso, EspressoProfile
from dftd4.ase import DFTD4
from ase.io import read, write
from ase.optimize import BFGS
from ase.io.trajectory import Trajectory
from ase.calculators.mixing import SumCalculator
from dftd4.interface import DampingParam
from dftd4.parameters import get_damping_param
import os
import numpy as np
import sys
sys.stdout.flush()

# ==============================================
# 1. Quantum Espresso Input Parameters
# ==============================================
pseudopotentials = {
    'C': 'C.pbe-n-kjpaw_psl.1.0.0.UPF',
    'Hg': 'Hg.pbe-n-kjpaw_psl.1.0.0.UPF'
}

input_data = {
    'control': {
        'prefix': 'graphene',
        'outdir': './tmp',
        'verbosity': 'low',
        'tstress': True,
        'tprnfor': True,
        'disk_io': 'minimal'
    },
    'system': {
        'ecutwfc': 50,
        'ecutrho': 400,
        'occupations': 'smearing',
        'smearing': 'gauss',
        'degauss': 0.01,
        'ibrav': 0,
        'nat': 19,
        'ntyp': 2
    },
    'electrons': {
        'conv_thr': 1.0e-10
    }
}

# ==============================================
# 2. Atomic Structure 
# ==============================================
vasp_file = 'far.vasp'  

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
qe_bin = "/home/dsen/work/bin/qe-7.4.1"

# Job commands
pw_command = f'mpirun -np 8 {qe_bin}/bin/pw.x'

profile = EspressoProfile(
    command=pw_command,
    pseudo_dir='./'
)

qe_calc = Espresso(
    profile=profile,
    pseudopotentials=pseudopotentials,
    input_data=input_data,
    kpts=(3, 3, 1) 
)

custom_params = {
    's6': 1.0,
    's9': 1.0,
    'alp': 16.0, 
    's8': 0.95948085,
    'a1': 0.38574991,
    'a2': 4.80688534,
}
dftd4_calc = DFTD4(verbose=True, params_tweaks=custom_params)

combined_calc = SumCalculator([qe_calc, dftd4_calc])
atoms.calc = combined_calc

# ==============================================
# 4. Cell Relaxation
# ==============================================
print("Starting atom relaxation with QE+D4 forces via ASE...", flush=True)

print("\nPBE default DFT-D4 parameters :", get_damping_param("pbe"), flush=True)
print("Custom DFT-D4 parameters      :", custom_params, flush=True)

# Create trajectory file
traj = Trajectory('far.traj', 'w', atoms)

# Define optimization (BFGS)
opt = BFGS(atoms, logfile='far.log', trajectory=traj)

try:
    # Run optimization
    opt.run(fmax=0.01)  # Convergence criterion
   
    # Calculate final energies
    qe_energy = qe_calc.get_potential_energy(atoms)
    d4_energy = dftd4_calc.get_potential_energy(atoms)
    total_energy = combined_calc.get_potential_energy(atoms)
    
    # Print final energies
    print("\n=== Final Relaxation Results ===", flush=True)
    print(f"\nEnergy Components:", flush=True)
    print(f"  QE Electronic Energy:    {qe_energy:>12.6f} eV", flush=True)
    print(f"  DFT-D4 Dispersion:       {d4_energy:>12.6f} eV", flush=True)
    print(f"  Total Energy (QE + D4):  {total_energy:>12.6f} eV", flush=True)
    
    # Energy consistency check
    energy_diff = abs(total_energy - (qe_energy + d4_energy))
    if energy_diff <= 0.001:
        print(f"\nEnergy check: consistent")
    else:
        print(f"\nEnergy check: inconsistent (Δ={energy_diff:.6f} eV)")
    
    # Get final forces and stress
    forces = opt.atoms.get_forces() # From ASE relaxation steps
    qe_style_forces = atoms.get_forces() 
    stress = atoms.get_stress() #Using QE+DFT-D4 forces, different than pure QE results 
    
    # Force analysis
    force_norms = np.linalg.norm(forces, axis=1)  # Euclidean norms
    max_force = np.max(force_norms)               # ASE-style max norm
    max_qe_force = np.max(np.abs(qe_style_forces)) # Max component across all atoms/directions
    pressure = -np.sum(stress[:3]) * 1602.1766208 / 3 #kbar
     
    # Print results
    print("\nFinal forces and stress", flush=True)    
    print(f"  ASE-style max force (norm)    : {max_force:>8.6f} eV/Å", flush=True)
    print(f"  QE-style max force            : {max_qe_force:>8.6f} eV/Å", flush=True)
    print(f"  Pressure                      : {pressure:>8.6f} kbar", flush=True)
  
    # Save final structure
    write('relaxed_far.vasp', atoms, format='vasp', direct=False)
    print("\n=== Final structure saved to: 'relaxed_far.vasp' ===")

except Exception as e:
    print(f"\nRelaxation failed: {str(e)}")
finally:
    traj.close()