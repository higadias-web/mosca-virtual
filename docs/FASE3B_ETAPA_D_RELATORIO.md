# Fase 3b, Etapa D: ablações diagnósticas, referência olfativa e ligações elétricas (relatório curto)

**Data:** 2026-09-24. Sem corpo, **sem interface, sem vídeo**. **O modelo oficial não mudou**: as ablações
foram feitas numa cópia do conectoma, só dentro do experimento. Pré-registro em `docs/FASE3B_PLANO.md` §R
(commit e2327a4, antes de rodar). Fila: 140/140 (`ABL_OK`) em ~15 min (estimativa: 10–20). Análise só com a
fila completa. Figura: `results/phase3b/s1/diagnostico_etapaD.png`. Dados: `results/phase3b/ablation.json`.

## 1. Ablações diagnósticas

**O que os terminais dos ORNs recebem na mosca real (fontes lidas, antes de definir B):**
- **Inibição GABAérgica pré-sináptica.** Olsen & Wilson 2008, *Nature* 452:956–960: "mediated by both GABAA
  and GABAB receptors on the same nerve terminal".
- **ORNs predominantemente pré-sinápticos, com algumas sinapses ORN–ORN.** Horne et al. 2018, *eLife*
  7:e37550.
- **Nenhuma fonte lida mostra entradas excitatórias nos terminais fazendo o ORN inteiro disparar.** A
  hipótese de B continua hipótese.

**Conjuntos removidos:**

| Ablação | Conjunto |
|---|---|
| A | 148 eLNs; 18.618 arestas e 142.287 sinapses eLN → PN |
| B | 51.695 arestas e 95.001 sinapses excitatórias em ORNs (76 % de LNs, 20 % de ORNs, 4 % de PNs) |
| C | A + B |

**Resultados** (vinagre de Faucher et al. 2013, odor em 0–200 ms e observação até 1 s, 10 sementes pareadas):

| Condição | Volta ao basal? (razão off/on; basal ≤ 0,01) | Cresce com a dose? | Ativos durante o odor, 0,1 % → 5 % | KC / PN / LN ativos (5 %) |
|---|---|---|---|---|
| Intacto | **não** (0,98–1,00) | sim (+7 %, p = 0,002) | 5,8 → 5,9 % | 64 / 80 / 84 % |
| A (sem eLN → PN) | **não** (0,89–0,99) | sim (+17 %, p = 0,002) | 0,98 → 1,13 % | **0,5 / 11 / 68 %** |
| B (sem excitação nos ORNs) | **não** (0,98–1,00) | sim (+7 %) | 5,5 → 5,6 % | 64 / 80 / 83 % |
| C (A + B) | **não** (0,88–0,99) | sim (+19 %) | 0,72 → 0,83 % | **0,6 / 8 / 68 %** |

Sem odor, todas as condições ficam em 0 spikes.

**Leitura:**
- **Nenhuma ablação traz a atividade de volta ao basal.** A persistência continua em todas.
- **A (e C) mudam muito o regime:** a fração ativa cai de ~6 % para ~1 %, as células de Kenyon quase se apagam
  (0,5 %) e os PNs caem para ~10 %. Mas **os LNs continuam 68 % ativos e persistentes.**
- **Sob A, a persistência vem de uma alça eLN → eLN** (spikes salvos, janela 900–1000 ms): os eLNs recebem
  **94 %** da excitação de outros eLNs, com I/E = 0,2; os LNs inibitórios recebem 86 % dos eLNs.
  - Yaksi & Wilson 2010 descrevem sinapses de eLNs sobre LNs **inibitórios**. **Não li nenhuma fonte sobre
    sinapses eLN → eLN** na mosca real. Isso fica como achado, sem teste.
- **B quase não muda nada:** a excitação que chega aos ORNs não é o que sustenta o estado.
- **"Cresce com a dose" passa em todas as condições pelo critério**, mas com aumento pequeno (7–19 % entre 0,1 %
  e 5 %). O pareamento das sementes faz diferenças pequenas darem p = 0,002. O critério foi cumprido, mas a
  resposta não é graduada no sentido fisiológico: a fração ativa quase não muda com a dose.
- **Achado registrado à parte:** 18 LNs são excitatórios no modelo, mas têm `known_nt` GABA, glutamato ou
  octopamina na anotação (12 com "gaba, MIP; acetylcholine-negative"). É um erro de sinal do modelo para
  eles. **Não foi corrigido.**

## 2. Referência olfativa para reprodução (proposta; nada foi rodado com ela)

**Proposta principal:** a transferência ORN → PN de Olsen, Bhandawat & Wilson 2010 (*Neuron* 66:287–299,
PMC2866644, lido):
- **Equação:** PN = Rmax · ORN^1,5 / (ORN^1,5 + σ^1,5 + s^1,5), com s = m · LFP (a inibição lateral cresce
  com a atividade total dos ORNs).
- **Parâmetros de DM1:** **Rmax = 144 spikes/s e σ = 44,8 spikes/s**. Os parâmetros gerais são Rmax = 165 e
  σ = 12.
