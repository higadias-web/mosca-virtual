# Fase 3b, Etapa C: o regime de atividade alta (relatório curto)

**Data:** 2026-09-24. Sem corpo, **sem interface, sem vídeo**. Pré-registro em `docs/FASE3B_PLANO.md` §P
(commit e2f304c, antes de rodar). Fila: 190/190 (`REGIME_OK`) em ~9 min (estimativa: 10–15). Análise só com a
fila completa. Figura: `results/phase3b/s1/diagnostico_etapaC.png`. Dados: `results/phase3b/regime.json`,
`breakdown_vin5.{csv,json}`, `loop_late.json`, `loop_LN_by_nt.json`.

## 1. Resultados pelos critérios pré-registrados

| Pergunta | Resultado | Números |
|---|---|---|
| A atividade se mantém sozinha depois do odor? | **SIM (conectoma real)** | razão [400–1000 ms]/[100–200 ms] = **0,98** (0,97–0,99 nas 10 sementes); spikes até o fim (1000 ms). Embaralhados: 0, com o último spike ~2 ms depois de desligar |
| Existe limiar com resposta graduada abaixo dele (doses com fonte)? | **NÃO** | 0,1 % (DM1 a 7 Hz, VA2 a 0), 0,5 % (16/11 Hz) e 5 % (42/22 Hz): 10/10 sementes em estado alto em todas; fração ativa de 6,10 a 6,16 %. Não há dose mista. Embaralhados: 0,05–0,17 %, graduados com a dose |
| O AOTU019 esquerdo contribui para o silêncio do DNa02 direito? | **SIM (causal)** | silenciado, o DNa02 D vai de **0 para 44,5 Hz** (p = 0,002; aumento mediano de 44,5 Hz); o DNa02 E vai de 54,5 para 50,5 Hz. **O viés some** |

Faucher et al. têm pontos abaixo de 20 Hz (0,1 % e 0,5 %), então 5 e 10 Hz sem fonte não foram acrescentados.

## 2. Quem está ativo (vinagre 5 %, conectoma real; spikes salvos, sem simulação)

| Classe (anotação do FlyWire) | Ativos / total | Taxa média dos ativos |
|---|---|---|
| Células de Kenyon | 3.412 / 5.177 (**66 %**) | 48 Hz |
| PNs do lobo antenal | 557 / 685 (**81 %**) | 102 Hz |
| LNs do lobo antenal | 362 / 429 (84 %) | 153 Hz |
| Corno lateral (LH*) | 1.097 / 1.611 (68 %) | 67 Hz |
| MBONs | 69 / 96 (72 %) | 114 Hz |
| DANs | 149 / 331 (45 %) | 57 Hz |
| LAL/AOTU | 121 / 778 (16 %) | 46 Hz |
| Descendentes | 197 / 1.299 (15 %) | 25 Hz |
| Sensoriais | 577 / 16.352 | 38 Hz |
| Demais centrais | 2.091 / 23.270 | 35 Hz |

- **APL: 346 Hz (E) e 331 Hz (D).**
- **AOTU019: 127 Hz (E) e 78 Hz (D).**

## 3. O que sustenta a atividade (janela 900–1000 ms, sem odor; spikes salvos)
- **O núcleo é o lobo antenal:**
  - os LNs recebem 62 % da excitação de outros LNs e 33 % dos PNs;
  - os PNs recebem 78 % da excitação dos LNs;
  - 358 ORNs (de 25 tipos, não só DM1/VA2) continuam disparando, 96 % excitados pelos LNs.
- Daí a atividade se espalha: as células de Kenyon recebem 74 % dos PNs, o corno lateral 82 % dos PNs, e
  MBONs e DANs ~60–70 % das células de Kenyon.
- **Os LNs que excitam são colinérgicos.** Os de maior peso têm previsão de transmissor **serotonina** (40
  células, confiança mediana de 0,35) ou **dopamina** (12, confiança de 0,29), mas a anotação traz
  **`known_nt = acetylcholine`** para a maioria (imuno-histoquímica, Shang et al. 2007). Pela regra do Shiu,
  todos viram excitatórios rápidos; corrigir o transmissor para ACh **não mudaria o sinal**.

## 4. Limitação conhecida do modelo apontada pela causa (nada foi corrigido)

**L1. LNs excitatórios do lobo antenal: no modelo, a excitação é química; na mosca, é elétrica.**
- Shang Y, Claridge-Chang A, Sjulson L, Pypaert M, Miesenböck G 2007, *Cell* 128:601–612: população de LNs
  colinérgicos multiglomerulares que excitam os PNs lateralmente ("lateral, interglomerular excitation").
- Yaksi E, Wilson RI 2010, *Neuron* 67:1034–1047 (resumo lido): "eLN-to-PN synapses … are not diminished by
  blocking chemical neurotransmission, and are abolished by a gap-junction mutation. … lateral excitation is
  mediated by electrical synapses from eLNs onto PNs. In addition, eLNs form synapses onto inhibitory LNs."
