"""Motoneurônios de perna do BANC → músculo-alvo → junta do NeuroMechFly (Fase 3a).

Músculo-alvo: coluna `peripheral_target_type` dos metadados do BANC v888 (anotada pelos autores do
BANC; 391 MNs de perna, 17 músculos). Perna: `body_part_effector` + `side`.

Músculo → junta e papel: anatomia da perna de Drosophila (Soler et al. 2004, Development 131:6041,
"Coordinated development of muscles and tendons of the Drosophila leg"; Azevedo et al. 2024,
Nature 631:360, que mapeou MNs a músculos no FANC). NON-CONNECTOME: a atribuição a UM grau de
liberdade do NeuroMechFly e o sinal do movimento são escolhas de modelagem, validadas no aparato
(teste de torque imposto) antes de usar em malha fechada.

Juntas (DOFs ativos do NeuroMechFly por perna, flygym_demo get_default_locomotion_dof_order):
  ThC  c_thorax-<leg>_coxa-{yaw,pitch,roll}          tórax–coxa
  CTr  <leg>_coxa-<leg>_trochanterfemur-pitch         coxa–trocanter (flexão/extensão)
  TrF  <leg>_coxa-<leg>_trochanterfemur-roll          rotação do fêmur (redutor)
  FTi  <leg>_trochanterfemur-<leg>_tibia-pitch        fêmur–tíbia
  TiTa <leg>_tibia-<leg>_tarsus1-pitch                tíbia–tarso
"""

from __future__ import annotations

# músculo → (junta, papel). Papel: o lado do par antagonista (usado na antifase e na ativação).
MUSCLE_JOINT = {
    "tergopleural_promotor_muscle": ("ThC", "promotor"),
    "pleural_remotor_and_abductor_muscle": ("ThC", "remotor"),
    "sternal_anterior_rotator_muscle": ("ThC", "rotator_ant"),
    "sternal_posterior_rotator_muscle": ("ThC", "rotator_post"),
    "sternal_adductor_muscle": ("ThC", "adductor"),
    "trochanter_flexor_muscle": ("CTr", "flexor"),
    "accessory_trochanter_flexor_muscle": ("CTr", "flexor"),
    "trochanter_extensor_muscle": ("CTr", "extensor"),
    "tergotrochanter_extensor_muscle": ("CTr", "extensor"),
    "sternotrochanter_extensor_muscle": ("CTr", "extensor"),
    "femur_reductor_muscle": ("TrF", "reductor"),
    "tibia_flexor_muscle": ("FTi", "flexor"),
    "accessory_tibia_flexor_muscle": ("FTi", "flexor"),
    "tibia_extensor_muscle": ("FTi", "extensor"),
    "tarsus_depressor_muscle": ("TiTa", "depressor"),
    "tarsus_levator_muscle": ("TiTa", "levator"),
    # o músculo do tendão longo (LTM) flexiona as garras/tarso a partir do fêmur e da tíbia
    "long_tendon_muscle": ("TiTa", "depressor"),
}
JOINTS = ["ThC", "CTr", "TrF", "FTi", "TiTa"]
LEGS = ["lf", "lm", "lh", "rf", "rm", "rh"]
_LEG = {("front_leg", "left"): "lf", ("middle_leg", "left"): "lm", ("hind_leg", "left"): "lh",
        ("front_leg", "right"): "rf", ("middle_leg", "right"): "rm", ("hind_leg", "right"): "rh"}
# pares antagonistas para a métrica de antifase
ANTAGONISTS = {"CTr": ("flexor", "extensor"), "FTi": ("flexor", "extensor"),
               "TiTa": ("depressor", "levator"), "ThC": ("promotor", "remotor")}


def leg_mn_table(meta):
    """DataFrame dos MNs de perna: banc_888_id, leg, joint, role, muscle (ordem: perna, junta)."""
    x = meta[meta["cell_class"] == "leg_motor_neuron"].copy()
    x["leg"] = [_LEG.get((b, s)) for b, s in zip(x["body_part_effector"], x["side"])]
    x["muscle"] = x["peripheral_target_type"]
    x["joint"] = [MUSCLE_JOINT.get(mu, ("?", "?"))[0] for mu in x["muscle"]]
    x["role"] = [MUSCLE_JOINT.get(mu, ("?", "?"))[1] for mu in x["muscle"]]
    x["leg_i"] = x["leg"].map({k: i for i, k in enumerate(LEGS)})
    x["joint_i"] = x["joint"].map({k: i for i, k in enumerate(JOINTS)}).fillna(len(JOINTS))
    x = x.sort_values(["leg_i", "joint_i", "role", "banc_888_id"])
    return x[["banc_888_id", "leg", "joint", "role", "muscle"]].reset_index(drop=True)
