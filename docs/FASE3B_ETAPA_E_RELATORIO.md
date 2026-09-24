# Fase 3b, Etapa E: sinais, fontes sobre eLNs, comparação com Olsen 2010 e trabalhos de 2026 (relatório curto)

**Data:** 2026-09-24. **Só análise e leitura: nenhuma simulação nova, o modelo oficial não mudou e não há
proposta de correção.** Dados: `results/phase3b/signs_AL.json`, `olsen_compare.json`. Scripts:
`experiments/phase3b_signs.py`, `phase3b_olsen_compare.py`.

## 1. Como o modelo define o sinal de cada neurônio
- **Campo:** a coluna `Excitatory` (±1) de `Connectivity_783.parquet` do repositório do Shiu. O peso é
  `Excitatory × Connectivity` (`third_party/Drosophila_brain_model/model.py:183`; `terrario/brain/flywire.py`).
  O sinal é **por neurônio**: nenhum dos 138.005 neurônios pré-sinápticos tem sinal misto.
- **Regra**, em Shiu et al. 2024 (*Nature* 634:210–219, PMC11446845, Métodos, lido):
  - "Neurotransmitter predictions are from ref. 3 [Eckstein et al.] … predicted for each synapse";
  - "we used a cleft score cutoff of 50 … if greater than half of all the presynaptic sites across the entire
    neuron are predicted to be inhibitory (GABA or Glut), we assigned this neuron as inhibitory";
  - "Neurons predicted to be dopaminergic, octopaminergic or serotonergic are assigned to the excitatory
    category";
  - "Gap junctions cannot be identified … so we ignore their possibility. We do not account for neuropeptides
    or neuromodulation."
- **Portanto:** o sinal vem da **previsão por sinapse** (Eckstein et al.), agregada por neurônio. **Não** usa a
  anotação conhecida (`known_nt`) nem o `top_nt` da anotação atual. Comparado com o `top_nt` da versão ≥ 3.1.0
  das anotações, há ~8 mil divergências no cérebro inteiro (versões diferentes de previsão).

**Os 18 LNs excitatórios no modelo com `known_nt` GABA, glutamato ou octopamina:**
- **Nenhum deles está entre os 148 eLNs.** A definição da ablação A os excluiu de propósito.
- Composição: 12 lLN2P_b ("gaba, MIP; acetylcholine-negative"), 2 il3LN6 (GABA), 2 v2LN36 (glutamato) e
  2 OA-VUMa5 (octopamina).
- Disparam a 140–295 Hz no estado persistente.
- **Fração da excitação que chega aos 148 eLNs vinda deles** (spikes salvos, 900–1000 ms, vinagre a 5 %):
  **3,7 % no intacto e 5,5 % na ablação A**. A maior parte vem dos próprios eLNs (60 % no intacto, 90 % na A).

**Outras divergências no lobo antenal** (sinal do modelo × anotação):

| Classe | n | Modelo exc. × `known_nt` inib. | Modelo inib. × `known_nt` exc. | Modelo exc. × `top_nt` GABA/Glu | Modelo inib. × `top_nt` exc. |
|---|---|---|---|---|---|
| LNs (ALLN) | 429 | 16 (+2 octopamina) | 0 | 40 (lLN2P_b 12, v2LN3A1_b 5, lLN2F_a 4, lLN2X04 4, …) | 8 |
| PNs (ALPN) | 685 | 0 | 0 | 0 | 0 |
| ORNs | 2.269 | 0 | 1 (ORN_V) | 3 | 0 |

**Correção de um erro meu, sem efeito em resultados:**
- Uma primeira contagem acusou 258 PNs "excitatórios com GABA conhecido". Era um defeito do meu filtro: o
  rótulo é "acetylcholine; gaba-negative".
- Corrigi a leitura do campo (marcadores "-negative" = negação) aqui e em `phase3b_ablation.py`.
- **O conjunto dos 148 eLNs da ablação A ficou idêntico** (verificado), então os resultados da Etapa D não
  mudam.

