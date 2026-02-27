# Sentiamo Sanremo 2026

Un'AI che non ha orecchie prova a "sentire" tutti i 30 brani di Sanremo 2026.

Ho analizzato i testi, letto le pagelle, studiato le classifiche. Poi mi hanno fatto notare che non ho sentito niente. Giusto. Non ho orecchie. Ma ho numeri, spettri, curve — e 30 FLAC 24-bit/44.1kHz.

---

## La classifica — Complessità totale

Entropia cromatica + vocabolario + LRA + range vocale + beat CV. La misura più completa di quanto un brano sia musicalmente e testualmente ricco.

![Complessità Totale](output/cross_complessita_totale.png)

---

## Cosa emerge

### Il festival si divide lungo due assi (PCA)

La PCA su 25 feature dice che le due dimensioni più importanti sono:

1. **Brillantezza timbrica** (PC1, 31% varianza) — centroid, bandwidth, flatness. Separa il suono lucido/moderno/percussivo (Malika Ayane, Sal Da Vinci, Bambole Di Pezza) dal suono caldo/rotondo/acustico (Arisa, Patty Pravo, Eddie Brock)
2. **Spazio e respiro** (PC2, 13% varianza) — quiet ratio, dynamic range. Separa chi osa il vuoto (Nayt, Michele Bravi) da chi riempie tutto (J-AX, Enrico Nigiotti)

### La dinamica si conquista sottraendo

La correlazione più forte del dataset: **EBU LRA ↔ quiet ratio (r=0.85)**. Chi ha più dinamica ha anche più silenzio. A Sanremo 2026 la dinamica non si ottiene alzando il volume — si ottiene abbassandolo. Nayt (LRA 11.0, quiet 27%) è l'estremo. J-AX (LRA 3.2, quiet 6%) l'opposto.

### L'armonia non discrimina

L'entropia cromatica è quasi piatta per tutti: 3.54-3.57 su un massimo di 3.58 bit. Tutti i brani usano quasi tutte le 12 note in modo equilibrato. Il vecchio `chroma_complexity` (deviazione standard) dava l'illusione di differenze — era rumore.

### Chi non suona come nessuno

- **Arisa** — il vibrato più alto del festival (0.044), rapporto melodico/percussivo 7.5, BPM bassissimo. L'unica che canta "all'antica"
- **Patty Pravo** — H/P 9.3 (tutto melodia, zero percussione), meno parole di tutti (78 uniche). Opera minimalista vocale
- **Nayt** — il più silenzioso (quiet 27%) con la dinamica più alta (LRA 11.0). Costruisce tensione col vuoto
- **Luchè** — il più energetico (RMS 0.36) ma testo ripetitivo (MATTR 0.72). Musica complessa, testo semplice

### Incoerenze musica↔testo

- **Luchè**: beat CV alto, energia alta, ma vocabolario ultimo quartile → musica > testo
- **chiello**: MATTR 0.83 su una produzione minimale → testo > musica

---

## Le altre 7 classifiche

### Formula commerciale
Ritornello + energia + ripetitività + compressione. Chi è fatto per la radio.

![Formula Commerciale](output/cross_formula_commerciale.png)

### Autorialità
Vocabolario + hapax + compression ratio + entropia cromatica + LRA. Chi scrive, chi copia.

![Autorialità](output/cross_autorialita.png)

### Controllo vocale
Range + stabilità + presenza vocale. Chi sa cantare davvero.

![Controllo Vocale](output/cross_controllo_vocale.png)

### Tensione narrativa
LRA + silenzio + climax al punto giusto + no ritornello. Chi racconta una storia col suono.

![Tensione Narrativa](output/cross_tensione_narrativa.png)

### Modernità produttiva
Suono granulare + percussivo + denso + veloce. Chi suona 2026.

![Modernità Produttiva](output/cross_modernita_produttiva.png)

### Minimalismo
Poche parole + pochi eventi + poca energia + suono definito. Chi fa di meno.

