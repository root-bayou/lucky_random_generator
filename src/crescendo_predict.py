"""
crescendo_predict.py
====================
Moteur de prediction Crescendo pour l'app Streamlit.

Strategie (5 grilles / heure) :
  1. Generer N candidats aleatoires ponderes (bayesien + greedy)
  2. Selectionner LA MEILLEURE grille (score composite max)
  3. Construire 4 VARIANTES : fixer 6-8 numeros de la meilleure,
     tirer les restants de facon ponderee parmi 1-25 non fixes
  4. Retourner les 5 grilles par heure pour le prochain samedi

Total : 7 heures x 5 grilles = 35 grilles
"""

import math, random, statistics
from collections import Counter
from datetime import datetime

HEURES       = ["13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00"]
N_RANDOM     = 25_000   # candidats random bayesiens par heure
N_GREEDY     = 5_000    # candidats greedy co-occurrence par heure
LAMBDA_DECAY = 0.05
BETA_PRIOR   = 25

# Table des gains officielle FDJ
GAINS_TABLE = {
    10: ("JACKPOT", "JACKPOT"),
    9:  (500, 1000),
    8:  (50, 100),
    7:  (7, 14),
    6:  (1, 2),
}


def calc_gain(n_match: int, has_lettre: bool = False):
    """Retourne le gain en EUR (int) ou 'JACKPOT' (str)."""
    if n_match == 10:
        return "JACKPOT"
    entry = GAINS_TABLE.get(n_match)
    if entry:
        return entry[1] if has_lettre else entry[0]
    return 1 if has_lettre else 0   # 0-5 + lettre = remboursement


# ── Utilitaires internes ───────────────────────────────────────────────────────

def _parse_date(d):
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(d, fmt)
        except Exception:
            pass
    return datetime.min


def _norm_heure(h):
    h = str(h).strip()
    if ":" in h:
        return h[:5]
    if h.endswith("h"):
        return h[:-1] + ":00"
    return h


def _precompute_global(tirages):
    nls  = [t["numeros"] for t in tirages]
    lc   = [sum(1 for x in nl if x <= 12) for nl in nls]
    pc   = [sum(1 for x in nl if x % 2 == 0) for nl in nls]
    sd   = [statistics.stdev(nl) for nl in nls if len(nl) > 1]
    freq = {i: 0 for i in range(1, 26)}
    for nl in nls:
        for x in nl:
            if 1 <= x <= 25:
                freq[x] += 1
    fv = list(freq.values())
    return {
        "low_mean":  statistics.mean(lc),
        "low_std":   max(statistics.stdev(lc), 0.01),
        "pair_mean": statistics.mean(pc),
        "pair_std":  max(statistics.stdev(pc), 0.01),
        "std_mean":  statistics.mean(sd) if sd else 6.5,
        "std_std":   max(statistics.stdev(sd), 0.01) if len(sd) > 1 else 1.0,
        "freq":      freq,
        "freq_mean": statistics.mean(fv),
        "freq_std":  max(statistics.stdev(fv), 0.01),
    }


def _score_stat(nums, sg):
    def zp(v, m, s):
        return max(0.0, 25.0 * (1.0 - abs(v - m) / s * 0.8))
    lw  = sum(1 for x in nums if x <= 12)
    pr  = sum(1 for x in nums if x % 2 == 0)
    sd  = statistics.stdev(nums) if len(nums) > 1 else 0.0
    fz  = sum(abs(sg["freq"].get(x, 0) - sg["freq_mean"]) for x in nums) / (10.0 * sg["freq_std"])
    raw = (
        zp(lw, sg["low_mean"], sg["low_std"]) +
        zp(pr, sg["pair_mean"], sg["pair_std"]) +
        zp(sd, sg["std_mean"], max(sg["std_mean"] * 0.3, 1.0)) +
        max(0.0, 25.0 * (1.0 - fz * 0.8))
    )
    return min(100, max(0, int(raw)))


