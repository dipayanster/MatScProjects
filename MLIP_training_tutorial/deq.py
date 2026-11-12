import sys
import numpy as np
from ase.io import read

atoms = read(sys.argv[1])

symbols = np.array(atoms.get_chemical_symbols())
positions = atoms.get_positions()

c_pos = positions[symbols == 'C']
hg_pos = positions[symbols == 'Hg'][0]

c_avg = c_pos.mean(axis=0)

# graphene plane normal: use lattice vectors a,b of the cell (z is c axis)
cell = atoms.get_cell()
normal = np.cross(cell[0], cell[1])
normal = normal / np.linalg.norm(normal)

d = abs(np.dot(hg_pos - c_avg, normal))
print(d)