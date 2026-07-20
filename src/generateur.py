"""
Générateur cryptographique — cœur du projet
Zéro PRNG : utilise secrets.randbelow() / secrets.choice() qui appellent
os.urandom (CryptGenRandom sur Windows) avec rejection sampling.
Distribution strictement uniforme sans aucun état interne prédictible.
"""

import secrets


# Configuration des jeux
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
    Tirage sans remplacement via os.urandom pur.
    Algorithme : Fisher-Yates partiel, chaque index tiré par secrets.randbelow()
    qui consomme des octets os.urandom avec rejection sampling.
    Aucune graine, aucun état interne → vrai non-déterminisme.
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
        Génère une combinaison :
        1. os.urandom pur via secrets — zéro PRNG, distribution uniforme exacte
        2. Pour Crescendo : toujours retournée, historique signalé dans meta
           Pour les autres jeux : boucle jusqu'à une combo jamais sortie
        Retourne (combo_dict, meta_dict)
        """
        MAX_TENTATIVES = 100_000

        for tentatives in range(1, MAX_TENTATIVES + 1):
            numeros = self._generer_numeros()
            complement = self._generer_complement()  # None pour Crescendo
            deja = self.historique.deja_sortie(numeros, complement)

            # Crescendo : on accepte même si déjà sortie, on le signale
            if self.jeu == "crescendo" or not deja:
                combo = {
                    "numeros": numeros,
                    "complement": complement,
                    "type_complement": self.config["complement"]["type"],
                }
                meta = {
                    "tentatives": tentatives,
                    "source": "os.urandom (CryptGenRandom) — zéro PRNG",
                    "deja_sortie": deja,
                }
                return combo, meta

        raise RuntimeError(f"Impossible de générer une combinaison après {MAX_TENTATIVES} tentatives.")

    def generer_pseudo(self, refs: list[dict]) -> tuple:
        """
        Génère une combo Crescendo en conservant ~4 numéros du pool des grilles
        de référence (tendances) et en complétant avec des numéros purs os.urandom.
        """
        # Pool de référence : union des numéros des grilles aléatoires
        pool_ref = list({n for combo in refs for n in combo["numeros"]})
        pool_hors_ref = [n for n in range(1, 26) if n not in pool_ref]

        # Nombre de numéros "pattern" à conserver : 3, 4 ou 5
        nb_pattern = secrets.randbelow(3) + 3
        nb_pattern = min(nb_pattern, len(pool_ref))

        # Tirage sans remplacement depuis pool_ref
        pool_ref_shuffle = list(pool_ref)
        pattern = []
        for _ in range(nb_pattern):
            i = secrets.randbelow(len(pool_ref_shuffle))
            pattern.append(pool_ref_shuffle.pop(i))

        # Compléter : numéros hors-ref + numéros ref non-choisis
        reste_pool = pool_hors_ref + pool_ref_shuffle
        nb_reste = 10 - len(pattern)
        reste = []
        for _ in range(nb_reste):
            if not reste_pool:
                break
            i = secrets.randbelow(len(reste_pool))
            reste.append(reste_pool.pop(i))

        numeros = sorted(pattern + reste)

        deja = self.historique.deja_sortie(numeros, None)
        combo = {
            "numeros": numeros,
            "complement": None,
            "type_complement": "none",
        }
        meta = {
            "tentatives": 1,
            "source": "os.urandom + tendances grilles 1 & 2",
            "deja_sortie": deja,
            "mode": "pseudo",
        }
        return combo, meta
