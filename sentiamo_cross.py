"""
Sentiamo Sanremo 2026 — Analisi incrociata
Incrocia acustica + voce + testi in 8 classifiche composite + grafici.
"""
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path("output")
base = json.load(open(OUT / "features.json"))
deep = json.load(open(OUT / "deep_features.json"))

# Merge
data = {}
for name in base:
    b = base[name]
    d = deep.get(name, {})
    v = d.get("vocals", {})
    l = d.get("lyrics", {})
    data[name] = {**b, **v, **l}

names = list(data.keys())

def short(n):
    return n.split(" - ")[0] if " - " in n else n[:25]

shorts = [short(n) for n in names]

def col(key, default=0):
    return np.array([float(data[n].get(key, default)) for n in names])

# All dimensions
energy = col("rms_mean")
dynrange = col("dynamic_range_db")
climax = col("climax_position")
quiet = col("quiet_ratio")
bpm = col("bpm")
beat_reg = col("beat_regularity")
onset = col("onset_density")
centroid = col("spectral_centroid")
contrast = col("spectral_contrast")
flatness = col("spectral_flatness")
hp = col("harmonic_percussive_ratio")
chroma = col("chroma_complexity")
voc_range = col("vocal_range_semitones")
pitch_stab = col("pitch_stability_cents")
vibrato = col("vibrato_strength")
voiced = col("voiced_ratio")
voc_cent = col("vocal_centroid")
mattr = col("mattr")  # Use MATTR instead of raw TTR
hapax = col("hapax_ratio")
chorus_r = col("chorus_ratio")
words = col("total_words")

def norm(arr):
    mn, mx = arr.min(), arr.max()
    if mx == mn:
        return np.zeros_like(arr)
    return (arr - mn) / (mx - mn)

# 8 rankings
rankings = {}

rankings["Complessità totale"] = {
    "sub": "Armonia + vocabolario + dinamica + range vocale + ritmo umano",
    "scores": norm(chroma) + norm(mattr) + norm(dynrange) + norm(voc_range) + norm(beat_reg),
}

rankings["Formula commerciale"] = {
    "sub": "Ritornello + energia + ripetitività + compressione",
    "scores": norm(chorus_r) + norm(energy) + (1 - norm(mattr)) + (1 - norm(dynrange)),
}

rankings["Autorialità"] = {
    "sub": "Vocabolario + hapax + no ritornello + armonia + dinamica",
    "scores": norm(mattr) + norm(hapax) + (1 - norm(chorus_r)) + norm(chroma) + norm(dynrange),
}

rankings["Controllo vocale"] = {
    "sub": "Range + stabilità + presenza vocale",
    "scores": norm(voc_range) + (1 - norm(pitch_stab)) + norm(voiced),
}

climax_score = 1 - np.abs(climax - 0.8)
rankings["Tensione narrativa"] = {
    "sub": "Dinamica + silenzio + climax al punto giusto + no ritornello",
    "scores": norm(dynrange) + norm(quiet) + norm(climax_score) + (1 - norm(chorus_r)),
}

rankings["Modernità produttiva"] = {
    "sub": "Suono granulare + percussivo + denso + veloce",
    "scores": norm(flatness) + (1 - norm(hp)) + norm(onset) + norm(bpm),
}

rankings["Minimalismo"] = {
    "sub": "Poche parole + pochi eventi + poca energia + suono definito",
    "scores": (1 - norm(words)) + (1 - norm(onset)) + (1 - norm(energy)) + norm(contrast),
}

# Incoerenze
mus_complex = norm(chroma) + norm(dynrange) + norm(voc_range) + norm(beat_reg)
lyr_complex = norm(mattr) + norm(hapax) + (1 - norm(chorus_r))
gap = np.abs(norm(mus_complex) - norm(lyr_complex))
direction = np.where(norm(mus_complex) > norm(lyr_complex), 1, -1)  # 1 = music > text
rankings["Incoerenza musica↔testo"] = {
    "sub": "Gap tra complessità musicale e testuale",
    "scores": gap,
    "direction": direction,
}

# Color palette
COLORS = {
    "Complessità totale": "#6C5B7B",
    "Formula commerciale": "#F67280",
    "Autorialità": "#355C7D",
    "Controllo vocale": "#C06C84",
    "Tensione narrativa": "#2C3E50",
    "Modernità produttiva": "#E8A87C",
    "Minimalismo": "#41B3A3",
    "Incoerenza musica↔testo": "#E27D60",
}


