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
from ase.units import Hartree, eV, mol, kJ, invcm 
import numpy as np
sys.stdout.flush()

# ==============================================
# 1. Quantum Espresso input parameters
# ==============================================
pseudopotentials = {
    'O': 'O.pbe-n-kjpaw_psl.1.0.0.UPF',
}

input_data = {
    'control': {
        'prefix': 'vibO',
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
pw_command = f'mpirun -np 8 {qe_bin}/bin/pw.x'  # Parallel

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

# Vibrations (Only on specific atoms, 0 based index)
# Set to None to vibrate all free atoms, or provide a list for specific ones
vib_atom_index = None  # Or e.g., [0, 1]

# Dynamically print which atoms will be vibrated
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

#4.1 Get energies
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

#4.2 Get forces and stress
forces = atoms.get_forces()
stress = atoms.get_stress()

force_norms = np.linalg.norm(forces, axis=1)
max_force = np.max(force_norms)
pressure = -np.sum(stress[:3]) * 1602.1766208 / 3  # kbar

print("\n 2. SCF forces and stress", flush=True)
print(f"  Max force (norm): {max_force:>8.6f} eV/Å", flush=True)
print(f"  Pressure: {pressure:>8.6f} kbar", flush=True)

# ==============================================
# 5. Vibrational Analysis
# ==============================================
print("\n[Phase B.] Starting vibrational analysis...", flush=True)
  
vib = Vibrations(atoms, indices=vib_atom_index, name='vib', delta=0.01)
vib.run()

# Extract frequencies
all_frequencies = vib.get_frequencies()  # in cm^-1 (ASE default)

print("\n" + "="*70, flush=True)
print("Vibrational Frequencies:", flush=True)
print("-"*70, flush=True)
print(f"{'Mode':>6} {'Raw (cm⁻¹)':>14} {'Energy (eV)':>14} {'Status':>20}", flush=True)
print("-"*70, flush=True)

real_frequencies_cm = []
imaginary_frequencies_cm = []

for i, freq in enumerate(all_frequencies):
    freq_cm = freq.real  # real part in cm^-1
    freq_ev = freq_cm * invcm
    
    # Determine status
    if freq.imag != 0 or freq_cm <= 0:
        status = "IMAGINARY" if freq_cm <= 0 else "COMPLEX"
        imaginary_frequencies_cm.append(freq)
    else:
        status = "Stable"
        real_frequencies_cm.append(freq)
    
    print(f"{i+1:6d} {freq_cm:14.4f} {freq_ev:14.6f} {status:>20}", flush=True)

print("="*70, flush=True)

# Store real frequencies for thermodynamics (convert to eV)
real_frequencies_ev = np.array([freq.real * invcm for freq in real_frequencies_cm])

# Warn if there are imaginary frequencies
if len(imaginary_frequencies_cm) > 0:
    print("\n ***WARNING***: Imaginary frequencies detected (indicates possible instability):", flush=True)
    for i, freq in enumerate(imaginary_frequencies_cm):
        freq_cm = freq.real
        freq_ev = freq_cm * invcm
        print(f"  Mode {i+1}: {freq_cm:.4f} cm⁻¹ ({freq_ev:.6f} eV) imaginary", flush=True)
    print("\nProceeding with only real frequencies for thermodynamics.", flush=True)

# Check if we have valid frequencies
if len(real_frequencies_ev) == 0:
    raise ValueError("No real vibrational frequencies found!")
    
# These are all possible and indicate instability:
#(-5.0 + 0.0j)    # Negative real, zero imaginary → unstable
#(-2.5 + 1.5j)    # Negative real, non-zero imaginary → unstable
#(0.0 + 4.0j)     # Zero real, non-zero imaginary → unstable (pure imaginary)
#(3.0 + 0.0j)     # Positive real, zero imaginary → STABLE (only good case)

   
# ==============================================
# 6. Thermodynamic Analysis
# ==============================================
# Initialize with vibrational frequencies
thermo = HarmonicThermo(vib_energies=real_frequencies_ev)

# Temperature range and steps
temperatures = np.arange(50, 501, 10)

# Get electronic energy (from prior SCF)
electronic_energy = initial_energy

print("\n[Phase C.] Starting thermodynamic analysis...")
print("\n" + "="*65, flush=True)
print("Temp(K)   ZPE(eV)   F_thermal(eV)   F_vib(eV)   E_elec(eV)   E_total(eV)", flush=True)
print("-"*65, flush=True)

results = []
for T in temperatures:
    # Calculate components
    zpe = thermo.get_ZPE_correction()
    
    if T == 0:
        F_vib = zpe
        F_thermal = 0.0
    else:
        with np.errstate(divide='ignore', invalid='ignore'):
            F_vib = thermo.get_helmholtz_energy(T, verbose=False)
            F_thermal = F_vib - zpe
    
    total_energy = electronic_energy + F_vib
    results.append([T, zpe, F_thermal, F_vib, electronic_energy, total_energy])
    
    # Print formatted table
    print(f"{T:5.0f}   {zpe:7.6f}   {F_thermal:12.6f}   {F_vib:9.6f}   "
          f"{electronic_energy:10.6f}   {total_energy:10.6f}", flush=True)
         
print("\n=== Thermodynamic Analysis Complete ===", flush=True)
sys.stdout.flush() 