"""Testes do motor LIF (terrario/brain/lif.py) contra o Brian2 e entre modos."""

import numpy as np
import pytest

from terrario.brain.flywire import FlyWireConnectome, load
from terrario.brain.lif import SHIU_PARAMS, ShiuLIF

SUGAR_630 = [  # figures.ipynb (Shiu), Fig. 1D: GRNs de açúcar do lábelo direito
    720575940624963786, 720575940630233916, 720575940637568838, 720575940638202345,
    720575940617000768, 720575940630797113, 720575940632889389, 720575940621754367,
    720575940621502051, 720575940640649691, 720575940639332736, 720575940616885538,
    720575940639198653, 720575940620900446, 720575940617937543, 720575940632425919,
    720575940633143833, 720575940612670570, 720575940628853239, 720575940629176663,
    720575940611875570,
]


def _random_conn(n=120, p=0.08, seed=1):
    rng = np.random.default_rng(seed)
    pre, post = np.nonzero(rng.random((n, n)) < p)
    keep = pre != post
    pre, post = pre[keep], post[keep]
    # contagens de sinapses com sinal (~25 % inibitórias), como 'Excitatory x Connectivity'
    cnt = rng.integers(1, 40, size=pre.size) * np.where(rng.random(pre.size) < 0.25, -1, 1)
    import scipy.sparse as sp
    W = sp.csr_matrix((cnt.astype(float), (pre, post)), shape=(n, n))
    return FlyWireConnectome("test", np.arange(n, dtype=np.int64), W.indptr.astype(np.int64),
                             W.indices.astype(np.int32), W.data.astype(float)), (pre, post, cnt)


def _brian_spikes(n, pre, post, cnt, exc, silence, t_ms):
    """Mesma construção de model.py:create_model/poi/silence, no alvo numpy do Brian2."""
    b2 = pytest.importorskip("brian2")
    from brian2 import NeuronGroup, Synapses, PoissonInput, SpikeMonitor, Network, ms, mV, Hz
    from textwrap import dedent
    b2.prefs.codegen.target = "numpy"
    p = {k: v for k, v in SHIU_PARAMS.items()}
    ns = dict(v_0=p["v_0"] * mV, v_rst=p["v_rst"] * mV, v_th=p["v_th"] * mV,
              t_mbr=p["t_mbr"] * ms, tau=p["tau"] * ms)
    eqs = dedent('''
        dv/dt = (v_0 - v + g) / t_mbr : volt (unless refractory)
        dg/dt = -g / tau               : volt (unless refractory)
        rfc                            : second
        ''')
    neu = NeuronGroup(n, eqs, method="linear", threshold="v > v_th",
                      reset="v = v_rst; w = 0; g = 0 * mV", refractory="rfc", namespace=ns)
    neu.v = p["v_0"] * mV
    neu.g = 0
    neu.rfc = p["t_rfc"] * ms
    syn = Synapses(neu, neu, "w : volt", on_pre="g += w", delay=p["t_dly"] * ms)
    syn.connect(i=pre, j=post)
    syn.w = cnt * p["w_syn"] * mV
    pois = []
    for i in exc:  # taxa = 1/dt => um evento por passo (determinístico)
        pois.append(PoissonInput(neu[i], "v", N=1, rate=10000 * Hz,
                                 weight=p["w_syn"] * p["f_poi"] * mV))
        neu[i].rfc = 0 * ms
    for i in silence:
        syn.w[f"{i} == i"] = 0 * mV
    mon = SpikeMonitor(neu)
    Network(neu, syn, mon, *pois).run(t_ms * ms)
    return sorted(zip(np.round(np.asarray(mon.t / ms) / 0.1).astype(int).tolist(),
                      np.asarray(mon.i).tolist()))


def _our_spikes(conn, exc, silence, t_ms, dense=False):
    m = ShiuLIF(conn, seed=0, dense=dense)
    m.set_poisson(exc, 10000.0)
    if silence:
        m.silence(silence)
    i, s = m.run(int(round(t_ms / 0.1)))
    return sorted(zip(s.tolist(), i.tolist()))


@pytest.mark.parametrize("silence", [[], [3, 7, 11]])
def test_matches_brian2_deterministic(silence):
    conn, (pre, post, cnt) = _random_conn()
    exc = [0, 1, 2, 5, 8]
    ours = _our_spikes(conn, exc, silence, 60.0)
    ref = _brian_spikes(conn.n, pre, post, cnt, exc, silence, 60.0)
    assert len(ref) > 50, "o teste precisa de atividade na rede"
    assert ours == ref


@pytest.fixture(scope="module")
def conn783():
    return load("783")


def test_active_equals_dense(conn783):
    exc = conn783.idx([f for f in SUGAR_630 if f in conn783.flyid2i])
    out = []
    for dense in (False, True):
        m = ShiuLIF(conn783, seed=3, dense=dense)
        m.set_poisson(exc, 150.0)
        i, st = m.run(2000)
        out.append(sorted(zip(st.tolist(), i.tolist())))  # ordem dentro do passo não importa
    assert out[0] == out[1]
    assert len(out[0]) > 1000


def test_checkpoint_roundtrip(conn783):
    exc = conn783.idx([f for f in SUGAR_630 if f in conn783.flyid2i])
    m = ShiuLIF(conn783, seed=5)
    m.set_poisson(exc, 150.0)
    m.run(500)
    st = m.get_state()
    a = m.run(500)
    m.set_state(st)
    b = m.run(500)
    assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1])


def test_silence_blocks_output(conn783):
    exc = conn783.idx([f for f in SUGAR_630 if f in conn783.flyid2i])
    m = ShiuLIF(conn783, seed=0)
    m.set_poisson(exc, 150.0)
    m.silence(exc)  # estimulados disparam, mas não transmitem nada
    i, _ = m.run(2000)
    assert set(np.unique(i)) <= set(exc.tolist())
