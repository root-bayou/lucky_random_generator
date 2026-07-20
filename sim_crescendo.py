"""
Simulation Crescendo — cross-check avec l'historique FDJ
Usage : python sim_crescendo.py [nombre_de_tirages]
"""

import sys
sys.path.insert(0, 'src')

from historique import Historique
from generateur import tirer_sans_remplacement
import math

N = int(sys.argv[1]) if len(sys.argv) > 1 else 100_000

h = Historique('crescendo')
print(f'\nHistorique FDJ : {h.nb_tirages()} tirages')
print(f'Simulation     : {N:,} grilles\n')

collisions = []

for i in range(N):
    nums = tirer_sans_remplacement(1, 25, 10)
    if h.deja_sortie(nums, None):
        collisions.append(nums)

total_combos = math.comb(25, 10)
attendu = N * h.nb_tirages() / total_combos

print(f'Collisions trouvees  : {len(collisions)}')
print(f'Attendu theorique    : {attendu:.1f}')
print(f'Taux                 : {len(collisions)/N*100:.4f}%')
print()

if collisions:
    print('Grilles deja sorties dans l\'historique FDJ :')
    for nums in collisions:
        n = '  '.join(f'{x:02d}' for x in nums)
        print(f'  {n}')
else:
    print('Aucune collision.')
