"""
Filtres qualité — élimine les combinaisons "mauvaises" statistiquement
"""


class Filtres:
    def __init__(self, jeu: str):
        self.jeu = jeu
        self.derniers_filtres_passes = []

    def valider(self, numeros: list[int], complement) -> tuple[bool, str]:
        """
        Retourne (True, "") si la combo passe tous les filtres
        Retourne (False, raison) sinon
        """
        self.derniers_filtres_passes = []
        checks = [
            self._check_tous_pairs_impairs,
            self._check_tous_petits_grands,
            self._check_consecutifs,
            self._check_suite_arithmetique,
            self._check_multiples,
        ]
        if self.jeu != "crescendo":
            checks.append(self._check_dates_uniquement)
        if self.jeu == "crescendo":
            checks.append(self._check_crescendo_equilibre)
        if self.jeu == "euromillions":
            checks.append(self._check_etoiles_consecutives)

        for check in checks:
            valide, raison = check(numeros, complement)
            if not valide:
                return False, raison
            self.derniers_filtres_passes.append(check.__name__.replace("_check_", ""))

        return True, ""

    def _check_tous_pairs_impairs(self, numeros, _):
        pairs = sum(1 for n in numeros if n % 2 == 0)
        impairs = len(numeros) - pairs
        # Accepte uniquement si mix (pas 100% pairs ni 100% impairs)
        if pairs == 0:
            return False, "Tous les numéros sont impairs"
        if impairs == 0:
            return False, "Tous les numéros sont pairs"
        return True, ""

    # Midpoint fixe par jeu (plage officielle, pas dynamique)
    _MIDPOINT = {"euromillions": 25, "loto": 25, "crescendo": 12}

    def _check_tous_petits_grands(self, numeros, _):
        milieu = self._MIDPOINT.get(self.jeu, max(numeros) // 2)
        petits = sum(1 for n in numeros if n <= milieu)
        grands = len(numeros) - petits
        if petits == 0:
            return False, "Tous les numéros sont grands"
        if grands == 0:
            return False, "Tous les numéros sont petits"
        return True, ""

    def _check_consecutifs(self, numeros, _):
        # Refuse ≥3 consécutifs d'affilée (EuroMillions/Loto), ≥4 pour Crescendo
        max_consec = 1
        consec = 1
        for i in range(1, len(numeros)):
            if numeros[i] == numeros[i-1] + 1:
                consec += 1
                max_consec = max(max_consec, consec)
            else:
                consec = 1
        seuil = 4 if self.jeu == "crescendo" else 3
        if max_consec >= seuil:
            return False, f"{max_consec} numéros consécutifs détectés"
        return True, ""

    def _check_suite_arithmetique(self, numeros, _):
        # Refuse les suites arithmétiques parfaites (5-10-15-20-25)
        if len(numeros) < 4:
            return True, ""
        diffs = [numeros[i+1] - numeros[i] for i in range(len(numeros)-1)]
        if len(set(diffs)) == 1:
            return False, "Suite arithmétique parfaite détectée"
        return True, ""

    def _check_multiples(self, numeros, _):
        # Refuse si tous multiples d'un même chiffre (ex: 3,6,9,12,15)
        for diviseur in range(2, 8):
            if all(n % diviseur == 0 for n in numeros):
                return False, f"Tous multiples de {diviseur}"
        return True, ""

    def _check_dates_uniquement(self, numeros, _):
        # Refuse si tous les numéros sont <= 31 (biais dates anniversaires)
        if all(n <= 31 for n in numeros):
            return False, "Tous les numéros ≤ 31 (biais dates)"
        return True, ""

    def _check_etoiles_consecutives(self, numeros, complement):
        # Refuse les étoiles consécutives (1-2, 5-6, etc.)
        if isinstance(complement, list) and len(complement) == 2:
            if abs(complement[0] - complement[1]) == 1:
                return False, "Étoiles consécutives"
        return True, ""

    def _check_crescendo_equilibre(self, numeros, _):
        # Pour Crescendo (10 numéros sur 1-25) :
        # Refuse si plus de 7 numéros dans la même moitié (1-12 ou 13-25)
        bas = sum(1 for n in numeros if n <= 12)
        haut = len(numeros) - bas
        if bas >= 8 or haut >= 8:
            return False, f"Déséquilibre bas/haut ({bas}/{haut})"
        return True, ""
