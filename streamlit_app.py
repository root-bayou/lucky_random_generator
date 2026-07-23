"""
FDJ RNG — Streamlit web interface (web / mobile)
Browser access: PC, tablet, smartphone
"""

import sys
import time
from pathlib import Path
from datetime import datetime, date, timedelta

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

# prediction engine — fail-safe import
try:
    from crescendo_predict import predict_crescendo, HEURES as CRDO_HEURES
    _PREDICT_OK = True
except Exception as _pe:
    _PREDICT_OK = False
    CRDO_HEURES = ["13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00"]

APP_VERSION = "1.2.0"

def next_saturday(d: date | None = None) -> date:
    """Return the date of the next Saturday (or today if already Saturday)."""
    d = d or date.today()
    days_ahead = 5 - d.weekday()   # Saturday = weekday 5
    if days_ahead < 0:
        days_ahead += 7
    return d + timedelta(days=days_ahead)


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

  /* ── GET MY CHANCE badges ── */
  .badge-best {
    display: inline-block; background: #1a4d2e; color: #a5d6a7;
    border-radius: 4px; padding: 1px 8px; font-size: 0.78rem;
    font-weight: bold; min-width: 6.5rem; margin-right: 6px;
  }
  .badge-var {
    display: inline-block; background: #1c2340; color: #9fa8da;
    border-radius: 4px; padding: 1px 8px; font-size: 0.78rem;
    min-width: 6.5rem; margin-right: 6px;
  }
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
| 🔵 **Distribution** | Count of numbers ≤ 12 vs ≥ 13 — compared to the average observed across all draws |
| ⚖️ **Parity** | Count of even vs odd numbers — compared to the observed average |
| 📐 **Spread** | Standard deviation of the 10 numbers — compared to the observed spread |
| 📈 **Frequency** | How close each number's *actual draw count* is to the historical average per number |

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

# Lock: only when current Crescendo results contain an already-drawn grid
_btn_locked = (
    jeu == "crescendo"
    and st.session_state.get("jeu_result") == "crescendo"
    and st.session_state.get("crdo_has_drawn", False)
)

_btn_area = st.empty()

if _btn_locked:
    # Replace the button with an unmissable error — no button in DOM = impossible to click
    _btn_area.error(
        "🛑 **STOP — A grid was already drawn!**  Scroll down to see which one.  "
        "*(Refresh the page to reset.)*",
        icon="🛑",
    )
else:
    if _btn_area.button(_btn_label, use_container_width=True, type="primary"):
        st.session_state["crdo_clicks"] = st.session_state.get("crdo_clicks", 0) + 1
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
            st.session_state["crescendo_nb"]   = nb
            st.session_state["crdo_has_drawn"] = any(m.get("deja_sortie") for _, m in resultats)
            if st.session_state["crdo_has_drawn"]:
                st.toast("🛑 Already-drawn grid found! Refresh to reset.", icon="🛑")
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

        # Popup warning for each already-drawn grid (above the grid list)
        for _idx, (_combo, _meta) in enumerate(resultats, 1):
            if _meta.get("deja_sortie"):
                _target = tuple(sorted(_combo["numeros"]))
                _draw = next(
                    (t for t in tirages if tuple(sorted(t["numeros"])) == _target),
                    None,
                )
                if _draw:
                    st.warning(
                        f"**Grid #{_idx}** already drawn — appeared on "
                        f"**{_draw['date']}** at **{_draw['heure']}**",
                        icon="⚠️",
                    )
                else:
                    st.warning(f"**Grid #{_idx}** already drawn!", icon="⚠️")

        # Display in generation order (no sort)
        for idx, (combo, meta) in enumerate(resultats, 1):
            is_drawn = bool(meta.get("deja_sortie"))

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
            html += (
                f'<div class="grid-row">'
                f'<span class="idx">{idx}</span>'
                f'<span class="{mode_cls}">{mode_lbl}</span>'
                f'{nums_html} &nbsp;{hist_html}'
                f'</div>'
            )
        st.markdown(f'<div class="results-scroll">{html}</div>', unsafe_allow_html=True)
        _clicks = st.session_state.get("crdo_clicks", 1)
        st.caption(
            f"🎲 {_nb} random · 🔄 {_nb} pattern-biased · ✓ new · ⚠ already drawn"
            f" · 🖱 {_clicks} click{'s' if _clicks > 1 else ''}"
        )

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

