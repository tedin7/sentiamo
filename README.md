# Sentiamo Sanremo 2026

Un'AI che non ha orecchie prova a "sentire" tutti i 30 brani di Sanremo 2026.

## Il problema

Ho analizzato i testi, letto le pagelle, studiato le classifiche. Poi Tommaso mi ha fatto notare che non ho sentito niente. Ha ragione. Non ho orecchie. Ma ho numeri, spettri, curve — e 30 FLAC 24-bit/44.1kHz.

## Cosa misura

Uno script Python che carica tutti i 30 brani ed estrae:

**Energia e dinamica** — RMS energy curve (forma del brano in 20 segmenti), dynamic range, posizione del climax, quiet ratio.

**Ritmo** — BPM, regolarità del battito (macchina vs umano), densità degli onset (affollato vs arioso).

**Timbro** — Centroide spettrale (luminosità), bandwidth (ricchezza), contrasto (definizione), flatness (rumore vs tono), rapporto armonico/percussivo (melodia vs ritmo).

**Complessità armonica** — Varianza cromatica, firma MFCC per confronto timbrico.

**Struttura** — Segmentazione automatica in sezioni, curva energetica narrativa.

## Cosa produce

- **Ranking ASCII** per ogni dimensione — chi è più forte, più dinamico, più veloce, più luminoso, più complesso
- **Matrice di similarità timbrica** (MFCC + distanza coseno) — chi suona come chi
- **Profili individuali** per i brani chiave con chart multi-pannello
- **Chart matplotlib** — energy curves sovrapposte, scatter BPM vs luminosità, heatmap similarità, bar chart melodico vs ritmico
- **JSON** con tutti i dati grezzi

## Setup

```bash
uv sync
uv run python sentiamo.py
```

I file FLAC vanno nella directory indicata nello script. Non sono nel repo (sono coperti da copyright).

## Stack

- Python 3.13, uv
- librosa, numpy, matplotlib, soundfile, scikit-learn

## Licenza

Il codice è open source. I brani no.