- **Com as taxas de ORN de Faucher et al. 2013** (DM1: 7, 16 e 42 Hz nas doses 0,1 %, 0,5 % e 5 %), a curva
  sem inibição lateral (s = 0) prevê para o PN de DM1: **~8, ~25 e ~69 spikes/s**. É uma dose-resposta
  graduada e saturante, que o modelo teria de reproduzir.
- **Ressalvas:**
  - s ≠ 0 quando outros glomérulos estão ativos (o vinagre ativa 6 glomérulos, segundo Semmelhack & Wang
    2009); aqui, só DM1 e VA2 recebem estímulo;
  - VA2 não tem parâmetros no trecho lido;
  - a curva é de ORN → PN, não da resposta ao vinagre medida diretamente.
- **Complementos:**
  - Bhandawat et al. 2007, *Nat Neurosci* 10:1474–1482 (PMC2838615, lido): registros pareados de ORNs e PNs
    de **DM1 e VA2**, entre 7 glomérulos, com 18 odores. Os números estão nas figuras, e não está confirmado
    que os dados estejam disponíveis;
  - células de Kenyon: codificação esparsa (Honegger et al. 2011, qualitativo no resumo lido; falta uma
    porcentagem com fonte).
- **Critério fisiológico sugerido para uma correção futura** (a aprovar):
  1. o PN de DM1 seguir essa curva dentro de uma tolerância a definir;
  2. a atividade voltar ao basal depois do odor (nenhuma fonte lida mostra persistência de segundos no lobo
     antenal);
  3. as células de Kenyon ficarem esparsas.

**Trabalhos recentes que simulam o olfato a partir do conectoma (encontrados, NÃO lidos):**
- "Elements of Olfactory Intelligence in Drosophila", bioRxiv 2026 (10.64898/2026.01.05.697602);
- "Connectome-constrained modeling identifies neurons and synapses that sustain spontaneous activity in
  Drosophila", bioRxiv 2026-08 (10.64898/2026.08.21.745055). Ajusta um modelo do cérebro inteiro no FlyWire a
  registros de atividade espontânea e pode ser relevante para o regime;
- "The Connectome and the Quest for the Functional Logic of the Drosophila Early Olfactory System", arXiv
  2608.19290 (2026);
- repositórios no GitHub com o FlyWire mais o NeuroMechFly, sem revisão por pares.

Nenhum desses trabalhos entra na interpretação antes de ser lido.

## 3. O hemibrain e o BANC registram ligações elétricas?
- **Hemibrain: não.** Scheffer et al. 2020, *eLife* 9:e57443 (lido): "Gap junctions … are difficult to reliably
  detect by FIB-SEM under the best of circumstances and not detectable at the low (for EM) resolution needed to
  complete this study … Their contribution to the connectome will need to be established through other means."
- **BANC: não há registro.** O texto do manuscrito do BANC no repositório local (`third_party/BANC-project`) não
  menciona junções comunicantes nem sinapses elétricas; os termos só aparecem em entradas da bibliografia de
  outros temas. Não li uma afirmação explícita dos autores; a conclusão vem da ausência.
- Lillvis et al. 2022, *eLife* 11:e81248: "gap junctions, which are difficult to detect in EM images".
- **Implicação para a O1:** trocar de conectoma **não traz** as ligações elétricas eLN → PN que a limitação L1
  pede. A O1 só testaria se a alça química depende do dataset. O ganho para a L1 é baixo, e o esforço é de 1–2
  sessões.

## 4. Registros feitos
- **NON_CONNECTOME.md:** princípio de que correções do modelo oficial só são aprovadas por critérios
  fisiológicos da literatura, nunca pelo comportamento; uma mudança de cada vez; ablações diagnósticas não são
  correções.
- **SPEC.md:** "Fase 9: voo", depois da Fase 8, com o flybody como corpo candidato (Vaxenburg et al. 2025,
  *Nature* 643:1312–1320) e controle pelo conectoma, sem controlador treinado por reforço. Nenhum trabalho agora.

## 5. O que isso implica
- Tirar a excitação química eLN → PN (a direção que tem fonte, L1) **apaga as células de Kenyon e a maior parte
  dos PNs**, mas deixa uma **alça eLN ↔ eLN persistente** e ainda não traz a atividade de volta ao basal. Pelo
  princípio de uma mudança de cada vez, e com aprovação só por fisiologia, nenhuma correção isolada testada
  aqui atende aos critérios sugeridos (volta ao basal, curva de DM1, células de Kenyon esparsas).
- O próximo passo lógico, **só se aprovado**:
  1. confirmar com fonte o que se sabe das sinapses eLN → eLN;
  2. medir, nos dados já salvos, a taxa do PN de DM1 no intacto e na A, para comparar com a curva de Olsen et
     al. 2010. Isso é análise, sem simulação nova, mas não foi feito porque o pedido foi não rodar nada com a
     referência ainda.
