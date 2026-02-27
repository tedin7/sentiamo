#!/usr/bin/env python3
"""
SENTIAMO SANREMO 2026
Analisi acustica di tutti i 30 brani in gara.

Claude non ha orecchie, ma ha numeri, spettri, curve.
Questo e' il suo modo di "sentire".
"""

import json
import os
import sys
from pathlib import Path

import librosa
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from sklearn.metrics import pairwise_distances
from sklearn.preprocessing import StandardScaler

# ── CONFIG ───────────────────────────────────────────────────────────
FLAC_DIR = Path(
    "/home/tomd/Documents/sentiamo/"
    "V.A. - I singoli di Sanremo 2026 (2026 Pop Hip Hop Rap) [Flac 24-44]"
)
OUT_DIR = Path("/home/tomd/Documents/sentiamo/output")
OUT_DIR.mkdir(exist_ok=True)

N_SEGMENTS = 20  # punti per la curva di energia
SR = 22050       # sample rate per analisi (librosa default)


# ── HELPERS ──────────────────────────────────────────────────────────
def clean_name(filename: str) -> str:
    """Da '01. SayF - Tu Mi Piaci Tanto.flac' a 'SayF - Tu Mi Piaci Tanto'."""
    name = Path(filename).stem
    # strip leading number + dot + space
    if name[:2].isdigit() and name[2] == ".":
        name = name[4:]
    return name.strip()


def ascii_bar(value: float, max_value: float, width: int = 30) -> str:
    """Barra ASCII proporzionale."""
    if max_value == 0:
        return " " * width
    filled = int(round(value / max_value * width))
    filled = max(0, min(width, filled))
    return "█" * filled + "░" * (width - filled)


def print_ranking(title: str, data: list[tuple[str, float]], unit: str = "",
                  reverse: bool = True, top_n: int = 30) -> str:
    """Stampa ranking formattato. Ritorna la stringa."""
    sorted_data = sorted(data, key=lambda x: x[1], reverse=reverse)[:top_n]
    max_val = max(abs(v) for _, v in sorted_data) if sorted_data else 1

    lines = [f"\n{'='*70}", f"  {title}", f"{'='*70}"]
    for i, (name, val) in enumerate(sorted_data, 1):
        bar = ascii_bar(abs(val), max_val)
        lines.append(f"  {i:2d}. {bar} {val:8.3f}{unit}  {name}")
    lines.append("")
    return "\n".join(lines)


