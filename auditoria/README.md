# Auditoria do Terrário Virtual (2026-09-25)

Teste feito na auditoria, com o motor do próprio projeto (`terrario/brain/lif.py`, ShiuLIF, FlyWire 783,
parâmetros da Fase 1). Rodar da raiz do projeto `terrario-virtual`.

**Pergunta:** sem odor, com só uma atividade espontânea baixa em todos os 2.275 ORNs, o modelo entra no
estado alto e persistente da Etapa C?

**Taxas:** varredura de 0,5 a 5 Hz, sem fonte. É um teste de sensibilidade, não um valor fisiológico.

**Sanidade:** vin5, semente 1000 → 474.799 spikes, idêntico ao `rates_runs.csv` da Etapa B.

| Condição (sem odor) | Neurônios ativos | PN de DM1 (mediana) | KCs ativas | Média dos ALPNs |
|---|---|---|---|---|
| Referência: vin5 (odor) | 6,1 % | 252 Hz | 65 % | 83 Hz |
| ORNs a 0,5 Hz | 6,6 % | 209–218 Hz | 65 % | 78–80 Hz |
| ORNs a 1 Hz | 6,9 % | 222–223 Hz | 65 % | 81–82 Hz |
| ORNs a 2 Hz | 7,3 % | 223–227 Hz | 65 % | 82–83 Hz |
| ORNs a 5 Hz | 7,5 % | 227–228 Hz | 66 % | 84 Hz |

3 sementes por taxa (1000–1002), 1 s cada. Dados brutos em `teste_espontanea_resultado.jsonl`.

**Conclusão:** qualquer entrada espontânea nos ORNs, a partir de 0,5 Hz, liga o mesmo estado que o odor.
O controle "sem odor = 0 spikes" das Etapas B a D só existe porque o modelo tem basal 0.

## Teste 2: DNg100 e DNb08 isolados no cordão (Fase 3a)

Pugliese et al. 2025 (bioRxiv 10.1101/2025.09.12.675944; código github.com/smpuglie/Pugliese_cpg_2025)
obtêm ritmo nos MNs de perna estimulando **só o DNg100** (e o DNb08), num **modelo de taxa** (tanh,
τ ≈ 20 ms, parâmetros sorteados por réplica), em malha aberta e sem propriocepção. No Terrário Virtual, esses
dois DNs só tinham sido estimulados dentro de G3 (20 DNs) e G4 (159 DNs).

**Protocolo:** o mesmo da Sessão 1 v2 (`experiments/phase3a_s1.py:main_v2`): híbrido FlyWire 783 + BANC, sinais
`verified`, 3,25 s, 5 sementes, métrica v2 congelada.

| DN estimulado | Taxa | MNs de perna ativos (de 391) | Taxa média dos MNs | Pernas rítmicas (v2) | Maior proeminência (limiar 5, precisa de 3/5 sementes) |
|---|---|---|---|---|---|
| DNg100 (2) | 100 Hz | 54 | 1,1 Hz | **0** | 5,0 (1 semente, LF, 9 Hz) |
| DNg100 (2) | 200 Hz | 67 | 2,3 Hz | **0** | 4,0 |
| DNb08 (4) | 100 Hz | 33 | 0,4 Hz | **0** | 4,9 |
| DNb08 (4) | 200 Hz | 40 | 0,8 Hz | **0** | 6,4 (1 semente, LH) |

**Conclusão:** os dois DNs que produzem ritmo no modelo de taxa de Pugliese não produzem ritmo no LIF do
Shiu com o mesmo tipo de conectoma. O negativo da Fase 3a em malha aberta aponta para a classe do modelo
(H4), não para o cordão.

## Medição 3: diferença de odor entre as antenas na Fase 2

Fonte: `runs/phase2/walk_soil_fruit_landscape.parquet` (travessia de 2,5 s da Fase 2, 500 amostras a 200 Hz).
Diferença relativa |E − D| / média, por canal:

| Canal | Mediana | p90 | Máximo |
|---|---|---|---|
| Fruta | 1,05 % | 1,33 % | 1,59 % |
| Fermento | 1,04 % | 2,61 % | 3,16 % |
| Bactérias | 0,80 % | 1,05 % | 1,54 % |

Campo de odor: difusão 2D em ar parado (D = 10 mm²/s, k = 0,05 /s), sem vento nem intermitência.
Em moscas que andam, a navegação olfativa depende de vento e de encontros intermitentes com o odor
(Álvarez-Salvado et al. 2018, eLife 7:e37815; Demir et al. 2020, eLife 9:e57524). O NeuroMechFly v2
já simula uma pluma de odor.