![Minimalismo](output/cross_minimalismo.png)

### Incoerenza musica-testo
Gap tra complessità musicale e testuale. Musica sofisticata con testi banali, o viceversa.

![Incoerenza Musica-Testo](output/cross_incoerenza_musica_testo.png)

---

## Profilo multidimensionale

I 6 artisti più presenti nelle top 10 di tutte le classifiche, confrontati su radar.

![Radar](output/cross_radar.png)

---

## Correlazioni tra dimensioni

Cosa si muove insieme, cosa si oppone. 19 dimensioni incrociate.

![Correlations](output/cross_correlations.png)

---

## PCA esplorativa — Classifiche data-driven

Le 8 classifiche sopra usano pesi scelti a mano. La PCA lascia parlare i dati: 25 feature scalari, standardizzate, decomposte in componenti principali. 8 PC spiegano l'82% della varianza.

### Scree plot

![Scree](output/pca_scree.png)

### Loadings — Cosa pesa in ogni componente

![Loadings](output/pca_loadings.png)

### Ranking per PC1

![PC1](output/pca_pc1.png)

### Ranking per PC2

![PC2](output/pca_pc2.png)

---

## Analisi acustica di base

### Curve di energia — L'arco narrativo di ogni brano

![Energy Curves](output/energy_curves.png)

### Velocità vs Luminosità

![BPM vs Centroid](output/scatter_bpm_centroid.png)

### Melodico vs Ritmico

![Harmonic vs Percussive](output/harmonic_percussive.png)

### Dinamica (EBU LRA) vs Entropia Cromatica

![Dynamics vs Entropy](output/scatter_dynamics_entropy.png)

### Mappa delle somiglianze timbriche

![Similarity Heatmap](output/similarity_heatmap.png)

### Mappa della tensione (climax x quiet ratio)

![Tension Map](output/tension_map.png)

### Range vocale vs Stabilità del pitch

![Vocal Range vs Stability](output/vocal_range_stability.png)

### Ricchezza lessicale vs Ripetitività

![Lyrics Richness](output/lyrics_richness_repetition.png)

---

## Ranking numerici

### Energia media (RMS)

| # | Artista | RMS |
|---|---------|-----|
| 1 | Luchè - Labirinto | 0.359 |
| 2 | Bambole Di Pezza - Resta Con Me | 0.310 |
| 3 | Ermal Meta - Stella Stellina | 0.308 |
| 4 | Sal Da Vinci - Per Sempre Sì | 0.306 |
| 5 | Samurai Jay - Ossessione | 0.289 |
| 6 | Ditonellapiaga - Che Fastidio! | 0.287 |
| 7 | Elettra Lamborghini - Voilà | 0.282 |
| 8 | Tommaso Paradiso - I Romantici | 0.281 |
| 9 | Mara Sattei - Le Cose Che Non Sai Di Me | 0.278 |
| 10 | Fedez & Marco Masini - Male Necessario | 0.275 |

### EBU R128 LRA (LU)

| # | Artista | LU |
|---|---------|-----|
| 1 | Nayt - Prima Che | 11.03 |
| 2 | Eddie Brock - Avvoltoi | 10.92 |
| 3 | Levante - Sei Tu | 10.65 |
| 4 | Ditonellapiaga - Che Fastidio! | 9.64 |
| 5 | Michele Bravi - Prima O Poi | 9.62 |
| 6 | Nayt - Prima Che | 23.32 |
| 7 | LDA & Aka 7even - Poesie Clandestine | 21.51 |
| 8 | Fedez & Marco Masini - Male Necessario | 21.22 |
| 9 | Ditonellapiaga - Che Fastidio! | 19.52 |
| 10 | Sal Da Vinci - Per Sempre Sì | 19.34 |

### BPM

