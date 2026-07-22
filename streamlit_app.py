"""
FDJ RNG — Streamlit web interface (web / mobile)
Browser access: PC, tablet, smartphone
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st
from generateur import Generateur
from historique import Historique, ETC_DIR, FOLDERS_PER_GAME

# stats module — fail-safe import (does not crash the app if unavailable)
try:
    from stats_crescendo import scorer as score_crescendo
    _STATS_OK = True
except Exception as _stats_err:
    _STATS_OK = False
    def score_crescendo(numeros, tirages):  # noqa: E302
        return {"score": 50, "etoiles": 3, "chauds": 0, "detail": "stats unavailable"}

APP_VERSION = "1.2.0"

@st.cache_data
def last_data_update(game: str) -> str:
    """Return the date of the most recently modified CSV for this game."""
    if game == "crescendo":
        folders = [ETC_DIR / "crescendo"]
    else:
        folders = [ETC_DIR / f for f in FOLDERS_PER_GAME.get(game, [])]
    mtimes = [
        f.stat().st_mtime
        for folder in folders if folder.exists()
        for f in folder.glob("*.csv")
    ]
    if not mtimes:
        return "unknown"
    return datetime.fromtimestamp(max(mtimes)).strftime("%Y-%m-%d")

# ─── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="FDJ RNG",
    page_icon="🎰",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
  /* ── Lottery ball badges ── */
  .num, .num-hot, .star, .dream, .chance {
    display: inline-flex; justify-content: center; align-items: center;
    border-radius: 50%; min-width: 2rem; height: 2rem;
    padding: 0 0.25rem; margin: 2px;
    font-weight: bold; font-size: 0.85rem; font-family: 'Courier New', monospace;
    box-shadow: 0 1px 4px rgba(0,0,0,0.45);
  }
  .num     { background: #1565c0; color: #fff; }
  .num-hot { background: #b35a00; color: #fff; }
  .star    { background: #7b5e00; color: #ffd700; }
  .dream   { background: #4a006b; color: #e0aaff; }
  .chance  { background: #7a0000; color: #ffcdd2; }

  /* ── Row layout ── */
  .grid-row {
    font-family: monospace; font-size: 1rem;
    padding: 6px 4px; border-bottom: 1px solid #2a2a2a;
  }
  .combo-row {
    font-family: monospace; font-size: 1.05rem;
    padding: 8px 4px; border-bottom: 1px solid #2a2a2a;
  }
  .idx    { color: #888; display: inline-block; min-width: 1.8rem; }
  .mode-r { color: #4fc3f7; font-size: 0.82rem;
            display: inline-block; min-width: 7rem; }
  .mode-p { color: #81c784; font-size: 0.82rem;
            display: inline-block; min-width: 7rem; }
  .ok     { color: #66bb6a; font-weight: bold; }
  .warn   { color: #ef5350; font-weight: bold; }
  .sep    { border-top: 2px solid #444; margin: 6px 0; }
  h1      { font-size: 1.3rem !important; }

  /* ── Compact Streamlit layout ── */
  .block-container {
    padding-top: 1rem !important;
    padding-bottom: 0.5rem !important;
  }

  /* ── Scrollable results container ── */
  .results-scroll {
    max-height: 52vh;
    overflow-y: auto;
    padding: 4px 8px;
    border: 1px solid #2a2a2a;
    border-radius: 6px;
    scrollbar-width: thin;
    scrollbar-color: #444 transparent;
  }
  .results-scroll::-webkit-scrollbar { width: 6px; }
  .results-scroll::-webkit-scrollbar-thumb { background: #444; border-radius: 3px; }

  /* ── Stat sub-row ── */
  .stat-row {
    font-size: 0.75rem;
    color: #999;
    padding: 1px 0 4px 1.8rem;
  }
  .score-hi  { color: #66bb6a; font-weight: bold; }
  .score-mid { color: #ffd54f; }
  .score-lo  { color: #ef5350; }


</style>
<script>
  // Prevent page scroll when mouse wheel is on a number input
  document.addEventListener('wheel', function(e) {
    if (document.activeElement && document.activeElement.type === 'number') {
      e.preventDefault();
    }
  }, { passive: false });
</script>
""", unsafe_allow_html=True)

