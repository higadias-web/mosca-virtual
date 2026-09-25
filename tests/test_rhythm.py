"""Controles da métrica de ritmo (Fase 3a): positivo sintético e negativo."""

import numpy as np

from terrario.vnc.rhythm import rhythm_test


def _trains(mod_hz, n=30, T=1500.0, rate=20.0, depth=0.9, seed=1):
    rng = np.random.default_rng(seed)
    dt = 0.1
    t = np.arange(0, T, dt)
    lam = rate * (1 + depth * np.sin(2 * np.pi * mod_hz * t / 1000)) if mod_hz else np.full_like(t, rate)
    ii, tt = [], []
    for k in range(n):
        s = t[rng.random(len(t)) < lam * dt / 1000]
        ii += [k] * len(s)
        tt += list(s)
    return np.array(ii), np.array(tt)


def test_positive_control_8hz():
    i, t = _trains(8.0)
    r = rhythm_test(i, t, np.arange(30), 0, 1500)
    assert r["rhythmic"] and abs(r["peak_hz"] - 8.0) < 1.0


def test_negative_control_flat():
    i, t = _trains(0.0)
    assert not rhythm_test(i, t, np.arange(30), 0, 1500)["rhythmic"]


def test_negative_control_independent_periodic():
    """Neurônios periódicos mas com fases aleatórias: não é ritmo populacional."""
    rng = np.random.default_rng(3)
    ii, tt = [], []
    for k in range(30):
        ph = rng.uniform(0, 125)
        s = np.arange(ph, 1500, 125.0)  # 8 Hz, fase própria
        ii += [k] * len(s)
        tt += list(s)
    assert not rhythm_test(np.array(ii), np.array(tt), np.arange(30), 0, 1500)["rhythmic"]


def _shared_broadband(n=30, T=1500.0, rate=20.0, seed=5):
    """Todos os neurônios modulados pela MESMA taxa aleatória (Ornstein-Uhlenbeck, τ = 20 ms)."""
    rng = np.random.default_rng(seed)
    dt = 0.1
    t = np.arange(0, T, dt)
    x = np.zeros(len(t))
    for k in range(1, len(t)):
        x[k] = x[k - 1] - x[k - 1] * dt / 20.0 + np.sqrt(2 * dt / 20.0) * rng.standard_normal()
    lam = rate * np.clip(1 + 0.8 * x, 0, None)
    ii, tt = [], []
    for k in range(n):
        s = t[rng.random(len(t)) < lam * dt / 1000]
        ii += [k] * len(s)
        tt += list(s)
    return np.array(ii), np.array(tt)


def test_v1_false_positive_shared_broadband():
    """Documenta a falha da v1: entrada comum sem periodicidade passa no teste de surrogados."""
    i, t = _shared_broadband()
    assert rhythm_test(i, t, np.arange(30), 0, 1500)["rhythmic"]


def test_v2_rejects_shared_broadband_and_keeps_8hz():
    from terrario.vnc.rhythm import rhythm_v2
    broad = [_shared_broadband(T=3250.0, seed=s) for s in range(5)]
    assert not rhythm_v2(broad, np.arange(30), 250, 3250)["rhythmic"]
    for fz in (4.0, 8.0, 16.0):
        osc = [_trains(fz, T=3250.0, seed=s) for s in range(5)]
        r = rhythm_v2(osc, np.arange(30), 250, 3250)
        assert r["rhythmic"] and abs(r["peak_hz"] - fz) <= 1.0, (fz, r["peak_hz"])