def _freq_tempo(tirages, lam=LAMBDA_DECAY):
    srt  = sorted(tirages, key=lambda x: _parse_date(x["date"]), reverse=True)
    freq, tw = Counter(), 0.0
    for i, t in enumerate(srt):
        w = math.exp(-lam * i)
        for n in t["numeros"]:
            freq[n] += w
        tw += w
    tot = tw * 10
    return {n: freq.get(n, 0) / max(tot, 1e-9) for n in range(1, 26)}


def _build_cooc(tirages):
    cooc = {i: Counter() for i in range(1, 26)}
    for t in tirages:
        for a in t["numeros"]:
            for b in t["numeros"]:
                if a != b:
                    cooc[a][b] += 1
    return cooc


def _gen_pondere(poids, rng):
    pop, w = list(range(1, 26)), [poids[n] for n in range(1, 26)]
    res = []
    for _ in range(10):
        tot = sum(w)
        r   = rng.random() * tot
        c   = 0.0
        for i, wi in enumerate(w):
            c += wi
            if c >= r or i == len(w) - 1:
                res.append(pop[i])
                pop.pop(i)
                w.pop(i)
                break
    return sorted(res)


def _gen_greedy(poids, cooc, rng, temp):
    remaining, choisis = list(range(1, 26)), []
    while len(choisis) < 10:
        scores = []
        for n in remaining:
            p  = poids.get(n, 1 / 25)
            cn = 0.0
            if choisis:
                mx = max(list(cooc[n].values()) or [1])
                cn = sum(cooc[n].get(ch, 0) for ch in choisis) / (mx * len(choisis)) if mx > 0 else 0.0
            scores.append((1 - temp) * p + temp * cn)
        ts  = sum(scores)
        r   = rng.random() * ts if ts > 0 else 0
        c   = 0.0
        idx = len(remaining) - 1
        for i, s in enumerate(scores):
            c += s
            if c >= r:
                idx = i
                break
        choisis.append(remaining[idx])
        remaining.pop(idx)
    return sorted(choisis)


def _composite(nums, poids, hot, analyse, sg):
    fs   = min(sum(poids.get(n, 1 / 25) for n in nums) * 25.0, 2.0) / 2.0
    ss   = _score_stat(nums, sg)
    lw   = sum(1 for x in nums if x <= 12)
    pr   = sum(1 for x in nums if x % 2 == 0)
    sd   = statistics.stdev(nums) if len(nums) > 1 else 0.0
    d_lw = abs(lw - analyse["low_mean"]) / max(analyse["low_std"], 0.5)
    d_pr = abs(pr - analyse["pair_mean"]) / max(analyse["pair_std"], 0.5)
    d_sd = abs(sd - analyse["std_mean"]) / max(analyse["std_mean"] * 0.3, 1.0)
    eq   = max(0.0, 1.0 - (d_lw + d_pr + d_sd) / 3.0)
    hs   = sum(1 for n in nums if n in hot) / 10.0
    return 0.40 * fs + 0.30 * (ss / 100.0) + 0.15 * eq + 0.15 * hs


def _build_variations(best_grid, poids, rng, n=4):
    """
    Construit n variantes de best_grid :
      - Fixe aleatoirement 6-8 numeros de la grille source
      - Tire les restants de facon ponderee parmi les 1-25 non fixes
    """
    variations = []
    seen       = {tuple(best_grid)}
    attempts   = 0

    while len(variations) < n and attempts < n * 300:
        attempts += 1
        n_fix  = rng.randint(6, 8)
        fixed  = sorted(rng.sample(best_grid, n_fix))
        pool   = [num for num in range(1, 26) if num not in fixed]
        w      = [poids.get(num, 1 / 25) for num in pool]
        n_need = 10 - n_fix

        chosen, pool_c, w_c, ok = [], list(pool), list(w), True
        for _ in range(n_need):
            tot = sum(w_c)
            if tot <= 0:
                ok = False
                break
            r = rng.random() * tot
            c = 0.0
            for i, wi in enumerate(w_c):
                c += wi
                if c >= r or i == len(w_c) - 1:
                    chosen.append(pool_c[i])
                    pool_c.pop(i)
                    w_c.pop(i)
                    break

        if ok and len(chosen) == n_need:
            candidate = sorted(fixed + chosen)
            key = tuple(candidate)
            if key not in seen:
                seen.add(key)
                variations.append((n_fix, fixed, candidate))

    return variations