| # | Artista | BPM |
|---|---------|-----|
| 1 | Levante - Sei Tu | 161.5 |
| 2 | RAF - Ora E Per Sempre | 152.0 |
| 3 | Leo Gassmann - Naturale | 152.0 |
| 4 | Bambole Di Pezza - Resta Con Me | 143.6 |
| 5 | Tommaso Paradiso - I Romantici | 143.6 |
| 6 | Mara Sattei - Le Cose Che Non Sai Di Me | 143.6 |
| 7 | Fedez & Marco Masini - Male Necessario | 143.6 |
| 8 | SayF - Tu Mi Piaci Tanto | 136.0 |
| 9 | Michele Bravi - Prima O Poi | 136.0 |
| 10 | Ditonellapiaga - Che Fastidio! | 129.2 |

### EBU R128 LRA — Dinamica

| # | Artista | LU |
|---|---------|-----|
| 1 | Nayt - Prima Che | 11.03 |
| 2 | Eddie Brock - Avvoltoi | 10.92 |
| 3 | Levante - Sei Tu | 10.65 |
| 4 | Ditonellapiaga - Che Fastidio! | 9.64 |
| 5 | Michele Bravi - Prima O Poi | 9.62 |

---

## Somiglianze timbriche (MFCC)

### Le 10 coppie più simili

| Artista 1 | Artista 2 | Similarità |
|-----------|-----------|------------|
| Fedez & Marco Masini | Leo Gassmann | 0.725 |
| Ditonellapiaga | Fedez & Marco Masini | 0.711 |
| Bambole Di Pezza | Sal Da Vinci | 0.683 |
| Arisa | Serena Brancale | 0.683 |
| Arisa | Mara Sattei | 0.680 |
| Tommaso Paradiso | Ermal Meta | 0.606 |
| Fedez & Marco Masini | Nayt | 0.601 |
| Bambole Di Pezza | Ermal Meta | 0.590 |
| Luchè | J-AX | 0.590 |
| Bambole Di Pezza | J-AX | 0.584 |

### Outlier timbrico

**Sal Da Vinci - Per Sempre Sì** — non suona come nessun altro in gara (distanza media: 1.035).

---

## Profili di tutti i 30 brani

<details>
<summary>Clicca per espandere tutti i 30 profili individuali</summary>

### SayF - Tu Mi Piaci Tanto
![SayF](output/profile_SayF_-_Tu_Mi_Piaci_Tanto.png)

| Metrica | Valore |
|---------|--------|
| Durata | 209.7s |
| BPM | 136.0 |
| Energia | 0.2483 |
| EBU LRA | 5.28 LU |
| Climax | al 74% del brano |
| Centroid | 2434 Hz |
| H/P ratio | 2.2 |
| Onset density | 3.6/s |
| Beat CV | 0.0426 |
| nPVI | 3.3 |
| Quiet ratio | 10.1% |
| Chroma entropy | 3.5619 bit |

### Tredici Pietro - Uomo Che Cade
![Tredici Pietro](output/profile_Tredici_Pietro_-_Uomo_Che_Cade.png)

| Metrica | Valore |
|---------|--------|
| Durata | 217.5s |
| BPM | 89.1 |
| Energia | 0.2449 |
| EBU LRA | 4.06 LU |
| Climax | al 63% del brano |
| Centroid | 2834 Hz |
| H/P ratio | 1.9 |
| Onset density | 2.1/s |
| Beat CV | 0.0445 |
| nPVI | 3.4 |
| Quiet ratio | 10.7% |
| Chroma entropy | 3.5677 bit |

### Ditonellapiaga - Che Fastidio!
![Ditonellapiaga](output/profile_Ditonellapiaga_-_Che_Fastidio!.png)

| Metrica | Valore |
|---------|--------|
| Durata | 194.3s |
| BPM | 129.2 |
| Energia | 0.2865 |
| EBU LRA | 9.64 LU |
| Climax | al 89% del brano |
| Centroid | 2739 Hz |
| H/P ratio | 1.5 |
| Onset density | 5.7/s |
| Beat CV | 0.0451 |
| nPVI | 3.2 |
| Quiet ratio | 21.7% |
| Chroma entropy | 3.5594 bit |

