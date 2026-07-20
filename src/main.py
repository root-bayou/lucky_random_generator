"""
FDJ RNG - Générateur cryptographique de combinaisons
Supporte : EuroMillions, Loto, Crescendo
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
        description="🎰 FDJ RNG — Générateur cryptographique de combinaisons",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--jeu",
        choices=["e", "l", "c", "euromillions", "loto", "crescendo"],
        required=True,
        help=(
            "Jeu à générer :\n"
            "  e / euromillions → 5 numéros (1-50) + 2 étoiles (1-12)\n"
            "  l / loto         → 5 numéros (1-49) + 1 chance (1-10)\n"
            "  c / crescendo    → 10 numéros (1-25) + 1 lettre (S/A/M/E/D/I)"
        )
    )
    parser.add_argument(
        "--add-tirage",
        action="store_true",
        help="[Crescendo uniquement] Ajouter un tirage à l'historique manuel"
    )
    parser.add_argument(
        "--historique",
        action="store_true",
        help="Afficher l'historique enregistré du jeu"
    )
    parser.add_argument(
        "--nb",
        type=int,
        default=1,
        help="Nombre de combinaisons à générer (défaut: 1)"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    jeu = ALIAS_JEU.get(args.jeu, args.jeu)  # e→euromillions, l→loto, c→crescendo
    affichage = Affichage()
    historique = Historique(jeu)

    # Mode affichage historique
    if args.historique:
        affichage.afficher_historique(historique, jeu)
        return

    # Mode ajout tirage manuel (Crescendo uniquement)
    if args.add_tirage:
        if jeu != "crescendo":
            affichage.erreur("--add-tirage est uniquement disponible pour Crescendo.")
            sys.exit(1)
        historique.ajouter_tirage_crescendo_interactif()
        return

    # Mode génération
    affichage.banniere(jeu)

    generateur = Generateur(jeu, historique)

    # Crescendo : 10 grilles (5 aléatoires + 5 pseudo-aléatoires)
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