# ─── Game selector ────────────────────────────────────────────
GAMES = {
    "🌟 EuroMillions": "euromillions",
    "💫 EuroDreams":   "eurodreams",
    "🍀 Loto":         "loto",
    "🎵 Crescendo":    "crescendo",
}

choice = st.radio(
    "Game",
    list(GAMES.keys()),
    index=2,
    horizontal=True,
    label_visibility="hidden",
    key="game_selector",
)
jeu = GAMES[choice]

# Clear results when switching games
if st.session_state.get("jeu_result") != jeu:
    st.session_state.pop("resultats", None)

# ─── History (cached per game) ────────────────────────────────
@st.cache_resource(show_spinner="Loading FDJ history…")
def load_historique(game: str):
    return Historique(game)

historique = load_historique(jeu)

# ─── Header ───────────────────────────────────────────────────
TITLES = {
    "euromillions": "🌟 EuroMillions",
    "eurodreams":   "💫 EuroDreams",
    "loto":         "🍀 Loto",
    "crescendo":    "🎵 Crescendo",
}
SUBTITLES = {
    "euromillions": "5 numbers (1–50) + 2 stars (1–12)",
    "eurodreams":   "6 numbers (1–40) + 1 dream number (1–5)",
    "loto":         "5 numbers (1–49) + 1 lucky number (1–10)",
    "crescendo":    "random + pattern-biased grids",
}

st.title(f"🎰 FDJ RNG — {TITLES[jeu]}")
_data_date = last_data_update(jeu)
st.caption(
    f"📚 {historique.nb_tirages()} FDJ draws · "
    f"📅 Data: {_data_date} · "
    "🔐 os.urandom (zero PRNG) · "
    f"{SUBTITLES[jeu]}"
)

st.divider()

# ─── How it works ─────────────────────────────────────────────
with st.expander("🔐 How does the randomness work?", expanded=False):
    st.markdown("""
**Source of randomness — `os.urandom`**

Every number is drawn by calling `secrets.randbelow()`, which reads directly from the
operating system's entropy pool (`CryptGenRandom` on Windows, `/dev/urandom` on Linux).
There is **no seed, no internal state, no PRNG** — each draw consumes fresh entropy independently.

**Algorithm — Fisher-Yates partial shuffle**

To pick *k* numbers from a pool of *N* without replacement, the generator performs a partial
Fisher-Yates shuffle with rejection sampling, giving each combination an exactly equal probability:

$$P = \\frac{1}{\\binom{N}{k}}$$

**History cross-check**

Every generated grid is compared against all official past FDJ draws loaded at startup.
A ⚠️ badge flags any grid that has already been drawn in an official FDJ game.

**Crescendo — Pattern mode**

For Crescendo, half the grids are *pure random* (🎲) and half are *pattern-biased* (🔄):
3 to 5 numbers are reused from the random grids, the rest are freshly drawn from `os.urandom`.
This mimics the statistical clustering observed in real Crescendo draws without weakening
the entropy of the independent numbers.

> **This tool cannot predict lottery results.** Every official draw is independent.
""")

