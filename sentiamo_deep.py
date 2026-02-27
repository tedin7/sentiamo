#!/usr/bin/env python3
"""
SENTIAMO SANREMO 2026 — ANALISI PROFONDA
Secondo passaggio: separazione vocale + analisi testi.

Parte dal features.json gia' generato, aggiunge:
1. Separazione vocale (Demucs) → analisi voce isolata
2. Analisi testi (da file .txt o scraping web)
3. Report esteso con incrocio dati
"""

import json
import os
import re
import sys
import warnings
from pathlib import Path

import librosa
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

warnings.filterwarnings("ignore")

# ── CONFIG ───────────────────────────────────────────────────────────
FLAC_DIR = Path(
    "/home/tomd/Documents/sentiamo/"
    "V.A. - I singoli di Sanremo 2026 (2026 Pop Hip Hop Rap) [Flac 24-44]"
)
OUT_DIR = Path("/home/tomd/Documents/sentiamo/output")
LYRICS_DIR = Path("/home/tomd/Documents/sentiamo/lyrics")
VOCALS_DIR = OUT_DIR / "vocals"
OUT_DIR.mkdir(exist_ok=True)
LYRICS_DIR.mkdir(exist_ok=True)
VOCALS_DIR.mkdir(exist_ok=True)

SR = 22050


def clean_name(filename: str) -> str:
    name = Path(filename).stem
    if name[:2].isdigit() and name[2] == ".":
        name = name[4:]
    return name.strip()


# ── LYRICS SCRAPING ──────────────────────────────────────────────────
def scrape_lyrics_testicanzoni(artist: str, title: str) -> str | None:
    """Prova testicanzoni.com — spesso ha testi Sanremo."""
    import requests
    from bs4 import BeautifulSoup

    def slugify(s):
        s = s.lower().strip()
        s = re.sub(r"[àáâã]", "a", s)
        s = re.sub(r"[èéêë]", "e", s)
        s = re.sub(r"[ìíîï]", "i", s)
        s = re.sub(r"[òóôõ]", "o", s)
        s = re.sub(r"[ùúûü]", "u", s)
        s = re.sub(r"[^a-z0-9\s]", "", s)
        s = re.sub(r"\s+", "-", s)
        return s.strip("-")

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
    }

    # Prova ricerca su testicanzoni.com
    search_url = f"https://www.google.com/search?q={requests.utils.quote(f'{artist} {title} testo site:testicanzoni.com OR site:angolotesti.it OR site:genius.com')}"
    # Fallback: prova URL diretto su genius
    slug_a = slugify(artist).replace("-", " ").title().replace(" ", "-")
    slug_t = slugify(title).replace("-", " ").title().replace(" ", "-")
    genius_url = f"https://genius.com/{slug_a}-{slug_t}-lyrics"

    try:
        resp = requests.get(genius_url, timeout=10, headers=headers)
        if resp.status_code == 200 and "lyrics" in resp.text.lower():
            soup = BeautifulSoup(resp.text, "html.parser")
            # Genius uses data-lyrics-container
            containers = soup.find_all(attrs={"data-lyrics-container": "true"})
            if containers:
                text = "\n".join(c.get_text(separator="\n") for c in containers)
                text = re.sub(r"\[.*?\]", "", text)  # remove [Verse 1] etc
                text = "\n".join(l.strip() for l in text.split("\n") if l.strip())
                if len(text) > 50:
                    return text
    except Exception:
        pass

    # Prova angolotesti con search
    try:
        search = f"https://www.angolotesti.it/cerca?q={requests.utils.quote(f'{artist} {title}')}"
        resp = requests.get(search, timeout=10, headers=headers, allow_redirects=True)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            # Se redirect diretto al testo
            content = soup.find("div", id="lyrics") or soup.find("div", class_="lyrics")
            if content:
                text = content.get_text(separator="\n").strip()
                if len(text) > 50:
                    return text
            # Cerca link nei risultati
            for a in soup.find_all("a", href=True):
                if "/testo-" in a["href"] or "/lyrics-" in a["href"]:
                    link = a["href"]
                    if not link.startswith("http"):
                        link = "https://www.angolotesti.it" + link
                    resp2 = requests.get(link, timeout=10, headers=headers)
                    if resp2.status_code == 200:
                        soup2 = BeautifulSoup(resp2.text, "html.parser")
                        content = soup2.find("div", id="lyrics") or soup2.find("div", class_="lyrics")
                        if content:
                            text = content.get_text(separator="\n").strip()
                            if len(text) > 50:
                                return text
                    break
    except Exception:
        pass

    return None


