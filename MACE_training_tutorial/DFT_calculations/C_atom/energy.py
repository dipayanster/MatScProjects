#!/usr/bin/env python
from ase import Atoms
from ase.calculators.espresso import Espresso, EspressoProfile
from ase.io import read, write
import numpy as np
import sys
sys.stdout.flush()

# ==============================================
# 1. Quantum Espresso Input Parameters
# ==============================================
pseudopotentials = {
    'C': 'C.pbe-n-kjpaw_psl.1.0.0.UPF'
}

input_data = {
    'control': {
        'prefix': 'C_atom',
        'outdir': './tmp',
        'verbosity': 'low',
        'disk_io': 'minimal'
    },
    'system': {
        'ecutwfc': 50,
        'ecutrho': 400,
        'occupations': 'smearing',
        'smearing': 'gauss',
        'degauss': 0.01,
        'assume_isolated': 'martyna-tuckerman',
        'ibrav': 0,
        'nat': 1,
        'ntyp': 1
    },
    'electrons': {
        'conv_thr': 1.0e-10
    }
}

# ==============================================
# 2. Atomic Structure (single atom in a box)
# ==============================================
vasp_file = 'atom.vasp'

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
qe_bin = "/home/dsen/work/bin/qe-7.4.1"
pw_command = f'mpirun -np 8 {qe_bin}/bin/pw.x'

profile = EspressoProfile(
    command=pw_command,
    pseudo_dir='./'
)

qe_calc = Espresso(
    profile=profile,
    pseudopotentials=pseudopotentials,
    input_data=input_data,
    kpts=(1, 1, 1)
)

atoms.calc = qe_calc

# ==============================================
# 4. SCF Calculation
# ==============================================
print("Starting SCF calculation for isolated atom...", flush=True)

total_energy = atoms.get_potential_energy()

print("\n=== SCF Results ===", flush=True)
print(f"  QE Electronic Energy:    {total_energy:>12.6f} eV", flush=True)

