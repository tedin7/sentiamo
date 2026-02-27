"""
Sentiamo Sanremo 2026 — Analisi incrociata v3
Incrocia acustica + voce + testi in 8 classifiche composite + PCA esplorativa.

Metriche aggiornate:
- ebu_lra_lu (EBU R128 LRA) al posto di dynamic_range_db nelle classifiche
- chroma_entropy (Shannon) al posto di chroma_complexity
- beat_cv, beat_npvi (Patel & Daniele 2003)
- compression_ratio (zlib, Parada-Cabaleiro et al. 2024)
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

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

# All dimensions — updated with new metrics
energy = col("rms_mean")
dynrange = col("dynamic_range_db")
ebu_lra = col("ebu_lra_lu")
climax = col("climax_position")
quiet = col("quiet_ratio")
bpm = col("bpm")
beat_reg = col("beat_regularity")
beat_cv = col("beat_cv")
beat_npvi = col("beat_npvi")
onset = col("onset_density")
centroid = col("spectral_centroid")
contrast = col("spectral_contrast")
flatness = col("spectral_flatness")
hp = col("harmonic_percussive_ratio")
chroma_ent = col("chroma_entropy")
voc_range = col("vocal_range_semitones")
pitch_stab = col("pitch_stability_cents")
vibrato = col("vibrato_strength")
voiced = col("voiced_ratio")
voc_cent = col("vocal_centroid")
mattr = col("mattr")
hapax = col("hapax_ratio")
chorus_r = col("chorus_ratio")
compress = col("compression_ratio")
words = col("total_words")

def norm(arr):
    mn, mx = arr.min(), arr.max()
    if mx == mn:
        return np.zeros_like(arr)
    return (arr - mn) / (mx - mn)

# ── 8 CLASSIFICHE AD-HOC ─────────────────────────────────────────────
# DISCLAIMER: indici esplorativi non validati
rankings = {}

rankings["Complessità totale"] = {
    "sub": "Entropia cromatica + vocabolario + LRA + range vocale + beat CV",
    "scores": norm(chroma_ent) + norm(mattr) + norm(ebu_lra) + norm(voc_range) + norm(beat_cv),
}

rankings["Formula commerciale"] = {
    "sub": "Ritornello + energia + ripetitività + compressione dinamica",
    "scores": norm(chorus_r) + norm(energy) + (1 - norm(mattr)) + (1 - norm(ebu_lra)),
}

rankings["Autorialità"] = {
    "sub": "Vocabolario + hapax + compression ratio + entropia cromatica + LRA",
    "scores": norm(mattr) + norm(hapax) + norm(compress) + norm(chroma_ent) + norm(ebu_lra),
}

rankings["Controllo vocale"] = {
    "sub": "Range + stabilità + presenza vocale",
    "scores": norm(voc_range) + (1 - norm(pitch_stab)) + norm(voiced),
}

climax_score = 1 - np.abs(climax - 0.8)
rankings["Tensione narrativa"] = {
    "sub": "LRA + silenzio + climax al punto giusto + no ritornello",
    "scores": norm(ebu_lra) + norm(quiet) + norm(climax_score) + (1 - norm(chorus_r)),
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
mus_complex = norm(chroma_ent) + norm(ebu_lra) + norm(voc_range) + norm(beat_cv)
lyr_complex = norm(mattr) + norm(hapax) + (1 - norm(chorus_r))
gap = np.abs(norm(mus_complex) - norm(lyr_complex))
direction = np.where(norm(mus_complex) > norm(lyr_complex), 1, -1)
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

    if direction is not None:
        sorted_dir = direction[idx]
        for bar, d in zip(bars, sorted_dir):
            bar.set_color("#E27D60" if d > 0 else "#355C7D")

    ax.set_yticks(range(len(sorted_names)))
    ax.set_yticklabels(sorted_names, fontsize=10, fontfamily="monospace")
    ax.invert_yaxis()
    ax.set_xlabel("Score", fontsize=11)

    fig.suptitle(title, fontsize=18, fontweight="bold", y=0.98)
    ax.set_title(subtitle, fontsize=10, color="#666", pad=12)

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
    short_rank = {
        "Complessità totale": "Complessità",
        "Formula commerciale": "Commerciale",
        "Autorialità": "Autorialità",
        "Controllo vocale": "Voce",
        "Tensione narrativa": "Tensione",
        "Modernità produttiva": "Modernità",
        "Minimalismo": "Minimalismo",
    }

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
        "Energia": energy, "EBU LRA": ebu_lra, "Quiet": quiet,
        "BPM": bpm, "Beat CV": beat_cv, "nPVI": beat_npvi,
        "Onset": onset, "Centroid": centroid,
        "H/P": hp, "Chr.Entropy": chroma_ent, "Flatness": flatness,
        "Voc.Range": voc_range, "Pitch.Stab": pitch_stab,
        "Voiced": voiced, "MATTR": mattr, "Hapax": hapax,
        "Chorus": chorus_r, "Compress": compress, "Words": words,
    }
    dim_names = list(dims.keys())
    matrix = np.column_stack(list(dims.values()))
    corr = np.corrcoef(matrix.T)

    fig, ax = plt.subplots(figsize=(14, 12))
    im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(dim_names)))
    ax.set_yticks(range(len(dim_names)))
    ax.set_xticklabels(dim_names, rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(dim_names, fontsize=9)

    for i in range(len(dim_names)):
        for j in range(len(dim_names)):
            val = corr[i, j]
            if abs(val) > 0.4 and i != j:
                ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                        fontsize=7, fontweight="bold",
                        color="white" if abs(val) > 0.6 else "black")

    plt.colorbar(im, ax=ax, label="Correlazione", shrink=0.8)
    ax.set_title("Matrice di correlazione — 19 dimensioni",
                 fontsize=13, fontweight="bold", pad=15)
    plt.tight_layout()
    plt.savefig(OUT / "cross_correlations.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  cross_correlations.png")


# ── PCA ESPLORATIVA ──────────────────────────────────────────────────
def run_pca():
    """PCA su ~25 feature scalari. Scree plot, loading heatmap, ranking per PC."""
    # Raccolta feature scalari
    feature_labels = [
        "rms_mean", "ebu_lra_lu", "dynamic_range_db", "quiet_ratio", "climax_position",
        "bpm", "beat_cv", "beat_npvi", "onset_density",
        "spectral_centroid", "spectral_bandwidth", "spectral_contrast",
        "spectral_flatness", "harmonic_percussive_ratio", "chroma_entropy",
        "vocal_range_semitones", "pitch_stability_cents", "vibrato_strength",
        "voiced_ratio", "vocal_centroid",
        "mattr", "hapax_ratio", "chorus_ratio", "compression_ratio", "total_words",
    ]

    matrix = np.array([
        [float(data[n].get(f, 0)) for f in feature_labels]
        for n in names
    ])

    # StandardScaler
    scaler = StandardScaler()
    X = scaler.fit_transform(matrix)

    # Replace any NaN with 0 after scaling
    X = np.nan_to_num(X, nan=0.0)

    # PCA
    pca = PCA()
    scores = pca.fit_transform(X)
    explained = pca.explained_variance_ratio_
    cumulative = np.cumsum(explained)

    # Quante PC per >=80% varianza
    n_pc = int(np.searchsorted(cumulative, 0.80) + 1)
    n_pc = max(n_pc, 2)  # almeno 2
    print(f"\n  PCA: {n_pc} componenti spiegano {cumulative[n_pc-1]*100:.1f}% della varianza")

    # ── Scree plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    ax1.bar(range(1, len(explained)+1), explained * 100, color="#6C5B7B", alpha=0.8)
    ax1.set_xlabel("Componente")
    ax1.set_ylabel("Varianza spiegata (%)")
    ax1.set_title("Scree plot")
    ax1.axhline(y=100/len(feature_labels), color="red", linestyle="--", alpha=0.5, label="Media attesa")
    ax1.legend()

    ax2.plot(range(1, len(cumulative)+1), cumulative * 100, "o-", color="#355C7D")
    ax2.axhline(y=80, color="red", linestyle="--", alpha=0.5, label="80%")
    ax2.axvline(x=n_pc, color="green", linestyle="--", alpha=0.5, label=f"n={n_pc}")
    ax2.set_xlabel("Numero componenti")
    ax2.set_ylabel("Varianza cumulativa (%)")
    ax2.set_title("Varianza cumulativa")
    ax2.legend()

    fig.suptitle("PCA — Scree plot", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "pca_scree.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  pca_scree.png")

    # ── Loading heatmap
    loadings = pca.components_[:n_pc]  # [n_pc, n_features]

    # Shorter labels for heatmap
    short_labels = [
        "RMS", "LRA", "DynRange", "Quiet", "Climax",
        "BPM", "BeatCV", "nPVI", "Onset",
        "Centroid", "Bandwidth", "Contrast",
        "Flatness", "H/P", "Chr.Ent",
        "VocRange", "PitchStab", "Vibrato",
        "Voiced", "VocCent",
        "MATTR", "Hapax", "Chorus", "Compress", "Words",
    ]

    fig, ax = plt.subplots(figsize=(16, max(4, n_pc * 1.5)))
    im = ax.imshow(loadings, cmap="RdBu_r", vmin=-0.5, vmax=0.5, aspect="auto")
    ax.set_xticks(range(len(short_labels)))
    ax.set_xticklabels(short_labels, rotation=60, ha="right", fontsize=8)

    # Auto-naming: top 3 loadings assoluti per ogni PC
    pc_names = []
    for i in range(n_pc):
        top_idx = np.argsort(np.abs(loadings[i]))[-3:][::-1]
        signs = [("+" if loadings[i][j] > 0 else "-") for j in top_idx]
        name_parts = [f"{signs[k]}{short_labels[top_idx[k]]}" for k in range(3)]
        pc_name = f"PC{i+1}: {', '.join(name_parts)}"
        pc_names.append(pc_name)

    ax.set_yticks(range(n_pc))
    ax.set_yticklabels(pc_names, fontsize=9)

    # Annotate values
    for i in range(n_pc):
        for j in range(len(short_labels)):
            val = loadings[i, j]
            if abs(val) > 0.2:
                ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                        fontsize=6, fontweight="bold",
                        color="white" if abs(val) > 0.35 else "black")

    plt.colorbar(im, ax=ax, label="Loading", shrink=0.8)
    ax.set_title("PCA Loadings — Feature × Componente", fontsize=13, fontweight="bold", pad=15)
    fig.tight_layout()
    fig.savefig(OUT / "pca_loadings.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  pca_loadings.png")

    # ── Bar chart ranking per ogni PC
    for i in range(n_pc):
        pc_scores = scores[:, i]
        idx = np.argsort(-pc_scores)
        sorted_names = [shorts[j] for j in idx]
        sorted_scores = pc_scores[idx]

        fig, ax = plt.subplots(figsize=(13, 11))
        colors = ["#6C5B7B" if s >= 0 else "#F67280" for s in sorted_scores]
        ax.barh(range(len(sorted_names)), sorted_scores, color=colors, alpha=0.85,
                edgecolor="white", linewidth=0.5, height=0.75)
        ax.set_yticks(range(len(sorted_names)))
        ax.set_yticklabels(sorted_names, fontsize=10, fontfamily="monospace")
        ax.invert_yaxis()
        ax.set_xlabel("Score PC", fontsize=11)
        ax.axvline(0, color="black", linewidth=0.5)

        fig.suptitle(pc_names[i], fontsize=16, fontweight="bold", y=0.98)
        ax.set_title(f"Varianza spiegata: {explained[i]*100:.1f}%", fontsize=10, color="#666", pad=12)

        for bar, val in zip(ax.patches, sorted_scores):
            x_pos = bar.get_width() + 0.05 if val >= 0 else bar.get_width() - 0.05
            ha = "left" if val >= 0 else "right"
            ax.text(x_pos, bar.get_y() + bar.get_height() / 2,
                    f"{val:.2f}", va="center", ha=ha, fontsize=8.5, color="#333")

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.subplots_adjust(top=0.92)
        fname = f"pca_pc{i+1}.png"
        plt.savefig(OUT / fname, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  {fname}")

    return n_pc, pc_names, explained, scores


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

print("\nPCA esplorativa...")
n_pc, pc_names, explained, pca_scores = run_pca()

# === ASCII REPORT ===
print("\nGenero report ASCII...")

report = []

# Disclaimer
report.append("\n" + "=" * 70)
report.append("  NOTA: le 8 classifiche ad-hoc sono indici esplorativi non validati.")
report.append("  Le componenti PCA sono data-driven e non richiedono pesi arbitrari.")
report.append("=" * 70)

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

# PCA rankings
report.append(f"\n{'=' * 70}")
report.append("  PCA — CLASSIFICHE DATA-DRIVEN")
report.append(f"{'=' * 70}")
for i in range(n_pc):
    idx = np.argsort(-pca_scores[:, i])
    report.append(f"\n  {pc_names[i]}  (varianza: {explained[i]*100:.1f}%)")
    report.append(f"  {'-' * 60}")
    for rank, j in enumerate(idx, 1):
        score = pca_scores[j, i]
        bar_len = max(0, int((score - pca_scores[:, i].min()) / (pca_scores[:, i].max() - pca_scores[:, i].min() + 1e-10) * 30))
        bar = "█" * bar_len + "░" * (30 - bar_len)
        report.append(f"  {rank:2d}. {bar}  {score:+.2f}  {shorts[j]}")

# Correlations
report.append(f"\n{'=' * 70}")
report.append("  CORRELAZIONI FORTI (|r| > 0.5)")
report.append(f"{'=' * 70}")
pairs = [
    ("Chorus ratio", chorus_r, "MATTR", mattr),
    ("Vocal centroid", voc_cent, "Spectral centroid", centroid),
    ("Word count", words, "MATTR", mattr),
    ("Onset density", onset, "Flatness", flatness),
    ("EBU LRA", ebu_lra, "Quiet ratio", quiet),
    ("Vocal range", voc_range, "Pitch stability", pitch_stab),
    ("Energy", energy, "MATTR", mattr),
    ("Compression", compress, "MATTR", mattr),
    ("Beat CV", beat_cv, "nPVI", beat_npvi),
    ("Chroma entropy", chroma_ent, "EBU LRA", ebu_lra),
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
    energy, ebu_lra, climax, quiet, bpm, beat_cv, beat_npvi, onset,
    centroid, contrast, flatness, hp, chroma_ent,
    voc_range, pitch_stab, vibrato, voiced, voc_cent,
    mattr, hapax, chorus_r, compress, words
])
z = np.abs(zscore(features_matrix, axis=0, nan_policy="omit"))
outlier_score = np.nanmean(z, axis=1)
idx = np.argsort(-outlier_score)
dim_names = ["energy", "ebu_lra", "climax", "quiet", "bpm", "beat_cv", "beat_npvi", "onset",
             "centroid", "contrast", "flatness", "hp", "chroma_ent",
             "voc_range", "pitch_stab", "vibrato", "voiced", "voc_cent",
             "mattr", "hapax", "chorus_r", "compress", "words"]
for rank, i in enumerate(idx[:10], 1):
    top_dims = np.argsort(-z[i])[:3]
    extremes = [dim_names[d] for d in top_dims]
    report.append(f"  {rank:2d}. {shorts[i]:28s}  score={outlier_score[i]:.3f}  estremi: {', '.join(extremes)}")

report_text = "\n".join(report)
(OUT / "cross_report.txt").write_text(report_text, encoding="utf-8")
print(f"\nReport salvato: {OUT / 'cross_report.txt'}")
print("Done.")
