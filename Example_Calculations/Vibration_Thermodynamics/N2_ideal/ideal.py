#!/usr/bin/env python
import os
import sys

# Cache fix for compute nodes (AlmaLinux + ZFS home)
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
from ase.thermochemistry import IdealGasThermo
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

# 3b. Ideal-gas thermo settings
# geometry: 'monatomic' | 'linear' | 'nonlinear'
# symmetrynumber: rotational symmetry number (int)
#   - 1 : no rotational symmetry / heteronuclear diatomic (CO, NO)
#   - 2 : homonuclear diatomic (N2, O2), H2O
#   - 3 : NH3 ; 12 : CH4
# spin: total spin S (NOT multiplicity)
#   - 0.0 : singlet   (N2, H2O, Hg, CH4)
#   - 0.5 : doublet   (NO, OH radical)
#   - 1.0 : triplet   (O2)

geometry       = 'linear'    
symmetrynumber = 2
spin           = 0.0
T_std          = 298.15     # K (standard temperature, 25 °C)
P_std          = 101325.0   # Pa (standard pressure, 1 bar)

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
print(f"  Total Energy :  {total_energy:>12.6f} eV", flush=True)

energy_diff = abs(total_energy - (qe_energy + d4_energy))
if energy_diff <= 0.001:
    print(f"    Energy check: consistent", flush=True)
else:
    print(f"    Energy check: inconsistent (Δ={energy_diff:.6f} eV)", flush=True)

# ==============================================
# 5. Vibrational Analysis
# ==============================================
# A single atom in a box has NO vibrational modes (3N-3 = 0).
# Anything with >=2 atoms does have modes and must be run.
if len(atoms) < 2:
    print("\n[Phase B.] Skipping vibrational analysis "
          "Single atom: no vibrational modes", flush=True)
    vib_energies = np.array([])
else:
    print(f"\n[Phase B.] Calculating vibrations for "
          f"{len(atoms)} atoms...", flush=True)    

    vib = Vibrations(atoms, indices=None, name='vib', delta=0.01)
    vib.run()

    print("\n" + "="*70, flush=True)
    print("Vibrational Analysis Summary:", flush=True)
    print("-"*70, flush=True)
    vib.summary()
    print("="*70, flush=True)

    vib_energies = vib.get_energies()
    print(f"  Collected {len(vib_energies)} vibrational energies", flush=True)

# ==============================================
# 6. Thermodynamic Analysis (Ideal Gas)
# ==============================================
print(f"\n[Phase C.] Ideal Gas Thermodynamic Analysis", flush=True)
print(f"  Geometry:          {geometry}", flush=True)
print(f"  Symmetry number:   {symmetrynumber}", flush=True)
print(f"  Spin:              {spin}", flush=True)
print(f"  Number of atoms:   {len(atoms)}", flush=True)
print(f"  Vibrational modes: {len(vib_energies)}", flush=True)

thermo_atoms = atoms.copy()
thermo_atoms.pbc = False #ASE 3.28+ includes PBC check, used to work with periodic atom objects in 3.26

thermo = IdealGasThermo(
    vib_energies=vib_energies,
    potentialenergy=initial_energy,
    atoms=thermo_atoms,
    geometry=geometry,
    symmetrynumber=symmetrynumber,
    spin=spin,
    ignore_imag_modes=True
)

temperatures = np.arange(50, 501, 10)

print("\n" + "="*100, flush=True)
print(f"{'Temp(K)':>7}   {'ZPE(eV)':>10}   {'H(eV)':>14}   {'S(eV/K)':>14}   {'G(eV)':>14}", flush=True)
print("-"*100, flush=True)

results = {}

for T in temperatures:
    zpe = thermo.get_ZPE_correction()

    H = thermo.get_enthalpy(T, verbose=False)
    S = thermo.get_entropy(T, P_std, verbose=False)
    G = thermo.get_gibbs_energy(T, P_std, verbose=False)

    results[T] = {
        'ZPE': zpe,
        'H': H,
        'S': S,
        'G': G,
    }

    print(f"{T:7.0f}   {zpe:10.6f}   {H:14.6f}   {S:14.6e}   {G:14.6f}", flush=True)

print("="*100, flush=True)

# Separate section for 298.15 K
print("\n" + "-"*100, flush=True)
print("Temperature: 298.15 K (Standard Conditions)", flush=True)
print("-"*100, flush=True)

zpe_std = thermo.get_ZPE_correction()
H_std = thermo.get_enthalpy(T_std, verbose=False)
S_std = thermo.get_entropy(T_std, P_std, verbose=False)
G_std = thermo.get_gibbs_energy(T_std, P_std, verbose=False)

print(f"  ZPE = {zpe_std:12.6f} eV", flush=True)
print(f"  H   = {H_std:12.6f} eV  (Enthalpy)", flush=True)
print(f"  S   = {S_std:12.6e} eV/K  (Entropy)", flush=True)
print(f"  G   = {G_std:12.6f} eV  (Gibbs Free Energy)", flush=True)
print("-"*100, flush=True)

# Consistency check
print("\nAdditional Thermodynamic Relations Check (298.15 K):", flush=True)
print(f"  G = H - T*S  =>  {G_std:.6f} = {H_std:.6f} - {T_std:.2f}*{S_std:.6e} = {H_std - T_std*S_std:.6f} eV", flush=True)

print("\n=== Thermodynamic Analysis Complete ===", flush=True)
sys.stdout.flush()