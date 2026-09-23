#!/usr/bin/env python
from ase import Atoms
from ase.calculators.espresso import Espresso, EspressoProfile
from ase.io import read, write
import os
import numpy as np
import subprocess
import shutil
import sys
sys.stdout.flush()  

# ==============================================
# ASE Band Structure Calculation
# ==============================================
#
# ==============================================
# 1. Quantum Espresso Input Parameters
# ==============================================
pseudopotentials = {
    'Be': 'Be.upf',
    'O': 'O.upf',
}

base_input_data = {
    'control': {
        'prefix': 'BeO_band',
        'outdir': './tmp',
        'verbosity': 'low',
        'disk_io': 'low',
        'tstress': True,
        'tprnfor': True
    },
    'system': {
        'ecutwfc': 125,
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
# 2. Atomic Structure (from seekpath)
#    https://seekpath.materialscloud.io/
# ==============================================
vasp_file = 'symmetrized_relaxed.vasp' 

try:
    prim_atoms = read(vasp_file, format='vasp')
    print(f"Successfully read {len(prim_atoms)} atoms from {vasp_file}")
except FileNotFoundError:
    print(f"Error: {vasp_file} not found!")
    sys.exit(1)
except Exception as e:
    print(f"Error reading {vasp_file}: {e}")
    sys.exit(1)

# ==============================================
# 3. K-point path for band structure calculation (from seekpath)
#    Labels of highly symmetric points are to be taken from seekpath
#    Copy the highly symmetric points list under "Quantum ESPRESSO pw.x input" in file 'kp'
#    Then use the following command to format it in ASE format
#    awk '{printf("    [%s, %s, %s, %s],\n", $1, $2, $3, $4)}' kp > kp_parsed
# ==============================================
kp_file = 'kp_parsed'

try:
    with open(kp_file, 'r') as f:
        content = f.read()
    namespace = {'np': np}
    exec(f"kpts_crystal = np.array([\n{content}\n])", namespace)
    kpts_crystal = namespace['kpts_crystal']
    print(f"Successfully read {len(kpts_crystal)} k-points from {kp_file}")
except FileNotFoundError:
    print(f"Error: {kp_file} not found!")
    sys.exit(1)
except Exception as e:
    print(f"Error reading {kp_file}: {e}")
    sys.exit(1)

# ==============================================
# 4. Calculator Configuration
# ==============================================
# Set QE bin directory 
qe_bin = "/home/dsen/work/bin/qe-7.4.1/bin"

# Job commands
# Main QE calculation 
pw_command = f'mpirun -np 8 {qe_bin}/pw.x'

# Serial post-processing commands for fast execution
bands_command = f"{qe_bin}/bands.x < bands.in > bands.out 2>&1"
plotband_command = f"{qe_bin}/plotband.x < plotband.in > plotband.out 2>&1"

profile = EspressoProfile(
    command=pw_command,
    pseudo_dir='./'
)

# Set k-grids (modify as needed)
scf_kpts = (10,10,5)

# Bands energy parameters
energy_range = -5, 25
tick = 2  

# QE tool executation format
def run_qe_tool(command, input_file, tool_name):
    """Run QE tool with input file and redirect output to file"""
    try:
        with open(input_file, 'r') as fin:
            subprocess.run(command, shell=True, stdin=fin, check=True)
        print(f"  {tool_name} completed successfully", flush=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {tool_name}: {e}", flush=True)
        return False

# ==============================================
# 5. SCF Calculation 
# ==============================================
print("\n[Phase A] Running SCF calculation...", flush=True)
scf_input_data = base_input_data.copy()
scf_input_data['control']['calculation'] = 'scf'

scf_calc = Espresso(
    profile=profile,
    pseudopotentials=pseudopotentials,
    input_data=scf_input_data,
    kpts=scf_kpts  
)
prim_atoms.calc = scf_calc
total_energy = prim_atoms.get_potential_energy()
fermi_energy = scf_calc.get_fermi_level()
print(f"  SCF completed. Total energy: {total_energy:.6f} eV", flush=True)
print(f"  Fermi energy from SCF: {fermi_energy:.6f} eV", flush=True)

# ==============================================
# 6. Clean up SCF files and prepare for NSCF
# ==============================================
print("\nCleaning up SCF files and preparing for band structure calculation...", flush=True)
os.makedirs('scf_files', exist_ok=True)

# Move ALL SCF-related files
for fname in os.listdir('.'):
    if (fname.startswith('Si_BandStructure.') or 
       fname in ['espresso.pwi', 'espresso.pwo']):
        shutil.move(fname, os.path.join('scf_files', fname))

print("  Moved all SCF-related files to scf_files directory", flush=True)

# ==============================================
# 7. NSCF (bands) Calculation
# ==============================================
print("\n[Phase B] Running NSCF (bands) calculation...", flush=True)
nscf_input_data = base_input_data.copy()
nscf_input_data['control']['calculation'] = 'bands'
nscf_input_data['control'].pop('tstress', None)
nscf_input_data['control'].pop('tprnfor', None)

nscf_calc = Espresso(
    profile=profile,
    pseudopotentials=pseudopotentials,
    input_data=nscf_input_data,
    kpts=kpts_crystal,
    kspacing=None
)

# Direct NSCF execution
nscf_calc.calculate(atoms=prim_atoms,
                   properties=[],
                   system_changes=['positions', 'cell', 'numbers', 'pbc'])
print("  NSCF (bands) calculation completed", flush=True)

# ==============================================
# 8. Extract bands
# ==============================================
print("  Calculating band structure from NSCF", flush=True)
with open('bands.in', 'w') as f:
    f.write(f"""&BANDS
    prefix = '{base_input_data['control']['prefix']}',
    outdir = '{base_input_data['control']['outdir']}',
    filband = 'bands.dat',
/
""")
run_qe_tool(bands_command, 'bands.in', 'bands.x')

# ==============================================
# 9. Plot bands
# ==============================================
print("  Plotting bands", flush=True)
with open('plotband.in', 'w') as f:
    f.write(f"""bands.dat
{energy_range[0]} {energy_range[1]}
bands.gnu
bands.ps
{fermi_energy}
{tick}, {fermi_energy} 
""")
run_qe_tool(plotband_command, 'plotband.in', 'plotband.x')

#if ghostscript installed, convert postscript to image directly. Otherwise disable this.
print("  Exporting plot as jpg image", flush=True)
os.system("gs -sDEVICE=jpeg -dJPEGQ=95 -r600 -sOutputFile=bands.jpg < bands.ps > gs.out")

print("\n=== Band Structure Calculation Complete ===", flush=True)
print("Generated files:", flush=True)
print(f"- SCF results: scf_files/", flush=True)
print(f"- Band structure data: bands.dat", flush=True)
print(f"- Band structure plot: bands.dat.gnu, bands.jpg", flush=True)