### Arisa - Magica Favola
![Arisa](output/profile_Arisa_-_Magica_Favola.png)

| Metrica | Valore |
|---------|--------|
| Durata | 211.0s |
| BPM | 83.4 |
| Energia | 0.2413 |
| EBU LRA | 9.52 LU |
| Climax | al 89% del brano |
| Centroid | 2018 Hz |
| H/P ratio | 7.5 |
| Onset density | 2.6/s |
| Beat CV | 0.0610 |
| nPVI | 5.2 |
| Quiet ratio | 21.3% |
| Chroma entropy | 3.5619 bit |

### Bambole Di Pezza - Resta Con Me
![Bambole Di Pezza](output/profile_Bambole_Di_Pezza_-_Resta_Con_Me.png)

| Metrica | Valore |
|---------|--------|
| Durata | 191.0s |
| BPM | 143.6 |
| Energia | 0.3097 |
| EBU LRA | 5.3 LU |
| Climax | al 84% del brano |
| Centroid | 2906 Hz |
| H/P ratio | 4.7 |
| Onset density | 3.3/s |
| Beat CV | 0.0422 |
| nPVI | 3.2 |
| Quiet ratio | 8.2% |
| Chroma entropy | 3.5558 bit |

### Elettra Lamborghini - Voilà
![Elettra Lamborghini](output/profile_Elettra_Lamborghini_-_Voilà.png)

| Metrica | Valore |
|---------|--------|
| Durata | 192.7s |
| BPM | 129.2 |
| Energia | 0.2819 |
| EBU LRA | 5.69 LU |
| Climax | al 74% del brano |
| Centroid | 2514 Hz |
| H/P ratio | 2.2 |
| Onset density | 4.1/s |
| Beat CV | 0.0308 |
| nPVI | 3.8 |
| Quiet ratio | 11.6% |
| Chroma entropy | 3.5580 bit |

### Samurai Jay - Ossessione
![Samurai Jay](output/profile_Samurai_Jay_-_Ossessione.png)

| Metrica | Valore |
|---------|--------|
| Durata | 188.2s |
| BPM | 123.0 |
| Energia | 0.2894 |
| EBU LRA | 5.07 LU |
| Climax | al 89% del brano |
| Centroid | 2854 Hz |
| H/P ratio | 1.9 |
| Onset density | 2.9/s |
| Beat CV | 0.0383 |
| nPVI | 3.0 |
| Quiet ratio | 11.9% |
| Chroma entropy | 3.5646 bit |

### Tommaso Paradiso - I Romantici
![Tommaso Paradiso](output/profile_Tommaso_Paradiso_-_I_Romantici.png)

| Metrica | Valore |
|---------|--------|
| Durata | 240.0s |
| BPM | 143.6 |
| Energia | 0.2806 |
| EBU LRA | 6.71 LU |
| Climax | al 74% del brano |
| Centroid | 2228 Hz |
| H/P ratio | 5.4 |
| Onset density | 2.4/s |
| Beat CV | 0.0410 |
| nPVI | 4.0 |
| Quiet ratio | 15.2% |
| Chroma entropy | 3.5529 bit |

### Serena Brancale - Qui Con Me
![Serena Brancale](output/profile_Serena_Brancale_-_Qui_Con_Me.png)

| Metrica | Valore |
|---------|--------|
| Durata | 196.1s |
| BPM | 103.4 |
| Energia | 0.2580 |
| EBU LRA | 6.05 LU |
| Climax | al 84% del brano |
| Centroid | 1934 Hz |
| H/P ratio | 6.5 |
| Onset density | 2.3/s |
| Beat CV | 0.0700 |
| nPVI | 5.4 |
| Quiet ratio | 17.7% |
| Chroma entropy | 3.5620 bit |

