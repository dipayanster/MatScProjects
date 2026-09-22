~~~~~~~~~~~~
Materials Modeling
~~~~~~~~~~~~

**For next school: update work function script to grab vacuum level in Ry, convert to eV and print in stdout**

**source ~/work/software/venv/bin/activate**

**/home/milias/work/software/qe/qe-7.5/bin**

**My working directory : /work/projects/schools/Molecular-and-Materials-Modeling-2026-August/materials-modeling/**

**Working with git:  git clone, git add -A, git commit -a, git push, git pull**

~~~~~~~~~~~~
Requirements:
~~~~~~~~~~~~
(1) Quantum ESPRESSO should be installed in the local machine. 

	$ /path/to/qe/bin/pw.x

	Program PWSCF v.7.5 starts on 27Aug2026 at 10:13: 2
 
(2) Python (python3-full).

	$ python --version

	Python 3.12.3


(3) ASE (Atomic Simulation Environment) should be installed and be in path. Install the latest version by: pip install --upgrade git+https://gitlab.com/ase/ase.git@master

	$ ase --version

	ase-3.28.0b1

~~~~~~~~~~~~
Structure and potentials:
~~~~~~~~~~~~

(1) Si: experimental cif file retrieved from  https://www.ccdc.cam.ac.uk/structures/Search?Ccdcid=60389&DatabaseToSearch=ICSD (single crystal xrd measurements, https://pubs.aip.org/aip/jcp/article-abstract/41/8/2324/81085)

(2) Graphite: experimental cif file retrieved from https://www.ccdc.cam.ac.uk/structures/Search?Ccdcid=193439&DatabaseToSearch=ICSD (neutron diffraction study, https://iopscience.iop.org/article/10.1149/2.0951410jes)

(3) Al: retrieved from from the Materials Project https://next-gen.materialsproject.org/materials/mp-134 for single-shot calculations

(4) Pseudopotential: scalar-relativistic optimised norm-conserving Vanderbilt pseudopotential files can be downloaded from (https://www.pseudo-dojo.org/), and are also suppiled. Other sources: (a) https://www.materialscloud.org/discover/sssp/table/efficiency (b) https://pseudopotentials.quantum-espresso.org/legacy_tables (c) https://www.quantum-espresso.org/other-resources/

(5) DOS Plotting scripts provided: ase_qe_np_tdos.py and ase_qe_np_pdos.py - for plotting TDOS and PDOS, works only for non-spin-polarized and non-SOC case. They expect the files to be organized in a certain order and local sumpdos.x must be supplied if needed.  

**For converting crystal structures to QE format, various online/ offline tools can be used.**

(1) https://qeinputgenerator.materialscloud.io/ 
(2) https://seekpath.materialscloud.io/ 
(3) VESTA
(4) ASE

~~~~~~~~~~~~
Quantum ESPRESSO basics
~~~~~~~~~~~~

**The input file for PWscf is structured in a number of NAMELISTS and INPUT CARDS.**

|

| &NAMELIST1 
|    ... 
| /
| &NAMELIST2 
|    ... 
| /
| &NAMELIST3 
|    ... 
| /
| INPUT_CARD1
| ....
| ....
| INPUT_CARD2
| ....
| ....

|

**NAMELISTS are read in a specific order**

**NAMELISTS that are not required are ignored**

**Logically independent INPUT_CARDS can be given in any order**

**There are three mandatory NAMELISTS**

(1) &CONTROL input variables that control the flux of the calculation and the amount of I/O on disk and on the screen.

(2) &SYSTEM input variables that specify the system under study.

(3) &ELECTRONS input variables that control the algorithms used to reach the self-consistent solution of KS equations for the electrons.

**We may also need:**

(1) &IONS needed when ATOMS MOVE! IGNORED otherwise !

(2) &CELL needed when CELL MOVES! IGNORED otherwise !

**There are three mandatory INPUT_CARDS**

(1) ATOMIC_SPECIES name, mass and pseudopotential used for each atomic species present in the system

(2) ATOMIC_POSITIONS type and coordinates of each atom in the unit cell

(3) K_POINTS coordinates and weights of the k-points used for BZ integration

**We will also need:**

(1) CELL_PARAMETERS

Details about input parameters can be found here: 

(1) https://www.quantum-espresso.org/Doc/INPUT_PW.html
(2) https://www.quantum-espresso.org/Doc/INPUT_PP.html
(3) https://www.quantum-espresso.org/Doc/INPUT_DOS.html
(4) https://www.quantum-espresso.org/Doc/INPUT_PROJWFC.html (orbital ordering)
(5) https://www.quantum-espresso.org/Doc/INPUT_BANDS.html

**For running jobs, the pseudopotential file must be in the job directory (or you have to specify the path).**

~~~~~~~~~~~~
Atomic Simulation Environment (ASE)
~~~~~~~~~~~~
The Atomic Simulation Environment (ASE) is a powerful Python toolkit designed for atomistic simulations, offering capabilities for setup, execution, analysis, and visualization. Its key advantages include:

(1) Streamlining complex, multistep computational workflows

(2) Enabling hybrid calculations by combining outputs from different codes (e.g., using Quantum ESPRESSO for DFT energies/forces while incorporating DFT-D4 for van der Waals corrections)

(3) Supporting interoperability with numerous electronic structure codes and force fields

The framework provides researchers with a unified interface for diverse simulation tasks while maintaining flexibility in method combinations.


~~~~~~~~~~~~
Optional software
~~~~~~~~~~~~

(1) Grace: (https://sourceforge.net/projects/qtgrace/)

(2) VESTA: (https://jp-minerals.org/vesta/en/download.html)

(3) Seekpath: (pip install seekpath, https://seekpath.materialscloud.io/)

(4) postscript: (sudo apt install gv)

