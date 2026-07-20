"""
Affichage stylé — utilise rich pour un rendu terminal soigné
Fallback colorama si rich absent
"""

from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    from rich.text import Text
    from rich.columns import Columns
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    try:
        import colorama
        colorama.init()
        ORANGE = "\033[93m"
        BLEU   = "\033[94m"
        VERT   = "\033[92m"
        ROUGE  = "\033[91m"
        RESET  = "\033[0m"
        GRAS   = "\033[1m"
    except ImportError:
        ORANGE = BLEU = VERT = ROUGE = RESET = GRAS = ""


EMOJIS = {
    "euromillions": "🌟",
    "loto":         "🍀",
    "crescendo":    "🎵",
}

TITRES = {
    "euromillions": "EUROMILLIONS",
    "loto":         "LOTO",
    "crescendo":    "CRESCENDO",
}


class Affichage:

    # ─────────────────────────────────────────
    # BANNIÈRE
    # ─────────────────────────────────────────

    def banniere(self, jeu: str):
        emoji = EMOJIS[jeu]
        titre = TITRES[jeu]

        if HAS_RICH:
            console.print()
            console.print(Panel(
                f"[bold yellow]{emoji}  FDJ RNG — {titre}  {emoji}[/bold yellow]\n"
                f"[dim]Générateur cryptographique · os.urandom (CryptGenRandom) — zéro PRNG[/dim]",
                border_style="yellow",
                expand=False,
                padding=(0, 4)
            ))
        else:
            print(f"\n{GRAS}{ORANGE}{'='*50}{RESET}")
            print(f"{GRAS}{ORANGE}  {emoji}  FDJ RNG — {titre}  {emoji}{RESET}")
            print(f"  os.urandom (CryptGenRandom) — zéro PRNG")
            print(f"{GRAS}{ORANGE}{'='*50}{RESET}\n")

    # ─────────────────────────────────────────
    # CRESCENDO — 5 GRILLES EN UN SEUL CARRÉ
    # ─────────────────────────────────────────

    def afficher_crescendo_5grilles(self, resultats: list):
        if HAS_RICH:
            table = Table(box=box.SIMPLE_HEAD, show_header=True, padding=(0, 1),
                          header_style="dim")
            table.add_column("#",       width=2,  style="bold")
            table.add_column("Mode",    width=3)
            table.add_column("Numéros", min_width=44)
            table.add_column("",        width=2,  justify="center")

            for idx, (combo, meta) in enumerate(resultats, 1):
                mode_str = "🎲" if meta.get("mode") == "random" else "🔄"
                nums_str = " ".join(f"[bold cyan]{n:02d}[/]" for n in combo["numeros"])
                hist_str = "[red]⚠[/red]" if meta.get("deja_sortie") else "[green]✓[/green]"
                table.add_row(str(idx), mode_str, nums_str, hist_str)
                if idx == 5:
                    table.add_section()

            console.print()
            console.print(Panel(
                table,
                title="[bold yellow]🎵  CRESCENDO — 10 Grilles[/bold yellow]",
                subtitle="[dim]🎲 aléatoire  🔄 tendances  ✓ inédit  ⚠ déjà sorti[/dim]",
                border_style="yellow",
                padding=(0, 1)
            ))
            console.print()
        else:
            print("\n🎵 CRESCENDO — 5 Grilles\n")
            for idx, (combo, meta) in enumerate(resultats, 1):
                mode = "🎲" if meta.get("mode") == "random" else "🔄"
                nums = "  ".join(f"{n:02d}" for n in combo["numeros"])
                hist = " ⚠️" if meta.get("deja_sortie") else " ✓"
                print(f"  [{idx}] {mode}  {nums}{hist}")
            print()

    # ─────────────────────────────────────────
    # AFFICHAGE COMBO
    # ─────────────────────────────────────────

    def afficher_combo(self, jeu: str, combo: dict, meta: dict):
        numeros = combo["numeros"]
        complement = combo["complement"]
        type_comp = combo["type_complement"]

        if HAS_RICH:
            self._afficher_combo_rich(jeu, numeros, complement, type_comp, meta)
        else:
            self._afficher_combo_simple(jeu, numeros, complement, type_comp, meta)

    def _afficher_combo_rich(self, jeu, numeros, complement, type_comp, meta):
        # Numéros
        nums_str = "  ".join(f"[bold white on blue] {n:02d} [/]" for n in numeros)

        # Complément
        if type_comp == "etoiles":
            comp_str = "  ".join(f"[bold black on yellow] ✦{e:02d} [/]" for e in complement)
            comp_label = "ÉTOILES"
        elif type_comp == "chance":
            comp_str = f"[bold white on red] {complement:02d} [/]"
            comp_label = "CHANCE"
        else:  # lettre
            comp_str = f"[bold white on cyan]  {complement}  [/]"
            comp_label = "LETTRE"

        # Panel principal
        panel_color = "cyan" if meta.get("mode") == "pseudo" else "green"
        contenu = (
            f"\n  [dim]NUMÉROS[/dim]\n"
            f"  {nums_str}\n\n"
            f"  [dim]{comp_label}[/dim]\n"
            f"  {comp_str}\n"
        )
        console.print(Panel(
            contenu,
            border_style=panel_color,
            expand=False,
            padding=(0, 2)
        ))

        # Méta-infos
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column(style="dim")
        table.add_column(style="green")
        if meta.get('deja_sortie'):
            histo_val = "[bold red]⚠️  Déjà sortie dans l'historique ![/bold red]"
        else:
            histo_val = "[green]Jamais sortie[/green]"
        table.add_row("🔐 Source",      meta['source'])
        table.add_row("🔄 Tentatives",   str(meta['tentatives']))
        table.add_row("📚 Historique",   histo_val)
        console.print(table)
        console.print()

    def _afficher_combo_simple(self, jeu, numeros, complement, type_comp, meta):
        nums_str = " - ".join(f"{n:02d}" for n in numeros)

        if type_comp == "etoiles":
            comp_str = " ".join(f"✦{e:02d}" for e in complement)
            comp_label = "ÉTOILES"
        elif type_comp == "chance":
            comp_str = f"{complement:02d}"
            comp_label = "CHANCE"
        else:
            comp_str = complement
            comp_label = "LETTRE"

        print(f"\n{VERT}{'─'*40}{RESET}")
        print(f"  {GRAS}NUMÉROS  :{RESET} {BLEU}{nums_str}{RESET}")
        print(f"  {GRAS}{comp_label:8} :{RESET} {ORANGE}{comp_str}{RESET}")
        print(f"{VERT}{'─'*40}{RESET}")
        if meta.get('deja_sortie'):
            print(f"  ⚠️  Déjà sortie dans l'historique !")
        print(f"  🔐 {meta['source']} · {meta['tentatives']} tentative(s)\n")

    # ─────────────────────────────────────────
    # HISTORIQUE
    # ─────────────────────────────────────────

    def afficher_historique(self, historique, jeu: str):
        tirages = historique.tous_les_tirages()
        nb = historique.nb_tirages()

        if HAS_RICH:
            console.print(Panel(
                f"[bold]📚 Historique {TITRES[jeu]}[/bold] — {nb} tirage(s) enregistré(s)",
                border_style="blue"
            ))
            if jeu == "crescendo" and tirages:
                table = Table(box=box.ROUNDED)
                table.add_column("Date", style="dim")
                table.add_column("Heure", style="cyan")
                table.add_column("Numéros", style="white")
                table.add_column("Lettre", style="yellow")
                for t in tirages:
                    nums = " ".join(f"{n:02d}" for n in t["numeros"])
                    table.add_row(t["date"], t["heure"], nums, t["lettre"])
                console.print(table)
            elif not tirages:
                console.print("[dim]  Aucun tirage enregistré.[/dim]")
        else:
            print(f"\n📚 Historique {jeu} — {nb} tirage(s)")
            if jeu == "crescendo":
                for t in tirages:
                    nums = " ".join(f"{n:02d}" for n in t["numeros"])
                    print(f"  {t['date']} {t['heure']} | {nums} | {t['lettre']}")

    # ─────────────────────────────────────────
    # UTILITAIRES
    # ─────────────────────────────────────────

    def separateur(self, texte: str):
        if HAS_RICH:
            console.rule(f"[dim]{texte}[/dim]")
        else:
            print(f"\n── {texte} ──")

    def erreur(self, message: str):
        if HAS_RICH:
            console.print(f"[bold red]❌ {message}[/bold red]")
        else:
            print(f"❌ {message}")
