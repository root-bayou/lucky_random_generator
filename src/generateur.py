"""
0 PRNG : secrets.randbelow() / secrets.choice()
os.urandom (CryptGenRandom for Windows) 
"""

import secrets


# Game configurations
CONFIGS = {
    "euromillions": {
        "numeros": {"min": 1, "max": 50, "count": 5},
        "complement": {"type": "etoiles", "min": 1, "max": 12, "count": 2},
    },
    "loto": {
        "numeros": {"min": 1, "max": 49, "count": 5},
        "complement": {"type": "chance", "min": 1, "max": 10, "count": 1},
    },
    "crescendo": {
        "numeros": {"min": 1, "max": 25, "count": 10},
        "complement": {"type": "none"},
    },
}


def tirer_sans_remplacement(pool_min: int, pool_max: int, count: int) -> list[int]:
    """
    Draw without replacement using pure os.urandom.
    Algorithm: partial Fisher-Yates, each index drawn by secrets.randbelow()
    which consumes os.urandom bytes with rejection sampling.
    No seed, no internal state — true non-determinism.
    """
    pool = list(range(pool_min, pool_max + 1))
    result = []
    for _ in range(count):
        i = secrets.randbelow(len(pool))
        result.append(pool.pop(i))
    return sorted(result)


class Generateur:
    def __init__(self, jeu: str, historique):
        self.jeu = jeu
        self.config = CONFIGS[jeu]
        self.historique = historique

    def _generer_numeros(self) -> list[int]:
        cfg = self.config["numeros"]
        return tirer_sans_remplacement(cfg["min"], cfg["max"], cfg["count"])

    def _generer_complement(self):
        cfg = self.config["complement"]
        if cfg["type"] == "none":
            return None
        if cfg["type"] == "lettre":
            return secrets.choice(cfg["valeurs"])
        resultat = tirer_sans_remplacement(cfg["min"], cfg["max"], cfg["count"])
        return resultat[0] if cfg["count"] == 1 else resultat

    def generer(self) -> tuple:
        """
        Generate a combination:
        1. Pure os.urandom via secrets — zero PRNG, exact uniform distribution
        2. Crescendo: always returned, history match flagged in meta
           Other games: loop until a never-drawn combination is found
        Returns (combo_dict, meta_dict)
        """
        MAX_TENTATIVES = 100_000

        for tentatives in range(1, MAX_TENTATIVES + 1):
            numeros = self._generer_numeros()
            complement = self._generer_complement()  # None for Crescendo
            deja = self.historique.deja_sortie(numeros, complement)

            # Crescendo: always accepted even if already drawn, flagged in meta
            if self.jeu == "crescendo" or not deja:
                combo = {
                    "numeros": numeros,
                    "complement": complement,
                    "type_complement": self.config["complement"]["type"],
                }
                meta = {
                    "tentatives": tentatives,
                    "source": "os.urandom (CryptGenRandom) — zero PRNG",
                    "deja_sortie": deja,
                }
                return combo, meta

        raise RuntimeError(f"Failed to generate a combination after {MAX_TENTATIVES} attempts.")

    def generer_pseudo(self, refs: list[dict]) -> tuple:
        """
        Generate a Crescendo grid keeping ~4 numbers from the reference grids
        (pattern bias) and filling the rest with pure os.urandom numbers.
        """
        # Reference pool: union of numbers from the random reference grids
        pool_ref = list({n for combo in refs for n in combo["numeros"]})
        pool_outside = [n for n in range(1, 26) if n not in pool_ref]

        # Number of "pattern" numbers to keep: 3, 4 or 5
        nb_pattern = secrets.randbelow(3) + 3
        nb_pattern = min(nb_pattern, len(pool_ref))

        # Draw without replacement from pool_ref
        pool_ref_shuffle = list(pool_ref)
        pattern = []
        for _ in range(nb_pattern):
            i = secrets.randbelow(len(pool_ref_shuffle))
            pattern.append(pool_ref_shuffle.pop(i))

        # Fill remaining slots: outside pool + unused ref numbers
        fill_pool = pool_outside + pool_ref_shuffle
        nb_fill = 10 - len(pattern)
        fill = []
        for _ in range(nb_fill):
            if not fill_pool:
                break
            i = secrets.randbelow(len(fill_pool))
            fill.append(fill_pool.pop(i))

        numeros = sorted(pattern + fill)

        deja = self.historique.deja_sortie(numeros, None)
        combo = {
            "numeros": numeros,
            "complement": None,
            "type_complement": "none",
        }
        meta = {
            "tentatives": 1,
            "source": "os.urandom + pattern bias from grids 1–5",
            "deja_sortie": deja,
            "mode": "pseudo",
        }
        return combo, meta