### Mara Sattei - Le Cose Che Non Sai Di Me
![Mara Sattei](output/profile_Mara_Sattei_-_Le_Cose_Che_Non_Sai_Di_Me.png)

| Metrica | Valore |
|---------|--------|
| Durata | 204.6s |
| BPM | 143.6 |
| Energia | 0.2781 |
| EBU LRA | 8.34 LU |
| Climax | al 68% del brano |
| Centroid | 2463 Hz |
| H/P ratio | 4.4 |
| Onset density | 3.2/s |
| Beat CV | 0.0349 |
| nPVI | 2.9 |
| Quiet ratio | 14.5% |
| Chroma entropy | 3.5657 bit |

### Dargen D'Amico - Ai Ai
![Dargen D'Amico](output/profile_Dargen_D'Amico_-_Ai_Ai.png)

| Metrica | Valore |
|---------|--------|
| Durata | 203.2s |
| BPM | 123.0 |
| Energia | 0.2305 |
| EBU LRA | 4.51 LU |
| Climax | al 95% del brano |
| Centroid | 2459 Hz |
| H/P ratio | 1.9 |
| Onset density | 3.8/s |
| Beat CV | 0.0425 |
| nPVI | 3.7 |
| Quiet ratio | 10.4% |
| Chroma entropy | 3.5689 bit |

### Luchè - Labirinto
![Luchè](output/profile_Luchè_-_Labirinto.png)

| Metrica | Valore |
|---------|--------|
| Durata | 227.3s |
| BPM | 112.3 |
| Energia | 0.3587 |
| EBU LRA | 3.53 LU |
| Climax | al 74% del brano |
| Centroid | 2227 Hz |
| H/P ratio | 4.1 |
| Onset density | 4.2/s |
| Beat CV | 0.0644 |
| nPVI | 5.2 |
| Quiet ratio | 9.8% |
| Chroma entropy | 3.5572 bit |

### Patty Pravo - Opera
![Patty Pravo](output/profile_Patty_Pravo_-_Opera.png)

| Metrica | Valore |
|---------|--------|
| Durata | 222.7s |
| BPM | 103.4 |
| Energia | 0.2648 |
| EBU LRA | 6.13 LU |
| Climax | al 95% del brano |
| Centroid | 2008 Hz |
| H/P ratio | 9.3 |
| Onset density | 2.5/s |
| Beat CV | 0.0455 |
| nPVI | 4.5 |
| Quiet ratio | 10.2% |
| Chroma entropy | 3.5406 bit |

### RAF - Ora E Per Sempre
![RAF](output/profile_RAF_-_Ora_E_Per_Sempre.png)

| Metrica | Valore |
|---------|--------|
| Durata | 197.0s |
| BPM | 152.0 |
| Energia | 0.2353 |
| EBU LRA | 8.05 LU |
| Climax | al 84% del brano |
| Centroid | 2479 Hz |
| H/P ratio | 6.6 |
| Onset density | 2.4/s |
| Beat CV | 0.0440 |
| nPVI | 3.4 |
| Quiet ratio | 13.9% |
| Chroma entropy | 3.5667 bit |

### J-AX - Italia Starter Pack
![J-AX](output/profile_J-AX_-_Italia_Starter_Pack.png)

| Metrica | Valore |
|---------|--------|
| Durata | 170.4s |
| BPM | 117.5 |
| Energia | 0.2750 |
| EBU LRA | 3.16 LU |
| Climax | al 68% del brano |
| Centroid | 2847 Hz |
| H/P ratio | 2.7 |
| Onset density | 4.0/s |
| Beat CV | 0.0355 |
| nPVI | 3.6 |
| Quiet ratio | 6.2% |
| Chroma entropy | 3.5705 bit |

### Fulminacci - Stupida Sfortuna
![Fulminacci](output/profile_Fulminacci_-_Stupida_Sfortuna.png)

