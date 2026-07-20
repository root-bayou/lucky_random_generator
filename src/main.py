"""
FDJ RNG - Cryptographic lottery combination generator
Supports: EuroMillions, Loto, Crescendo
"""

import sys
import argparse
sys.stdout.reconfigure(encoding='utf-8')

from generateur import Generateur
from historique import Historique
from affichage import Affichage


ALIAS_JEU = {"e": "euromillions", "l": "loto", "c": "crescendo"}


def parse_args():
    parser = argparse.ArgumentParser(
        description="🎰 FDJ RNG — Cryptographic lottery combination generator",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--jeu",
        choices=["e", "l", "c", "euromillions", "loto", "crescendo"],
        required=True,
        help=(
            "Game to generate:\n"
            "  e / euromillions → 5 numbers (1-50) + 2 stars (1-12)\n"
            "  l / loto         → 5 numbers (1-49) + 1 lucky number (1-10)\n"
            "  c / crescendo    → 10 numbers (1-25) + 1 letter (S/A/M/E/D/I)"
        )
    )
    parser.add_argument(
        "--add-tirage",
        action="store_true",
        help="[Crescendo only] Add a draw to the manual history"
    )
    parser.add_argument(
        "--historique",
        action="store_true",
        help="Display the recorded history for the game"
    )
    parser.add_argument(
        "--nb",
        type=int,
        default=1,
        help="Number of combinations to generate (default: 1)"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    jeu = ALIAS_JEU.get(args.jeu, args.jeu)  # e→euromillions, l→loto, c→crescendo
    affichage = Affichage()
    historique = Historique(jeu)

    # History display mode
    if args.historique:
        affichage.afficher_historique(historique, jeu)
        return

    # Manual draw entry mode (Crescendo only)
    if args.add_tirage:
        if jeu != "crescendo":
            affichage.erreur("--add-tirage is only available for Crescendo.")
            sys.exit(1)
        historique.ajouter_tirage_crescendo_interactif()
        return

    # Generation mode
    affichage.banniere(jeu)

    generateur = Generateur(jeu, historique)

    # Crescendo: 10 grids (5 random + 5 pattern-based)
    if jeu == "crescendo":
        refs = []
        resultats = []
        for i in range(5):
            combo, meta = generateur.generer()
            meta["mode"] = "random"
            refs.append(combo)
            resultats.append((combo, meta))
        for i in range(5):
            combo, meta = generateur.generer_pseudo(refs)
            resultats.append((combo, meta))
        affichage.afficher_crescendo_5grilles(resultats)
        return

    for i in range(args.nb):
        if args.nb > 1:
            affichage.separateur(f"Combinaison {i+1}/{args.nb}")
        combo, meta = generateur.generer()
        affichage.afficher_combo(jeu, combo, meta)


if __name__ == "__main__":
    main()
