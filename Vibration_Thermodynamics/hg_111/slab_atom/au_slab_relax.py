#!/usr/bin/env python
from ase import Atoms
from ase.calculators.espresso import Espresso, EspressoProfile
from dftd4.ase import DFTD4
from ase.io import read, write
from ase.optimize import BFGS
from ase.io.trajectory import Trajectory
#from ase.constraints import FixAtoms
from ase.filters import UnitCellFilter 
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
    'Au': 'Au_PBE_fr.upf',
}

input_data = {
    'control': {
        'prefix': 'Au_SOCD4',
        'outdir': './tmp',
        'verbosity': 'low',
        'tstress': True,
        'tprnfor': True,
        'disk_io': 'minimal'
    },
    'system': {
#       'input_dft': 'XC-000I-000I-116L-133L-000I-000I',
        'ecutwfc': 120,
        'occupations': 'smearing',
        'smearing': 'gauss',
        'degauss': 0.01,
#       'assume_isolated': '2D',
        'nosym': True,
        'noinv': True,
        'ibrav': 0,
        'nat': 48,
        'ntyp': 1,
        'noncolin': True,
        'lspinorb': True
    },
    'electrons': {
        'mixing_beta': 0.2,
        'electron_maxstep': 100,
        'diagonalization': 'david',
        'diago_full_acc': True,
        'startingpot': 'atomic',
        'startingwfc': 'atomic+random',
        'conv_thr': 1.0e-9,
#        'diago_thr_init': 1.0e-6,
    }
}

# ==============================================
# 2. Import atomic structure
# ==============================================
vasp_file = 'startPBEsol_111_120526.vasp'  

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
# 3. Set Constraints
# ==============================================

#fixed_indices = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52]
#constraint = FixAtoms(indices=fixed_indices)
#atoms.set_constraint(constraint)

# ==============================================
# 4. Define Calculator Configuration
# ==============================================
# Main QE calculation with full parallelization
pw_command = f'srun -v   --mpi=pmi2    {os.environ["QE"]}/bin/pw.x '

profile = EspressoProfile(
    command=pw_command,
    pseudo_dir='./'
)

qe_calc = Espresso(
    profile=profile,
    pseudopotentials=pseudopotentials,
    input_data=input_data,
    kpts=(3, 3, 1), 
    koffset=(1, 1, 0) 
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
# 5. Run Cell Relaxation (Slab, Cell Angles Fixed)
# ==============================================

print("Starting relaxation with QE+D4 forces via ASE...")
print("PBE default DFT-D4 parameters :", get_damping_param("pbe"), flush=True)
print("Custom DFT-D4 parameters      :", custom_params, flush=True)

# Define the constraint mask: [xx, yy, zz, yz, xz, xy]
mask = [True, True, False,  # Relax xx (a), yy (b); fix zz (c)
        False, False, False]  # Fix all angles (no distortion)

# Apply UnitCellFilter to enable cell relaxation
ucf = UnitCellFilter(atoms, mask=mask)

# Create a trajectory file to store relaxation steps
traj = Trajectory('relaxation.traj', 'w', atoms)

# Pass the Trajectory object directly to BFGS 
opt = BFGS(ucf, trajectory=traj, logfile='relaxation.log')

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
    write('final_relaxed_structure.vasp', atoms, format='vasp', direct=False)
    print("\n=== Final structure saved to: 'final_relaxed_structure.vasp' ===")

except Exception as e:
    print(f"\nRelaxation failed: {str(e)}")
finally:
    traj.close()