## 2. Fontes sobre eLN → eLN e sobre a persistência dos LNs
- **Existem conexões eLN → eLN funcionais:** Huang J, Zhang W, Qiao W, Hu A, Wang Z 2010, *Neuron*
  67:1021–1033 (resumo lido). Registros pareados de eLNs krasavietz e PNs mostraram "reciprocal excitatory
  connections mediated by dendrodendritic cholinergic synapses and gap junctions"; "Reciprocal connections were
  also found between two krasavietz eLNs but were rare between krasavietz eLNs and inhibitory LNs".
  - O resumo **não diz** se a conexão eLN–eLN é química ou elétrica.
  - Huang et al. dão às conexões eLN–PN um componente **químico** colinérgico; Yaksi & Wilson 2010 dizem que a
    via eLN → PN é **elétrica** (não cai com o bloqueio químico). **As duas fontes divergem**, e registro a
    divergência.
- **Os LNs mantêm atividade depois do estímulo?** Nagel KI, Wilson RI 2016, *J Neurosci* 36:4325–4338 (resumo e
  trechos lidos): há LNs com respostas "ON", "OFF" ou ambas; respostas OFF "were more stable over time, or else
  they tended to grow" ao longo de trens de pulsos; taxa espontânea de 4,6 ± 2,8 spikes/s.
  - **Não encontrei fonte com números mostrando se, e em quanto tempo, a atividade dos LNs volta ao basal**
    depois do odor.
  - **Também não encontrei fonte de persistência indefinida.**
  - Os LNs reais têm atividade espontânea (~4,6 Hz), que o modelo não tem (basal = 0).

## 3. PN de DM1 contra a curva de Olsen et al. 2010
**A entrada e a saída da curva são o aumento sobre o basal.** Olsen SR, Bhandawat V, Wilson RI 2010, *Neuron*
66:287–299 (Métodos, lidos no texto completo): "The response magnitude for each cell/stimulus combination was
quantified as the trial-averaged number of spikes during the 500-msec odor stimulus period, minus the
trial-averaged baseline spike rate during the preceding 500 msec". É a mesma convenção de Faucher et al. 2013
(aumento sobre o pré-estímulo). O modelo tem basal 0, então a taxa do modelo durante o odor já é o aumento.

**Equação (1), forma exata** (no artigo, "the input variables (ORN, σ, s) are raised to an exponent (1.5)"):

  PN = Rmax · ORN^1,5 / (ORN^1,5 + σ^1,5 + s^1,5), com s = m · LFP (s = 0 sem inibição lateral)

- DM1: **Rmax = 144 spikes/s e σ = 44,8 spikes/s**, ajustados com o **odor privado de DM1** (acetato de etila,
  que ativa só esse glomérulo) em solução normal.
- Os autores atribuem o σ maior de DM1 a "odor-evoked intra-glomerular GABA release and/or tonic
  inter-glomerular GABA release".
- O expoente 1,5 foi escolhido por dar o melhor ajuste (mínimo entre 1,5 e 1,6).

**Comparação** (spikes salvos; janela de 0–200 ms com o odor, contra os 500 ms de Olsen; taxa do ORN medida no
modelo; s = 0):

| Condição | Vinagre | ORN de DM1 (medido) | PN de DM1 no modelo (mediana; mín.–máx.) | Curva de Olsen | Modelo / Olsen |
|---|---|---|---|---|---|
| Intacto | 0,1 % | 7,1 Hz | **212,5 Hz** (202–225) | 8,5 Hz | 25× |
| Intacto | 0,5 % | 16,4 Hz | **227,5 Hz** (218–232) | 26,0 Hz | 8,8× |
| Intacto | 5 % | 41,6 Hz | **247,5 Hz** (242–255) | 68,0 Hz | 3,6× |
| A (sem eLN → PN) | 0,1 % | 7,1 Hz | **7,5 Hz** (5–10) | 8,5 Hz | 0,88× |
| A | 0,5 % | 16,4 Hz | **10,0 Hz** (10–12) | 26,0 Hz | 0,38× |
| A | 5 % | 41,6 Hz | **111,2 Hz** (102–122) | 68,0 Hz | 1,6× |

