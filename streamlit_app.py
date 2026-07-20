"""
FDJ RNG — Streamlit web interface (web / mobile)
Browser access: PC, tablet, smartphone
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st
from generateur import Generateur
from historique import Historique

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
  .grid-row  { font-family: monospace; font-size: 1.05rem; padding: 6px 0;
               border-bottom: 1px solid #2a2a2a; }
  .combo-row { font-family: monospace; font-size: 1.1rem; padding: 10px 0;
               border-bottom: 1px solid #2a2a2a; }
  .num    { display: inline-block; background: #1a4a8a; color: #fff;
            border-radius: 4px; padding: 2px 7px; margin: 2px; font-weight: bold; }
  .num-hot{ display: inline-block; background: #b35a00; color: #fff;
            border-radius: 4px; padding: 2px 7px; margin: 2px; font-weight: bold; }
  .num-hot{ display: inline-block; background: #b35a00; color: #fff;
            border-radius: 4px; padding: 2px 7px; margin: 2px; font-weight: bold; }
  .star   { display: inline-block; background: #6b5000; color: #ffd700;
            border-radius: 4px; padding: 2px 7px; margin: 2px; font-weight: bold; }
  .dream  { display: inline-block; background: #4a006b; color: #e0aaff;
            border-radius: 4px; padding: 2px 7px; margin: 2px; font-weight: bold; }
  .chance { display: inline-block; background: #7a0000; color: #fff;
            border-radius: 4px; padding: 2px 7px; margin: 2px; font-weight: bold; }
  .mode-r { color: #4fc3f7; font-size: 0.85rem; }
  .mode-p { color: #81c784; font-size: 0.85rem; }
  .ok     { color: #66bb6a; font-weight: bold; }
  .warn   { color: #ef5350; font-weight: bold; }
  .sep    { border-top: 2px solid #444; margin: 8px 0; }
  h1      { font-size: 1.5rem !important; }
</style>
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
    label_visibility="collapsed",
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
    "crescendo":    "10 grids · 5 random + 5 pattern-biased",
}

st.title(f"🎰 FDJ RNG — {TITLES[jeu]}")
st.caption(
    f"📚 {historique.nb_tirages()} FDJ draws · "
    "🔐 os.urandom (zero PRNG) · "
    f"{SUBTITLES[jeu]}"
)

st.divider()

# ─── Options ──────────────────────────────────────────────────
if jeu != "crescendo":
    nb = st.slider("Number of combinations", 1, 10, 1)
else:
    nb = None

# ─── Generate button ──────────────────────────────────────────
BTN_LABELS = {
    "euromillions": "🌟  GENERATE",
    "eurodreams":   "💫  GENERATE",
    "loto":         "🍀  GENERATE",
    "crescendo":    "🎲  GENERATE 10 GRIDS",
}

if st.button(BTN_LABELS[jeu], use_container_width=True, type="primary"):
    gen = Generateur(jeu, historique)

    if jeu == "crescendo":
        refs, resultats = [], []
        for _ in range(5):
            combo, meta = gen.generer()
            meta["mode"] = "random"
            refs.append(combo)
            resultats.append((combo, meta))
        for _ in range(5):
            combo, meta = gen.generer_pseudo(refs)
            resultats.append((combo, meta))
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

    html = ""

    if jeu_r == "crescendo":
        for idx, (combo, meta) in enumerate(resultats, 1):
            if idx == 6:
                html += '<div class="sep"></div>'
            mode_lbl = "🎲 Random"  if meta.get("mode") == "random" else "🔄 Pattern"
            mode_cls = "mode-r"     if meta.get("mode") == "random" else "mode-p"
            hist_html = (
                '<span class="warn">⚠ Already drawn</span>'
                if meta.get("deja_sortie") else
                '<span class="ok">✓ New</span>'
            )
            nums_html = "".join(
                f'<span class="num">{n:02d}</span>' for n in combo["numeros"]
            )
            html += (
                f'<div class="grid-row">'
                f'<span style="color:#888;width:1.5rem;display:inline-block">{idx}</span>'
                f'<span class="{mode_cls}" style="width:7rem;display:inline-block">{mode_lbl}</span>'
                f'{nums_html} &nbsp;{hist_html}'
                f'</div>'
            )
        st.markdown(html, unsafe_allow_html=True)
        st.divider()
        st.caption("🎲 pure random · 🔄 pattern from first 5 · ✓ new · ⚠ already drawn in FDJ history")

        # ─── BETA: Overlap Analysis ───────────────────────────────────
        if historique.nb_tirages() > 0:
            with st.expander("🔬 Overlap Analysis · BETA", expanded=False):
                max_n = min(50, historique.nb_tirages())
                n_draws = st.slider(
                    "Last N draws to analyze",
                    min_value=1, max_value=max_n,
                    value=min(10, max_n),
                    key="overlap_n",
                    help="Numbers that appeared in the last N official FDJ draws are highlighted in orange"
                )
                pool = historique.recent_pool_crescendo(n_draws)

                st.caption(
                    f"🔥 {len(pool)} unique numbers out of 25 appeared in the last {n_draws} draws"
                )

                # Hot/cold overview of all 25 numbers
                overview = "".join(
                    f'<span class="num-hot">{n:02d}</span>' if n in pool
                    else f'<span style="display:inline-block;background:#1a1a2e;color:#444;'
                         f'border-radius:4px;padding:2px 7px;margin:2px;font-family:monospace;font-weight:bold">{n:02d}</span>'
                    for n in range(1, 26)
                )
                st.markdown(f'<div style="margin:6px 0">{overview}</div>', unsafe_allow_html=True)
                st.divider()

                # Per-grid overlap count
                ov_html = ""
                for idx, (combo, meta) in enumerate(resultats, 1):
                    if idx == 6:
                        ov_html += '<div class="sep"></div>'
                    mode_icon = "🎲" if meta.get("mode") == "random" else "🔄"
                    hot_count = sum(1 for n in combo["numeros"] if n in pool)
                    nums_ov = "".join(
                        f'<span class="num-hot">{n:02d}</span>' if n in pool
                        else f'<span class="num">{n:02d}</span>'
                        for n in combo["numeros"]
                    )
                    bar_color = (
                        "#ef5350" if hot_count >= 7
                        else "#ff9800" if hot_count >= 4
                        else "#66bb6a"
                    )
                    ov_html += (
                        f'<div class="grid-row">'
                        f'<span style="color:#888;width:1.5rem;display:inline-block">{idx}</span>'
                        f'<span style="width:1.5rem;display:inline-block">{mode_icon}</span>'
                        f'{nums_ov}'
                        f' &nbsp;<span style="color:{bar_color};font-weight:bold">{hot_count}/10 🔥</span>'
                        f'</div>'
                    )
                st.markdown(ov_html, unsafe_allow_html=True)
                st.caption("🔥 orange = appeared in last N draws · 🔵 blue = not recently drawn")

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
                f'<span style="color:#888;margin-right:8px">#{idx}</span>'
                f'{nums_html}{comp_html} &nbsp; {hist_html}'
                f'</div>'
            )
        st.markdown(html, unsafe_allow_html=True)
        st.divider()
        if jeu_r == "euromillions":
            st.caption("🔵 numbers · ✦ stars · ✓ new · ⚠ already drawn in FDJ history")
        elif jeu_r == "eurodreams":
            st.caption("🔵 numbers · 💫 dream number · ✓ new · ⚠ already drawn in FDJ history")
        else:
            st.caption("🔵 numbers · 🍀 lucky number · ✓ new · ⚠ already drawn in FDJ history")

