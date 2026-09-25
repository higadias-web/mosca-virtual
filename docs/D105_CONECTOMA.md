# D-105: qual conectoma usar na mosca adulta (Fase 3) (2026-09-23)

**Decisão (usuário, 2026-09-23): opção (c)**, FlyWire 783 no cérebro + cordão do BANC. D-106
(3a/3b) aprovada com prazo; ver `docs/DECISIONS.md` e `docs/FASE3_PLANO.md`.

Pedido: comparar (a) FlyWire 783 + controlador; (b) BANC inteiro (cérebro + cordão);
(c) FlyWire no cérebro + cordão do BANC por correspondência entre datasets. Para cada uma:
benchmark nesta máquina, revalidação (Fig. 1D no BANC contra o FlyWire), cobertura de revisão
dos circuitos de alimentação e locomoção e impacto da lâmina ausente na visão.

**Resumo:** o BANC **não reproduz a Fig. 1D**. Os GRNs de açúcar do labelo têm 15× menos sinapses
de saída que no FlyWire, e o MN9 fica em 0 Hz em todas as variantes testadas. A opção (c)
mantém a Fig. 1D idêntica à da v783, custa +31 % no cérebro e acrescenta o cordão do BANC,
com 87 % dos DNs pareados. Com os parâmetros do Shiu, porém, estimular DNs de marcha quase não
ativa motoneurônios de perna, em (b) e em (c). **Recomendação: (c), com a Fase 3 dividida em
3a (bolinha) e 3b (terrário), e (a) como saída se a marcha não emergir em 3a.**

## 1. Fontes (confirmadas)

- **BANC**: Bates, Phelps, Kim, Yang et al., "Distributed control circuits across a
  brain-and-cord connectome", *Nature* (2026), doi:10.1038/s41586-026-10735-w; preprint bioRxiv
  2025.07.31.667571. Fêmea adulta, cérebro + cordão (VNC) do mesmo animal. **A lâmina e o gânglio
  ocelar não estão no volume** (dito no artigo, "as in the independent maleCNS project").
  Dados: Harvard Dataverse doi:10.7910/DVN/7WTH1N, **versão 3 (2026-07-01), materialização
  v888**. Código: github.com/htem/BANC-project (commit e31a2e2). Usamos `banc_888_meta.feather` e
  `banc_888_edgelist_simple_v2.feather` (padrão do próprio projeto, `R/startup/banc-edgelist.R`:
  sinapses v2 com tamanho ≥ 5; só neurônios `proofread`/`roughly_proofread`; sem autoconexões).
  Também testamos a edgelist v3 (sinapses v3, tamanho ≥ 10).
- **FlyGM** (arXiv 2602.17997 v3, Jin, Zhu, Zhang e Sui, 2026): usa o **FlyWire v783 só do
  cérebro** (não o BANC) como grafo de uma rede de taxa (message passing), com **descritores
  por neurônio treináveis**, codificador e decodificador MLP. É treinado por imitação de um
  especialista MLP e depois por PPO, para controlar o corpo *flybody*, numa A100. O conectoma
  entra como *prior* de arquitetura, não como modelo mecanístico: os pesos do conectoma são
  fixos, mas a dinâmica é aprendida. Relevância para nós: (1) mostra que um grafo do cérebro
  pode virar controlador de marcha **se** for treinado. Isso violaria a regra do projeto
  (comportamento aprendido de um especialista é comportamento programado) e exige GPU. (2) O
  "SNN baseline" do artigo é um MLP com ativações LIF, sem conectoma, e não diz nada sobre um
  LIF de conectoma. (3) Não resolve o VNC: o decodificador MLP faz o papel do cordão.
  **Não muda a decisão.** É um contraponto útil à opção (a), mostrando o que seria preciso
  para "controlar" a marcha a partir de DNs sem cordão.

## 2. Como cada opção foi montada (código)