def plot_ranking(title, subtitle, scores, color, filename, direction=None):
    """Horizontal bar chart for a ranking."""
    idx = np.argsort(-scores)
    sorted_names = [shorts[i] for i in idx]
    sorted_scores = scores[idx]

    fig, ax = plt.subplots(figsize=(13, 11))
    bars = ax.barh(range(len(sorted_names)), sorted_scores, color=color, alpha=0.85,
                   edgecolor="white", linewidth=0.5, height=0.75)

    # If incoerenza, color differently based on direction
    if direction is not None:
        sorted_dir = direction[idx]
        for bar, d in zip(bars, sorted_dir):
            bar.set_color("#E27D60" if d > 0 else "#355C7D")

    ax.set_yticks(range(len(sorted_names)))
    ax.set_yticklabels(sorted_names, fontsize=10, fontfamily="monospace")
    ax.invert_yaxis()
    ax.set_xlabel("Score", fontsize=11)

    # Title and subtitle — separate clearly
    fig.suptitle(title, fontsize=18, fontweight="bold", y=0.98)
    ax.set_title(subtitle, fontsize=10, color="#666", pad=12)

    # Value labels
    for bar, val in zip(bars, sorted_scores):
        ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height() / 2,
                f"{val:.2f}", va="center", fontsize=8.5, color="#333")

    if direction is not None:
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor="#E27D60", label="Musica > Testo"),
            Patch(facecolor="#355C7D", label="Testo > Musica"),
        ]
        ax.legend(handles=legend_elements, loc="lower right", fontsize=10)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.subplots_adjust(top=0.92)
    plt.savefig(OUT / filename, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  {filename}")


def plot_overview():
    """Spider/radar overview of top artists across all dimensions."""
    rank_names = [k for k in rankings if k != "Incoerenza musica↔testo"]
    # Shorter labels for radar axes
    short_rank = {
        "Complessità totale": "Complessità",
        "Formula commerciale": "Commerciale",
        "Autorialità": "Autorialità",
        "Controllo vocale": "Voce",
        "Tensione narrativa": "Tensione",
        "Modernità produttiva": "Modernità",
        "Minimalismo": "Minimalismo",
    }

    # Find artists who appear most in top 10s
    from collections import Counter
    appearances = Counter()
    for rname in rank_names:
        scores = rankings[rname]["scores"]
        top10 = np.argsort(-scores)[:10]
        for i in top10:
            appearances[shorts[i]] += 1

    top_artists = [a for a, _ in appearances.most_common(6)]

    angles = np.linspace(0, 2 * np.pi, len(rank_names), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(12, 12), subplot_kw=dict(polar=True))
    palette = ["#6C5B7B", "#F67280", "#355C7D", "#C06C84", "#E8A87C", "#41B3A3"]

    for artist, color in zip(top_artists, palette):
        idx_a = shorts.index(artist)
        values = []
        for rname in rank_names:
            scores = rankings[rname]["scores"]
            rank = np.searchsorted(np.sort(scores), scores[idx_a]) / len(scores)
            values.append(rank)
        values += values[:1]
        ax.plot(angles, values, "o-", linewidth=2.5, label=artist, color=color, markersize=6)
        ax.fill(angles, values, alpha=0.08, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([short_rank.get(r, r) for r in rank_names], fontsize=12, fontweight="bold")
    ax.set_ylim(0, 1)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["25%", "50%", "75%", "100%"], fontsize=9, color="#888")
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1), fontsize=12,
              frameon=True, fancybox=True, shadow=True)
    fig.suptitle("Profilo multidimensionale — Top 6 artisti", fontsize=16, fontweight="bold", y=0.98)
    fig.subplots_adjust(top=0.90)
    plt.savefig(OUT / "cross_radar.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  cross_radar.png")


def plot_correlations():
    """Correlation heatmap of key dimensions."""
    dims = {
        "Energia": energy, "Dinamica": dynrange, "Quiet": quiet,
        "BPM": bpm, "Onset": onset, "Centroid": centroid,
        "H/P": hp, "Chroma": chroma, "Flatness": flatness,
        "Voc.Range": voc_range, "Pitch.Stab": pitch_stab,
        "Voiced": voiced, "MATTR": mattr, "Hapax": hapax,
        "Chorus": chorus_r, "Words": words,
    }
    dim_names = list(dims.keys())
    matrix = np.column_stack(list(dims.values()))
    corr = np.corrcoef(matrix.T)

    fig, ax = plt.subplots(figsize=(12, 10))
    im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(dim_names)))
    ax.set_yticks(range(len(dim_names)))
    ax.set_xticklabels(dim_names, rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(dim_names, fontsize=9)

    # Annotate strong correlations
    for i in range(len(dim_names)):
        for j in range(len(dim_names)):
            val = corr[i, j]
            if abs(val) > 0.4 and i != j:
                ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                        fontsize=7, fontweight="bold",
                        color="white" if abs(val) > 0.6 else "black")

    plt.colorbar(im, ax=ax, label="Correlazione", shrink=0.8)
    ax.set_title("Matrice di correlazione — 16 dimensioni",
                 fontsize=13, fontweight="bold", pad=15)
    plt.tight_layout()
    plt.savefig(OUT / "cross_correlations.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  cross_correlations.png")