# ── API publique ───────────────────────────────────────────────────────────────

def predict_crescendo(tirages: list) -> dict:
    """
    Predit 5 grilles pour chaque creneau horaire du prochain samedi.

    Args:
        tirages: liste de tirages historiques Crescendo
                 (chaque dict: {"date": "DD/MM/YYYY", "heure": ..., "numeros": [...]})

    Returns:
        dict { heure: [ (label, nums, stat_score), ... ] }
        - label  : "BEST" ou "VAR f=N" (N = nb numeros fixes)
        - nums   : liste triee de 10 entiers 1-25
        - stat_score : int 0-100 (vraisemblance historique)
        5 entrees par heure, dans l'ordre BEST en premier.
    """
    # Normaliser les heures du dataset
    normalized = []
    for t in tirages:
        tc = dict(t)
        tc["heure"] = _norm_heure(tc.get("heure", ""))
        normalized.append(tc)

    sg           = _precompute_global(normalized)
    freq_g_tempo = _freq_tempo(normalized)
    rng          = random.SystemRandom()
    result       = {}

    for heure in HEURES:
        tirages_h = [t for t in normalized if t["heure"] == heure]
        n_h       = len(tirages_h)

        # Poids bayesiens : frequence horaire (avec decroissance) + prior global
        freq_h_t = _freq_tempo(tirages_h)
        poids    = {}
        for n in range(1, 26):
            poids[n] = (
                freq_h_t.get(n, 0) * n_h +
                freq_g_tempo.get(n, 1 / 25) * BETA_PRIOR
            ) / (n_h + BETA_PRIOR)
        tot   = sum(poids.values())
        poids = {k: v / tot for k, v in poids.items()}

        cooc_h = _build_cooc(tirages_h)

        # Hot numbers (5 derniers tirages de cette heure)
        hot = set()
        for t in sorted(tirages_h, key=lambda x: _parse_date(x["date"]))[-5:]:
            hot.update(t["numeros"])

        # Distribution horaire pour le scoring d'equilibre
        if n_h > 1:
            lc2 = [sum(1 for x in t["numeros"] if x <= 12) for t in tirages_h]
            pc2 = [sum(1 for x in t["numeros"] if x % 2 == 0) for t in tirages_h]
            sd2 = [statistics.stdev(t["numeros"]) for t in tirages_h if len(t["numeros"]) > 1]
            analyse = {
                "low_mean":  statistics.mean(lc2),
                "low_std":   max(statistics.stdev(lc2), 0.5),
                "pair_mean": statistics.mean(pc2),
                "pair_std":  max(statistics.stdev(pc2), 0.5),
                "std_mean":  statistics.mean(sd2) if sd2 else 6.5,
            }
        else:
            analyse = {
                "low_mean": 5.0, "low_std": 1.5,
                "pair_mean": 5.0, "pair_std": 1.5,
                "std_mean": 6.5,
            }

        def scorer(nums):
            return _composite(nums, poids, hot, analyse, sg)

        # Generation des candidats
        candidats = []
        for _ in range(N_RANDOM):
            nums = _gen_pondere(dict(poids), rng)
            candidats.append((scorer(nums), nums))
        for _ in range(N_GREEDY):
            nums = _gen_greedy(poids, cooc_h, rng, rng.uniform(0.15, 0.7))
            candidats.append((scorer(nums), nums))

        # Meilleure grille
        best_score, best_nums = max(candidats, key=lambda x: x[0])

        # 4 variantes
        variations = _build_variations(best_nums, poids, rng, n=4)

        # Construire la liste finale : BEST + 4 VAR
        grilles = [("BEST", best_nums, _score_stat(best_nums, sg))]
        for n_fix, _fixed, var_nums in variations:
            grilles.append((f"VAR f={n_fix}", var_nums, _score_stat(var_nums, sg)))

        result[heure] = grilles

    return result
