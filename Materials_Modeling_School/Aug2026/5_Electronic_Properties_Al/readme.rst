=======================================================
TASK 5: Electronic properties: Al (Charge and DOS, ASE)
=======================================================

For this task, we will perform a quick electronic properties calculation of aluminum (Al). 
This is a metal with a cubic Fm̅3m crystal structure. I

Instead of following the ful production workflow — which would involve obtaining an experimental structure from a database like the ICSD or CCDC, performing convergence tests, and conducting cell relaxation — we will, for simplicity, use a standard structure from the Materials Project and run single-shot density of states (DOS) and band structure calculations.

First symmetrize the Al structure using the SeekPath tool.

Step 5.1:
~~~~~~~~~
Copy the TASK 4: Electronic properties: A script into your working directory. In the "Electronic properties: A" script, update the necessary parameters—including the pseudopotential, prefix, nat fields, and atoms object to match your Al system.

Run the calculation:
python3 electronic_properties_al.py > electronic_properties_al.out

(update the Quantum ESPRESSO executable path to your local pw.x location.)

Visualize the DOS plots and compare with Si.

Challenge
---------
Find an experimental Al structure from databases, run convergence test and cell relaxation. 

Then recalculate the electronic properties using the relaxed unit cell and optimized cut off and k points. 

