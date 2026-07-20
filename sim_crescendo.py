"""
Crescendo collision simulation — cross-check against FDJ history
Usage: python sim_crescendo.py [number_of_draws]
"""

import sys
sys.path.insert(0, 'src')

from historique import Historique
from generateur import tirer_sans_remplacement
import math

N = int(sys.argv[1]) if len(sys.argv) > 1 else 100_000

h = Historique('crescendo')
print(f'FDJ history  : {h.nb_tirages()} draws')
print(f'Simulation   : {N:,} grids\n')

collisions = []

for i in range(N):
    nums = tirer_sans_remplacement(1, 25, 10)
    if h.deja_sortie(nums, None):
        collisions.append(nums)

total_combos = math.comb(25, 10)
attendu = N * h.nb_tirages() / total_combos

print(f'Collisions found     : {len(collisions)}')
print(f'Expected (theory)    : {attendu:.1f}')
print(f'Rate                 : {len(collisions)/N*100:.4f}%')
print()

if collisions:
    print('Grids already drawn in FDJ history:')
    for nums in collisions:
        n = '  '.join(f'{x:02d}' for x in nums)
        print(f'  {n}')
else:
    print('No collisions.')
