"""D-105: carregadores do BANC e do híbrido FlyWire + VNC do BANC (dados em data/banc)."""

import numpy as np
import pytest

from terrario import DATA

pytestmark = pytest.mark.skipif(not (DATA / "banc" / "banc_888_meta.feather").exists(),
                                reason="dados do BANC não baixados (ver docs/D105_CONECTOMA.md)")


def test_banc_matches_meta_and_sign_rule():
    from terrario.brain import banc
    c = banc.load("v2")
    m = banc.load_meta()
    assert c.n == len(m) and (c.flyids == m["banc_888_id"].to_numpy()).all()
    # sinal por neurônio pré: todas as arestas de saída com o mesmo sinal (lei de Dale)
    pre = np.repeat(np.arange(c.n), np.diff(c.indptr))
    neg = np.zeros(c.n, bool)
    neg[pre[c.syn_count < 0]] = True
    pos = np.zeros(c.n, bool)
    pos[pre[c.syn_count > 0]] = True
    assert not (neg & pos).any()
    inh = m["neurotransmitter_predicted"].isin(["gaba", "glutamate", "histamine"]).to_numpy()
    has_out = np.diff(c.indptr) > 0
    assert (neg[has_out] == inh[has_out]).all()
    assert (pre != c.indices).all()  # sem autoconexões


def test_hybrid_keeps_flywire_brain_intact():
    from terrario.brain import flywire, hybrid
    fw = flywire.load("783")
    h = hybrid.load()
    assert (h.flyids[:fw.n] == fw.flyids).all()
    # toda aresta do FlyWire continua lá, com o mesmo peso, salvo onde o BANC somou (pontes)
    i = 12345
    a = dict(zip(fw.indices[fw.indptr[i]:fw.indptr[i + 1]], fw.syn_count[fw.indptr[i]:fw.indptr[i + 1]]))
    b = dict(zip(h.indices[h.indptr[i]:h.indptr[i + 1]], h.syn_count[h.indptr[i]:h.indptr[i + 1]]))
    assert all(b.get(k) == v for k, v in a.items())
    assert h.n > fw.n + 20000  # + VNC do BANC
