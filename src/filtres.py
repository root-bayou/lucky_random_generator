"""
Quality filters — discard statistically "bad" combinations
"""


class Filtres:
    def __init__(self, jeu: str):
        self.jeu = jeu
        self.derniers_filtres_passes = []

    def valider(self, numeros: list[int], complement) -> tuple[bool, str]:
        """
        Returns (True, "") if the combo passes all filters
        Returns (False, reason) otherwise
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
            return False, "All numbers are odd"
        if impairs == 0:
            return False, "All numbers are even"
        return True, ""

    # Fixed midpoint per game (official range, not dynamic)
    _MIDPOINT = {"euromillions": 25, "loto": 25, "crescendo": 12}

    def _check_tous_petits_grands(self, numeros, _):
        milieu = self._MIDPOINT.get(self.jeu, max(numeros) // 2)
        petits = sum(1 for n in numeros if n <= milieu)
        grands = len(numeros) - petits
        if petits == 0:
            return False, "All numbers are high"
        if grands == 0:
            return False, "All numbers are low"
        return True, ""

    def _check_consecutifs(self, numeros, _):
        # Reject ≥3 consecutive (EuroMillions/Loto), ≥4 for Crescendo
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
            return False, f"{max_consec} consecutive numbers detected"
        return True, ""

    def _check_suite_arithmetique(self, numeros, _):
        # Reject perfect arithmetic sequences (e.g. 5-10-15-20-25)
        if len(numeros) < 4:
            return True, ""
        diffs = [numeros[i+1] - numeros[i] for i in range(len(numeros)-1)]
        if len(set(diffs)) == 1:
            return False, "Perfect arithmetic sequence detected"
        return True, ""

    def _check_multiples(self, numeros, _):
        # Reject if all numbers are multiples of the same divisor (e.g. 3,6,9,12,15)
        for diviseur in range(2, 8):
            if all(n % diviseur == 0 for n in numeros):
                return False, f"All multiples of {diviseur}"
        return True, ""

    def _check_dates_uniquement(self, numeros, _):
        # Reject if all numbers are ≤ 31 (birthday bias)
        if all(n <= 31 for n in numeros):
            return False, "All numbers ≤ 31 (date bias)"
        return True, ""

    def _check_etoiles_consecutives(self, numeros, complement):
        # Reject consecutive stars (1-2, 5-6, etc.)
        if isinstance(complement, list) and len(complement) == 2:
            if abs(complement[0] - complement[1]) == 1:
                return False, "Consecutive stars"
        return True, ""

    def _check_crescendo_equilibre(self, numeros, _):
        # For Crescendo (10 numbers on 1-25):
        # Reject if more than 7 numbers in the same half (1-12 or 13-25)
        bas = sum(1 for n in numeros if n <= 12)
        haut = len(numeros) - bas
        if bas >= 8 or haut >= 8:
            return False, f"Low/high imbalance ({bas}/{haut})"
        return True, ""