- **No modelo:** o FlyWire só registra sinapses químicas, e o LIF do Shiu converte cada sinapse química de um
  LN colinérgico em excitação rápida. Os eLNs viram uma **alça química excitatória eLN ↔ PN ↔ eLN** (mais
  eLN → ORN) que, uma vez ligada, não desliga (§1, persistência de 0,98). Na mosca, segundo a fonte, a
  excitação eLN → PN é elétrica, e as sinapses químicas dos eLNs recrutam inibição (via LNs inibitórios).
- **Ressalva:** que essa alça seja a causa suficiente da persistência é uma **inferência** a partir das fontes
  de excitação (§3). Não houve teste causal.

**L2. APL: no modelo dispara spikes; na mosca é não disparador.**
- Amin H, Apostolopoulou AA, Suárez-Grimalt R, Vrontou E, Lin AC 2020, *eLife* 9:e56954: "Like its locust
  homolog, the giant GABAergic neuron (GGN), APL is non-spiking."
- No modelo, o APL dispara a 331–346 Hz, e as células de Kenyon ficam **66 % ativas**. Honegger KS, Campbell
  RA, Turner GC 2011, *J Neurosci* 31:11772–11785 (resumo lido): o corpo pedunculado codifica odores em
  "sparse patterns of activity", consistentes "even [for] complex natural smells". O resumo não dá uma
  porcentagem, e nenhum número é citado aqui.
- L2 **não** explica a persistência (o APL é inibitório), mas mostra que a camada das células de Kenyon está
  fora do regime da mosca real.

**L3 (estrutural, do código):** o LIF do Shiu não tem atividade de fundo nem adaptação de frequência
(`terrario/brain/lif.py`, parâmetros de Shiu et al. 2024), e trata como excitatório rápido todo transmissor
que não seja GABA ou glutamato, inclusive monoaminas. Aqui isso não muda o sinal dos eLNs, que são
colinérgicos pela anotação.

## 5. Opções (nenhuma executada), com prós, contras e interferência no conectoma

| # | Opção | Prós | Contras | Interferência no conectoma |
|---|---|---|---|---|
| O0 | **Aceitar e documentar**: a 3b encerra com o negativo ("no LIF do Shiu com o FlyWire, o odor liga um estado persistente, e os DNs de marcha não carregam direção nem avanço") | nenhuma engenharia nova; respeita os princípios | a mosca não chega à fruta por este caminho | **nenhuma** |
| O1 | **Testar outro conectoma do cérebro** (p. ex., o hemibrain, cuja cobertura do lobo antenal é parcial, **a verificar**; ou o BANC, que não reproduziu a Fig. 1D) com o mesmo protocolo | diz se a alça depende do dataset; sem mudar o modelo | cobertura parcial (hemibrain) ou validação falha (BANC); custo de 1–2 sessões | **nenhuma** no modelo; troca de dataset |
| O2 | **APL como neurônio graduado** (modelo de taxa, D-102), só o APL | tem fonte (Amin et al. 2020); muda 2 neurônios | não resolve a persistência (L1); os parâmetros do modelo de taxa não têm fonte | **baixa** (modelo de 2 neurônios; nenhuma sinapse muda) |
| O3 | **Tratar as saídas eLN → PN como elétricas** (tirar o efeito químico excitatório eLN → PN, mantendo eLN → LN inibitório) | ataca a causa apontada; a direção tem fonte (Yaksi & Wilson 2010) | o FlyWire não mede junções comunicantes: a condutância elétrica ficaria sem fonte, ou a excitação lateral some; é preciso definir quem é eLN (80–130 LNs, por `known_nt`/`top_nt`) | **alta e localizada**: muda o efeito das sinapses de ~100 neurônios sobre os PNs |
| O4 | **Adaptação de frequência** nos neurônios (global ou só no lobo antenal) | mecanismo biológico geral que encerra estados persistentes | sem fonte para os parâmetros neste modelo; muda a dinâmica de todo o cérebro validado na Fase 1 (a Fig. 1D teria de ser refeita) | **média** (propriedade intrínseca; nenhuma sinapse muda) |
| O5 | **Reescalar pesos** (w_syn) no lobo antenal ou no caminho olfativo | simples | ajuste sem fonte, feito para o resultado; contraria os princípios | **alta** |
| O6 | **Remover sinapses** eLN → PN/eLN | acaba com a alça | apaga dado do conectoma; contraria os princípios | **muito alta** |

Pelos princípios do projeto, as opções de menor interferência são O0 e O1 (e O2, que tem fonte mas não
resolve L1). O3 é a única que ataca a causa apontada com direção de fonte, mas deixa um parâmetro sem fonte
(a condutância elétrica) ou remove a excitação lateral. **A decisão é do usuário.**

## 6. O que isso implica para a S2
- **O efeito do AOTU019 E é causal:** o viés do DNa02 esquerdo vem da inibição contralateral do AOTU019 E.
- **O estado que o odor liga não depende da dose e não desliga.** Com ele, não há gradiente que uma interface
  possa usar para dirigir a mosca à fruta: qualquer odor, em qualquer taxa com fonte, leva ao mesmo estado.
- **Nenhuma interface deve ser construída sobre este regime.** Antes, é preciso escolher entre O0–O6.
