# 🎰 FDJ RNG — Cryptographic Lottery Generator

A cryptographically secure combination generator for four **FDJ** (French National Lottery) games:
**EuroMillions**, **EuroDreams**, **Loto**, and **Crescendo**.

Zero PRNG — powered by `os.urandom` (CryptGenRandom on Windows, `/dev/urandom` on Linux/Android)
with Fisher-Yates partial shuffle and rejection sampling for a perfectly uniform distribution.

---

## ✨ Features

- **True randomness** — `secrets.randbelow()` calls `os.urandom` directly, no seed, no internal state
- **History cross-check** — generated grids are checked against all past official FDJ draws
- **Crescendo special mode** — generates 10 grids per run: 5 pure random + 5 pattern-biased
- **Web UI** — Streamlit interface, works in any mobile browser
- **CLI** — full-featured terminal interface with rich formatting

---

## 📦 Installation

```bash
git clone https://github.com/YOUR_USERNAME/fdj-rng.git
cd fdj-rng
pip install -r requirements.txt
```

Optional (CLI rich display):
```bash
pip install rich colorama
```

---

## 🚀 Usage

### Web interface (mobile-friendly)
[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://lucky-random-generator.streamlit.app/)

```bash
python -m streamlit run streamlit_app.py
# Then open http://localhost:8501
```

### CLI — Generate combinations
```bash
python src/main.py --jeu euromillions     # 5 numbers (1-50) + 2 stars (1-12)
python src/main.py --jeu loto             # 5 numbers (1-49) + 1 chance (1-10)
python src/main.py --jeu crescendo        # 10 grids: 5 random + 5 pattern-biased
```

### CLI — Multiple combinations
```bash
python src/main.py --jeu euromillions --nb 5
```

### CLI — Display draw history
```bash
python src/main.py --jeu crescendo --historique
python src/main.py --jeu euromillions --historique
```

### Collision simulation
```bash
python sim_crescendo.py            # 100 000 draws (default)
python sim_crescendo.py 1000000    # custom count
```

---

## 🔐 RNG Security

| Source | Bits | Detail |
|--------|------|--------|
| `secrets.randbelow()` | ∞ | Calls `os.urandom` with rejection sampling |
| **Algorithm** | — | Fisher-Yates partial shuffle |
| **State** | **none** | Zero PRNG, zero seed, non-deterministic |

Each draw independently consumes fresh entropy from the OS.
Probability of each combination is exactly $\frac{1}{\binom{N}{k}}$.

---

## 🎵 Crescendo Mode

Crescendo generates **10 grids per session**:

| Grid | Mode | Description |
|------|------|-------------|
| 1–5 | 🎲 Random | Pure `os.urandom`, fully independent |
| 6–10 | 🔄 Pattern | 3–5 numbers reused from grids 1–5, rest random |

All grids are cross-checked against the official FDJ draw history.
A ⚠️ indicator flags any grid that matches a past official draw.
The letter drawn by FDJ is automatic (not chosen) and is not generated.

---

## 📁 Project Structure

```
fdj-rng/
├── streamlit_app.py     → Web UI (Streamlit)
├── sim_crescendo.py     → Collision simulation script
├── requirements.txt
├── src/
│   ├── main.py          → CLI entry point (argparse)
│   ├── generateur.py    → Cryptographic RNG core
│   ├── historique.py    → CSV/JSON history loader
│   ├── affichage.py     → Terminal display (rich)
│   └── filtres.py       → (unused) Statistical filters
└── etc/
    ├── euro_m/          → EuroMillions draw history (CSV)
    ├── loto/            → Loto draw history (CSV)
    ├── grand_loto/      → Grand Loto draw history (CSV)
    ├── super_loto/      → Super Loto draw history (CSV)
    └── crescendo/       → Crescendo draw history (CSV)
```

---

## 📊 Statistical Validation

Verified over 1 000 000 simulated draws:
- **Chi² = 16.19** (critical threshold: 36.42) → uniform distribution confirmed
- **Shannon entropy = 4.6437 bits** (theoretical max: 4.6439) → 100.00% efficiency
- **Collision rate = 0.0079%** — matches the theoretical $\frac{259}{3{,}268{,}760}$

---

## ⚠️ Disclaimer

This tool is a statistical utility. It does not predict lottery outcomes.
Every draw is pure chance — each combination has an identical probability.

Gambling carries risks. Please play responsibly.
Problem Gambling Helpline (France): **09 74 75 13 13**