# ── FEATURE EXTRACTION ───────────────────────────────────────────────
def extract_features(filepath: Path) -> dict:
    """Estrae tutte le feature acustiche da un file audio."""
    # Carica audio
    y, sr = librosa.load(filepath, sr=SR, mono=True)
    duration = len(y) / sr

    features = {"duration_s": round(duration, 1)}

    # ── 1. ENERGIA E DINAMICA ────────────────────────────────────────
    # RMS energy curve (N_SEGMENTS punti)
    frame_length = 2048
    hop_length = 512
    rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]

    # Segmenta in N_SEGMENTS blocchi
    seg_size = len(rms) // N_SEGMENTS
    energy_curve = []
    for i in range(N_SEGMENTS):
        start = i * seg_size
        end = start + seg_size if i < N_SEGMENTS - 1 else len(rms)
        energy_curve.append(float(np.mean(rms[start:end])))
    features["energy_curve"] = energy_curve

    # RMS media
    rms_mean = float(np.mean(rms))
    features["rms_mean"] = rms_mean

    # Dynamic range (rapporto picco/minimo in dB, escludendo silenzi) — legacy
    rms_nonzero = rms[rms > 0]
    if len(rms_nonzero) > 10:
        p95 = np.percentile(rms_nonzero, 95)
        p5 = np.percentile(rms_nonzero, 5)
        if p5 > 0:
            features["dynamic_range_db"] = round(float(20 * np.log10(p95 / p5)), 2)
        else:
            features["dynamic_range_db"] = 0.0
    else:
        features["dynamic_range_db"] = 0.0

    # EBU R128 Loudness Range (LRA) — EBU Tech 3342
    # Carica a sample rate nativo per K-weighting accurato
    try:
        audio_native, sr_native = sf.read(str(filepath))
        if audio_native.ndim > 1:
            audio_native = np.mean(audio_native, axis=1)
        meter = pyln.Meter(sr_native)
        features["ebu_lra_lu"] = round(float(meter.loudness_range(audio_native)), 2)
    except Exception:
        features["ebu_lra_lu"] = 0.0

    # Climax position (dove cade il picco di energia, 0.0-1.0)
    peak_idx = int(np.argmax(energy_curve))
    features["climax_position"] = round(peak_idx / (N_SEGMENTS - 1), 2)

    # Quiet ratio (% tempo sotto meta' del mediano)
    rms_median = np.median(rms_nonzero) if len(rms_nonzero) > 0 else 0
    if rms_median > 0:
        quiet_frames = np.sum(rms < rms_median * 0.5)
        features["quiet_ratio"] = round(float(quiet_frames / len(rms)), 3)
    else:
        features["quiet_ratio"] = 0.0

    # ── 2. RITMO ─────────────────────────────────────────────────────
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    # tempo can be array in newer librosa
    if hasattr(tempo, '__len__'):
        tempo = float(tempo[0]) if len(tempo) > 0 else 0.0
    features["bpm"] = round(float(tempo), 1)

    # Beat regularity (std degli intervalli tra beat) — legacy
    if len(beats) > 2:
        beat_times = librosa.frames_to_time(beats, sr=sr)
        intervals = np.diff(beat_times)
        features["beat_regularity"] = round(float(np.std(intervals)), 4)

        # Beat CV (Coefficient of Variation) — adimensionale, normalizzato
        mean_ioi = float(np.mean(intervals))
        if mean_ioi > 0:
            features["beat_cv"] = round(float(np.std(intervals) / mean_ioi), 4)
        else:
            features["beat_cv"] = 0.0

        # nPVI (normalized Pairwise Variability Index) — Patel & Daniele 2003
        if len(intervals) > 1:
            d = intervals
            npvi = 100 * np.mean(
                np.abs(d[:-1] - d[1:]) / ((d[:-1] + d[1:]) / 2)
            )
            features["beat_npvi"] = round(float(npvi), 2)
        else:
            features["beat_npvi"] = 0.0
    else:
        features["beat_regularity"] = 0.0
        features["beat_cv"] = 0.0
        features["beat_npvi"] = 0.0

    # Onset density (eventi per secondo)
    onsets = librosa.onset.onset_detect(y=y, sr=sr)
    onset_times = librosa.frames_to_time(onsets, sr=sr)
    features["onset_density"] = round(float(len(onset_times) / duration), 2)

    # ── 3. TIMBRO ────────────────────────────────────────────────────
    # Spectral centroid
    cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    features["spectral_centroid"] = round(float(np.mean(cent)), 1)

    # Spectral bandwidth
    bw = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
    features["spectral_bandwidth"] = round(float(np.mean(bw)), 1)

    # Spectral contrast (media delle 7 bande)
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    features["spectral_contrast"] = round(float(np.mean(contrast)), 2)

    # Spectral flatness
    flatness = librosa.feature.spectral_flatness(y=y)[0]
    features["spectral_flatness"] = round(float(np.mean(flatness)), 5)

    # Harmonic/Percussive ratio
    y_harm, y_perc = librosa.effects.hpss(y)
    harm_energy = float(np.sum(y_harm**2))
    perc_energy = float(np.sum(y_perc**2))
    if perc_energy > 0:
        features["harmonic_percussive_ratio"] = round(harm_energy / perc_energy, 2)
    else:
        features["harmonic_percussive_ratio"] = float("inf")

    # ── 4. COMPLESSITA' ARMONICA ─────────────────────────────────────
    # Shannon entropy cromatica — Weiss & Mueller 2015, ICASSP
    # max = log2(12) = 3.585 (distribuzione uniforme su 12 classi)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    chroma_mean = np.mean(chroma, axis=1)  # 12 valori
    chroma_sum = np.sum(chroma_mean)
    if chroma_sum > 0:
        p = chroma_mean / chroma_sum
        p = p[p > 0]  # evita log(0)
        features["chroma_entropy"] = round(float(-np.sum(p * np.log2(p))), 4)
    else:
        features["chroma_entropy"] = 0.0

    # MFCC signature (primi 13 coefficienti, media)
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    features["mfcc_signature"] = [round(float(m), 3) for m in np.mean(mfccs, axis=1)]

    # ── 5. STRUTTURA ─────────────────────────────────────────────────
    # Segmentazione basata su novelty function
    # Usa spectral flux + RMS per trovare cambi di sezione
    S = np.abs(librosa.stft(y))
    # Novelty function from spectral features
    chroma_cq = librosa.feature.chroma_cqt(y=y, sr=sr)
    # Self-similarity via recurrence matrix
    try:
        bound_frames = librosa.segment.agglomerative(chroma_cq, k=6)
        bound_times = librosa.frames_to_time(bound_frames, sr=sr)
        features["section_boundaries_s"] = [round(float(t), 1) for t in bound_times]
        features["n_sections"] = len(bound_times) + 1
    except Exception:
        features["section_boundaries_s"] = []
        features["n_sections"] = 1

    return features


