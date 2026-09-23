"""Opção (c) da D-105: cérebro do FlyWire 783 + cordão nervoso ventral (VNC) do BANC v888.

Os dois datasets vêm de moscas diferentes, então a ponte é feita por correspondência de
neurônios que atravessam o pescoço (DNs e ANs), por tipo celular e lado (`match_bridges`).

Nós do modelo:
  1. todos os neurônios do FlyWire 783 (mesmos índices de flywire.load("783"));
  2. neurônios do BANC residentes no VNC (region == ventral_nerve_cord) que não são ponte;
  3. neurônios-ponte do BANC SEM par no FlyWire (ficam só com a parte do VNC).
Ponte = super_class descending, ascending, sensory_ascending, sensory_descending,
ascending_visceral_circulatory. Uma ponte pareada vira um único nó: o do FlyWire,
que recebe também as arestas do VNC que o BANC atribui ao seu par.

Arestas:
  - todas as do FlyWire 783 (cérebro), com o sinal do Shiu;
  - do BANC, as que têm pelo menos uma ponta residente no VNC (grupo 2). Essas sinapses estão
    necessariamente no VNC ou nos nervos.
  - NÃO entram as arestas ponte→ponte do BANC (DN→AN, AN→DN, DN→DN, AN→AN): a edgelist simples
    não diz se a sinapse está no cérebro (já coberta pelo FlyWire) ou no VNC. Quantificado no
    relatório de `build()`. Resolver exigiria synapse_neuropil_lookup_v2.parquet (2,2 GB).
  - arestas do BANC entre o VNC e neurônios só do cérebro do BANC (sem ponte) são descartadas.

NON-CONNECTOME: a própria costura (dois animais), o pareamento dentro de tipos com vários
membros e `vnc_scale` (ganho das contagens do BANC; 1 = contagem bruta). Sinal de uma ponte
pareada: o do FlyWire (lei de Dale: um neurônio, um transmissor), nas arestas das duas origens.
"""

from __future__ import annotations

import numpy as np

from terrario import DATA
from terrario.brain import banc, flywire
from terrario.brain.flywire import FlyWireConnectome

BRIDGE = {"descending", "ascending", "sensory_ascending", "sensory_descending",
          "ascending_visceral_circulatory"}


def build(vnc_scale: float = 1.0, sign_mode: str = "predicted"):
    """Monta o híbrido. Retorna (conectoma, relatório dict)."""
    import scipy.sparse as sp

    fw = flywire.load("783")
    bc = banc.load("v2")
    m = banc.load_meta()
    assert (m["banc_888_id"].to_numpy() == bc.flyids).all()
    sc = m["super_class"].astype(str).to_numpy()
    is_bridge = np.isin(sc, list(BRIDGE))
    is_vnc = (m["region"].astype(str).to_numpy() == "ventral_nerve_cord") & ~is_bridge

    b2fw = match_bridges(m[is_bridge], fw)

    # índices do híbrido para cada neurônio do BANC (-1 = fora do modelo)
    hmap = np.full(bc.n, -1, dtype=np.int64)
    nxt = fw.n
    new_ids = []
    for i in range(bc.n):
        bid = int(bc.flyids[i])
        if is_bridge[i] and bid in b2fw:
            hmap[i] = b2fw[bid]
        elif is_vnc[i] or is_bridge[i]:
            hmap[i] = nxt
            new_ids.append(bid)
            nxt += 1
    n = nxt

    # arestas do BANC com pelo menos uma ponta residente no VNC
    pre = np.repeat(np.arange(bc.n), np.diff(bc.indptr))
    post = bc.indices.astype(np.int64)
    w = np.abs(bc.syn_count)
    keep = is_vnc[pre] | is_vnc[post]
    both_in = keep & (hmap[pre] >= 0) & (hmap[post] >= 0)
    bb = is_bridge[pre] & is_bridge[post]
    # sinal: o do neurônio pré no modelo (FlyWire para pontes casadas, BANC nos demais)
    fw_sign = np.ones(fw.n)
    neg = np.zeros(fw.n, dtype=bool)
    fpre = np.repeat(np.arange(fw.n), np.diff(fw.indptr))
    neg[fpre[fw.syn_count < 0]] = True
    fw_sign[neg] = -1
    # sinal dos neurônios do BANC pelo modo da H6 (banc.neuron_signs); "predicted" = load()
    b_sign = banc.neuron_signs(m, sign_mode)[pre].astype(float)
    hp, hq = hmap[pre[both_in]], hmap[post[both_in]]
    sgn = np.where(hp < fw.n, fw_sign[np.minimum(hp, fw.n - 1)], b_sign[both_in])
    wb = w[both_in] * sgn * vnc_scale

    Wf = sp.csr_matrix((fw.syn_count, fw.indices, fw.indptr), shape=(fw.n, fw.n))
    Wf.resize((n, n))
    Wb = sp.csr_matrix((wb, (hp, hq)), shape=(n, n))
    W = (Wf + Wb).tocsr()
    W.sum_duplicates()
    W.eliminate_zeros()

    # discordância de sinal entre datasets nas pontes casadas
    bidx = np.array([bc.idx([b])[0] for b in b2fw])
    disagree = int((b_sign_by_neuron(bc)[bidx] != fw_sign[list(b2fw.values())]).sum()) \
        if len(bidx) else 0
    rep = dict(
        n_fw=fw.n, n_vnc=int(is_vnc.sum()), n_bridge_banc=int(is_bridge.sum()),
        n_bridge_matched=len(b2fw), n_bridge_unmatched=int(is_bridge.sum() - len(b2fw)),
        n_total=n, edges=int(W.nnz),
        banc_syn_used=float(w[both_in].sum()),
        banc_syn_bridge_bridge_skipped=float(w[bb & ~keep].sum()),
        banc_syn_vnc_to_brainonly_dropped=float(w[keep & ~both_in].sum()),
        bridge_sign_disagreements=disagree, vnc_scale=vnc_scale, sign_mode=sign_mode,
        matched_by_class={k: int(v) for k, v in
                          m.loc[m["banc_888_id"].isin(list(b2fw)), "super_class"]
                          .value_counts().items()},
        bridge_by_class={k: int(v) for k, v in m.loc[is_bridge, "super_class"]
                         .value_counts().items()},
    )
    ids = np.concatenate([fw.flyids, np.array(new_ids, dtype=np.int64)])
    assert len(np.unique(ids)) == len(ids), "IDs do FlyWire e do BANC colidem"
    c = FlyWireConnectome("fw783+bancvnc", ids, W.indptr.astype(np.int64),
                          W.indices.astype(np.int32), W.data.astype(np.float64))
    return c, rep


