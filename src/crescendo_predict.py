"""
crescendo_predict.py  v2
========================
Moteur de prediction Crescendo pour l'app Streamlit.

Strategie amelioree -- SELECT DIVERSE (5 grilles / heure) :
  1. Generer 4 types de candidats :
       - Bayesien     : poids freq horaire + prior (numeros chauds)
       - Exploratoire : poids aplatis (numeros tiedis)
       - Cold-biased  : poids inverses (numeros froids) -- NOUVEAU
       - Greedy cooc  : exploite les paires frequentes
  2. Scorer tous avec le composite (freq + stat + equilibre + hot)
  3. Selectionner 5 via SELECT DIVERSE :
       - Pool des 2000 meilleurs
       - Greedy : adj = 0.65 * score + 0.35 * coverage_bonus
       - Garantit couverture collective maximale de 1-25

vs v1 (1 BEST + 4 VAR) :
  - v1 : toutes les VAR fixent 6-8 num du BEST => blind spot systeme
  - v2 : selection diversifiee + cold candidates => large couverture
"""

import math, random, statistics
from collections import Counter
from datetime import datetime

HEURES       = ["13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00"]
N_RANDOM     = 8_000
N_EXPLORE    = 2_000
N_COLD       = 2_000
N_GREEDY     = 1_000
POOL_DIV     = 1_000
LAMBDA_DECAY = 0.05
BETA_PRIOR   = 25

GAINS_TABLE = {
    10: ("JACKPOT", "JACKPOT"),
    9:  (500, 1000),
    8:  (50, 100),
    7:  (7, 14),
    6:  (1, 2),
}


def calc_gain(n_match: int, has_lettre: bool = False):
    if n_match == 10:
        return "JACKPOT"
    entry = GAINS_TABLE.get(n_match)
    if entry:
        return entry[1] if has_lettre else entry[0]
    return 1 if has_lettre else 0


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


def _select_diverse(candidats, n=5, pool_size=POOL_DIV):
    """
    Selectionne n grilles maximisant la couverture collective de 1-25.
    Greedy : adj = 0.65 * score + 0.35 * coverage_bonus
    La 1ere grille est la meilleure par score (coverage_bonus identique au debut).
    """
    vu, pool = set(), []
    for sc, nums in sorted(candidats, key=lambda x: -x[0]):
        key = tuple(nums)
        if key not in vu:
            vu.add(key)
            pool.append((sc, list(nums)))
            if len(pool) == pool_size:
                break

    selected, sel_keys = [], set()
    coverage = {num: 0 for num in range(1, 26)}

    for _ in range(n):
        best_adj, best_grid = -1.0, None
        for sc, nums in pool:
            key = tuple(nums)
            if key in sel_keys:
                continue
            cov_bonus = sum(1.0 / (coverage[num] + 1) for num in nums) / 10.0
            adj = 0.65 * sc + 0.35 * cov_bonus
            if adj > best_adj:
                best_adj  = adj
                best_grid = (sc, list(nums))
        if best_grid:
            selected.append(best_grid)
            sel_keys.add(tuple(best_grid[1]))
            for num in best_grid[1]:
                coverage[num] += 1

    return selected, coverage


def predict_crescendo(tirages: list, n_grilles: int = 5) -> dict:
    """
    Predit n_grilles grilles pour chaque creneau horaire du prochain samedi.
    Utilise tous les tirages (pas de filtre par heure) — signal plus robuste.

    Returns:
        dict { heure: [ (label, nums, stat_score), ... ] }
        label = "BEST" (1ere, meilleur score) ou "DIV N" (diverse)
    """
    normalized = []
    for t in tirages:
        tc = dict(t)
        tc["heure"] = _norm_heure(tc.get("heure", ""))
        normalized.append(tc)

    sg    = _precompute_global(normalized)
    rng   = random.SystemRandom()
    result = {}

    # Calcul global (tous tirages) — fait une seule fois
    n_h      = len(normalized)
    freq_g   = _freq_tempo(normalized)
    poids    = {n: freq_g.get(n, 1 / 25) for n in range(1, 26)}
    tot      = sum(poids.values())
    poids    = {k: v / tot for k, v in poids.items()}

    explore  = {n: (poids[n] + 1 / 25) / 2 for n in range(1, 26)}
    tot_e    = sum(explore.values())
    explore  = {k: v / tot_e for k, v in explore.items()}

    cold     = {n: 1.0 / (poids[n] + 1e-6) for n in range(1, 26)}
    tot_c    = sum(cold.values())
    cold     = {k: v / tot_c for k, v in cold.items()}

    cooc_g   = _build_cooc(normalized)

    hot      = set()
    for t in sorted(normalized, key=lambda x: _parse_date(x["date"]))[-5:]:
        hot.update(t["numeros"])

    lc2 = [sum(1 for x in t["numeros"] if x <= 12) for t in normalized]
    pc2 = [sum(1 for x in t["numeros"] if x % 2 == 0) for t in normalized]
    sd2 = [statistics.stdev(t["numeros"]) for t in normalized if len(t["numeros"]) > 1]
    analyse = {
        "low_mean":  statistics.mean(lc2),
        "low_std":   max(statistics.stdev(lc2), 0.5),
        "pair_mean": statistics.mean(pc2),
        "pair_std":  max(statistics.stdev(pc2), 0.5),
        "std_mean":  statistics.mean(sd2) if sd2 else 6.5,
    }

    def scorer(nums):
        return _composite(nums, poids, hot, analyse, sg)

    for heure in HEURES:

        # Poids exploratoires (aplatis)
        candidats = []

        for _ in range(N_RANDOM):
            nums = _gen_pondere(dict(poids), rng)
            candidats.append((scorer(nums), nums))

        for _ in range(N_EXPLORE):
            nums = _gen_pondere(dict(explore), rng)
            candidats.append((scorer(nums), nums))

        for _ in range(N_COLD):
            nums = _gen_pondere(dict(cold), rng)
            candidats.append((scorer(nums), nums))

        for _ in range(N_GREEDY):
            nums = _gen_greedy(poids, cooc_g, rng, rng.uniform(0.15, 0.7))
            candidats.append((scorer(nums), nums))

        selected, _ = _select_diverse(candidats, n=n_grilles)

        grilles = []
        for i, (sc, nums) in enumerate(selected):
            label = "BEST" if i == 0 else f"DIV {i + 1}"
            grilles.append((label, nums, _score_stat(nums, sg)))

        result[heure] = grilles

    return result