# ── SIMILARITY MATRIX ────────────────────────────────────────────────
def compute_similarity(all_features: dict) -> tuple[np.ndarray, list[str]]:
    """Matrice di distanza timbrica basata su MFCC."""
    names = list(all_features.keys())
    mfcc_matrix = np.array([all_features[n]["mfcc_signature"] for n in names])

    scaler = StandardScaler()
    mfcc_scaled = scaler.fit_transform(mfcc_matrix)
    dist_matrix = pairwise_distances(mfcc_scaled, metric="cosine")

    return dist_matrix, names


# ── CHARTS ───────────────────────────────────────────────────────────
def plot_energy_curves(all_features: dict):
    """Energy curves sovrapposte per tutti i brani."""
    fig, ax = plt.subplots(figsize=(14, 8))
    for name, feats in all_features.items():
        short = name.split(" - ")[0] if " - " in name else name[:15]
        ax.plot(range(N_SEGMENTS), feats["energy_curve"], alpha=0.5, label=short, linewidth=1)
    ax.set_xlabel("Segmento temporale")
    ax.set_ylabel("RMS Energy")
    ax.set_title("Curve di energia — Sanremo 2026")
    ax.legend(fontsize=5, ncol=3, loc="upper left")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "energy_curves.png", dpi=150)
    plt.close(fig)


def plot_similarity_heatmap(dist_matrix: np.ndarray, names: list[str]):
    """Heatmap della similarita' timbrica."""
    short_names = []
    for n in names:
        parts = n.split(" - ")
        short_names.append(parts[0][:18] if len(parts) > 1 else n[:18])

    fig, ax = plt.subplots(figsize=(16, 14))
    # Converti distanza in similarita'
    sim_matrix = 1 - dist_matrix
    im = ax.imshow(sim_matrix, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(short_names)))
    ax.set_yticks(range(len(short_names)))
    ax.set_xticklabels(short_names, rotation=90, fontsize=6)
    ax.set_yticklabels(short_names, fontsize=6)
    ax.set_title("Similarita' timbrica (MFCC) — Sanremo 2026")
    fig.colorbar(im, label="Similarita' (1 - cosine distance)")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "similarity_heatmap.png", dpi=150)
    plt.close(fig)


def plot_scatter_bpm_centroid(all_features: dict):
    """Scatter: BPM vs Spectral Centroid (velocita' vs luminosita')."""
    fig, ax = plt.subplots(figsize=(12, 8))
    for name, feats in all_features.items():
        short = name.split(" - ")[0] if " - " in name else name[:15]
        ax.scatter(feats["bpm"], feats["spectral_centroid"], s=60, alpha=0.7)
        ax.annotate(short, (feats["bpm"], feats["spectral_centroid"]),
                    fontsize=5, alpha=0.8, ha="center", va="bottom")
    ax.set_xlabel("BPM (velocita')")
    ax.set_ylabel("Spectral Centroid Hz (luminosita')")
    ax.set_title("Velocita' vs Luminosita' — Sanremo 2026")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "scatter_bpm_centroid.png", dpi=150)
    plt.close(fig)


