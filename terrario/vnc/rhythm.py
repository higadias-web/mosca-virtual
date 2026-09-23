"""Métrica de ritmo da Fase 3a (fixada antes dos testes; docs/FASE3_PLANO.md §2).

Para cada grupo de MNs (p. ex. os de uma perna): taxa populacional em janelas de `bin_ms`,
espectro de potência (sem a média), potência máxima na banda de passada. A banda é 3–20 Hz:
o período de passada de Drosophila chega a ~60 ms (~16 Hz) na marcha mais rápida (Mendes et al.
2013, eLife 2:e00231), e a marcha lenta fica abaixo; 20 Hz dá margem acima do máximo medido.

Teste contra o acaso: 200 surrogados em que o trem de cada MN é deslocado circularmente por um
atraso aleatório independente. Isso preserva a taxa e a estrutura temporal de cada neurônio,
mas destrói a sincronia entre eles. Um ritmo populacional exige potência acima do percentil 99
dos surrogados. Critério mínimo de dados: ≥ 20 spikes no grupo.

Obs.: um único MN com disparo periódico passa neste teste só se o grupo inteiro oscilar junto;
a periodicidade de um neurônio isolado não é "ritmo de marcha".
"""

from __future__ import annotations

import numpy as np

BAND_HZ = (3.0, 20.0)


def _band_power(counts: np.ndarray, bin_s: float, band=BAND_HZ):
    h = counts - counts.mean()
    p = np.abs(np.fft.rfft(h)) ** 2
    f = np.fft.rfftfreq(len(h), d=bin_s)
    sel = (f >= band[0]) & (f <= band[1])
    k = np.argmax(p[sel])
    return float(p[sel][k]), float(f[sel][k]), f, p


def rhythm_test(spike_idx, spike_t_ms, members, t0_ms, t1_ms, *, bin_ms=5.0, n_surr=200,
                band=BAND_HZ, seed=0):
    """Testa ritmo populacional nos neurônios `members` entre t0 e t1 (ms)."""
    members = np.asarray(members)
    sel = np.isin(spike_idx, members) & (spike_t_ms >= t0_ms) & (spike_t_ms < t1_ms)
    ii, tt = spike_idx[sel], spike_t_ms[sel] - t0_ms
    T = t1_ms - t0_ms
    nb = int(round(T / bin_ms))
    out = dict(n_spikes=int(len(tt)), n_active=int(len(np.unique(ii))), n=int(len(members)),
               rate_hz=float(len(tt) / len(members) / (T / 1000)))
    if len(tt) < 20:
        out.update(rhythmic=False, peak_hz=None, power=0.0, p99=None, ratio=None)
        return out
    counts, _ = np.histogram(tt, bins=nb, range=(0, T))
    pw, fpk, f, p = _band_power(counts, bin_ms / 1000, band)
    rng = np.random.default_rng(seed)
    uniq, inv = np.unique(ii, return_inverse=True)
    sp = np.empty(n_surr)
    for s in range(n_surr):
        sh = rng.uniform(0, T, len(uniq))[inv]
        c, _ = np.histogram((tt + sh) % T, bins=nb, range=(0, T))
        sp[s] = _band_power(c, bin_ms / 1000, band)[0]
    p99 = float(np.percentile(sp, 99))
    out.update(rhythmic=bool(pw > p99), peak_hz=fpk, power=pw, p99=p99, ratio=pw / p99 if p99 else None,
               freqs=f, spectrum=p, surr_p99_level=p99)
    return out