# === GENERATE ===
print("Genero grafici incrociati...")

for title, info in rankings.items():
    fname = "cross_" + title.lower().replace(" ", "_").replace("↔", "_").replace("à", "a").replace("è", "e").replace("ì", "i") + ".png"
    plot_ranking(
        title, info["sub"], info["scores"],
        COLORS.get(title, "#666"),
        fname,
        direction=info.get("direction"),
    )

plot_overview()
plot_correlations()

# === ASCII REPORT ===
print("\nGenero report ASCII...")

report = []
for title, info in rankings.items():
    scores = info["scores"]
    idx = np.argsort(-scores)
    lines = [f"\n{'=' * 70}",
             f"  {title.upper()}",
             f"  {info['sub']}",
             f"{'=' * 70}"]
    for rank, i in enumerate(idx, 1):
        bar_len = int(scores[i] / scores.max() * 30) if scores.max() > 0 else 0
        bar = "█" * bar_len + "░" * (30 - bar_len)
        extra = ""
        if "direction" in info:
            extra = "  MUSICA>TESTO" if info["direction"][i] > 0 else "  TESTO>MUSICA"
        lines.append(f"  {rank:2d}. {bar}  {scores[i]:.2f}  {shorts[i]}{extra}")
    report.extend(lines)

# Correlations
report.append(f"\n{'=' * 70}")
report.append("  CORRELAZIONI FORTI (|r| > 0.5)")
report.append(f"{'=' * 70}")
pairs = [
    ("Chorus ratio", chorus_r, "MATTR", mattr),
    ("Vocal centroid", voc_cent, "Spectral centroid", centroid),
    ("Word count", words, "MATTR", mattr),
    ("Onset density", onset, "Flatness", flatness),
    ("Dynamic range", dynrange, "Quiet ratio", quiet),
    ("Vocal range", voc_range, "Pitch stability", pitch_stab),
    ("Energy", energy, "MATTR", mattr),
]
for n1, a1, n2, a2 in pairs:
    mask = (a1 > 0) & (a2 > 0)
    if mask.sum() > 5:
        r = np.corrcoef(a1[mask], a2[mask])[0, 1]
        if abs(r) > 0.3:
            report.append(f"  {n1:20s} x {n2:20s}  r={r:+.3f}")

# Outliers
report.append(f"\n{'=' * 70}")
report.append("  OUTLIER MULTIDIMENSIONALI")
report.append(f"{'=' * 70}")
from scipy.stats import zscore
features_matrix = np.column_stack([
    energy, dynrange, climax, quiet, bpm, beat_reg, onset,
    centroid, contrast, flatness, hp, chroma,
    voc_range, pitch_stab, vibrato, voiced, voc_cent,
    mattr, hapax, chorus_r, words
])
z = np.abs(zscore(features_matrix, axis=0, nan_policy="omit"))
outlier_score = np.nanmean(z, axis=1)
idx = np.argsort(-outlier_score)
dim_names = ["energy", "dynrange", "climax", "quiet", "bpm", "beat_reg", "onset",
             "centroid", "contrast", "flatness", "hp", "chroma",
             "voc_range", "pitch_stab", "vibrato", "voiced", "voc_cent",
             "mattr", "hapax", "chorus_r", "words"]
for rank, i in enumerate(idx[:10], 1):
    top_dims = np.argsort(-z[i])[:3]
    extremes = [dim_names[d] for d in top_dims]
    report.append(f"  {rank:2d}. {shorts[i]:28s}  score={outlier_score[i]:.3f}  estremi: {', '.join(extremes)}")

report_text = "\n".join(report)
(OUT / "cross_report.txt").write_text(report_text, encoding="utf-8")
print(f"\nReport salvato: {OUT / 'cross_report.txt'}")
print("Done.")