| | Arquivo | Neurônios | Arestas | Sinapses |
|---|---|---|---|---|
| (a) FlyWire 783 (Fase 1) | `terrario/brain/flywire.py` | 138.639 | 15,09 M | 54,5 M |
| (b) BANC v888, edgelist v2 | `terrario/brain/banc.py` | 155.858 | 11,40 M | 34,0 M |
| (b') BANC v888, edgelist v3 | idem, `load("v3")` | 155.858 | 13,37 M | 41,8 M |
| (c) FlyWire 783 + VNC do BANC | `terrario/brain/hybrid.py` | 162.197 | 17,70 M | 54,5 M + 9,5 M |

- Sinal no BANC: mesma regra do Shiu (GABA/glutamato → −1, demais → +1, conferida contra a
  v783), com **histamina → −1** (o FlyWire não previa histamina; ~7.400 neurônios, quase todos
  ópticos). NON-CONNECTOME.
- Híbrido: cérebro do FlyWire intacto, mais 22.232 neurônios residentes no VNC do BANC. As
  pontes (DNs, ANs, sensoriais ascendentes/descendentes) são pareadas por (tipo FAFB, lado):
  **DNs 1.148/1.316 (87 %)**, ANs 1.078/1.849 (58 %), sensoriais ascendentes 138/516 (27 %).
  Uma ponte pareada vira um nó só (o do FlyWire). As não pareadas ficam só com a parte do VNC.
  A coluna `fafb_match` sozinha não serve: ela aponta para um representante do tipo, e em ~40 %
  dos casos está do lado oposto. Perdas: 0,84 M sinapses ponte→ponte do BANC ficam de fora
  (a edgelist não diz se estão no cérebro ou no VNC) e há 197 discordâncias de sinal entre
  datasets nas 2.373 pontes. Relatório: `results/d105/hybrid_report.json`.
- **Escala entre datasets** (medida em 25.600 pares de neurônios casados 1-1): o BANC tem
  **~0,5× as sinapses do FlyWire** para os mesmos pares (soma 0,53; mediana da entrada por
  neurônio 0,46). Isso bate com a captura de revisão (§5): pré ~0,8 × pós ~0,2 no BANC, contra
  ~0,96 × ~0,38 no FlyWire.

## 3. Benchmark nesta máquina

Um processo, perfil Desempenho, na tomada. Açúcar a 200 Hz, 1 s simulado em chamadas de 1 ms
(como na co-simulação, D-006), mediana de 3 trials (`experiments/connectome_eval.py bench`,
`results/d105/bench.jsonl`). Workers: RAM livre (16 GB − 3 GB) ÷ RAM de pico por processo.

| Opção | s de parede por trial de 1 s | Spikes/s | RAM de pico por processo | Workers pela RAM | Workers na prática |
|---|---|---|---|---|---|
| (a) FlyWire 783 | **0,68** | 16.219 | 0,66 GB | 19 | 10 (CPU: 2P+8E) |
| (b) BANC v2 | 0,05 (*) | 6.207 | 0,56 GB | 22 | 10 |
| (b') BANC v3 | 0,07 (*) | 6.561 | 0,61 GB | 20 | 10 |
| (b) BANC v2, `w_syn` × 1,9 | **11,6** (**) | — | ~0,6 GB | 22 | 10 |
| (c) FlyWire + VNC BANC | **0,89** (+31 %) | 16.735 | 0,73 GB | 17 | 10 |

(*) Barato porque o sinal **não se propaga**: quase só os GRNs estimulados disparam (§4).
(**) Com o peso compensado, a rede entra em atividade autossustentada (até 16 mil neurônios
ativos) e cada trial custa 11,6 s. Não é um ponto de operação utilizável.

O custo do cérebro é pequeno perto da física (a mosca no terrário custa 3,1–3,4 s/s, ver
`docs/FASE2_RELATORIO.md`). Em malha fechada: (a) ≈ 3,8 s/s e (c) ≈ 4,0 s/s, mais o que o VNC
gastar quando estiver de fato gerando marcha (desconhecido: só medível em 3a). Carga do conectoma
em cache: < 0,1 s em todas.

## 4. Revalidação: Fig. 1D do Shiu no BANC e no híbrido

Mesmo protocolo da Fase 1 (açúcar 10–200 Hz, 30 trials × 1 s, `experiments/connectome_eval.py
fig1d`; comparação em `experiments/compare_d105.py`, `results/d105/fig1d_compare.json`).
Estímulo no BANC: GRNs de açúcar do labelo, lado esquerdo (o mesmo lado dos 21 do Shiu nas
anotações v783): tipos **LB3b + LB3c** ("sugar, Gr64f"), 31 neurônios revisados. Variante `match`:
os 12 neurônios do BANC cujo `fafb_match` é um dos IDs do Shiu. MN9: no BANC, o direito
(720575941623285450, `fafb_match` = MN9 do Shiu).

| Conectoma | MN9 a 40 / 60 / 100 / 150 / 200 Hz | Ativos a 200 Hz | Tipos do top-200 que estão no top-200 da v783 | r (taxa por tipo) |
|---|---|---|---|---|
| v783 (referência, Fase 1) | 3,5 / 28,5 / 62,2 / 79,2 / 89,9 | 446 | 120 tipos | — |
| **(c) FlyWire + VNC BANC** | **3,1 / 27,8 / 61,5 / 79,7 / 90,0** | 508 | **113 de 122** | **0,98** |
| (b) BANC v2, LB3b+c | 0 / 0 / 0 / 0 / 0 | 42 | 8 de 11 | −0,02 |
| (b) BANC v2, `match` | 0 / 0 / 0 / 0 / 0 | 20 | 6 de 9 | −0,08 |
| (b') BANC v3 | 0 / 0 / 0 / 0 / 0 | 57 | 16 de 23 | 0,03 |
| (b) BANC v2, `w_syn` × 1,9 | 0 / 0 / 0 / 0 / 0,5 | 16.146 (autossustentada) | — | — |
| (b') BANC v3, `w_syn` × 1,3 | 0 / 0 / 0 / 0 / 0 | 2.682 | — | — |

**Por quê.** A edgelist do BANC dá aos 31 GRNs de açúcar uma mediana de **21 sinapses de
saída** (v2; 46 na v3), contra **325** para os GRNs do Shiu no FlyWire. As arestas mais fortes
têm 2–13 sinapses, contra 18–23. O filtro de revisão não explica: as saídas para neurônios não
revisados são zero (medido). Os axônios desses GRNs estão pouco reconstruídos ou pouco
anotados com sinapses no BANC (comprimento mediano 136 µm; 9 dos 31 com alguma marca na coluna
`status`, como TRACING_ISSUE, UNROOTED ou IN_NERVE). Não verificamos a causa exata.
O BANC lista regiões-problema (`banc_problem_regions.csv`, entre elas uma "dorsal esophageal
crush"), mas não cruzamos as coordenadas com os GRNs.
Compensar o peso globalmente não resolve: o déficit dos GRNs é de ~15×, o do resto é de ~2×,
e a rede fica instável antes de o MN9 responder.

**No híbrido**, o cérebro é o do FlyWire, e a Fig. 1D fica igual à da v783 (MN9 dentro de ±1 Hz).
Dos 508 ativos a 200 Hz, 67 são do VNC do BANC, alcançados pelos DNs. Os 441 do cérebro
coincidem com os 446 da v783, com 4 a mais e 9 a menos, todos com taxa ≤ 0,17 Hz (1–5 spikes em 30 trials).
A realimentação pelos ANs não altera a resposta alimentar.

## 5. Cobertura de revisão dos circuitos

**Neurônios revisados** (BANC v888, fração dos segmentos anotados como neurônio): DNs 100 %,
ANs 100 %, motoneurônios 100 %, VNC intrínsecos 99,8 %, cérebro central 97 %, sensoriais 94 %.
No FlyWire 783, todos os 138.639 do modelo são revisados.

**Captura de sinapses por neurônio** no BANC v888 (`results/d105/banc_coverage.csv`):
"entrada" = fração das sinapses de entrada vindas de neurônios revisados; "saída" = fração das
de saída que chegam a neurônios revisados (base: `input_connections`/`output_connections` dos
metadados).

| Circuito (BANC) | n | Entrada | Saída | Sinapses úteis de saída (mediana) |
|---|---|---|---|---|
| GRNs de açúcar do labelo (LB3b/c, E) | 31 | 0,77 | 0,23 | **21** (FlyWire: 325) |
| GRNs do labelo (todos) | 285 | 0,78 | 0,23 | 71 |
| GRNs das pernas | 766 | 0,76 | 0,33 | 100 |
| MNs da probóscide / MN9 | 35 / 2 | 0,76 / 0,67 | 0,14 / 0,10 | — |
| DNs (todos) | 1.316 | 0,79 | 0,20 | 776 |
| DNs de marcha (DNp09, DNa01, DNa02, DNg100, DNb05) | 10 | 0,83 | 0,19 | 3.107 |
| MNs de perna | 391 | 0,84 | — | entrada: 2.105 |
| VNC intrínsecos | 12.835 | 0,83 | 0,27 | 318 |
| ANs | 1.849 | 0,82 | 0,20 | 643 |
| Cordotonais / placas de pelos / campaniformes (propriocepção) | 2.023 / 320 / 576 | 0,68–0,76 | 0,22–0,26 | 80 / 357 / 166 |

Referências por neurópilo, dos próprios dados de captura do projeto BANC
(`third_party/BANC-project/data/synapse_capture/`): FlyWire 783 na GNG = **96 % pré / 38 % pós**
revisados. BANC v610 na GNG = 70–75 % pré / 18–21 % pós. MANC nos neurópilos de perna =
86–90 % pré / 38–48 % pós. Leitura: **alimentação** (GNG, GRNs, MN9) está bem mais completa no
FlyWire. **Locomoção**: o VNC do BANC tem boa captura pré-sináptica (0,83–0,84), como o MANC,
e metade da pós-sináptica. O FlyWire não tem VNC. Os 391 MNs de perna do BANC vêm com o músculo-alvo
anotado (`peripheral_target_type`, p. ex. `tibia_flexor_muscle`), o que ajuda a montar o
mapeamento MN → junta em 3a.

## 6. Lâmina ausente e visão

| | R1–R6 | Lai | L1–L5 | R7 / R8 | Via de movimento (R1–6 → L1/L2 → T4/T5) |
|---|---|---|---|---|---|
| FlyWire 783 | 8.452 | 311 | 1.378–1.699 por tipo | 1.342 / 1.324 | presente |
| BANC v888 | **0** | **0** | 783–1.683 por tipo (só a parte na medula) | 924 / 914 | **cortada na entrada**: L1–L3 existem, mas sem sinapses de fotorreceptores |

- (a) e (c): o cérebro é o do FlyWire, então a visão fica como está (omatídeos do FlyGym →
  R1–R6/R7/R8, com mapeamento retinotópico a fazer).
- (b): sem R1–R6 e sem sinapses na lâmina, a entrada visual teria de ser injetada **direto nos
  L1–L3** (e nos R7/R8, que existem em menor número), com um filtro de "lâmina virtual"
  inteiramente NON-CONNECTOME. A visão está desligada por padrão (SPEC, consequência 4), então
  isso afeta só o perfil `completo`.

## 7. Sonda de locomoção (exploratória)

Pergunta: com o modelo do Shiu, sem propriocepção e sem corpo, o comando de um DN de marcha chega
aos motoneurônios de perna? Poisson no par bilateral de DNp09 (marcha para a frente, "P9";
Bidaye et al. 2020, *Neuron*) ou de DNa02 (virada; Rayshubskiy et al., *eLife* 2025), 50–200 Hz, 1 s (`connectome_eval.py probe`,
`results/d105/probe_*.json`).

| Conectoma | MNs de perna ativos (de 391) a 200 Hz | Taxa média | Ritmo |
|---|---|---|---|
| (b) BANC | DNp09: 5 · DNa02: 6 | ≤ 0,2 Hz | nenhum |
| (c) híbrido (VNC bruto) | DNp09: 4 · DNa02: 7 | ≤ 0,2 Hz | nenhum |
| (c) híbrido, VNC × 2 | DNp09: 49 · DNa02: 63 | 0,4–2,4 Hz | nenhum (tônico) |

Esperado: marcha real depende de populações de DNs, excitabilidade do VNC e da realimentação
proprioceptiva. **Nenhum conectoma entrega marcha "de graça" com o LIF do Shiu.** Essa é a
pergunta de pesquisa da Fase 3a, qualquer que seja o dataset do VNC.

## 8. Opções

| | (a) FlyWire 783 + controlador | (b) BANC inteiro | (c) FlyWire (cérebro) + VNC do BANC |
|---|---|---|---|
| Alimentação (Fig. 1D) | **validada** (Fase 1) | **falha** (MN9 = 0; GRNs com 15× menos sinapses) | **validada** (igual à v783) |
| Marcha | controlador FlyGym (NON-CONNECTOME), garantida | VNC real, não demonstrada | VNC real, não demonstrada; (a) como saída |
| DN → MN | mapeamento escolhido à mão | mesmo animal, 100 % | 87 % dos DNs pareados entre animais |
| Visão | intacta | sem lâmina (lâmina virtual NON-CONNECTOME) | intacta |
| Propriocepção pelo conectoma | não | sim (cordotonais etc. no VNC) | sim (do BANC) |
| Custo do cérebro | 0,68 s/s | 0,05 s/s bruto (não propaga); instável com compensação | 0,89 s/s |
| NON-CONNECTOME a mais | controlador + mapeamento DN → comando | recalibração de pesos (não resolveu), lâmina virtual | costura entre animais, pareamento dentro de tipos, escala do VNC |
| Risco | baixo | **alto** (a validação central falha hoje) | médio (costura; marcha incerta) |

**Recomendação: (c).** Ela preserva o que foi validado na Fase 1 e traz o cordão do BANC, onde
ele é melhor: DNs, MNs com músculo-alvo, VNC intrínseco e propriocepção. Nada se perde em
relação a (a): se a marcha pelo VNC não emergir em 3a, a Fase 3b usa o controlador de (a) com o
mesmo cérebro (é a D-101, já aprovada). (b) fica registrada para reavaliação: se uma
materialização nova do BANC corrigir os GRNs, `connectome_eval.py fig1d` + `compare_d105.py`
refazem a revalidação em ~5 min.

## 9. Proposta: dividir a Fase 3 (⚠️ D-106)

Como a opção recomendada usa o cordão do BANC, proponho a divisão pedida:

**3a) Mosca presa sobre bolinha virtual: validar a marcha gerada pelo cordão.**
- Aparato (NON-CONNECTOME): `TetheredWorld` do FlyGym 2.1 (tórax fixo como corpo *mocap*) +
  bola esférica livre para girar, com massa e inércia de bola de espuma sustentada por ar
  (valores a tirar da literatura). O FlyGym 2.1 não traz a bola simulada (o tutorial 5a só
  reproduz cinemática gravada), então ela será nossa.
- Saída motora: 391 MNs de perna → ativação dos músculos-alvo anotados → torque nas juntas
  do NeuroMechFly (mapeamento NON-CONNECTOME, documentado por músculo).
- Entrada proprioceptiva: cordotonais, campaniformes e placas de pelos do BANC ← ângulos,
  velocidades e cargas das juntas (transdução NON-CONNECTOME).
- Estímulo: DNs de marcha (DNp09; DNa01/DNa02 para virada), como na optogenética.
- Critérios (a fixar com a literatura antes de começar): alternância rítmica flexor/extensor por
  perna; coordenação entre pernas (trípode/tetrápode); rotação da bola para a frente com DNp09 e
  virada lateralizada com DNa02; ablação (silenciar os DNs ou a propriocepção muda ou elimina a
  marcha); custo em s/s.
- **Prazo e saída:** se os critérios não forem atingidos no prazo combinado, 3b segue com (a).
  O VNC continua como experimento paralelo.

**3b) Mosca livre no terrário.** Malha fechada com os sensores da Fase 2 → neurônios sensoriais
anotados na v783 (ORNs, GRNs de perna e labelo, mecanossensores; IDs tirados das anotações, e
não herdados da lista v630); DNs → VNC (se 3a passou) ou → controlador (a); MN9 → probóscide
(exige juntas na probóscide). Critérios da SPEC: marcha estável no terreno; mudança de
comportamento com estímulo olfativo/gustativo; ablação.

## 10. Limitações desta avaliação
- 3 trials por medição de custo; a Fig. 1D usa 30 trials por condição, como na Fase 1.
- A escala `w_syn` só foi testada em 1,9 (v2) e 1,3 (v3); outras não mudariam o diagnóstico dos GRNs.
- O pareamento do híbrido é por tipo. Dentro de tipos com vários membros, a atribuição é
  arbitrária, e as sinapses ponte→ponte do BANC ficaram de fora.
- A sonda de locomoção é de 1 s, sem corpo: mostra a ausência de propagação, não prova que a
  marcha é impossível.
