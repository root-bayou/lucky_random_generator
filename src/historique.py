"""
Historique des tirages
- EuroMillions / Loto : CSV FDJ dézippés manuellement dans etc/
- Crescendo : fichier JSON manuel dans src/data/
"""

import json
import csv
from pathlib import Path
from datetime import datetime


# Dossier etc/ à la racine du projet (un niveau au-dessus de src/)
ETC_DIR = Path(__file__).parent.parent / "etc"

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

CRESCENDO_JSON = DATA_DIR / "historique_crescendo.json"
LETTRES_VALIDES = ["S", "A", "M", "E", "D", "I"]

# Sous-dossiers etc/ par jeu (loto = tous les tirages loto FDJ)
DOSSIERS_PAR_JEU = {
    "euromillions": ["euro_m"],
    "loto":         ["loto", "grand_loto", "super_loto"],
}


class Historique:
    def __init__(self, jeu: str):
        self.jeu = jeu
        self.combos = set()          # set de tuples pour recherche O(1)
        self._tirages_crescendo = [] # liste complète pour affichage
        self._charger()

    def _charger(self):
        if self.jeu == "crescendo":
            self._charger_crescendo()
        else:
            self._charger_fdj_csv()

    # ─────────────────────────────────────────
    # EUROMILLIONS / LOTO — CSV locaux (etc/)
    # ─────────────────────────────────────────

    def _charger_fdj_csv(self):
        """
        Charge tous les CSV depuis les sous-dossiers etc/ correspondant au jeu.
        Les fichiers sont dézippés manuellement depuis le site FDJ.
          euromillions → etc/euro_m/
          loto         → etc/loto/, etc/grand_loto/, etc/super_loto/
        Les fichiers anciens format (6 boules sans numero_chance) sont ignorés
        silencieusement via le try/except dans _parser_csv.
        """
        if not ETC_DIR.exists():
            print(f"⚠️  Dossier etc/ introuvable — historique {self.jeu} désactivé.")
            return

        sous_dossiers = DOSSIERS_PAR_JEU.get(self.jeu, [])
        fichiers = []
        for dossier in sous_dossiers:
            chemin_dossier = ETC_DIR / dossier
            if chemin_dossier.exists():
                fichiers.extend(sorted(chemin_dossier.glob("*.csv")))

        if not fichiers:
            print(f"⚠️  Aucun CSV trouvé dans etc/ pour {self.jeu} — historique désactivé.")
            return

        for chemin in fichiers:
            self._parser_csv(chemin)

        print(f"✅ {len(self.combos)} tirages chargés ({len(fichiers)} fichier(s)).")

    def _parser_csv(self, chemin: Path):
        """Parse le CSV FDJ et stocke les combos comme tuples."""
        try:
            for encodage in ("utf-8", "latin-1"):
                try:
                    with open(chemin, encoding=encodage) as f:
                        reader = csv.DictReader(f, delimiter=";")
                        for row in reader:
                            try:
                                if self.jeu == "euromillions":
                                    nums = tuple(sorted([
                                        int(row["boule_1"]),
                                        int(row["boule_2"]),
                                        int(row["boule_3"]),
                                        int(row["boule_4"]),
                                        int(row["boule_5"]),
                                    ]))
                                    etoiles = tuple(sorted([
                                        int(row["etoile_1"]),
                                        int(row["etoile_2"]),
                                    ]))
                                    self.combos.add((nums, etoiles))

                                elif self.jeu == "loto":
                                    # Ignore les anciens fichiers à 6 boules (pas de numero_chance)
                                    if "numero_chance" not in row:
                                        break
                                    nums = tuple(sorted([
                                        int(row["boule_1"]),
                                        int(row["boule_2"]),
                                        int(row["boule_3"]),
                                        int(row["boule_4"]),
                                        int(row["boule_5"]),
                                    ]))
                                    chance = int(row["numero_chance"])
                                    self.combos.add((nums, chance))
                            except (ValueError, KeyError):
                                continue
                    break  # lecture réussie, pas besoin d'essayer latin-1
                except UnicodeDecodeError:
                    continue
        except Exception as e:
            print(f"⚠️  Erreur lecture CSV : {e}")

    # ─────────────────────────────────────────
    # CRESCENDO — JSON manuel
    # ─────────────────────────────────────────

    def _charger_crescendo(self):
        """Charge l'historique Crescendo depuis :
        - etc/crescendo/*.csv  (format FDJ officiel : boule1…boule10 + lettre)
        - src/data/historique_crescendo.json  (entrées manuelles)
        """
        # 1) CSV officiels FDJ
        crescendo_dir = ETC_DIR / "crescendo"
        if crescendo_dir.exists():
            for chemin in sorted(crescendo_dir.glob("*.csv")):
                for encodage in ("utf-8", "latin-1"):
                    try:
                        with open(chemin, encoding=encodage) as f:
                            reader = csv.DictReader(f, delimiter=";")
                            for row in reader:
                                try:
                                    nums = tuple(sorted(
                                        int(row[f"boule{i}"]) for i in range(1, 11)
                                    ))
                                    lettre = row["lettre"].strip().upper()
                                    if lettre not in LETTRES_VALIDES:
                                        continue
                                    self.combos.add(nums)  # lettre ignorée
                                    self._tirages_crescendo.append({
                                        "date":    row.get("date_de_tirage", ""),
                                        "heure":   row.get("heure_de_tirage", "")[:5],
                                        "numeros": list(nums),
                                        "lettre":  lettre,
                                    })
                                except (ValueError, KeyError):
                                    continue
                        break
                    except UnicodeDecodeError:
                        continue

        # 2) JSON manuel
        if not CRESCENDO_JSON.exists():
            CRESCENDO_JSON.write_text("[]", encoding="utf-8")
        else:
            try:
                data = json.loads(CRESCENDO_JSON.read_text(encoding="utf-8"))
                for entry in data:
                    nums = tuple(sorted(entry["numeros"]))
                    self.combos.add(nums)  # lettre ignorée
                    self._tirages_crescendo.append(entry)
            except Exception as e:
                print(f"⚠️  Erreur lecture historique Crescendo JSON : {e}")

        # Trier par date décroissante pour l'affichage
        def _sort_key(t):
            d = t.get("date", "")
            try:
                return datetime.strptime(d, "%d/%m/%Y")
            except ValueError:
                try:
                    return datetime.strptime(d, "%Y-%m-%d")
                except ValueError:
                    return datetime.min

        self._tirages_crescendo.sort(key=_sort_key, reverse=True)

    def ajouter_tirage_crescendo_interactif(self):
        """Mode interactif pour ajouter un tirage Crescendo manuellement."""
        print("\n📝 Ajout d'un tirage Crescendo")
        print("─" * 40)

        # Date
        date_str = input("Date du tirage (YYYY-MM-DD, Entrée = aujourd'hui) : ").strip()
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        # Heure
        heures_valides = ["13h", "14h", "15h", "16h", "17h", "18h", "19h"]
        heure = ""
        while heure not in heures_valides:
            heure = input(f"Heure {heures_valides} : ").strip()

        # Numéros
        numeros = []
        while len(numeros) != 10:
            raw = input("10 numéros tirés (séparés par virgule, 1-25) : ").strip()
            try:
                numeros = sorted(set(int(x) for x in raw.split(",")))
                if len(numeros) != 10 or not all(1 <= n <= 25 for n in numeros):
                    print("❌ Exactement 10 numéros distincts entre 1 et 25.")
                    numeros = []
            except ValueError:
                print("❌ Format invalide.")
                numeros = []

        # Lettre
        lettre = ""
        while lettre not in LETTRES_VALIDES:
            lettre = input(f"Lettre tirée {LETTRES_VALIDES} : ").strip().upper()

        # Sauvegarde
        data = json.loads(CRESCENDO_JSON.read_text(encoding="utf-8"))
        data.append({
            "date": date_str,
            "heure": heure,
            "numeros": numeros,
            "lettre": lettre
        })
        CRESCENDO_JSON.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"\n✅ Tirage enregistré ! ({len(data)} tirages dans l'historique)")

    # ─────────────────────────────────────────
    # VÉRIFICATION
    # ─────────────────────────────────────────

    def deja_sortie(self, numeros: list[int], complement) -> bool:
        """Vérifie si la combinaison est déjà dans l'historique.
        Pour Crescendo : comparaison sur les numéros uniquement (lettre non choisie).
        """
        if not self.combos:
            return False

        nums_tuple = tuple(sorted(numeros))

        if self.jeu == "crescendo":
            return nums_tuple in self.combos

        if isinstance(complement, list):
            comp_key = tuple(sorted(complement))
        else:
            comp_key = complement

        return (nums_tuple, comp_key) in self.combos

    def nb_tirages(self) -> int:
        return len(self.combos)

    def tous_les_tirages(self):
        """Retourne la liste des tirages pour affichage."""
        if self.jeu != "crescendo":
            return list(self.combos)
        return self._tirages_crescendo