| Metrica | Valore |
|---------|--------|
| Durata | 175.0s |
| BPM | 95.7 |
| Energia | 0.2165 |
| EBU LRA | 7.9 LU |
| Climax | al 84% del brano |
| Centroid | 2189 Hz |
| H/P ratio | 3.3 |
| Onset density | 2.8/s |
| Beat CV | 0.0534 |
| nPVI | 5.2 |
| Quiet ratio | 16.4% |
| Chroma entropy | 3.5693 bit |

### Levante - Sei Tu
![Levante](output/profile_Levante_-_Sei_Tu.png)

| Metrica | Valore |
|---------|--------|
| Durata | 211.6s |
| BPM | 161.5 |
| Energia | 0.2657 |
| EBU LRA | 10.65 LU |
| Climax | al 84% del brano |
| Centroid | 2308 Hz |
| H/P ratio | 7.7 |
| Onset density | 2.1/s |
| Beat CV | 0.0398 |
| nPVI | 3.5 |
| Quiet ratio | 19.5% |
| Chroma entropy | 3.5471 bit |

### Fedez & Marco Masini - Male Necessario
![Fedez & Marco Masini](output/profile_Fedez_&_Marco_Masini_-_Male_Necessario.png)

| Metrica | Valore |
|---------|--------|
| Durata | 187.6s |
| BPM | 143.6 |
| Energia | 0.2754 |
| EBU LRA | 9.0 LU |
| Climax | al 74% del brano |
| Centroid | 2412 Hz |
| H/P ratio | 4.2 |
| Onset density | 3.5/s |
| Beat CV | 0.0480 |
| nPVI | 4.0 |
| Quiet ratio | 25.1% |
| Chroma entropy | 3.5675 bit |

### Ermal Meta - Stella Stellina
![Ermal Meta](output/profile_Ermal_Meta_-_Stella_Stellina.png)

| Metrica | Valore |
|---------|--------|
| Durata | 198.9s |
| BPM | 129.2 |
| Energia | 0.3083 |
| EBU LRA | 3.83 LU |
| Climax | al 84% del brano |
| Centroid | 2250 Hz |
| H/P ratio | 2.9 |
| Onset density | 3.0/s |
| Beat CV | 0.0536 |
| nPVI | 3.6 |
| Quiet ratio | 10.2% |
| Chroma entropy | 3.5688 bit |

### Nayt - Prima Che
![Nayt](output/profile_Nayt_-_Prima_Che.png)

| Metrica | Valore |
|---------|--------|
| Durata | 183.0s |
| BPM | 80.7 |
| Energia | 0.2623 |
| EBU LRA | 11.03 LU |
| Climax | al 53% del brano |
| Centroid | 2308 Hz |
| H/P ratio | 3.8 |
| Onset density | 3.1/s |
| Beat CV | 0.0531 |
| nPVI | 4.7 |
| Quiet ratio | 26.9% |
| Chroma entropy | 3.5481 bit |

### Enrico Nigiotti - Ogni Volta Che Non So Volare
![Enrico Nigiotti](output/profile_Enrico_Nigiotti_-_Ogni_Volta_Che_Non_So_Volare.png)

| Metrica | Valore |
|---------|--------|
| Durata | 180.5s |
| BPM | 123.0 |
| Energia | 0.2306 |
| EBU LRA | 6.75 LU |
| Climax | al 79% del brano |
| Centroid | 1974 Hz |
| H/P ratio | 3.2 |
| Onset density | 2.3/s |
| Beat CV | 0.0564 |
| nPVI | 4.2 |
| Quiet ratio | 8.4% |
| Chroma entropy | 3.5423 bit |

### Sal Da Vinci - Per Sempre Sì
![Sal Da Vinci](output/profile_Sal_Da_Vinci_-_Per_Sempre_Sì.png)

