"""
Styled display — uses rich for polished terminal output
Fallback to colorama if rich is absent
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
        BLUE   = "\033[94m"
        GREEN  = "\033[92m"
        RED    = "\033[91m"
        RESET  = "\033[0m"
        BOLD   = "\033[1m"
    except ImportError:
        ORANGE = BLUE = GREEN = RED = RESET = BOLD = ""


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
    # BANNER
    # ─────────────────────────────────────────

    def banniere(self, jeu: str):
        emoji = EMOJIS[jeu]
        titre = TITRES[jeu]

        if HAS_RICH:
            console.print()
            console.print(Panel(
                f"[bold yellow]{emoji}  FDJ RNG — {titre}  {emoji}[/bold yellow]\n"
                f"[dim]Cryptographic generator \u00b7 os.urandom (CryptGenRandom) — zero PRNG[/dim]",
                border_style="yellow",
                expand=False,
                padding=(0, 4)
            ))
        else:
            print(f"\n{BOLD}{ORANGE}{'='*50}{RESET}")
            print(f"{BOLD}{ORANGE}  {emoji}  FDJ RNG \u2014 {titre}  {emoji}{RESET}")
            print(f"  os.urandom (CryptGenRandom) \u2014 zero PRNG")
            print(f"{BOLD}{ORANGE}{'='*50}{RESET}\n")

    # ─────────────────────────────────────────
    # CRESCENDO — 10 GRIDS IN ONE PANEL
    # ─────────────────────────────────────────

    def afficher_crescendo_5grilles(self, resultats: list):
        if HAS_RICH:
            table = Table(box=box.SIMPLE_HEAD, show_header=True, padding=(0, 1),
                          header_style="dim")
            table.add_column("#",       width=2,  style="bold")
            table.add_column("Mode",    width=3)
            table.add_column("Numbers", min_width=44)
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
                title="[bold yellow]🎵  CRESCENDO — 10 Grids[/bold yellow]",
                subtitle="[dim]🎲 random  🔄 pattern  ✓ new  ⚠ already drawn[/dim]",
                border_style="yellow",
                padding=(0, 1)
            ))
            console.print()
        else:
            print("\n🎵 CRESCENDO — 10 Grids\n")
            for idx, (combo, meta) in enumerate(resultats, 1):
                mode = "🎲" if meta.get("mode") == "random" else "🔄"
                nums = "  ".join(f"{n:02d}" for n in combo["numeros"])
                hist = " ⚠️" if meta.get("deja_sortie") else " ✓"
                print(f"  [{idx}] {mode}  {nums}{hist}")
            print()

    # ─────────────────────────────────────────
    # COMBO DISPLAY
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
        # Numbers
        nums_str = "  ".join(f"[bold white on blue] {n:02d} [/]" for n in numeros)

        # Complement
        if type_comp == "etoiles":
            comp_str = "  ".join(f"[bold black on yellow] ❆{e:02d} [/]" for e in complement)
            comp_label = "STARS"
        elif type_comp == "chance":
            comp_str = f"[bold white on red] {complement:02d} [/]"
            comp_label = "CHANCE"
        else:  # letter
            comp_str = f"[bold white on cyan]  {complement}  [/]"
            comp_label = "LETTER"

        # Main panel
        panel_color = "cyan" if meta.get("mode") == "pseudo" else "green"
        contenu = (
            f"\n  [dim]NUMBERS[/dim]\n"
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

        # Meta table
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column(style="dim")
        table.add_column(style="green")
        if meta.get('deja_sortie'):
            hist_val = "[bold red]⚠️  Already drawn in history![/bold red]"
        else:
            hist_val = "[green]Never drawn[/green]"
        table.add_row("🔐 Source",     meta['source'])
        table.add_row("🔄 Attempts",   str(meta['tentatives']))
        table.add_row("📚 History",    hist_val)
        console.print(table)
        console.print()

    def _afficher_combo_simple(self, jeu, numeros, complement, type_comp, meta):
        nums_str = " - ".join(f"{n:02d}" for n in numeros)

        if type_comp == "etoiles":
            comp_str = " ".join(f"✦{e:02d}" for e in complement)
            comp_label = "STARS"
        elif type_comp == "chance":
            comp_str = f"{complement:02d}"
            comp_label = "CHANCE"
        else:
            comp_str = complement
            comp_label = "LETTER"

        sep = '─' * 40
        print(f"\n{GREEN}{sep}{RESET}")
        print(f"  {BOLD}NUMBERS  :{RESET} {BLUE}{nums_str}{RESET}")
        print(f"  {BOLD}{comp_label:8} :{RESET} {ORANGE}{comp_str}{RESET}")
        print(f"{GREEN}{sep}{RESET}")
        if meta.get('deja_sortie'):
            print(f"  ⚠️  Already drawn in history!")
        print(f"  🔐 {meta['source']} \u00b7 {meta['tentatives']} attempt(s)\n")

    # ─────────────────────────────────────────
    # HISTORY
    # ─────────────────────────────────────────

    def afficher_historique(self, historique, jeu: str):
        tirages = historique.tous_les_tirages()
        nb = historique.nb_tirages()

        if HAS_RICH:
            console.print(Panel(
                f"[bold]📚 {TITRES[jeu]} History[/bold] — {nb} draw(s)",
                border_style="blue"
            ))
            if jeu == "crescendo" and tirages:
                table = Table(box=box.ROUNDED)
                table.add_column("Date", style="dim")
                table.add_column("Time", style="cyan")
                table.add_column("Numbers", style="white")
                table.add_column("Letter", style="yellow")
                for t in tirages:
                    nums = " ".join(f"{n:02d}" for n in t["numeros"])
                    table.add_row(t["date"], t["heure"], nums, t["lettre"])
                console.print(table)
            elif not tirages:
                console.print("[dim]  No draws recorded.[/dim]")
        else:
            print(f"\n📚 {jeu} history — {nb} draw(s)")
            if jeu == "crescendo":
                for t in tirages:
                    nums = " ".join(f"{n:02d}" for n in t["numeros"])
                    print(f"  {t['date']} {t['heure']} | {nums} | {t['lettre']}")

    # ─────────────────────────────────────────
    # UTILITIES
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