def plot_scatter_dynamics_entropy(all_features: dict):
    """Scatter: EBU LRA vs Chroma Entropy."""
    fig, ax = plt.subplots(figsize=(12, 8))
    for name, feats in all_features.items():
        short = name.split(" - ")[0] if " - " in name else name[:15]
        ax.scatter(feats["ebu_lra_lu"], feats["chroma_entropy"], s=60, alpha=0.7)
        ax.annotate(short, (feats["ebu_lra_lu"], feats["chroma_entropy"]),
                    fontsize=5, alpha=0.8, ha="center", va="bottom")
    ax.set_xlabel("EBU R128 LRA (LU)")
    ax.set_ylabel("Chroma Entropy (bit)")
    ax.set_title("Dinamica (EBU LRA) vs Entropia Cromatica — Sanremo 2026")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "scatter_dynamics_entropy.png", dpi=150)
    plt.close(fig)


def plot_harmonic_vs_percussive(all_features: dict):
    """Bar chart: Harmonic/Percussive ratio."""
    names_short = []
    ratios = []
    for name, feats in all_features.items():
        short = name.split(" - ")[0] if " - " in name else name[:15]
        names_short.append(short)
        ratios.append(feats["harmonic_percussive_ratio"])

    # Ordina
    pairs = sorted(zip(names_short, ratios), key=lambda x: x[1], reverse=True)
    names_sorted, ratios_sorted = zip(*pairs)

    fig, ax = plt.subplots(figsize=(10, 12))
    colors = ["#2ecc71" if r > np.median(ratios) else "#e74c3c" for r in ratios_sorted]
    ax.barh(range(len(names_sorted)), ratios_sorted, color=colors, alpha=0.8)
    ax.set_yticks(range(len(names_sorted)))
    ax.set_yticklabels(names_sorted, fontsize=7)
    ax.set_xlabel("Harmonic / Percussive Ratio")
    ax.set_title("Melodico vs Ritmico — Sanremo 2026\n(verde = melodico, rosso = ritmico)")
    ax.invert_yaxis()
    ax.grid(True, alpha=0.3, axis="x")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "harmonic_percussive.png", dpi=150)
    plt.close(fig)


