#!/usr/bin/env python
import os
import sys
# ==============================================
# Cache fix for compute nodes (AlmaLinux + ZFS home)
# ==============================================
cache_dir = os.path.join(os.getcwd(), 'cache')
os.makedirs(cache_dir, exist_ok=True)
os.environ['XDG_CACHE_HOME'] = cache_dir
os.environ['MPLCONFIGDIR'] = os.path.join(cache_dir, 'matplotlib')
os.makedirs(os.environ['MPLCONFIGDIR'], exist_ok=True)

from ase import Atoms
from ase.calculators.espresso import Espresso, EspressoProfile
from dftd4.ase import DFTD4
from ase.io import read, write
from ase.calculators.mixing import SumCalculator
from dftd4.interface import DampingParam
from dftd4.parameters import get_damping_param
from ase.vibrations import Vibrations
from ase.thermochemistry import HarmonicThermo
import numpy as np
sys.stderr = sys.stdout
sys.stdout.flush()

# ==============================================
# 1. Quantum Espresso input parameters
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
    }
}

# ==============================================
# 2. Import atomic structure
# ==============================================
vasp_file = 'final_relaxed_structure.vasp'  

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
# 3. Calculator configuration
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
    kpts=(1, 1, 1), 
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

vib_atom_index = None
#vib_atom_index = [1]

if vib_atom_index is None:
    print("\nVibrating atoms: ALL freely moving atoms (constraints will be respected)", flush=True)
else:
    atom_list = [f"{idx} ({atoms.symbols[idx]})" for idx in vib_atom_index]
    print(f"\nVibrating atoms (0 based): {', '.join(atom_list)}", flush=True)

# ==============================================
# 4. SCF Calculation 
# ==============================================
print("\nPBE default DFT-D4 parameters :", get_damping_param("pbe"), flush=True)
print("Custom DFT-D4 parameters      :", custom_params, flush=True)

print("\n[Phase A.] Running SCF calculation...", flush=True)
total_energy = combined_calc.get_potential_energy(atoms)
initial_energy = total_energy

qe_energy = qe_calc.get_potential_energy(atoms)
d4_energy = dftd4_calc.get_potential_energy(atoms)

print("\n 1. SCF Energy Results", flush=True)
print(f"  QE Electronic Energy:    {qe_energy:>12.6f} eV", flush=True)
print(f"  DFT-D4 Dispersion:       {d4_energy:>12.6f} eV", flush=True)
print(f"  Total Energy (QE + D4):  {total_energy:>12.6f} eV", flush=True)

energy_diff = abs(total_energy - (qe_energy + d4_energy))
if energy_diff <= 0.001:
    print(f"    Energy check: consistent", flush=True)
else:
    print(f"    Energy check: inconsistent (Δ={energy_diff:.6f} eV)", flush=True)

forces = atoms.get_forces()
stress = atoms.get_stress()

force_norms = np.linalg.norm(forces, axis=1)
max_force = np.max(force_norms)
pressure = -np.sum(stress[:3]) * 1602.1766208 / 3

print("\n 2. SCF forces and stress", flush=True)
print(f"  Max force (norm): {max_force:>8.6f} eV/Å", flush=True)
print(f"  Pressure: {pressure:>8.6f} kbar", flush=True)

# ==============================================
# 5. Vibrational Analysis
# ==============================================
print("\n[Phase B.] Starting vibrational analysis...", flush=True)
  
vib = Vibrations(atoms, indices=vib_atom_index, name='vib', delta=0.01)
vib.run()

print("\n" + "="*70, flush=True)
print("Vibrational Analysis Summary:", flush=True)
print("-"*70, flush=True)
vib.summary()
print("="*70, flush=True)

vib_energies = vib.get_energies()

# ==============================================
# 6. Thermodynamic Analysis
# ==============================================
thermo = HarmonicThermo(
    vib_energies=vib_energies,
    potentialenergy=initial_energy,
    ignore_imag_modes=True
)

temperatures = np.arange(50, 501, 10)

print("\n[Phase C.] Starting thermodynamic analysis...")
print("\n" + "="*95, flush=True)
print(f"{'Temp(K)':>5}   {'ZPE(eV)':>8}   {'F(eV)':>14}   {'U(eV)':>14}   {'S(eV/K)':>12}", flush=True)
print("-"*95, flush=True)

for T in temperatures:
    zpe = thermo.get_ZPE_correction()
    
    if T == 0:
        F = zpe
        U = zpe
        S = 0.0
    else:
        with np.errstate(divide='ignore', invalid='ignore'):
            F = thermo.get_helmholtz_energy(T, verbose=False)
            U = thermo.get_internal_energy(T, verbose=False)
            S = thermo.get_entropy(T, verbose=False)
    
    print(f"{T:5.0f}   {zpe:8.6f}   {F:14.6f}   {U:14.6f}   {S:12.6e}", flush=True)

print("="*95, flush=True)

# Separate section for 298.15 K
print("\n" + "-"*95, flush=True)
print("Temperature: 298.15 K", flush=True)
print("-"*95, flush=True)

zpe_298 = thermo.get_ZPE_correction()
F_298 = thermo.get_helmholtz_energy(298.15, verbose=False)
U_298 = thermo.get_internal_energy(298.15, verbose=False)
S_298 = thermo.get_entropy(298.15, verbose=False)

print(f"  ZPE = {zpe_298:10.6f} eV", flush=True)
print(f"  F   = {F_298:10.6f} eV", flush=True)
print(f"  U   = {U_298:10.6f} eV", flush=True)
print(f"  S   = {S_298:10.6e} eV/K", flush=True)
print("-"*95, flush=True)

print("\n=== Thermodynamic Analysis Complete ===", flush=True)
sys.stdout.flush()