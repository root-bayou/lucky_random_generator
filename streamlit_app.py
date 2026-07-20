"""
FDJ RNG — Interface Streamlit (web / mobile)
Accès navigateur : PC, tablette, smartphone
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st
from generateur import Generateur
from historique import Historique

# ─── Config page ───────────────────────────────────────────────
st.set_page_config(
    page_title="FDJ RNG — Crescendo",
    page_icon="🎵",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─── CSS compact mobile ────────────────────────────────────────
st.markdown("""
<style>
  .grid-row   { font-family: monospace; font-size: 1.05rem; padding: 6px 0; border-bottom: 1px solid #2a2a2a; }
  .num        { display: inline-block; background: #1a4a8a; color: #fff;
                border-radius: 4px; padding: 2px 6px; margin: 1px; font-weight: bold; }
  .mode-r     { color: #4fc3f7; font-size: 0.85rem; }
  .mode-p     { color: #81c784; font-size: 0.85rem; }
  .ok         { color: #66bb6a; font-weight: bold; }
  .warn       { color: #ef5350; font-weight: bold; }
  .sep        { border-top: 2px solid #444; margin: 8px 0; }
  h1          { font-size: 1.5rem !important; }
</style>
""", unsafe_allow_html=True)


# ─── Chargement historique (mis en cache) ─────────────────────
@st.cache_resource(show_spinner="Chargement historique FDJ…")
def load_historique():
    return Historique("crescendo")


historique = load_historique()


# ─── En-tête ──────────────────────────────────────────────────
st.title("🎵 FDJ RNG — Crescendo")
st.caption(
    f"📚 {historique.nb_tirages()} tirages FDJ chargés · "
    "🔐 os.urandom (zéro PRNG) · "
    "🎲×5 aléatoire + 🔄×5 tendances"
)

st.divider()


# ─── Bouton génération ────────────────────────────────────────
if st.button("🎲  GÉNÉRER 10 GRILLES", use_container_width=True, type="primary"):

    gen = Generateur("crescendo", historique)

    refs, resultats = [], []
    for _ in range(5):
        combo, meta = gen.generer()
        meta["mode"] = "random"
        refs.append(combo)
        resultats.append((combo, meta))
    for _ in range(5):
        combo, meta = gen.generer_pseudo(refs)
        resultats.append((combo, meta))

    st.session_state["resultats"] = resultats


# ─── Affichage résultats ──────────────────────────────────────
if "resultats" in st.session_state:
    resultats = st.session_state["resultats"]

    html = ""
    for idx, (combo, meta) in enumerate(resultats, 1):
        # Séparateur entre les deux blocs
        if idx == 6:
            html += '<div class="sep"></div>'

        mode_label = "🎲 Aléatoire" if meta.get("mode") == "random" else "🔄 Tendances"
        mode_cls   = "mode-r"        if meta.get("mode") == "random" else "mode-p"
        hist_html  = '<span class="warn">⚠ Déjà sortie</span>' if meta.get("deja_sortie") \
                     else '<span class="ok">✓</span>'

        nums_html = "".join(f'<span class="num">{n:02d}</span>' for n in combo["numeros"])

        html += (
            f'<div class="grid-row">'
            f'<span style="color:#888;width:1.4rem;display:inline-block">{idx}</span>'
            f'<span class="{mode_cls}" style="width:6.5rem;display:inline-block">{mode_label}</span>'
            f'{nums_html} &nbsp;{hist_html}'
            f'</div>'
        )

    st.markdown(html, unsafe_allow_html=True)

    st.divider()
    st.caption("🎲 aléatoire pur · 🔄 tendances des 5 premières · ✓ inédite · ⚠ déjà sortie FDJ")