def plot_individual_profile(name: str, feats: dict, all_features: dict):
    """Profilo individuale con radar-ish multi-panel."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle(f"Profilo: {name}", fontsize=14, fontweight="bold")

    # 1. Energy curve
    ax = axes[0, 0]
    ax.plot(range(N_SEGMENTS), feats["energy_curve"], "b-", linewidth=2)
    ax.fill_between(range(N_SEGMENTS), feats["energy_curve"], alpha=0.3)
    ax.set_title("Curva di energia")
    ax.set_xlabel("Segmento")
    ax.set_ylabel("RMS")
    ax.grid(True, alpha=0.3)

    # 2. Percentili rispetto al festival
    ax = axes[0, 1]
    metrics = ["rms_mean", "ebu_lra_lu", "bpm", "spectral_centroid",
               "spectral_contrast", "onset_density", "chroma_entropy"]
    labels = ["Energia", "LRA (LU)", "BPM", "Luminosita'",
              "Contrasto", "Densita'", "Entropia"]
    percentiles = []
    for m in metrics:
        all_vals = sorted([f[m] for f in all_features.values()])
        rank = all_vals.index(feats[m]) if feats[m] in all_vals else 0
        percentiles.append(rank / max(len(all_vals) - 1, 1) * 100)

    colors = plt.cm.RdYlGn(np.array(percentiles) / 100)
    bars = ax.barh(range(len(labels)), percentiles, color=colors, alpha=0.8)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlim(0, 100)
    ax.set_title("Percentile nel festival")
    ax.axvline(50, color="gray", linestyle="--", alpha=0.5)
    ax.grid(True, alpha=0.3, axis="x")

    # 3. Spectral profile (MFCC)
    ax = axes[1, 0]
    mfccs = feats["mfcc_signature"]
    ax.bar(range(len(mfccs)), mfccs, color="#3498db", alpha=0.8)
    ax.set_title("MFCC Signature")
    ax.set_xlabel("Coefficiente")
    ax.grid(True, alpha=0.3)

    # 4. Key stats text
    ax = axes[1, 1]
    ax.axis("off")
    stats_text = (
        f"Durata: {feats['duration_s']:.0f}s\n"
        f"BPM: {feats['bpm']}\n"
        f"Energia media: {feats['rms_mean']:.4f}\n"
        f"EBU LRA: {feats['ebu_lra_lu']:.1f} LU\n"
        f"Dynamic range: {feats['dynamic_range_db']:.1f} dB\n"
        f"Climax al: {feats['climax_position']*100:.0f}% del brano\n"
        f"Quiet ratio: {feats['quiet_ratio']*100:.1f}%\n"
        f"Centroid: {feats['spectral_centroid']:.0f} Hz\n"
        f"H/P ratio: {feats['harmonic_percussive_ratio']:.1f}\n"
        f"Onset density: {feats['onset_density']:.1f}/s\n"
        f"Beat CV: {feats['beat_cv']:.4f} | nPVI: {feats['beat_npvi']:.1f}\n"
        f"Sezioni: {feats['n_sections']}\n"
        f"Entropia cromatica: {feats['chroma_entropy']:.4f} bit"
    )
    ax.text(0.1, 0.9, stats_text, transform=ax.transAxes, fontsize=10,
            verticalalignment="top", fontfamily="monospace",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))

    fig.tight_layout()
    safe_name = name.replace("/", "-").replace(" ", "_")[:50]
    fig.savefig(OUT_DIR / f"profile_{safe_name}.png", dpi=150)
    plt.close(fig)


# ── PROFILI CHIAVE ───────────────────────────────────────────────────
FOCUS_ARTISTS = [
    "Nayt", "Ditonellapiaga", "Ermal Meta", "SayF", "Fulminacci",
    "Brancale", "Fedez", "Levante"
]


def matches_focus(name: str) -> bool:
    name_lower = name.lower()
    return any(a.lower() in name_lower for a in FOCUS_ARTISTS)


# ── MAIN ─────────────────────────────────────────────────────────────
def main():
    # Trova tutti i FLAC
    flac_files = sorted(FLAC_DIR.glob("*.flac"))
    print(f"\nTrovati {len(flac_files)} file FLAC\n")

    if len(flac_files) == 0:
        print("ERRORE: nessun file FLAC trovato!")
        sys.exit(1)

    # Estrai features
    all_features = {}
    for i, fp in enumerate(flac_files, 1):
        name = clean_name(fp.name)
        print(f"[{i:2d}/{len(flac_files)}] Analizzo: {name}")
        try:
            feats = extract_features(fp)
            all_features[name] = feats
            print(f"         OK — {feats['duration_s']}s, {feats['bpm']} BPM")
        except Exception as e:
            print(f"         ERRORE: {e}")

    print(f"\nAnalizzati con successo: {len(all_features)}/{len(flac_files)}")

    # Verifica NaN
    nan_count = 0
    for name, feats in all_features.items():
        for key, val in feats.items():
            if isinstance(val, float) and np.isnan(val):
                print(f"  NaN trovato: {name} -> {key}")
                nan_count += 1
    if nan_count == 0:
        print("  Nessun NaN nei risultati.\n")

    # ── Salva JSON ───────────────────────────────────────────────────
    json_path = OUT_DIR / "features.json"
    with open(json_path, "w") as f:
        json.dump(all_features, f, indent=2, ensure_ascii=False)
    print(f"Features salvate in {json_path}\n")

    # ── RANKING ──────────────────────────────────────────────────────
    report_lines = []
    report_lines.append("\n" + "█" * 70)
    report_lines.append("  SENTIAMO SANREMO 2026 — ANALISI ACUSTICA")
    report_lines.append("  30 brani. Zero orecchie. Solo numeri.")
    report_lines.append("█" * 70)

    # Energia
    r = print_ranking(
        "ENERGIA MEDIA (RMS) — Chi spinge di piu'?",
        [(n, f["rms_mean"]) for n, f in all_features.items()])
    report_lines.append(r)

    # Dinamica
    r = print_ranking(
        "DYNAMIC RANGE (dB) — Chi respira di piu'?",
        [(n, f["dynamic_range_db"]) for n, f in all_features.items()],
        unit=" dB")
    report_lines.append(r)

    # Quiet ratio
    r = print_ranking(
        "QUIET RATIO — Chi osa il silenzio?",
        [(n, f["quiet_ratio"]) for n, f in all_features.items()])
    report_lines.append(r)

    # BPM
    r = print_ranking(
        "BPM — Chi corre di piu'?",
        [(n, f["bpm"]) for n, f in all_features.items()],
        unit=" bpm")
    report_lines.append(r)

    # Beat regularity (bassa = piu' regolare)
    r = print_ranking(
        "BEAT REGULARITY — Chi e' piu' umano? (alta varianza = respira)",
        [(n, f["beat_regularity"]) for n, f in all_features.items()])
    report_lines.append(r)

    # Onset density
    r = print_ranking(
        "ONSET DENSITY — Chi e' piu' affollato?",
        [(n, f["onset_density"]) for n, f in all_features.items()],
        unit="/s")
    report_lines.append(r)

    # Luminosita'
    r = print_ranking(
        "SPECTRAL CENTROID (Hz) — Chi brilla di piu'?",
        [(n, f["spectral_centroid"]) for n, f in all_features.items()],
        unit=" Hz")
    report_lines.append(r)

    # Bandwidth
    r = print_ranking(
        "SPECTRAL BANDWIDTH — Chi ha il suono piu' ricco?",
        [(n, f["spectral_bandwidth"]) for n, f in all_features.items()],
        unit=" Hz")
    report_lines.append(r)

    # Contrasto
    r = print_ranking(
        "SPECTRAL CONTRAST — Chi ha il suono piu' definito?",
        [(n, f["spectral_contrast"]) for n, f in all_features.items()])
    report_lines.append(r)

    # Flatness
    r = print_ranking(
        "SPECTRAL FLATNESS — Chi sperimenta di piu'? (alto = noise/texture)",
        [(n, f["spectral_flatness"]) for n, f in all_features.items()])
    report_lines.append(r)

    # H/P ratio
    r = print_ranking(
        "HARMONIC/PERCUSSIVE RATIO — Chi e' melodico vs ritmico?",
        [(n, f["harmonic_percussive_ratio"]) for n, f in all_features.items()])
    report_lines.append(r)

    # Chroma entropy
    r = print_ranking(
        "CHROMA ENTROPY (bit) — Chi ha l'armonia piu' ricca?",
        [(n, f["chroma_entropy"]) for n, f in all_features.items()],
        unit=" bit")
    report_lines.append(r)

    # EBU R128 LRA
    r = print_ranking(
        "EBU R128 LRA (LU) — Chi ha piu' dinamica?",
        [(n, f["ebu_lra_lu"]) for n, f in all_features.items()],
        unit=" LU")
    report_lines.append(r)

    # Beat CV
    r = print_ranking(
        "BEAT CV — Chi ha il ritmo piu' variabile? (alto = umano)",
        [(n, f["beat_cv"]) for n, f in all_features.items()])
    report_lines.append(r)

    # nPVI
    r = print_ranking(
        "nPVI — Variabilita' ritmica (Patel & Daniele 2003)",
        [(n, f["beat_npvi"]) for n, f in all_features.items()])
    report_lines.append(r)

    # Climax position
    r = print_ranking(
        "CLIMAX POSITION — Dove esplode il brano? (0=inizio, 1=fine)",
        [(n, f["climax_position"]) for n, f in all_features.items()])
    report_lines.append(r)

    # ── SIMILARITY ───────────────────────────────────────────────────
    dist_matrix, sim_names = compute_similarity(all_features)

    report_lines.append(f"\n{'='*70}")
    report_lines.append("  MAPPA DELLE SOMIGLIANZE TIMBRICHE (MFCC)")
    report_lines.append(f"{'='*70}")

    # Trova le coppie piu' simili
    pairs = []
    for i in range(len(sim_names)):
        for j in range(i + 1, len(sim_names)):
            pairs.append((sim_names[i], sim_names[j], dist_matrix[i, j]))
    pairs.sort(key=lambda x: x[2])

    report_lines.append("\n  Le 10 coppie PIU' SIMILI:")
    for n1, n2, d in pairs[:10]:
        short1 = n1.split(" - ")[0][:15]
        short2 = n2.split(" - ")[0][:15]
        sim = 1 - d
        report_lines.append(f"    {short1:>15} <-> {short2:<15}  sim={sim:.3f}")

    report_lines.append("\n  Le 10 coppie PIU' DIVERSE:")
    for n1, n2, d in pairs[-10:]:
        short1 = n1.split(" - ")[0][:15]
        short2 = n2.split(" - ")[0][:15]
        sim = 1 - d
        report_lines.append(f"    {short1:>15} <-> {short2:<15}  sim={sim:.3f}")

    # Outlier: chi ha la distanza media piu' alta?
    mean_dists = np.mean(dist_matrix, axis=1)
    outlier_idx = np.argmax(mean_dists)
    report_lines.append(f"\n  OUTLIER TIMBRICO: {sim_names[outlier_idx]}")
    report_lines.append(f"  (distanza media dal resto: {mean_dists[outlier_idx]:.3f})")

    # ── PROFILI TUTTI I BRANI ───────────────────────────────────────
    report_lines.append(f"\n{'='*70}")
    report_lines.append("  PROFILI DI TUTTI I BRANI")
    report_lines.append(f"{'='*70}")

    for name, feats in all_features.items():
        report_lines.append(f"\n  --- {name} ---")
        report_lines.append(f"  Durata: {feats['duration_s']}s | BPM: {feats['bpm']}")
        report_lines.append(f"  Energia: {feats['rms_mean']:.4f} | Dinamica: {feats['dynamic_range_db']:.1f} dB")
        report_lines.append(f"  Climax al {feats['climax_position']*100:.0f}% del brano")
        report_lines.append(f"  Centroid: {feats['spectral_centroid']:.0f} Hz | Bandwidth: {feats['spectral_bandwidth']:.0f} Hz")
        report_lines.append(f"  Contrasto: {feats['spectral_contrast']:.2f} | Flatness: {feats['spectral_flatness']:.5f}")
        report_lines.append(f"  H/P ratio: {feats['harmonic_percussive_ratio']:.1f} | Onset: {feats['onset_density']:.1f}/s")
        report_lines.append(f"  Beat CV: {feats['beat_cv']:.4f} | nPVI: {feats['beat_npvi']:.1f} | Quiet: {feats['quiet_ratio']*100:.1f}%")
        report_lines.append(f"  Entropia cromatica: {feats['chroma_entropy']:.4f} bit | EBU LRA: {feats['ebu_lra_lu']:.1f} LU")
        report_lines.append(f"  Sezioni: {feats['n_sections']}")

        # Plot individuale
        plot_individual_profile(name, feats, all_features)
        report_lines.append(f"  [Chart salvato in output/]")

    # ── CHARTS ───────────────────────────────────────────────────────
    print("Genero charts...")
    plot_energy_curves(all_features)
    print("  energy_curves.png")
    plot_similarity_heatmap(dist_matrix, sim_names)
    print("  similarity_heatmap.png")
    plot_scatter_bpm_centroid(all_features)
    print("  scatter_bpm_centroid.png")
    plot_scatter_dynamics_entropy(all_features)
    print("  scatter_dynamics_entropy.png")
    plot_harmonic_vs_percussive(all_features)
    print("  harmonic_percussive.png")

    # ── OUTPUT REPORT ────────────────────────────────────────────────
    full_report = "\n".join(report_lines)
    print(full_report)

    report_path = OUT_DIR / "report.txt"
    with open(report_path, "w") as f:
        f.write(full_report)
    print(f"\nReport salvato in {report_path}")
    print(f"Charts salvati in {OUT_DIR}/")
    print("\nDone.")


if __name__ == "__main__":
    main()
