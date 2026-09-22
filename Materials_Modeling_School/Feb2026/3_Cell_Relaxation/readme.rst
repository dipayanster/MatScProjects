====================================
TASK 3: Cell relaxation (QE and ASE)
====================================

In this task, we will relax the silicon experimental unit cell to determine its ground state structure, allowing both lattice parameters and atomic positions to adjust freely.

Given that we're starting from a well-defined experimental structure, only minor changes are expected during the relaxation process. We will perform this using two distinct methods: direct relaxation through QE and by ASE using QE as calculator.

Step 3.1: Direct QE run
~~~~~~~~~~~~~~~~~~~~~~~
/path/to/qe/bin/qe-7.4.1/bin/pw.x < cell_relaxation_si.in > cell_relaxation_si_direct.out

Step 3.2: ASE driven QE run
~~~~~~~~~~~~~~~~~~~~~~~~~~~
ASE: python3 cell_relaxation_si.py > cell_relaxation_si.out (Replace the QE executable path with your local pw.x location in the script)

When using QE directly, the calculation type must be set to 'vc-relax',
requiring both the &IONS and &CELL NAMELISTs in the input file. 

QE's relaxation convergence is controlled by thresholds like etot_conv_thr and forc_conv_thr in the &CONTROL NAMELIST,
which default to specific values if not specified (in this example we did not, so check the pw.x manual what those values are and if they are same or different for both jobs). 

In direct QE relaxations, the final co-ordinates are after "Begin final coordinates" line in the output.

ASE, on the other hand, employs QE as a calculator to perform a series of SCF calculations, using the calculated energies and forces to optimize the structure through its own BFGS implementation. 

While both methods utilize the BFGS algorithm, slight differences may appear in the final structures due to variations in their implementations (such as minimizing max force vs norm) and different threshold values.

After completing both relaxations, carefully compare the resulting forces, pressure, energy, lattice parameters, and atomic coordinates in both jobs. For a well-relaxed structure, the stress should remain within ±50 kbar and forces should be negligible, how are your results?

Note1: When performing a series of calculations, ASE automatically overwrites the Quantum ESPRESSO output (.pwo) and input (.pwi) files after each step.

Note2: ASE automatically saves the complete relaxation history in the trajectory file (relaxation.traj). You can visualize the step-by-step structural evolution using ASE's GUI by loading this trajectory file. To view it, simply run: ase gui relaxation.traj

Challenge
---------
Modify the TASK 3: For cell relaxation (QE and ASE), use a custom, tighter etot_conv_thr and forc_conv_thr, shift the atoms manually and run the convergence again. try the same in ASE.