# ─── GET MY CHANCE — Crescendo prediction ─────────────────────
if jeu == "crescendo" and _PREDICT_OK:
    st.divider()
    st.subheader("🎯 GET MY CHANCE — Saturday Prediction")

    _next_sat     = next_saturday()
    _next_sat_str = _next_sat.strftime("%d/%m/%Y")

    _n_grilles = int(st.number_input(
        "Grids per draw",
        min_value=1, max_value=10, value=5, step=1,
        key="nb_predict",
        help="Number of optimised grids per hourly draw. Total stake = 7 × N × €1",
    ))
    _stake = 7 * _n_grilles
    st.info(
        f"📅 Next Saturday **{_next_sat_str}** · 7 draws (1pm–7pm) · "
        f"{_n_grilles} grid{'s' if _n_grilles > 1 else ''}/draw · Total stake: **€{_stake}**",
        icon="🎰",
    )

    if st.button("🍀  GET MY CHANCE", use_container_width=True, type="primary", key="btn_predict"):
        with st.spinner("Computing optimal grids… (30–60 sec)"):
            _tirages_all = historique.tous_les_tirages()
            _predictions = predict_crescendo(_tirages_all, n_grilles=_n_grilles)
        st.session_state["crescendo_predict"]      = _predictions
        st.session_state["crescendo_predict_date"] = _next_sat_str
        st.session_state["crescendo_predict_n"]    = _n_grilles

    if "crescendo_predict" in st.session_state:
        _predictions = st.session_state["crescendo_predict"]
        _pred_date   = st.session_state.get("crescendo_predict_date", "—")

        st.caption(
            f"Generated for **{_pred_date}** · "
            f"🏆 BEST = top-scoring grid · 🌐 DIV = diversity-selected (covers cold numbers) · "
            f"{historique.nb_tirages()} draws · Score = historical likelihood (0–100)"
        )

        _tabs = st.tabs([f"⏰ {h}" for h in CRDO_HEURES])
        for _tab, _heure in zip(_tabs, CRDO_HEURES):
            with _tab:
                _grilles  = _predictions.get(_heure, [])
                _html     = ""
                for _i, (_label, _nums, _ss) in enumerate(_grilles, 1):
                    _is_best   = _label == "BEST"
                    _badge_cls = "badge-best" if _is_best else "badge-var"
                    _badge_txt = "🏆 BEST" if _is_best else f"🌐 {_label}"
                    _nums_html = "".join(f'<span class="num">{n:02d}</span>' for n in _nums)
                    _sc_cls    = "score-hi" if _ss >= 65 else "score-mid" if _ss >= 40 else "score-lo"
                    _html += (
                        f'<div class="grid-row">'
                        f'<span class="idx">{_i}</span>'
                        f'<span class="{_badge_cls}">{_badge_txt}</span>'
                        f'{_nums_html}'
                        f' &nbsp;<span class="{_sc_cls}">{_ss}/100</span>'
                        f'</div>'
                    )
                st.markdown(f'<div class="results-scroll">{_html}</div>', unsafe_allow_html=True)

        with st.expander("💶 Crescendo Prize Table", expanded=False):
            st.markdown("""
| Correct numbers | Without letter | With letter |
|:---:|---:|---:|
| **10** (Jackpot) | ≥ €100,000 | ≥ €100,000 |
| **9** | €500 | €1,000 |
| **8** | €50 | €100 |
| **7** | €7 | €14 |
| **6** | €1 | €2 |
| 0–5 + letter | — | €1 *(refund)* |

*The letter (S/A/M/E/D/I) is assigned randomly on your ticket at purchase.*
*Jackpot: €100,000 min at 1pm draw, +€100,000 each hour without a winner, up to €700,000 at 7pm.*
""")

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