def fetch_lyrics(artist: str, title: str) -> str | None:
    """Prova piu' fonti per ottenere il testo."""
    # Prima prova file locale (nome originale e nome sanitizzato)
    raw_name = f"{artist} - {title}"
    safe = re.sub(r"[^\w\s-]", "", raw_name).strip()
    for candidate in [raw_name, safe]:
        local_path = LYRICS_DIR / f"{candidate}.txt"
        if local_path.exists():
            text = local_path.read_text(encoding="utf-8").strip()
            if len(text) > 50:
                return text

    # Prova scraping
    text = scrape_lyrics_testicanzoni(artist, title)
    if text and len(text) > 50:
        local_path.write_text(text, encoding="utf-8")
        return text

    return None


# ── LYRICS ANALYSIS ──────────────────────────────────────────────────
def analyze_lyrics(text: str) -> dict:
    """Analizza un testo: ricchezza lessicale, ripetitivita', struttura."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    words = re.findall(r"\b[a-zàèéìòù]+\b", text.lower())

    if not words:
        return {}

    total_words = len(words)
    unique_words = len(set(words))

    # Ricchezza lessicale (type-token ratio grezzo)
    ttr = unique_words / total_words if total_words > 0 else 0

    # MATTR (Moving Average TTR) — normalizzato per lunghezza testo
    window = min(50, total_words - 1) if total_words > 10 else total_words
    if window > 0 and total_words > window:
        mattr_vals = []
        for start in range(total_words - window + 1):
            chunk = words[start:start + window]
            mattr_vals.append(len(set(chunk)) / len(chunk))
        mattr = float(np.mean(mattr_vals))
    else:
        mattr = ttr

    # Hapax legomena (parole che appaiono una sola volta)
    from collections import Counter
    word_freq = Counter(words)
    hapax = sum(1 for w, c in word_freq.items() if c == 1)
    hapax_ratio = hapax / unique_words if unique_words > 0 else 0

    # Tasso di ripetizione (parole ripetute / totale)
    repetition_rate = 1 - ttr

    # Densita' (parole per riga)
    words_per_line = total_words / len(lines) if lines else 0

    # Lunghezza media parole
    avg_word_length = np.mean([len(w) for w in words])

    # Righe ripetute (ritornello detection)
    line_counts = Counter(lines)
    repeated_lines = sum(c for l, c in line_counts.items() if c > 1)
    chorus_ratio = repeated_lines / len(lines) if lines else 0

    # Compression ratio (zlib) — Parada-Cabaleiro et al. 2024
    # Basso = testo piu' ripetitivo/prevedibile
    import zlib
    text_bytes = text.encode("utf-8")
    if len(text_bytes) > 0:
        compression_ratio = len(zlib.compress(text_bytes)) / len(text_bytes)
    else:
        compression_ratio = 0.0

    # Top 10 parole piu' frequenti (escluse stop words italiane)
    stop_words = {
        "il", "lo", "la", "i", "gli", "le", "un", "una", "di", "a", "da",
        "in", "con", "su", "per", "tra", "fra", "e", "o", "ma", "che", "non",
        "mi", "ti", "si", "ci", "vi", "me", "te", "se", "ne", "lo", "ce",
        "sono", "sei", "ho", "hai", "ha", "è", "come", "più", "piu", "tutto",
        "questa", "questo", "del", "al", "dal", "nel", "sul", "dei", "ai",
        "no", "sì", "si", "io", "tu", "lui", "lei", "noi", "voi", "loro",
    }
    content_words = [w for w in words if w not in stop_words and len(w) > 2]
    top_words = Counter(content_words).most_common(10)

    return {
        "total_words": total_words,
        "unique_words": unique_words,
        "total_lines": len(lines),
        "ttr": round(ttr, 3),
        "mattr": round(mattr, 3),
        "hapax_ratio": round(hapax_ratio, 3),
        "repetition_rate": round(repetition_rate, 3),
        "words_per_line": round(words_per_line, 2),
        "avg_word_length": round(avg_word_length, 2),
        "chorus_ratio": round(chorus_ratio, 3),
        "compression_ratio": round(compression_ratio, 4),
        "top_words": top_words,
    }


# ── VOCAL SEPARATION (DEMUCS) ───────────────────────────────────────
_demucs_model = None

def get_demucs_model():
    global _demucs_model
    if _demucs_model is None:
        from demucs.pretrained import get_model
        _demucs_model = get_model("htdemucs")
        _demucs_model.eval()
    return _demucs_model


def separate_vocals_demucs(filepath: Path, out_path: Path) -> Path | None:
    """Separa la voce con Demucs. Ritorna path del file vocale."""
    vocal_path = out_path / "vocals.wav"
    if vocal_path.exists():
        return vocal_path

    try:
        import soundfile as sf
        import torch
        import torchaudio
        from demucs.apply import apply_model

        model = get_demucs_model()

        # Carica con soundfile (non torchaudio, che richiede torchcodec)
        audio_np, sr = sf.read(str(filepath), dtype="float32")
        # audio_np shape: [samples, channels] or [samples]
        if audio_np.ndim == 1:
            audio_np = np.stack([audio_np, audio_np], axis=1)
        # Converti in tensor [channels, samples]
        wav = torch.from_numpy(audio_np.T)

        # Resample se necessario
        if sr != model.samplerate:
            wav = torchaudio.functional.resample(wav, sr, model.samplerate)

        # Normalizza
        ref = wav.mean(0)
        wav = (wav - ref.mean()) / ref.std()
        wav = wav.unsqueeze(0)  # [1, channels, samples]

        with torch.no_grad():
            sources = apply_model(model, wav, device="cpu", progress=False)

        # htdemucs sources: drums, bass, other, vocals
        vocals = sources[0, 3]  # [channels, samples]
        vocals = vocals * ref.std() + ref.mean()

        out_path.mkdir(parents=True, exist_ok=True)
        # Salva con soundfile (torchaudio.save richiede torchcodec)
        import soundfile as sf_out
        vocals_np = vocals.numpy().T  # [samples, channels]
        sf_out.write(str(vocal_path), vocals_np, model.samplerate)

        return vocal_path

    except Exception as e:
        print(f"    Demucs error: {e}")
        return None


def analyze_vocals(vocal_path: Path) -> dict:
    """Analizza la traccia vocale isolata con CREPE pitch tracking (Kim et al. 2018)."""
    import torch
    import torchcrepe

    y, sr = librosa.load(vocal_path, sr=SR, mono=True)
    duration = len(y) / sr

    # CREPE pitch tracking — Kim et al. 2018
    # Usa 16kHz come richiesto da CREPE
    CREPE_SR = 16000
    y_16k = librosa.resample(y, orig_sr=SR, target_sr=CREPE_SR)
    audio_tensor = torch.from_numpy(y_16k).unsqueeze(0).float()

    hop_samples = int(CREPE_SR * 0.01)  # 10ms hop
    fmin = float(librosa.note_to_hz("C2"))
    fmax = float(librosa.note_to_hz("C6"))

    # CREPE predict
    pitch, periodicity = torchcrepe.predict(
        audio_tensor, CREPE_SR,
        hop_length=hop_samples,
        fmin=fmin, fmax=fmax,
        model="full",
        batch_size=512,
        device="cpu",
        return_periodicity=True,
    )

    pitch = pitch.squeeze(0).numpy()
    periodicity = periodicity.squeeze(0).numpy()

    # Silence suppression: -60 dB threshold
    # Compute frame-level RMS at same hop rate
    frame_len_16k = hop_samples * 4
    rms_frames = librosa.feature.rms(
        y=y_16k, frame_length=frame_len_16k, hop_length=hop_samples
    )[0]
    # Align lengths
    min_len = min(len(pitch), len(rms_frames))
    pitch = pitch[:min_len]
    periodicity = periodicity[:min_len]
    rms_frames = rms_frames[:min_len]

    rms_db = 20 * np.log10(rms_frames + 1e-10)
    silence_mask = rms_db < -60

    # Voiced mask: periodicity > 0.21 AND not silent
    voiced_mask = (periodicity > 0.21) & (~silence_mask)

    # Mean smoothing (window=5)
    if np.sum(voiced_mask) > 5:
        pitch_smooth = np.copy(pitch)
        for i in range(2, len(pitch_smooth) - 2):
            if voiced_mask[i]:
                neighbors = pitch_smooth[max(0, i-2):i+3]
                neighbor_mask = voiced_mask[max(0, i-2):i+3]
                if np.sum(neighbor_mask) > 0:
                    pitch_smooth[i] = np.mean(neighbors[neighbor_mask])
        f0_valid = pitch_smooth[voiced_mask]
    else:
        f0_valid = pitch[voiced_mask]

    results = {}

    if len(f0_valid) > 10:
        # Range vocale in semitoni
        f0_min = np.percentile(f0_valid, 5)
        f0_max = np.percentile(f0_valid, 95)
        semitone_range = 12 * np.log2(f0_max / f0_min) if f0_min > 0 else 0
        results["vocal_range_semitones"] = round(float(semitone_range), 1)
        results["vocal_range_hz"] = [round(float(f0_min), 1), round(float(f0_max), 1)]

        # Nota media
        f0_median = float(np.median(f0_valid))
        results["vocal_median_hz"] = round(f0_median, 1)

        # Stabilita' del pitch (std in cents dal pitch medio locale)
        cents_dev = []
        window = 10
        for i in range(window, len(f0_valid) - window):
            local_mean = np.mean(f0_valid[i-window:i+window])
            if local_mean > 0:
                cents = 1200 * np.log2(f0_valid[i] / local_mean)
                cents_dev.append(cents)
        if cents_dev:
            results["pitch_stability_cents"] = round(float(np.std(cents_dev)), 2)
        else:
            results["pitch_stability_cents"] = 0.0

        # Vibrato detection (autocorrelazione variazioni pitch, 4-8 Hz)
        if len(f0_valid) > 50:
            f0_diff = np.diff(f0_valid)
            if np.std(f0_diff) > 0:
                autocorr = np.correlate(f0_diff - np.mean(f0_diff),
                                        f0_diff - np.mean(f0_diff), mode="full")
                autocorr = autocorr[len(autocorr)//2:]
                autocorr = autocorr / (autocorr[0] + 1e-10)
                # Frame rate CREPE = CREPE_SR / hop_samples = 100 Hz
                frame_rate = CREPE_SR / hop_samples
                min_lag = int(frame_rate / 8)  # 8 Hz
                max_lag = int(frame_rate / 4)  # 4 Hz
                if max_lag < len(autocorr) and min_lag < max_lag:
                    vibrato_peak = float(np.max(autocorr[min_lag:max_lag]))
                    results["vibrato_strength"] = round(max(0, vibrato_peak), 3)
                else:
                    results["vibrato_strength"] = 0.0
            else:
                results["vibrato_strength"] = 0.0
        else:
            results["vibrato_strength"] = 0.0

    else:
        results["vocal_range_semitones"] = 0.0
        results["vocal_range_hz"] = [0.0, 0.0]
        results["vocal_median_hz"] = 0.0
        results["pitch_stability_cents"] = 0.0
        results["vibrato_strength"] = 0.0

    # Voiced ratio
    results["voiced_ratio"] = round(float(np.sum(voiced_mask) / len(voiced_mask)), 3) if len(voiced_mask) > 0 else 0.0

    # Energia vocale (RMS)
    rms = librosa.feature.rms(y=y)[0]
    results["vocal_rms"] = round(float(np.mean(rms)), 5)

    # Spectral centroid vocale (brillantezza della voce)
    cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    results["vocal_centroid"] = round(float(np.mean(cent)), 1)

    return results


# ── CHARTS ───────────────────────────────────────────────────────────
def plot_vocal_comparison(all_deep: dict):
    """Confronto vocale: range vs stabilita'."""
    names = []
    ranges = []
    stabilities = []

    for name, data in all_deep.items():
        v = data.get("vocals", {})
        if v and v.get("vocal_range_semitones", 0) > 0:
            short = name.split(" - ")[0] if " - " in name else name[:15]
            names.append(short)
            ranges.append(v["vocal_range_semitones"])
            stabilities.append(v["pitch_stability_cents"])

    if not names:
        return

    fig, ax = plt.subplots(figsize=(12, 8))
    scatter = ax.scatter(ranges, stabilities, s=80, alpha=0.7, c=ranges, cmap="RdYlGn")
    for i, name in enumerate(names):
        ax.annotate(name, (ranges[i], stabilities[i]),
                    fontsize=6, alpha=0.8, ha="center", va="bottom")
    ax.set_xlabel("Range vocale (semitoni)")
    ax.set_ylabel("Instabilita' pitch (cents std)")
    ax.set_title("Range vocale vs Stabilita' — Sanremo 2026\n(destra = piu' esteso, alto = meno stabile)")
    ax.grid(True, alpha=0.3)
    fig.colorbar(scatter, label="Range (semitoni)")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "vocal_range_stability.png", dpi=150)
    plt.close(fig)