def match_bridges(mb, fw: FlyWireConnectome) -> dict[int, int]:
    """Pareia pontes do BANC com neurônios do FlyWire 783 por (tipo FAFB, lado).

    A coluna `fafb_match` sozinha não serve: ela aponta para *um* neurônio do tipo, às vezes o
    mesmo para vários do BANC, e em ~40 % dos casos do lado oposto (medido). Então, para cada
    grupo (fafb_cell_type do BANC == cell_type do FlyWire, mesmo lado), pareamos min(nB, nF)
    neurônios: primeiro os pares cujo `fafb_match` cai num membro livre do grupo; o resto em
    ordem de ID (arbitrário dentro do tipo: NON-CONNECTOME, ver docs/NON_CONNECTOME.md).
    Tipos celulares e lados do FlyWire: flywire_annotations, Supplemental_file1 (v783).
    """
    import pandas as pd

    from terrario import THIRD_PARTY

    a = pd.read_csv(THIRD_PARTY / "flywire_annotations/supplemental_files/"
                    "Supplemental_file1_neuron_annotations.tsv", sep="\t", low_memory=False,
                    usecols=["root_id", "side", "super_class", "cell_type"])
    a = a[a["super_class"].isin(["descending", "ascending", "sensory_ascending", "sensory"])
          & a["root_id"].isin(fw.flyids)]
    fgroups = {k: sorted(g["root_id"].tolist()) for k, g in a.groupby(["cell_type", "side"])}
    out: dict[int, int] = {}
    fwi = fw.flyid2i
    for key, g in mb.dropna(subset=["fafb_cell_type"]).groupby(["fafb_cell_type", "side"]):
        free = list(fgroups.get(key, []))
        if not free:
            continue
        rest = []
        for bid, fm in zip(g["banc_888_id"].tolist(), g["fafb_match"].tolist()):
            f = int(fm) if isinstance(fm, str) and fm.isdigit() else None
            if f is not None and f in free:
                out[bid] = fwi[f]
                free.remove(f)
            else:
                rest.append(bid)
        for bid, f in zip(sorted(rest), free):
            out[bid] = fwi[f]
    return out


def banc_index(c: FlyWireConnectome, meta=None):
    """Função ids_do_BANC → índices no híbrido `c` (−1 se o neurônio não está no modelo).
    Pontes pareadas vão para o nó do FlyWire (match_bridges); as demais usam o próprio ID."""
    m = banc.load_meta() if meta is None else meta
    b2fw = match_bridges(m[m["super_class"].isin(BRIDGE)], flywire.load("783"))
    f2i = c.flyid2i

    def f(ids):
        return [b2fw.get(int(b), f2i.get(int(b), -1)) for b in ids]
    return f


def b_sign_by_neuron(bc: FlyWireConnectome) -> np.ndarray:
    """Sinal de cada neurônio do BANC (pelo sinal das suas arestas de saída; +1 se não tem)."""
    s = np.ones(bc.n)
    pre = np.repeat(np.arange(bc.n), np.diff(bc.indptr))
    s[pre[bc.syn_count < 0]] = -1
    return s


def load(vnc_scale: float = 1.0, cache: bool = True, sign_mode: str = "predicted") -> FlyWireConnectome:
    tag = "" if sign_mode == "predicted" else f"_{sign_mode}"
    path = DATA / "cache" / f"fw783_bancvnc_s{vnc_scale:g}{tag}.npz"
    if cache and path.exists():
        z = np.load(path)
        return FlyWireConnectome("fw783+bancvnc", z["flyids"], z["indptr"], z["indices"],
                                 z["syn_count"])
    c, rep = build(vnc_scale, sign_mode)
    if cache:
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(path, flyids=c.flyids, indptr=c.indptr, indices=c.indices, syn_count=c.syn_count)
    return c
