"""
Statistical scoring of a Crescendo grid against historical draws.
Score: 0–100, composed of 5 criteria.
"""
import statistics


def _precompute(tirages: list[dict]) -> dict:
    """Precompute historical statistics once from the full draw list."""
    n = len(tirages)
    if n == 0:
        return None

    # Individual number frequencies across all draws
    freq = {i: 0 for i in range(1, 26)}
    for t in tirages:
        for num in t["numeros"]:
            if 1 <= num <= 25:
                freq[num] += 1

    # "Hot" pool: numbers that appeared in the last 20 draws
    hot_pool: set[int] = set()
    for t in tirages[:20]:
        hot_pool.update(t["numeros"])

    # Average count of low numbers (≤ 12) per draw
    avg_low = sum(
        sum(1 for num in t["numeros"] if num <= 12)
        for t in tirages
    ) / n

    # Average even count per draw
    avg_pair = sum(
        sum(1 for num in t["numeros"] if num % 2 == 0)
        for t in tirages
    ) / n

    # Average standard deviation per draw (spread of numbers)
    stds = [
        statistics.stdev(t["numeros"])
        for t in tirages
        if len(t["numeros"]) > 1
    ]
    avg_std = sum(stds) / len(stds) if stds else 6.0

    return {
        "freq":     freq,
        "max_freq": max(freq.values()) or 1,
        "hot_pool": hot_pool,
        "avg_low":  avg_low,
        "avg_pair": avg_pair,
        "avg_std":  avg_std,
        "n":        n,
    }


def scorer(numeros: list[int], tirages: list[dict]) -> dict:
    """
    Score a Crescendo grid (0–100) using 5 historical criteria.

    Returns:
        score   : int 0-100
        etoiles : int 1-5
        chauds  : int (hot numbers count out of 10)
        detail  : str (short explanation)
    """
    if not tirages:
        return {"score": 50, "etoiles": 3, "chauds": 0, "detail": "no history"}

    s = _precompute(tirages)

    # ── 1. Fréquence individuelle (30 pts) ───────────────────────────────────
    # Numbers that appear often historically → higher score
    freq_sum = sum(s["freq"].get(n, 0) for n in numeros)
    freq_score = int(30 * freq_sum / (10 * s["max_freq"]))

    # ── 2. Chauds / Froids (25 pts) ─────────────────────────────────────────
    # Numbers appearing in the last 20 draws score positively
    chauds = sum(1 for n in numeros if n in s["hot_pool"])
    # Historical expectation: ~7 hot numbers per random grid
    chaud_score = int(25 * min(chauds, 8) / 8)

    # ── 3. Répartition basse / haute (20 pts) ───────────────────────────────
    # Compare our low-number count (≤ 12) to the historical average
    our_low = sum(1 for n in numeros if n <= 12)
    diff_low = abs(our_low - s["avg_low"])
    repartition_score = max(0, int(20 * (1 - diff_low / 5)))

    # ── 4. Parité pair / impair (15 pts) ────────────────────────────────────
    our_pair = sum(1 for n in numeros if n % 2 == 0)
    diff_pair = abs(our_pair - s["avg_pair"])
    parite_score = max(0, int(15 * (1 - diff_pair / 4)))

    # ── 5. Écart-type / étalement (10 pts) ──────────────────────────────────
    our_std = statistics.stdev(numeros) if len(numeros) > 1 else 0.0
    diff_std = abs(our_std - s["avg_std"])
    std_score = max(0, int(10 * (1 - diff_std / 4)))

    total = min(100, max(0,
        freq_score + chaud_score + repartition_score + parite_score + std_score
    ))

    # Stars (1–5)
    if   total >= 80: etoiles = 5
    elif total >= 65: etoiles = 4
    elif total >= 50: etoiles = 3
    elif total >= 35: etoiles = 2
    else:             etoiles = 1

    # Short explanation
    parts = []
    if   chauds >= 8: parts.append(f"{chauds}/10 hot 🔥")
    elif chauds >= 6: parts.append(f"{chauds}/10 hot")
    else:             parts.append(f"{chauds}/10 cold ❄️")

    if diff_low <= 1:        parts.append("spread ok")
    elif our_low > s["avg_low"] + 1: parts.append("low-heavy")
    else:                    parts.append("high-heavy")

    if diff_pair <= 1:       parts.append("parity ok")
    elif our_pair > s["avg_pair"] + 1: parts.append("even-heavy")
    else:                    parts.append("odd-heavy")

    return {
        "score":   total,
        "etoiles": etoiles,
        "chauds":  chauds,
        "detail":  " · ".join(parts),
    }