if jeu == "crescendo":
    with st.expander("📊 How does score ranking work?", expanded=False):
        st.markdown(f"""
The score **(0 – 100)** measures how closely a grid matches the distributional patterns
observed in the **{historique.nb_tirages()} official FDJ Crescendo draws** on record.
It does **not** predict winning — every combination has an equal probability.

**4 criteria · 25 pts each — all computed exclusively from observed draws**

| Criterion | What is measured |
|---|---|
| 🔵 **Répartition** | Count of numbers ≤ 12 vs ≥ 13 — compared to the average observed across all draws |
| ⚖️ **Parité** | Count of even vs odd numbers — compared to the observed average |
| 📐 **Étalement** | Standard deviation of the 10 numbers — compared to the observed spread |
| 📈 **Fréquence** | How close each number's *actual draw count* is to the historical average per number |

Each criterion computes a **z-score** (distance from the observed mean in units of observed
standard deviation). A grid at exactly the historical average on all 4 axes would score 100.
A typical random grid scores **35 – 65**; unusual distributions score lower.

| Score | Stars | Meaning |
|---|---|---|
| ≥ 80 | ★★★★★ | Extremely close to historical norms |
| 65 – 79 | ★★★★☆ | Very typical |
| 50 – 64 | ★★★☆☆ | Average |
| 30 – 49 | ★★☆☆☆ | Slightly atypical |
| < 30 | ★☆☆☆☆ | Unusual distribution |

The **🔥 X/10** indicator shows how many of the 10 numbers appeared in the **last 5 draws**
(display only — not included in the score).

> Grids are sorted **best score first**. ⚠️ already-drawn grids are always pinned to the top.
""")

# ─── Options ──────────────────────────────────────────────────
if jeu == "crescendo":
    nb = int(st.number_input(
        "Number of grids per type",
        min_value=1, value=5, step=1,
        key="nb_crescendo",
        help="Generates N random grids + N pattern-biased grids",
    ))
else:
    nb = int(st.number_input(
        "Number of grids",
        min_value=1, value=1, step=1,
        key="nb_other",
    ))

# ─── Generate button ──────────────────────────────────────────
BTN_ICONS = {"euromillions": "🌟", "eurodreams": "💫", "loto": "🍀", "crescendo": "🎲"}
_icon = BTN_ICONS[jeu]
if jeu == "crescendo":
    _btn_label = f"{_icon}  GENERATE {nb * 2} GRIDS  ({nb} random + {nb} pattern)"
else:
    _btn_label = f"{_icon}  GENERATE {nb} GRID{'S' if nb > 1 else ''}"

if st.button(_btn_label, use_container_width=True, type="primary"):
    gen = Generateur(jeu, historique)

    if jeu == "crescendo":
        refs, resultats = [], []
        for _ in range(nb):
            combo, meta = gen.generer()
            meta["mode"] = "random"
            refs.append(combo)
            resultats.append((combo, meta))
        for _ in range(nb):
            combo, meta = gen.generer_pseudo(refs)
            resultats.append((combo, meta))
        st.session_state["crescendo_nb"] = nb
    else:
        resultats = []
        for _ in range(nb):
            combo, meta = gen.generer()
            resultats.append((combo, meta))

    st.session_state["resultats"]  = resultats
    st.session_state["jeu_result"] = jeu