**Leitura:**
- **No modelo oficial, o PN de DM1 fica saturado** (212–248 Hz) já na dose mínima: 3,6× a 25× acima da curva e
  quase sem dependência da dose, **acima do Rmax de 144** medido.
- **Na ablação diagnóstica A**, a dose mínima cai perto da curva, mas o formato é outro: plano entre 0,1 % e
  0,5 % e um salto a 5 %, em vez da saturação suave.
- **Ressalvas:** janela de 200 ms contra 500 ms; o vinagre ativa também VA2 (s pode ser > 0, mas Olsen et al.
  mostram inibição lateral fraca com 1 glomérulo); nenhuma tolerância foi pré-fixada para esta comparação, que
  é **descritiva**.

## 4. Os trabalhos de 2026 (lidos)
**(i) Li Q, Ping W, Zhang K, Wang C, "Connectome-constrained modeling identifies neurons and synapses that sustain
spontaneous activity in Drosophila", bioRxiv 2026 (10.64898/2026.08.21.745055; preprint)**
- **Modelo:** equação de taxa de 1ª ordem com ativação ReLU (não é LIF), sobre o FlyWire v783, com topologia e
  sinal fixos ("polarity labels were taken from FlyWire neurotransmitter predictions").
  - **Treinam** por retropropagação no tempo as **magnitudes de ~1,5×10⁷ pesos sinápticos** e as constantes de
    tempo, ajustando-as a registros de cálcio da atividade espontânea.
- **Regime:** a atividade de repouso é sustentada por um núcleo esparso de **neurônios inibitórios "hub"**.
  "Silencing one inhibitory hub releases its excitatory partner into runaway activity". Um dos hubs é o **ILN2F_b,
  "a GABAergic antennal-lobe interneuron"**.
- **Ligações elétricas:** "FlyWire also omits gap junctions, graded transmission, and neuromodulation … [the
  mechanisms] remain model-derived hypotheses".
- **Correção com fonte? Não.** A estabilidade deles vem de **pesos aprendidos** (não das contagens de sinapses),
  o que contraria os princípios do projeto. Serve como indício: modelos no FlyWire sem inibição forte o
  bastante entram em atividade descontrolada.

**(ii) Lazar AA, Zhou Y, "Elements of Olfactory Intelligence in Drosophila", bioRxiv 2026 (10.64898/2026.01.05.697602;
preprint); e o texto de revisão dos mesmos autores, "The Connectome and the Quest for the Functional Logic of the
Drosophila Early Olfactory System", arXiv:2608.19290 (2026)**
- **Modelo:** abstrações funcionais (processadores de normalização divisiva, "DNPs") da antena, do lobo antenal e
  do cálice, e **não** uma simulação do FlyWire neurônio a neurônio.
  - No lobo antenal: Pre-LNs (inibitórios pan-glomerulares, com retroalimentação nos terminais dos ORNs),
    Post-eLNs uniglomerulares excitatórios e Post-iLNs.
  - Dizem reproduzir dados registrados de PNs, com parâmetros próprios.
- **Regime e alças:** não tratam de persistência nem de alças eLN–eLN. Registram que "some nonspiking" LNs
  interagem localmente. Silenciar o APL tira a esparsidade das células de Kenyon.
- **Ligações elétricas:** não são mencionadas.
- **Correção com fonte? Não** para o LIF do Shiu. O que se aproveita é a arquitetura conceitual (eLN
  uniglomerular, inibição pré-sináptica global nos ORNs), coerente com Olsen & Wilson 2008.

## 5. Critério registrado
Qualquer teste futuro de dose-resposta será julgado **contra a curva de Olsen et al. 2010** (Eq. 1, DM1: Rmax 144,
σ 44,8, expoente 1,5), com **tolerância numérica fixada no pré-registro**, e não só por significância estatística.
Registrado em `docs/NON_CONNECTOME.md` e em `docs/FASE3B_PLANO.md` §T.
