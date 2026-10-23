#!/usr/bin/env python
from ase import Atoms
from ase.io import read
from mace.calculators import MACECalculator
import os
import numpy as np
import sys
sys.stdout.flush()

# ==============================================
# 1. Atomic Structure (single atom in a box)
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
# 2. Calculator Configuration (MACE)
# ==============================================
model_path = '../../MACE_GrapheneHg.model'

mace_calc = MACECalculator(
    model_paths=model_path,
    device='cpu',          # change to 'cuda' if GPU available
    default_dtype='float64'
)
atoms.calc = mace_calc

# ==============================================
# 3. Energy Calculation
# ==============================================
print("Calculating energy for isolated atom with MACE...", flush=True)

total_energy = atoms.get_potential_energy()

print("\n=== Energy Results ===", flush=True)
print(f"  MACE Total Energy:       {total_energy:>12.6f} eV", flush=True)