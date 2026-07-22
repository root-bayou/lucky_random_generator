"""
Statistical scoring of a Crescendo grid against historical draws.
Score: 0–100 — measures how "typical" the grid is relative to past FDJ draws.

Method: z-score distance on 4 distributional features.
  A score near 50 = statistically average draw.
  A score near 80+ = very close to historical norms on all criteria.
  A score near 20  = atypical distribution.
"""
import statistics


def _precompute(tirages: list) -> dict:
    """Precompute historical distribution stats from the full draw list."""
    n = len(tirages)
    if n < 2:
        return None

    nums_lists = [t["numeros"] for t in tirages]

    # --- aggregate per-draw features (observed distributions) ---
    low_counts  = [sum(1 for x in nums if x <= 12) for nums in nums_lists]
    pair_counts = [sum(1 for x in nums if x % 2 == 0) for nums in nums_lists]
    std_devs    = [statistics.stdev(nums) for nums in nums_lists if len(nums) > 1]

    # --- individual number frequencies (directly observed counts) ---
    freq = {i: 0 for i in range(1, 26)}
    for nums in nums_lists:
        for x in nums:
            if 1 <= x <= 25:
                freq[x] += 1
    freq_values = list(freq.values())
    freq_mean = statistics.mean(freq_values)
    freq_std  = statistics.stdev(freq_values)

    # Hot pool: numbers seen in the last 5 draws (for display info only)
    hot_pool = set()
    for t in tirages[:5]:
        hot_pool.update(t["numeros"])

    return {
        "low_mean":  statistics.mean(low_counts),
        "low_std":   statistics.stdev(low_counts),
        "pair_mean": statistics.mean(pair_counts),
        "pair_std":  statistics.stdev(pair_counts),
        "std_mean":  statistics.mean(std_devs) if std_devs else 6.5,
        "std_std":   statistics.stdev(std_devs) if len(std_devs) > 1 else 1.0,
        "freq":      freq,
        "freq_mean": freq_mean,
        "freq_std":  freq_std,
        "hot_pool":  hot_pool,
        "n":         n,
    }


def scorer(numeros: list, tirages: list) -> dict:
    """
    Score a Crescendo grid (0–100) by measuring z-score distance
    from historical distributional norms on 4 criteria (25 pts each):
      1. Répartition basse/haute  (≤12 vs ≥13)
      2. Parité pair/impair
      3. Étalement  (standard deviation)
      4. Somme totale

    Returns:
        score   : int 0-100
        etoiles : int 1-5
        chauds  : int (numbers seen in last 5 draws — display only)
        detail  : str
    """
    if not tirages or len(tirages) < 2:
        return {"score": 50, "etoiles": 3, "chauds": 0, "detail": "no history"}

    s = _precompute(tirages)
    if s is None:
        return {"score": 50, "etoiles": 3, "chauds": 0, "detail": "no history"}

    def z_to_pts(val, mean, std, max_pts=25):
        """Full pts at z=0, decays linearly to 0 at z=1.25."""
        z = abs(val - mean) / max(std, 0.01)
        return max(0.0, max_pts * (1.0 - z * 0.8))

    our_low  = sum(1 for n in numeros if n <= 12)
    our_pair = sum(1 for n in numeros if n % 2 == 0)
    our_std  = statistics.stdev(numeros) if len(numeros) > 1 else 0.0

    # Criterion 1 — Répartition basse/haute (observed from 259 draws)
    pts_low  = z_to_pts(our_low,  s["low_mean"],  s["low_std"])
    # Criterion 2 — Parité pair/impair (observed from 259 draws)
    pts_pair = z_to_pts(our_pair, s["pair_mean"], s["pair_std"])
    # Criterion 3 — Étalement / écart-type (observed from 259 draws)
    pts_std  = z_to_pts(our_std,  s["std_mean"],  s["std_std"])
    # Criterion 4 — Fréquence individuelle : average z-score of each number's
    #               observed count across the 259 draws
    avg_freq_z = sum(
        abs(s["freq"].get(n, 0) - s["freq_mean"]) for n in numeros
    ) / (10 * max(s["freq_std"], 0.01))
    pts_freq = max(0.0, 25.0 * (1.0 - avg_freq_z * 0.8))

    total = min(100, max(0, int(pts_low + pts_pair + pts_std + pts_freq)))

    # Stars
    if   total >= 80: etoiles = 5
    elif total >= 65: etoiles = 4
    elif total >= 50: etoiles = 3
    elif total >= 30: etoiles = 2
    else:             etoiles = 1

    # Hot numbers (display only — not used in score)
    chauds = sum(1 for n in numeros if n in s["hot_pool"])

    # Detail text
    parts = []
    if   chauds >= 8: parts.append(f"{chauds}/10 🔥")
    elif chauds >= 5: parts.append(f"{chauds}/10")
    else:             parts.append(f"{chauds}/10 ❄️")

    diff_low = our_low - s["low_mean"]
    if   abs(diff_low) <= 0.8: parts.append("répart. ✓")
    elif diff_low > 0:         parts.append("biais bas")
    else:                      parts.append("biais haut")

    diff_pair = our_pair - s["pair_mean"]
    if   abs(diff_pair) <= 0.8: parts.append("parité ✓")
    elif diff_pair > 0:         parts.append("pairs+")
    else:                       parts.append("impairs+")

    return {
        "score":   total,
        "etoiles": etoiles,
        "chauds":  chauds,
        "detail":  " · ".join(parts),
    }
