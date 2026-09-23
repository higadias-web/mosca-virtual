"""Escolha do conectoma pelo nome da versão (os três candidatos da D-105).

  "630", "783"      FlyWire (só o cérebro), formato do Shiu              → flywire.load
  "banc888"         BANC v888, cérebro + cordão, edgelist v2 (padrão)     → banc.load("v2")
  "banc888v3"       idem, edgelist v3 (sinapses v3, tamanho >= 10)        → banc.load("v3")
  "fw783+bancvnc"   FlyWire 783 no cérebro + cordão do BANC por correspondência → hybrid.load
"""

from __future__ import annotations

from terrario.brain.flywire import FlyWireConnectome


def load(version: str) -> FlyWireConnectome:
    if version in ("630", "783"):
        from terrario.brain import flywire
        return flywire.load(version)
    if version == "banc888":
        from terrario.brain import banc
        return banc.load("v2")
    if version == "banc888v3":
        from terrario.brain import banc
        return banc.load("v3")
    if version == "fw783+bancvnc":
        from terrario.brain import hybrid
        return hybrid.load()
    raise ValueError(f"conectoma desconhecido: {version}")
