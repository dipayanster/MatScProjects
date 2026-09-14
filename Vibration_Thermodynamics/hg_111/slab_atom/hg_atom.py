#!/usr/bin/env python
from ase import Atoms
from ase.calculators.espresso import Espresso, EspressoProfile
from dftd4.ase import DFTD4
from ase.io import write
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
    'Hg': 'Hg_PBE_fr.upf'
}

input_data = {
    'control': {
        'verbosity': 'low',
        'disk_io': 'minimal'
    },
    'system': {
#       'input_dft': 'XC-000I-000I-116L-133L-000I-000I',
        'ecutwfc': 120,
        'occupations': 'fixed',
        'assume_isolated': 'martyna-tuckerman',
        'nosym': True,
        'noinv': True,
        'ibrav': 0,
        'nat': 1,
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
        'conv_thr': 1.0e-9
    }
}


# ==============================================
# 2. Atomic Structure and Cell Parameters
# ==============================================
atoms = Atoms(
    symbols=['Hg'],
    positions=[ # positions in Angstrom
        [10.0000000000, 10.0000000000, 10.0000000000],
    ],
    cell=[ # positions in Angstrom
        [20.0000000000, 0.0000000000, 0.0000000000],
        [0.0000000000, 20.0000000000, 0.0000000000],
        [0.0000000000, 0.0000000000, 20.0000000000]
    ],
    pbc=[True, True, True]
)


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
    kpts=(1, 1, 1), 
    koffset=(0, 0, 0) 
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
# 5. Run SCF Calculation
# ==============================================

print("\nStarting SCF total energy calculation with QE+D4...", flush=True)

# Get total energy (QE+D4) from combined calculator
total_energy = combined_calc.get_potential_energy(atoms)

# Get individual components
qe_energy = qe_calc.get_potential_energy(atoms)
d4_energy = dftd4_calc.get_potential_energy(atoms)

# Verify sum matches combined energy
tolerance = 1e-6  # eV
sum_energy = qe_energy + d4_energy
energy_diff = abs(total_energy - sum_energy)

print("\nSCF Energy Results:", flush=True)
print(f"  QE Electronic Energy: {qe_energy:.6f} eV", flush=True)
print(f"  DFT-D4 Dispersion:    {d4_energy:.6f} eV", flush=True)
print(f"  Sum (QE + D4):        {sum_energy:.6f} eV", flush=True)
print(f"  Total Energy (QE+D4): {total_energy:.6f} eV", flush=True)

if energy_diff > tolerance:
    print(f"\nWARNING: Energy difference exceeds tolerance ({energy_diff:.2e} eV)", flush=True)
    print("Possible causes:", flush=True)
    print("1. Different atomic positions used in calculations", flush=True)
    print("2. Numerical precision issues in SumCalculator", flush=True)
    print("3. Convergence problems in either QE or DFTD4", flush=True)
else:
    print("\nEnergy sum verified (QE + D4 = Total within tolerance)", flush=True)
    print(f"Difference: {energy_diff:.2e} eV", flush=True)

# Force final flush
sys.stdout.flush()