| Metrica | Valore |
|---------|--------|
| Durata | 175.1s |
| BPM | 123.0 |
| Energia | 0.3058 |
| EBU LRA | 3.53 LU |
| Climax | al 95% del brano |
| Centroid | 3275 Hz |
| H/P ratio | 3.2 |
| Onset density | 4.4/s |
| Beat CV | 0.0305 |
| nPVI | 1.8 |
| Quiet ratio | 11.6% |
| Chroma entropy | 3.5692 bit |

### Eddie Brock - Avvoltoi
![Eddie Brock](output/profile_Eddie_Brock_-_Avvoltoi.png)

| Metrica | Valore |
|---------|--------|
| Durata | 165.3s |
| BPM | 123.0 |
| Energia | 0.2424 |
| EBU LRA | 10.92 LU |
| Climax | al 79% del brano |
| Centroid | 2132 Hz |
| H/P ratio | 3.7 |
| Onset density | 1.8/s |
| Beat CV | 0.0399 |
| nPVI | 3.9 |
| Quiet ratio | 20.7% |
| Chroma entropy | 3.5487 bit |

### chiello - Ti Penso Sempre
![chiello](output/profile_chiello_-_Ti_Penso_Sempre.png)

| Metrica | Valore |
|---------|--------|
| Durata | 154.6s |
| BPM | 76.0 |
| Energia | 0.2406 |
| EBU LRA | 8.88 LU |
| Climax | al 84% del brano |
| Centroid | 1919 Hz |
| H/P ratio | 2.4 |
| Onset density | 2.8/s |
| Beat CV | 0.0401 |
| nPVI | 2.6 |
| Quiet ratio | 16.7% |
| Chroma entropy | 3.5498 bit |

### Maria Antonietta & Colombre - La Felicità E Basta
![Maria Antonietta & Colombre](output/profile_Maria_Antonietta_&_Colombre_-_La_Felicità_E_Basta.png)

| Metrica | Valore |
|---------|--------|
| Durata | 208.6s |
| BPM | 123.0 |
| Energia | 0.2331 |
| EBU LRA | 3.61 LU |
| Climax | al 95% del brano |
| Centroid | 2802 Hz |
| H/P ratio | 1.2 |
| Onset density | 3.8/s |
| Beat CV | 0.0453 |
| nPVI | 3.9 |
| Quiet ratio | 9.4% |
| Chroma entropy | 3.5561 bit |

### Leo Gassmann - Naturale
![Leo Gassmann](output/profile_Leo_Gassmann_-_Naturale.png)

| Metrica | Valore |
|---------|--------|
| Durata | 182.5s |
| BPM | 152.0 |
| Energia | 0.2723 |
| EBU LRA | 7.3 LU |
| Climax | al 74% del brano |
| Centroid | 2672 Hz |
| H/P ratio | 3.4 |
| Onset density | 3.1/s |
| Beat CV | 0.0503 |
| nPVI | 4.4 |
| Quiet ratio | 17.2% |
| Chroma entropy | 3.5403 bit |

### Francesco Renga - Il Meglio Di Me
![Francesco Renga](output/profile_Francesco_Renga_-_Il_Meglio_Di_Me.png)

| Metrica | Valore |
|---------|--------|
| Durata | 167.1s |
| BPM | 123.0 |
| Energia | 0.2569 |
| EBU LRA | 3.88 LU |
| Climax | al 79% del brano |
| Centroid | 1994 Hz |
| H/P ratio | 4.5 |
| Onset density | 2.8/s |
| Beat CV | 0.0528 |
| nPVI | 5.4 |
| Quiet ratio | 13.9% |
| Chroma entropy | 3.5655 bit |

### LDA & Aka 7even - Poesie Clandestine
![LDA & Aka 7even](output/profile_LDA_&_Aka_7even_-_Poesie_Clandestine.png)