# ---------------------------------------------------------------------------------------------
# Métrica v2 (corrigida na Sessão 1, 2026-09-23, antes de qualquer teste em malha fechada).
# Motivo: a v1 dá falso positivo com entrada comum de banda larga (tests/test_rhythm.py::
# test_v1_false_positive_shared_broadband): os surrogados destroem a correlação entre neurônios,
# então QUALQUER sincronia (em todas as frequências) passa do p99. A v2 exige, além da v1:
#   (1) pico proeminente no espectro de Welch (janelas de 1 s, 50 % de sobreposição, bins de
#       1 Hz; exige ≥ 2 s de registro): máximo LOCAL dentro da banda (maior que os dois vizinhos), com potência ≥ PROMINENCE × a
#       média dos flancos (bins a 2–3 Hz de cada lado). Um espectro que só decai (entrada comum
#       lenta, "vermelho") não tem máximo local e é rejeitado;
#   (2) reprodutibilidade: o pico aparece (1) em ≥ 3 de 5 sementes, com frequência a ±1 Hz da
#       mediana das sementes que passaram.
# A mudança só torna o critério mais estrito.
# Limiar calibrado pela distribuição nula: 200 sementes de entrada comum sem periodicidade
# (Ornstein-Uhlenbeck, τ = 20 ms; tests/test_rhythm.py::_shared_broadband): p95 3,97; p99 4,79.
PROMINENCE = 5.0


def welch_peak(spike_idx, spike_t_ms, members, t0_ms, t1_ms, *, bin_ms=5.0, seg_ms=1000.0,
               band=BAND_HZ, fmax=60.0):
    sel = np.isin(spike_idx, members) & (spike_t_ms >= t0_ms) & (spike_t_ms < t1_ms)
    tt = spike_t_ms[sel] - t0_ms
    T = t1_ms - t0_ms
    if len(tt) < 20:
        return dict(prominent=False, peak_hz=None, prominence=None, n_spikes=int(len(tt)))
    counts, _ = np.histogram(tt, bins=int(round(T / bin_ms)), range=(0, T))
    L = int(seg_ms / bin_ms)
    step = L // 2
    win = np.hanning(L)
    P = []
    for s in range(0, len(counts) - L + 1, step):
        x = counts[s:s + L] - counts[s:s + L].mean()
        P.append(np.abs(np.fft.rfft(x * win)) ** 2)
    P = np.mean(P, axis=0)
    f = np.fft.rfftfreq(L, d=bin_ms / 1000)
    best_k, prom = None, 0.0
    for k in range(3, len(f) - 3):
        if not (band[0] <= f[k] <= band[1]) or f[k] > fmax:
            continue
        if P[k] <= P[k - 1] or P[k] <= P[k + 1]:
            continue  # não é máximo local
        flank = np.r_[P[k - 3:k - 1], P[k + 2:k + 4]]
        pr = float(P[k] / flank.mean()) if flank.mean() > 0 else 0.0
        if pr > prom:
            best_k, prom = k, pr
    if best_k is None:
        return dict(prominent=False, peak_hz=None, prominence=0.0, n_spikes=int(len(tt)),
                    freqs=f, welch=P)
    k = best_k
    return dict(prominent=bool(prom >= PROMINENCE), peak_hz=float(f[k]), prominence=prom,
                n_spikes=int(len(tt)), freqs=f, welch=P)


def rhythm_v2(runs, members, t0_ms, t1_ms, min_seeds=3):
    """runs: lista de (spike_idx, spike_t_ms), uma por semente. Aplica v1 + proeminência + reprodutibilidade."""
    per = []
    for i, t in runs:
        a = rhythm_test(i, t, members, t0_ms, t1_ms, n_surr=200)
        b = welch_peak(i, t, members, t0_ms, t1_ms)
        per.append(dict(v1=a["rhythmic"], prominent=b["prominent"], peak_hz=b["peak_hz"],
                        prominence=b["prominence"]))
    ok = [p for p in per if p["v1"] and p["prominent"] and p["peak_hz"] is not None]
    f0 = float(np.median([p["peak_hz"] for p in ok])) if ok else None
    n_ok = sum(abs(p["peak_hz"] - f0) <= 1.0 for p in ok) if ok else 0
    return dict(rhythmic=bool(n_ok >= min_seeds), n_seeds_ok=int(n_ok), n_seeds=len(runs),
                peak_hz=f0, per_seed=per)
