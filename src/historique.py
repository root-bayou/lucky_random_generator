"""
Draw history loader
- EuroMillions / Loto: FDJ CSV files (manually unzipped) in etc/
- Crescendo: manual JSON entries in src/data/
"""

import json
import csv
from pathlib import Path
from datetime import datetime


# etc/ directory at project root (one level above src/)
ETC_DIR = Path(__file__).parent.parent / "etc"

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

CRESCENDO_JSON = DATA_DIR / "historique_crescendo.json"
VALID_LETTERS = ["S", "A", "M", "E", "D", "I"]

# etc/ subfolders per game
FOLDERS_PER_GAME = {
    "euromillions": ["euro_m"],
    "eurodreams":   ["euro_d"],
    "loto":         ["loto", "grand_loto", "super_loto"],
}


class Historique:
    def __init__(self, jeu: str):
        self.jeu = jeu
        self.combos: set = set()           # O(1) lookup set
        self._tirages_crescendo: list = []  # full list for display
        self._charger()

    def _charger(self):
        if self.jeu == "crescendo":
            self._charger_crescendo()
        else:
            self._charger_fdj_csv()

    # ─────────────────────────────────────────
    # EUROMILLIONS / LOTO — local CSV (etc/)
    # ─────────────────────────────────────────

    def _charger_fdj_csv(self):
        """
        Load all CSV files from the etc/ subfolders for the current game.
        Files are manually unzipped from the FDJ website.
          euromillions → etc/euro_m/
          loto         → etc/loto/, etc/grand_loto/, etc/super_loto/
        Old-format files (6 balls, no numero_chance) are silently skipped.
        """
        if not ETC_DIR.exists():
            print(f"⚠️  etc/ directory not found — {self.jeu} history disabled.")
            return

        subfolders = FOLDERS_PER_GAME.get(self.jeu, [])
        files = []
        for folder in subfolders:
            folder_path = ETC_DIR / folder
            if folder_path.exists():
                files.extend(sorted(folder_path.glob("*.csv")))

        if not files:
            print(f"⚠️  No CSV found in etc/ for {self.jeu} — history disabled.")
            return

        for path in files:
            self._parser_csv(path)

        print(f"✅ {len(self.combos)} draws loaded ({len(files)} file(s)).")

    def _parser_csv(self, chemin: Path):
        """Parse a FDJ CSV file and store combos as tuples."""
        try:
            for encoding in ("utf-8", "latin-1"):
                try:
                    with open(chemin, encoding=encoding) as f:
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
                                    stars = tuple(sorted([
                                        int(row["etoile_1"]),
                                        int(row["etoile_2"]),
                                    ]))
                                    self.combos.add((nums, stars))

                                elif self.jeu == "eurodreams":
                                    nums = tuple(sorted([
                                        int(row["boule_1"]),
                                        int(row["boule_2"]),
                                        int(row["boule_3"]),
                                        int(row["boule_4"]),
                                        int(row["boule_5"]),
                                        int(row["boule_6"]),
                                    ]))
                                    dream = int(row["numero_dream"])
                                    self.combos.add((nums, dream))

                                elif self.jeu == "loto":
                                    # Skip old 6-ball files (no numero_chance column)
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
                    break  # successful read, no need to try latin-1
                except UnicodeDecodeError:
                    continue
        except Exception as e:
            print(f"⚠️  CSV read error: {e}")

    # ─────────────────────────────────────────
    # CRESCENDO — manual JSON + official CSV
    # ─────────────────────────────────────────

    def _charger_crescendo(self):
        """Load Crescendo history from:
        - etc/crescendo/*.csv  (official FDJ format: boule1…boule10 + lettre)
        - src/data/historique_crescendo.json  (manual entries)
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
                                    if lettre not in VALID_LETTERS:
                                        continue
                                    self.combos.add(nums)  # letter ignored
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
                print(f"⚠️  Crescendo JSON read error: {e}")

        # Sort by date descending for display
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
        """Interactive mode to manually add a Crescendo draw."""
        print("\n📝 Add a Crescendo draw")
        print("─" * 40)

        # Date
        date_str = input("Draw date (YYYY-MM-DD, Enter = today): ").strip()
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        # Time
        valid_times = ["13h", "14h", "15h", "16h", "17h", "18h", "19h"]
        heure = ""
        while heure not in valid_times:
            heure = input(f"Time {valid_times}: ").strip()

        # Numbers
        numeros = []
        while len(numeros) != 10:
            raw = input("10 drawn numbers (comma-separated, 1-25): ").strip()
            try:
                numeros = sorted(set(int(x) for x in raw.split(",")))
                if len(numeros) != 10 or not all(1 <= n <= 25 for n in numeros):
                    print("❌ Exactly 10 distinct numbers between 1 and 25.")
                    numeros = []
            except ValueError:
                print("❌ Invalid format.")
                numeros = []

        # Letter
        lettre = ""
        while lettre not in VALID_LETTERS:
            lettre = input(f"Drawn letter {VALID_LETTERS}: ").strip().upper()

        # Save
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
        print(f"\n✅ Draw saved! ({len(data)} draws in history)")

    # ─────────────────────────────────────────
    # LOOKUP
    # ─────────────────────────────────────────

    def deja_sortie(self, numeros: list[int], complement) -> bool:
        """Check whether the combination has already been drawn.
        For Crescendo: comparison on numbers only (letter is not chosen by player).
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
        """Return the list of draws for display."""
        if self.jeu != "crescendo":
            return list(self.combos)
        return self._tirages_crescendo

    def recent_pool_crescendo(self, n_draws: int) -> set[int]:
        """Return all unique numbers that appeared in the last n_draws Crescendo draws."""
        if self.jeu != "crescendo":
            return set()
        return {
            num
            for t in self._tirages_crescendo[:n_draws]
            for num in t["numeros"]
        }