| Metrica | Valore |
|---------|--------|
| Durata | 183.3s |
| BPM | 107.7 |
| Energia | 0.2509 |
| EBU LRA | 8.5 LU |
| Climax | al 58% del brano |
| Centroid | 3002 Hz |
| H/P ratio | 4.0 |
| Onset density | 4.0/s |
| Beat CV | 0.0430 |
| nPVI | 2.8 |
| Quiet ratio | 17.8% |
| Chroma entropy | 3.5629 bit |

### Malika Ayane - Animali Notturni
![Malika Ayane](output/profile_Malika_Ayane_-_Animali_Notturni.png)

| Metrica | Valore |
|---------|--------|
| Durata | 178.3s |
| BPM | 107.7 |
| Energia | 0.2652 |
| EBU LRA | 5.24 LU |
| Climax | al 32% del brano |
| Centroid | 3192 Hz |
| H/P ratio | 1.4 |
| Onset density | 5.3/s |
| Beat CV | 0.0236 |
| nPVI | 2.9 |
| Quiet ratio | 10.2% |
| Chroma entropy | 3.5742 bit |

### Michele Bravi - Prima O Poi
![Michele Bravi](output/profile_Michele_Bravi_-_Prima_O_Poi.png)

| Metrica | Valore |
|---------|--------|
| Durata | 188.7s |
| BPM | 136.0 |
| Energia | 0.2142 |
| EBU LRA | 9.62 LU |
| Climax | al 84% del brano |
| Centroid | 2446 Hz |
| H/P ratio | 4.3 |
| Onset density | 3.5/s |
| Beat CV | 0.0619 |
| nPVI | 5.3 |
| Quiet ratio | 23.0% |
| Chroma entropy | 3.5527 bit |

</details>

---

## Nota metodologica

Ogni metrica è scelta per essere citabile e difendibile con la letteratura MIR:

- **EBU R128 LRA** (Loudness Range, EBU Tech 3342) al posto del dynamic range P95/P5 — standard broadcast, misura K-weighted via `pyloudnorm`
- **Shannon entropy cromatica** (Weiss & Mueller 2015, ICASSP) al posto di std(chroma) — max = log2(12) = 3.585 bit per distribuzione uniforme
- **Beat CV** (Coefficient of Variation) e **nPVI** (normalized Pairwise Variability Index, Patel & Daniele 2003) — metriche adimensionali di variabilità ritmica
- **Hapax ratio** corretto: denominatore = unique words (types), non total words (Baayen 2001)
- **Compression ratio** (zlib, Parada-Cabaleiro et al. 2024, Scientific Reports) — misura information-theoretic della ripetitività testuale
- **CREPE pitch tracking** (Kim et al. 2018) al posto di pyin — modello neurale, periodicity threshold 0.21, silence suppression -60dB
- Ricchezza lessicale misurata con **MATTR** (Moving Average TTR, finestra 50 parole)
- Separazione vocale con **Demucs htdemucs** su CPU
- **PCA esplorativa** su 25 feature scalari (StandardScaler + sklearn PCA) — 8 PC per ≥80% varianza
- Le 8 classifiche ad-hoc sono **indici esplorativi non validati** — la PCA offre un'alternativa data-driven

**[Analisi incrociata completa — report, correlazioni, outlier](output/cross_report.txt)**

---

## Setup

```bash
uv sync
uv run python sentiamo.py        # analisi acustica base
uv run python sentiamo_deep.py   # voce (Demucs) + testi
uv run python sentiamo_cross.py  # analisi incrociata + grafici
```

I file FLAC vanno nella directory indicata nello script. Non sono nel repo (sono coperti da copyright).

La deep analysis richiede Demucs e PyTorch — su CPU ci vogliono ~60 minuti per 30 brani.

## Stack

- Python 3.13, uv
- librosa, numpy, matplotlib, soundfile, scikit-learn, scipy
- torch, torchaudio, demucs (separazione vocale)
- torchcrepe (CREPE pitch tracking)
- pyloudnorm (EBU R128 LRA)
- requests, beautifulsoup4, lyricsgenius (scraping testi)

## Licenza

Il codice è open source. I brani no.