# ─── Results display ──────────────────────────────────────────
if (
    "resultats" in st.session_state
    and st.session_state.get("jeu_result") == jeu
):
    resultats = st.session_state["resultats"]
    jeu_r     = st.session_state["jeu_result"]
    tirages   = historique.tous_les_tirages() if jeu_r == "crescendo" else []

    html = ""

    if jeu_r == "crescendo":
        _nb = st.session_state.get("crescendo_nb", nb)

        # Compute stats for every grid, then sort:
        # already-drawn first (rare highlight), then by score descending
        enriched = []
        for combo, meta in resultats:
            try:
                stat = score_crescendo(combo["numeros"], tirages)
            except Exception:
                stat = {"score": 50, "etoiles": 3, "chauds": 0, "detail": "—"}
            enriched.append((combo, meta, stat))
        enriched.sort(key=lambda x: (0 if x[1].get("deja_sortie") else 1, -x[2]["score"]))

        prev_drawn = None
        for idx, (combo, meta, stat) in enumerate(enriched, 1):
            is_drawn = bool(meta.get("deja_sortie"))
            # separator between already-drawn group and new group
            if prev_drawn is not None and prev_drawn != is_drawn:
                html += '<div class="sep"></div>'
            prev_drawn = is_drawn

            mode_lbl = "🎲 Random" if meta.get("mode") == "random" else "🔄 Pattern"
            mode_cls = "mode-r"    if meta.get("mode") == "random" else "mode-p"
            hist_html = (
                '<span class="warn">⚠ Already drawn</span>'
                if is_drawn else
                '<span class="ok">✓ New</span>'
            )
            nums_html = "".join(
                f'<span class="num">{n:02d}</span>' for n in combo["numeros"]
            )
            stars_str = "★" * stat["etoiles"] + "☆" * (5 - stat["etoiles"])
            score_cls = (
                "score-hi"  if stat["score"] >= 65 else
                "score-mid" if stat["score"] >= 40 else
                "score-lo"
            )
            stat_html = (
                f'<div class="stat-row">'
                f'<span class="{score_cls}">{stat["score"]}/100 {stars_str}</span>'
                f' &nbsp;{stat["detail"]}'
                f'</div>'
            )
            html += (
                f'<div class="grid-row">'
                f'<span class="idx">{idx}</span>'
                f'<span class="{mode_cls}">{mode_lbl}</span>'
                f'{nums_html} &nbsp;{hist_html}'
                f'</div>'
                f'{stat_html}'
            )
        st.markdown(f'<div class="results-scroll">{html}</div>', unsafe_allow_html=True)
        st.caption(f"🎲 {_nb} random · 🔄 {_nb} pattern-biased · ✓ new · ⚠ already drawn · score: vraisemblance historique")

    else:
        for idx, (combo, meta) in enumerate(resultats, 1):
            nums_html = "".join(
                f'<span class="num">{n:02d}</span>' for n in combo["numeros"]
            )
            if jeu_r == "euromillions":
                comp_html = " &nbsp;✦ " + "".join(
                    f'<span class="star">{e:02d}</span>' for e in combo["complement"]
                )
            elif jeu_r == "eurodreams":
                comp_html = f' &nbsp;💫 <span class="dream">{combo["complement"]:02d}</span>'
            else:
                comp_html = f' &nbsp;🍀 <span class="chance">{combo["complement"]:02d}</span>'

            hist_html = (
                '<span class="warn">⚠ Already drawn</span>'
                if meta.get("deja_sortie") else
                '<span class="ok">✓ New</span>'
            )
            html += (
                f'<div class="combo-row">'
                f'<span class="idx">#{idx}</span>'
                f'{nums_html}{comp_html} &nbsp; {hist_html}'
                f'</div>'
            )
        st.markdown(f'<div class="results-scroll">{html}</div>', unsafe_allow_html=True)
        if jeu_r == "euromillions":
            st.caption("🔵 numbers · ✦ stars · ✓ new · ⚠ already drawn in FDJ history")
        elif jeu_r == "eurodreams":
            st.caption("🔵 numbers · 💫 dream number · ✓ new · ⚠ already drawn in FDJ history")
        else:
            st.caption("🔵 numbers · 🍀 lucky number · ✓ new · ⚠ already drawn in FDJ history")

# ─── Disclaimer ───────────────────────────────────────────────
st.divider()
st.markdown(f"""
<div style="font-size:0.78rem;color:#888;text-align:center;line-height:1.6">
  ⚠️ <strong>Disclaimer</strong> — This tool is a statistical utility.
  It does <em>not</em> predict lottery outcomes.<br>
  Every draw is pure chance — each combination has an identical probability of winning.<br>
  Gambling carries risks. Please play responsibly.<br>
  🇫🇷 Problem Gambling Helpline: <strong>09 74 75 13 13</strong> (France, free 24/7)<br>
  <span style="opacity:0.45">v{APP_VERSION} · Python {sys.version[:6]} · stats:{'ok' if _STATS_OK else 'err'}</span>
</div>
""", unsafe_allow_html=True)

