#!/usr/bin/env python
from ase import Atoms
from ase.calculators.espresso import Espresso, EspressoProfile
from ase.io import read
import os
import numpy as np
import sys
sys.stdout.flush()

# ==============================================
# ASE Convergence test (Cutoff and K-points)
# ==============================================

# ==============================================
# 1. Quantum Espresso input parameters
# ==============================================
pseudopotentials = {
    'Be': 'Be.upf',
    'O': 'O.upf',
}


# Base SCF input parameters
base_input_data = {
    'control': {
        'prefix': 'BeO',
        'outdir': './tmp',
        'verbosity': 'low',
        'disk_io': 'minimal'
    },
    'system': {
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
# 2. Import atomic structure 
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
# 3. Calculator configuration
# ==============================================
# Set QE bin directory 
qe_bin = "/home/dsen/work/bin/qe-7.4.1/bin"

# Job commands
#pw_command = f'{qe_bin}/bin/pw.x'
pw_command = f'mpirun -np 8 {qe_bin}/pw.x'

pw_profile = EspressoProfile(
    command=pw_command,
    pseudo_dir='./'
)

# Test values
ecutwfc_values = np.arange(50, 200, 5)  
kpoints_values = [(2*k,2*k,k) for k in range(2, 12)] 

# Convergence threshold (meV/atom)
energy_tol = 0.01  

# ==============================================
# 4. Run Convergence Tests
# ==============================================
def run_convergence_test():
    results = []
    natoms = base_input_data['system']['nat']  
    
    # Determine intermediate k-point grid for cutoff testing (ensuring integer values)
    mid_index = len(kpoints_values) // 2
    k_intermediate = kpoints_values[mid_index]
    print(f"\nUsing k-point grid {k_intermediate} for ecutwfc convergence testing", flush=True)
    
    print("\nStarting convergence tests...", flush=True)
    print("="*60, flush=True)
    
    # 1. ecutwfc convergence testing
    print("\n1. Testing ecutwfc convergence with k-point grid", k_intermediate, ":", flush=True)
    print("-"*60, flush=True)
    print("ecutwfc (Ry)   Energy (eV)    ΔE (meV/atom)", flush=True)
    print("-"*60, flush=True)
    
    prev_energy = None
    converged_ecut = None
    
    for ecut in ecutwfc_values:
        input_data = base_input_data.copy()
        input_data['system']['ecutwfc'] = int(ecut)
        
        calc = Espresso(
            profile=pw_profile,
            pseudopotentials=pseudopotentials,
            input_data=input_data,
            kpts=k_intermediate)
        atoms.calc = calc
        energy = atoms.get_potential_energy()
        
        if prev_energy is not None:
            delta_e = (energy - prev_energy)/natoms * 1000  # meV/atom
            converged = "*" if abs(delta_e) < energy_tol else ""
            print(f"{ecut:10.1f}    {energy:12.6f}   {delta_e:8.3f} {converged}", flush=True)
            
            if abs(delta_e) < energy_tol and converged_ecut is None:
                converged_ecut = ecut
                print("-"*60, flush=True)
                print(f">>> ecutwfc CONVERGED at {ecut} Ry (ΔE < {energy_tol} meV/atom)", flush=True)
                print("-"*60, flush=True)
                break
        else:
            print(f"{ecut:10.1f}    {energy:12.6f}     -", flush=True)
        
        results.append(('ecut', ecut, k_intermediate, energy, delta_e if prev_energy is not None else 0))
        prev_energy = energy
    
    # 2. k-point convergence testing
    print("\n2. Testing k-point convergence with ecutwfc =", 
          f"{converged_ecut if converged_ecut else ecutwfc_values[-1]} Ry" +
          f"{' (using max value)' if not converged_ecut else ''}:", flush=True)
    print("-"*60, flush=True)
    print("K-point grid   Energy (eV)    ΔE (meV/atom)", flush=True)
    print("-"*60, flush=True)
    
    prev_k_energy = None
    converged_kpts = None
    
    for kpts in kpoints_values:
        input_data = base_input_data.copy()
        input_data['system']['ecutwfc'] = int(converged_ecut if converged_ecut else ecutwfc_values[-1])
        
        calc = Espresso(
            profile=pw_profile,
            pseudopotentials=pseudopotentials,
            input_data=input_data,
            kpts=kpts)
        atoms.calc = calc
        energy = atoms.get_potential_energy()
        
        if prev_k_energy is not None:
            delta_e = (energy - prev_k_energy)/natoms * 1000  # meV/atom
            converged = "*" if abs(delta_e) < energy_tol else ""
            print(f"{str(kpts):12s}    {energy:12.6f}   {delta_e:8.3f} {converged}", flush=True)
            
            if abs(delta_e) < energy_tol and converged_kpts is None:
                converged_kpts = kpts
                print("-"*60, flush=True)
                print(f">>> K-points CONVERGED at {kpts} (ΔE < {energy_tol} meV/atom)", flush=True)
                print("-"*60, flush=True)
                break
        else:
            print(f"{str(kpts):12s}    {energy:12.6f}     -", flush=True)
        
        results.append(('kpts', converged_ecut if converged_ecut else ecutwfc_values[-1], 
                       kpts, energy, delta_e if prev_k_energy is not None else 0))
        prev_k_energy = energy
    
    print("="*60, flush=True)
    print("Convergence summary:", flush=True)
    print(f"- ecutwfc: {converged_ecut if converged_ecut else 'Not converged (using max value)'}", flush=True)
    print(f"- k-points: {converged_kpts if converged_kpts else 'Not converged'}", flush=True)
    print("="*60, flush=True)
    
    return results

# Run the tests
convergence_results = run_convergence_test()