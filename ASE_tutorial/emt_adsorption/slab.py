from ase.build import fcc111, add_adsorbate
from ase.io import write

# Build Au(111) slab: 4 layers, 4x4 supercell
slab = fcc111('Au', size=(4, 4, 4), vacuum=10.0)

# Add Hg adsorbate at fcc hollow site
add_adsorbate(slab, 'Pd', height=2.0, position='fcc')

# Save as VASP POSCAR (Cartesian coordinates)
write('ads.vasp', slab, format='vasp')