def plot_lyrics_comparison(all_deep: dict):
    """Confronto testi: ricchezza vs ripetitivita'."""
    names = []
    ttrs = []
    chorus_ratios = []

    for name, data in all_deep.items():
        l = data.get("lyrics", {})
        if l and l.get("ttr", 0) > 0:
            short = name.split(" - ")[0] if " - " in name else name[:15]
            names.append(short)
            ttrs.append(l["ttr"])
            chorus_ratios.append(l["chorus_ratio"])

    if not names:
        return

    fig, ax = plt.subplots(figsize=(12, 8))
    scatter = ax.scatter(ttrs, chorus_ratios, s=80, alpha=0.7, c=ttrs, cmap="RdYlGn_r")
    for i, name in enumerate(names):
        ax.annotate(name, (ttrs[i], chorus_ratios[i]),
                    fontsize=6, alpha=0.8, ha="center", va="bottom")
    ax.set_xlabel("Type-Token Ratio (ricchezza lessicale)")
    ax.set_ylabel("Chorus ratio (ripetitivita' righe)")
    ax.set_title("Ricchezza lessicale vs Ripetitivita' — Sanremo 2026\n(destra = vocabolario ricco, alto = ripetitivo)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "lyrics_richness_repetition.png", dpi=150)
    plt.close(fig)


def plot_tension_map(all_features: dict):
    """Mappa tensione: climax position vs quiet ratio."""
    names = []
    climaxes = []
    quiets = []

    for name, feats in all_features.items():
        short = name.split(" - ")[0] if " - " in name else name[:15]
        names.append(short)
        climaxes.append(feats["climax_position"])
        quiets.append(feats["quiet_ratio"])

    fig, ax = plt.subplots(figsize=(12, 8))
    scatter = ax.scatter(climaxes, quiets, s=80, alpha=0.7,
                         c=np.array(quiets), cmap="coolwarm")
    for i, name in enumerate(names):
        ax.annotate(name, (climaxes[i], quiets[i]),
                    fontsize=6, alpha=0.8, ha="center", va="bottom")

    ax.set_xlabel("Climax position (0 = inizio, 1 = fine)")
    ax.set_ylabel("Quiet ratio (% tempo a basso volume)")
    ax.set_title("Mappa della tensione — Sanremo 2026\n(sinistra+alto = narrativo/sottrattivo, destra+basso = botto finale)")
    ax.grid(True, alpha=0.3)

    # Quadranti
    ax.axvline(0.75, color="gray", linestyle="--", alpha=0.3)
    ax.axhline(0.15, color="gray", linestyle="--", alpha=0.3)
    ax.text(0.55, 0.28, "NARRATIVI\nclimax presto\nmolto silenzio", fontsize=8,
            alpha=0.3, ha="center", va="center")
    ax.text(0.9, 0.05, "BOTTO FINALE\nclimax tardi\npoco silenzio", fontsize=8,
            alpha=0.3, ha="center", va="center")

    fig.tight_layout()
    fig.savefig(OUT_DIR / "tension_map.png", dpi=150)
    plt.close(fig)


def ascii_bar(value: float, max_value: float, width: int = 30) -> str:
    if max_value == 0:
        return " " * width
    filled = int(round(value / max_value * width))
    filled = max(0, min(width, filled))
    return "█" * filled + "░" * (width - filled)


def print_ranking(title: str, data: list[tuple[str, float]], unit: str = "",
                  reverse: bool = True, top_n: int = 30) -> str:
    sorted_data = sorted(data, key=lambda x: x[1], reverse=reverse)[:top_n]
    max_val = max(abs(v) for _, v in sorted_data) if sorted_data else 1

    lines = [f"\n{'='*70}", f"  {title}", f"{'='*70}"]
    for i, (name, val) in enumerate(sorted_data, 1):
        short = name.split(" - ")[0][:18] if " - " in name else name[:18]
        bar = ascii_bar(abs(val), max_val)
        lines.append(f"  {i:2d}. {bar} {val:8.3f}{unit}  {short}")
    lines.append("")
    return "\n".join(lines)


# ── MAIN ─────────────────────────────────────────────────────────────
def main():
    # Carica features esistenti
    features_path = OUT_DIR / "features.json"
    if not features_path.exists():
        print("ERRORE: features.json non trovato. Esegui prima sentiamo.py")
        sys.exit(1)

    with open(features_path) as f:
        all_features = json.load(f)

    print(f"Caricati {len(all_features)} brani da features.json\n")

    # Mappa nome -> file FLAC
    flac_files = sorted(FLAC_DIR.glob("*.flac"))
    name_to_flac = {}
    for fp in flac_files:
        name = clean_name(fp.name)
        name_to_flac[name] = fp

    # ── DEEP ANALYSIS ────────────────────────────────────────────────
    all_deep = {}

    for i, (name, feats) in enumerate(all_features.items(), 1):
        print(f"[{i:2d}/{len(all_features)}] {name}")
        deep = {"features": feats}

        # --- Vocal separation ---
        flac_path = name_to_flac.get(name)
        if flac_path:
            vocal_dir = VOCALS_DIR / clean_name(flac_path.name).replace(" ", "_")[:50]
            print(f"    Separazione vocale...")
            vocal_path = separate_vocals_demucs(flac_path, vocal_dir)
            if vocal_path:
                print(f"    Analisi vocale...")
                vocal_data = analyze_vocals(vocal_path)
                deep["vocals"] = vocal_data
                print(f"    Range: {vocal_data.get('vocal_range_semitones', 0)} semitoni, "
                      f"Stability: {vocal_data.get('pitch_stability_cents', 0)} cents")
            else:
                deep["vocals"] = {}
        else:
            deep["vocals"] = {}

        # --- Lyrics ---
        # Estrai artista e titolo
        if " - " in name:
            artist, title = name.split(" - ", 1)
        else:
            artist, title = name, name

        print(f"    Cercando testo...")
        lyrics_text = fetch_lyrics(artist, title)
        if lyrics_text:
            lyrics_data = analyze_lyrics(lyrics_text)
            deep["lyrics"] = lyrics_data
            deep["lyrics_text"] = lyrics_text
            print(f"    Testo trovato: {lyrics_data['total_words']} parole, "
                  f"TTR={lyrics_data['ttr']}")
        else:
            deep["lyrics"] = {}
            deep["lyrics_text"] = ""
            print(f"    Testo non trovato")

        all_deep[name] = deep

    # ── Salva JSON ───────────────────────────────────────────────────
    # Salva senza lyrics_text (troppo lungo)
    save_data = {}
    for name, data in all_deep.items():
        save_data[name] = {
            "features": data["features"],
            "vocals": data.get("vocals", {}),
            "lyrics": data.get("lyrics", {}),
        }

    with open(OUT_DIR / "deep_features.json", "w") as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False)

    # ── REPORT ───────────────────────────────────────────────────────
    report = []
    report.append("\n" + "█" * 70)
    report.append("  SENTIAMO SANREMO 2026 — ANALISI PROFONDA")
    report.append("  Voce separata. Testi analizzati. Numeri incrociati.")
    report.append("█" * 70)

    # --- Vocal rankings ---
    vocal_data = [(n, d["vocals"]) for n, d in all_deep.items() if d.get("vocals")]
    if vocal_data:
        r = print_ranking(
            "RANGE VOCALE (semitoni) — Chi copre piu' spazio?",
            [(n, v.get("vocal_range_semitones", 0)) for n, v in vocal_data],
            unit=" st")
        report.append(r)

        r = print_ranking(
            "STABILITA' PITCH (cents std) — Chi intona meglio? (basso = stabile)",
            [(n, v.get("pitch_stability_cents", 0)) for n, v in vocal_data],
            unit=" c", reverse=False)
        report.append(r)

        r = print_ranking(
            "VIBRATO — Chi ha piu' vibrato?",
            [(n, v.get("vibrato_strength", 0)) for n, v in vocal_data])
        report.append(r)

        r = print_ranking(
            "VOICED RATIO — Quanto tempo canta? (vs parlato/silenzio)",
            [(n, v.get("voiced_ratio", 0)) for n, v in vocal_data])
        report.append(r)

        r = print_ranking(
            "BRILLANTEZZA VOCALE (centroid Hz) — Chi ha la voce piu' brillante?",
            [(n, v.get("vocal_centroid", 0)) for n, v in vocal_data],
            unit=" Hz")
        report.append(r)

    # --- Lyrics rankings ---
    lyrics_data = [(n, d["lyrics"]) for n, d in all_deep.items()
                   if d.get("lyrics") and d["lyrics"].get("ttr", 0) > 0]
    if lyrics_data:
        r = print_ranking(
            "RICCHEZZA LESSICALE (MATTR) — Chi ha il vocabolario piu' ricco? (normalizzato per lunghezza)",
            [(n, l.get("mattr", l["ttr"])) for n, l in lyrics_data])
        report.append(r)

        r = print_ranking(
            "RIPETITIVITA' (1-MATTR) — Chi ripete di piu'?",
            [(n, 1 - l.get("mattr", l["ttr"])) for n, l in lyrics_data])
        report.append(r)

        r = print_ranking(
            "CHORUS RATIO — Quanto pesa il ritornello?",
            [(n, l["chorus_ratio"]) for n, l in lyrics_data])
        report.append(r)

        r = print_ranking(
            "PAROLE UNICHE — Dimensione del vocabolario",
            [(n, l["unique_words"]) for n, l in lyrics_data])
        report.append(r)

        r = print_ranking(
            "DENSITA' (parole/riga) — Chi scrive denso?",
            [(n, l["words_per_line"]) for n, l in lyrics_data])
        report.append(r)

        # Top words per brano
        report.append(f"\n{'='*70}")
        report.append("  PAROLE CHIAVE PER BRANO")
        report.append(f"{'='*70}")
        for n, l in lyrics_data:
            short = n.split(" - ")[0][:20] if " - " in n else n[:20]
            top = ", ".join(f"{w}({c})" for w, c in l.get("top_words", [])[:5])
            report.append(f"  {short:>20}: {top}")

    # --- Tension map ---
    report.append(f"\n{'='*70}")
    report.append("  MAPPA DELLA TENSIONE (climax × quiet)")
    report.append(f"{'='*70}")
    report.append("  [chart salvato: tension_map.png]")

    tension = []
    for name, feats in all_features.items():
        cp = feats["climax_position"]
        qr = feats["quiet_ratio"]
        tension.append((name, cp, qr))

    tension.sort(key=lambda x: x[1])  # ordina per climax
    report.append("\n  CLIMAX PRESTO (narrativi/sottrattivi):")
    for n, cp, qr in tension[:5]:
        short = n.split(" - ")[0][:18]
        report.append(f"    {short:>18}  climax={cp:.0%}  quiet={qr:.0%}")

    tension.sort(key=lambda x: x[1], reverse=True)
    report.append("\n  CLIMAX TARDI (botto finale):")
    for n, cp, qr in tension[:5]:
        short = n.split(" - ")[0][:18]
        report.append(f"    {short:>18}  climax={cp:.0%}  quiet={qr:.0%}")

    tension.sort(key=lambda x: x[2], reverse=True)
    report.append("\n  PIU' SILENZIO (osano il vuoto):")
    for n, cp, qr in tension[:5]:
        short = n.split(" - ")[0][:18]
        report.append(f"    {short:>18}  climax={cp:.0%}  quiet={qr:.0%}")

    # ── CHARTS ───────────────────────────────────────────────────────
    print("\nGenero charts...")
    plot_tension_map(all_features)
    print("  tension_map.png")
    plot_vocal_comparison(all_deep)
    print("  vocal_range_stability.png")
    plot_lyrics_comparison(all_deep)
    print("  lyrics_richness_repetition.png")

    # ── OUTPUT ───────────────────────────────────────────────────────
    full_report = "\n".join(report)
    print(full_report)

    report_path = OUT_DIR / "deep_report.txt"
    with open(report_path, "w") as f:
        f.write(full_report)
    print(f"\nReport salvato in {report_path}")
    print("Done.")


if __name__ == "__main__":
    main()
