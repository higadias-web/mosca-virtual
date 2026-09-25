# Para a IA que orienta o projeto Terrário Virtual

Olá. Sou outra instância do Claude, rodando no Claude Code na nuvem. O Marcelo me pediu uma **auditoria crítica**
do projeto e me deu acesso ao zip completo (`terrario-virtual`, ~6 GB, com dados e caches, o que me permitiu rodar
simulações). Li o SPEC, todos os relatórios (Fases 0, 1, 2,
D-105, 3a e 3b até a Etapa E), DECISIONS, BENCHMARK e NON_CONNECTOME. Também li o código principal (`lif.py`,
`hybrid.py`, `fields.py`, `sensors.py`, `rhythm.py`, os experimentos) e rodei **dois testes novos com o motor do
próprio projeto**. Fiz ainda uma revisão de literatura e de repositórios.

Escrevo para você porque é você quem pesquisa, orienta e gera os prompts do Claude Code. Então quem precisa
entender, **conferir** e decidir é você, com o Marcelo.

## Como ler esta mensagem (importante)

**Não aceite nada daqui como fato só porque eu disse.** Eu posso ter errado: li resumos no lugar de textos
completos em alguns casos, a minha rede bloqueou bioRxiv, arXiv e eon.systems em parte da auditoria, e posso ter
interpretado mal alguma decisão de vocês.

Cada afirmação importante vem marcada com o grau de confiança:
- **[VERIFICADO: código/dados]**: conferi nos arquivos do projeto ou rodei.
- **[VERIFICADO: repositório]**: li o código ou o README do repositório citado.
- **[FONTE: resumo/trecho]**: li só o resumo ou um trecho de busca, não o texto completo.
- **[SECUNDÁRIA]**: veio de reportagem ou blog, não da fonte primária.
- **[HIPÓTESE]** ou **[OPINIÃO]**: interpretação minha, que precisa de teste ou de discussão.

Peço que você:
1. **Verifique** o que puder (arquivos, comandos e links estão indicados) e diga, item por item, se **concorda,
   discorda ou não consegue verificar**, com o motivo.
2. **Conteste** a minha proposta de objetivo se achar outra melhor. Não quero que ela seja adotada por inércia.
3. Só depois disso, gere o prompt do Claude Code para a primeira etapa que vocês decidirem.

## Onde estão os arquivos (fonte da verdade)

O projeto está no GitHub, no repositório `higadias-web/mosca-virtual`, branch `claude/large-folder-delivery-ec5qgm`
(https://github.com/higadias-web/mosca-virtual/tree/claude/large-folder-delivery-ec5qgm).
- É a **versão enxuta**: os 203 arquivos que o projeto versiona, com o **histórico original de 40 commits**. As datas dos
  commits permitem conferir que cada pré-registro veio antes do resultado.
- Ficaram de fora `.venv/`, `third_party/`, `data/`, `runs/` e `bench/results/raw/` (~6 GB). Servem para rodar, não para ler.
- O `README.md` da raiz indica por onde começar.
- Os meus testes estão em `auditoria/`: `README.md` (números), `teste_espontanea.py`, `teste_dng100.py` e os resultados.

Você lê pelo repositório. **Quem executa é o Claude Code, no computador do Marcelo**, onde está o projeto completo. Para
rodar os meus scripts, basta copiar a pasta `auditoria/` para dentro do `terrario-virtual` local e rodar da raiz dele.

**Sobre os resumos das conversas anteriores:** o conhecimento do projeto no claude.ai tem resumos das conversas "Mosca
Virtual Parte 1, 2, 3" e "Brainstorm Simulações". Eles são **histórico** e podem conter crenças antigas, inclusive suas.
**Confira esta auditoria contra os arquivos e os dados do repositório, não contra os resumos.** Quando um resumo e um
arquivo divergirem, vale o arquivo.

---

## 1. O novo objetivo do Marcelo

Nas palavras dele, resumidas: quer **algo novo, único e impressionante**, que seja rodado e rodado até atingir algo
que ainda ninguém conseguiu. O terrário perdeu o sentido para ele: com o que sabe hoje, percebe que um terrário com
uma mosca andando poderia ter sido montado juntando repositórios que já existem (Eon, FlyGym) e um cenário. Ele
acha que o projeto ainda pode virar algo impressionante e quer saber como.

**Proposta minha [OPINIÃO], para você avaliar:** trocar o objetivo "terrário com 4 animais" por:

> **A primeira mosca virtual cuja marcha é gerada pelo conectoma do próprio cordão nervoso (VNC), num corpo
> físico, em malha fechada com a propriocepção.** Nenhuma linha de código diz "ande" ou "trípode": o ritmo, a
> alternância e a coordenação saem do conectoma do BANC. Silenciar o circuito gerador faz a mosca parar.

Justificativa e caminho nas seções 4 e 5. Alternativas estão na seção 6, para você comparar.

### Atualização: o Marcelo escolheu a alternativa C (seção 6)

Depois de ler as alternativas, o Marcelo escolheu **C: a mosca vai até o odor com a marcha e a direção vindas do
conectoma**, isto é, A (marcha pelo cordão) + B (olfato corrigido por fisiologia). Duas premissas precisam ficar
claras, e peço que você as confira:

1. **Nenhum dos dois lados está pronto; os dois estão em fase de diagnóstico.** [VERIFICADO: código/dados]
   - Cordão: 0 de 6 pernas rítmicas, mesmo com o DNg100 isolado (meu teste 2).
   - Olfato: qualquer entrada, inclusive 0,5 Hz espontâneos, satura o lobo antenal (meu teste 1).
   - O que está avançado é a infraestrutura e o diagnóstico, não o resultado.
2. **Os laboratórios não estão focados só em andar.** [FONTE: resumo]
   - O laboratório da Wilson estuda como sinais olfativos chegam ao DNa02 (Rayshubskiy et al. 2025, *eLife*).
   - O NeuroMechFly v2 (laboratório Ramdya) já navega em pluma de odor, com controlador programado.
   - Wang-Chen & Ramdya 2026 (*Curr Opin Neurobiol*, arXiv 2601.08056) tratam modelos neuromecânicos integrados como
     a direção da área.
   - A Eon persegue a mosca "multicomportamento".

   A junção é um objetivo conhecido da área. Ela não foi feita porque é difícil, não por falta de interesse.
   **[OPINIÃO]** O que seria novo é fazê-la **sem controlador programado**: marcha pelo cordão e direção pelo cérebro,
   ambos pelo conectoma, com ablações e comparação com dados reais.

**Estrutura sugerida para C [OPINIÃO; conteste se discordar]:** duas trilhas **independentes, em paralelo**, cada uma
com resultado próprio publicável, e a junção no fim.
- **Trilha A (cordão):** Etapas 1–5 da seção 5. Resultado próprio: marcha gerada pelo VNC num corpo.
- **Trilha B (cérebro):**
  - corrigir o lobo antenal contra fisiologia, com atividade espontânea ligada;
  - critérios: curva de Olsen 2010, retorno ao basal, KCs esparsas;
  - depois, mostrar que o **lado do odor** chega ao DNa02 como diferença E − D (hoje não chega).
  - Resultado próprio: olfato fisiológico no cérebro inteiro.
- **Junção:** a diferença E − D do DNa02 vinda do cérebro entra no cordão da trilha A. Segundo Yang et al. 2024, o
  DNa02 unilateral encurta o passo ipsilateral; a curva tem que emergir do cordão, não de um mapeamento manual.
- **Ordem:** as trilhas não dependem uma da outra até a junção. Cada uma tem critérios de parada próprios. Se uma
  falhar, a outra ainda entrega.

---

## 2. Auditoria do projeto, da Fase 0 até a Etapa E da 3b

Primeiro o que está **bom**, porque é raro e deve ser mantido: pré-registro com commit antes de rodar, execução
separada da análise, registro de tudo que não vem do conectoma (NON_CONNECTOME), preservação dos negativos,
métrica de ritmo validada contra controle nulo, motor exato bit a bit e a comparação com Olsen 2010. Na minha
leitura, é mais rigoroso que todos os projetos amadores comparáveis que encontrei.

Os furos abaixo são sobre **direção e premissas**, não sobre execução.

### Fase 0 (ambiente, benchmark, motor)
- **Feito:** motor LIF em numba com conjunto ativo, 0,64 s/s contra 2,4–2,8 do Brian2, idêntico bit a bit;
  correção de 13 premissas da SPEC. [VERIFICADO: código/dados]
- **Furo 1, duplicação não avaliada.** O relatório da Fase 0 lista a Eon, `erojasoficial-byte/fly-brain`,
  `statsleelab/embodied-fly-lab` e `Fly.exe` como "trabalhos prévios semelhantes, **não verificados**". O risco de
  duplicação era conhecido no dia 1 e nunca foi avaliado. [VERIFICADO: `docs/FASE0_RELATORIO.md` §2, fim]
- **Furo 2, o problema central foi visto e não testado.** O item 10 já diz que o modelo não tem atividade
  espontânea. Foi tratado como questão de "exploração", não de validade do modelo. Isso virou a causa do estado
  saturado da 3b (ver o teste 1 abaixo). [VERIFICADO: código/dados]
- **Furo 3.** A D-101 já dizia que a opção (a) "é a abordagem do NeuroMechFly v2 e da Eon" e que marcha por VNC em
  LIF "é pergunta de pesquisa em aberto". Ou seja, o caminho padrão era, por construção, o mesmo dos outros.
  [VERIFICADO: código/dados]
- O motor em si é classe A: já existem várias versões do modelo do Shiu (Eon `fly-brain` com 6 backends em GPU,
  FastFly, MLX, Loihi 2, webgpu-fly). O valor é prático (CPU de notebook), não científico. [VERIFICADO: repositório]

### Fase 1 (reprodução do Shiu)
- **Feito:** 100.200 simulações, correlação ≥ 0,997, os 200 mais ativos idênticos (200/200), análise do excesso de
  |z| com Bessel e t de Student. Excelente. [VERIFICADO: código/dados]
- **Furo 4, validação usada fora do domínio.** A Fase 1 valida o LIF num regime específico: via gustativa → MN9,
  ~0,3 % dos neurônios ativos, 1 s, circuito quase direto. Os relatórios da 3b falam em "parâmetros validados na
  Fase 1" ao usar o modelo no **lobo antenal** (6 % ativos, circuito recorrente) e no **cordão** (outro conectoma,
  circuito recorrente). Nesses circuitos, nunca houve validação. Além disso, a Fase 1 comparou com a **simulação**
  do Shiu, não com a **fisiologia** da mosca. [VERIFICADO: código/dados] A leitura de que isso liga a Fase 1 às
  falhas da Fase 3 é [OPINIÃO].

### Fase 2 (terrário, sensores)
- **Feito:** arena de 80 × 60 mm, 798 pares de contato, campo de odor 2D, sensores a 1 kHz, gravação e 17 testes.
  É classe A: o FlyGym tem arenas, o NeuroMechFly v2 tem pluma de odor e navegação multimodal, e o
  `embodied-fly-lab` já faz FlyWire LIF + NeuroMechFly + fontes de odor + painel 3D do cérebro, que é a Fase 6 do
  SPEC. [VERIFICADO: repositório]
- **Furo 5, mundo olfativo irrealista para a pergunta.** O odor é difusão lisa em ar parado, sem vento. Em moscas
  que andam, a navegação por odor depende de vento e de encontros intermitentes com o odor:
  - subir contra o vento durante o odor exige os mecanorreceptores da antena (Álvarez-Salvado et al. 2018, *eLife*
    7:e37815) [FONTE: resumo];
  - as viradas são guiadas pelo *timing* dos encontros com o odor (Demir et al. 2020, *eLife* 9:e57524) [FONTE: resumo].
- **Medi na gravação da travessia** (`runs/phase2/walk_soil_fruit_landscape.parquet`) a diferença relativa de odor
  entre as antenas: mediana de **1,05 %** (fruta), máxima de 3,2 % (fermento). É o único sinal de direção que o
  terrário oferece. [VERIFICADO: código/dados]
- 36 % do custo da física vem do relevo decorativo, que serve à harmonia visual e não à pergunta. [VERIFICADO: código/dados]

### D-105 e Fase 3a (cordão do BANC na bolinha)
- **Feito:** híbrido FlyWire + BANC; mapa de 391 MNs → 17 músculos → 7 DOF por perna, pelos alvos anotados no BANC;
  transdução de 941 proprioceptores; métrica de ritmo v2 com controle nulo; testes de inibição recíproca (12/12 e
  11/12); saldo E/I proprioceptor → MN. **Essa infraestrutura é rara, e nenhum outro projeto que encontrei a tem.**
  [VERIFICADO: código/dados]
- **Furo 6, o trabalho mais relevante da literatura nunca foi lido.** Pugliese et al. 2025, "Connectome simulations
  identify a central pattern generator circuit for fly walking" (bioRxiv 10.1101/2025.09.12.675944; código
  `github.com/smpuglie/Pugliese_cpg_2025`), **não aparece em nenhum documento do projeto** (`grep -ri pugliese docs/`
  não retorna nada). [VERIFICADO: código/dados] O que ele faz:
  - modelo de **taxa** (tanh), não LIF [VERIFICADO: repositório, `src/simulation/vnc_sim.py`];
  - estimular **só o DNg100** (ou o DNb08) gera ritmo nos MNs de perna, em malha aberta e **sem propriocepção**
    [FONTE: resumo; configs VERIFICADO];
  - a poda isola um **gerador de 3 neurônios** (1 inibitório, 2 excitatórios), necessário e suficiente, em 4
    conectomas. O repositório tem dados de MANC, FANC, **BANC** ("banc t1 premotor") e outro [VERIFICADO: repositório];
  - a previsão sobre o DNb08 foi **confirmada por optogenética** em moscas reais [FONTE: resumo];
  - os parâmetros não são medidos: τ ~ 20 ± 2 ms, limiar 7,5 ± 0,6, ganho 1 ± 0,1, teto de 200 Hz, multiplicadores
    E/I de 0,03, sorteados em 1.024 réplicas [VERIFICADO: repositório, `configs/neuron_params/default.yaml`];
  - segundo um trecho de busca, os autores citam como **trabalho futuro** acoplar a simulação do VNC a um corpo
    biomecânico, com sensores proprioceptivos e atuadores musculares [FONTE: trecho de busca; confira no texto].
- **Meu teste 2 (o que faltava na 3a):** o projeto estimulou DNg100 e DNb08, mas sempre dentro de G3 (20 DNs) e G4
  (159 DNs). Rodei **cada um isolado** no híbrido LIF, com o protocolo da Sessão 1 v2 (sinais `verified`, 3,25 s,
  5 sementes, métrica v2 congelada):
  - DNg100 a 100/200 Hz: 54/67 MNs ativos, **0 de 6 pernas rítmicas**;
  - DNb08 a 100/200 Hz: 33/40 MNs ativos, **0 de 6 pernas rítmicas**;
  - maior proeminência de 5,0–6,4 em uma única semente (o critério exige 3 de 5).

  [VERIFICADO: código/dados; script `auditoria/teste_dng100.py`]
- **Leitura [HIPÓTESE com evidência forte]:** o negativo de malha aberta da 3a vem da **classe do modelo** (LIF do
  Shiu no cordão), que é a H4 do plano de vocês, e não do cordão. A H4 foi deixada para as sessões 4–6, que nunca
  aconteceram. Evidências a favor:
  - o modelo de taxa oscila com os mesmos DNs em vários conectomas (Pugliese);
  - o `Lulzx/fly-brain`, projeto amador sem revisão, rodou o cordão em LIF (MaleCNS e BANC), fez uma varredura de 512
    variantes e **não obteve marcha** (docs 46–48 do repositório) [VERIFICADO: repositório].
- **Furo 7, a 3a foi encerrada por engenharia, não por biologia.** O teto foi o batente das juntas (impacto >
  tolerância nas 3 tentativas), não um negativo da malha fechada. E a saída foi para a opção (a), o
  `HybridTurningController` do FlyGym, **o mesmo gerador escrito à mão que o `Fly.exe` usa** (README: "The walking is
  engineered. No part of the simulated ventral nerve cord contributes to leg movement"). [VERIFICADO: repositório]
  Com isso, a parte única do projeto foi trocada pelo caminho comum.

### Fase 3b (olfato → DNs), Etapas S1 a E
- **Feito:** odor → DNa01/02 específico (o embaralhado zera); o DNp09 nunca é excitado; o DNa02 E tem viés fixo e
  nenhum DN carrega o lado; estado persistente; ablações diagnósticas; comparação com Olsen 2010 (PN de DM1 a
  212–248 Hz contra 8,5–68 Hz da curva). [VERIFICADO: código/dados]
- **Meu teste 1:** **sem odor**, só atividade espontânea nos 2.275 ORNs:
  - com 0,5 Hz, o modelo já entra no mesmo estado alto: 6,6 % ativos, PN de DM1 a 209–218 Hz, 65 % das KCs ativas;
  - de 1 a 5 Hz, o mesmo quadro;
  - a checagem de sanidade (vin5, semente 1000) deu **474.799 spikes, idêntico** ao `rates_runs.csv` da Etapa B.

  Consequência: o controle "sem odor = 0 spikes" só existe porque o basal é 0. Com qualquer atividade espontânea, o
  modelo não distingue odor de ausência de odor. Por isso o viés do DNa02, o efeito causal do AOTU019, a
  persistência e a falta de dose-resposta são **propriedades do estado saturado**, não respostas olfativas.
  [VERIFICADO: código/dados; `auditoria/teste_espontanea.py`] A taxa espontânea real dos ORNs não foi fixada com
  fonte; foi uma varredura de sensibilidade.
- **Furo 8.** O AOTU019 faz parte da **via visual** de perseguição de objetos: LC10a → AOTU019 (inibitório) → DNa02
  contralateral (Collie et al. 2026, *Neuron*, "Specialized parallel pathways for adaptive control of visual object
  pursuit") [FONTE: resumo]. No modelo, ele dispara a 127 Hz com vinagre por arrasto do estado saturado. O projeto
  não cita Collie. O efeito causal vale **dentro do modelo**, mas não descreve olfação. [HIPÓTESE]
- **Furo 9, sobreposição não detectada.** O `yukincom/fly-odor-onoff` (publicado em 17/09/2026) fez, em outro
  conectoma (MaleCNS, via `fly-brain-minecraft`): persistência após o odor, bloqueio eLN → PN, bloqueio das entradas
  de retorno nos ORNs, sementes pareadas e dois ganhos. O `fly-brain-minecraft` documenta a saturação do lobo antenal
  ("PNs ~410–430 Hz, a known limitation of uniform LIF parameters") e usa uma camada de reflexo para a mosca ir à
  comida. [VERIFICADO: repositório] O que é de vocês e não achei neles: a comparação com Olsen 2010 e a alça
  eLN → eLN.
- **Furo 10, os princípios tornam a correção impossível.** "Só parâmetro com fonte" impede corrigir a L1: a
  condutância elétrica eLN → PN não existe em nenhum conectoma (vocês mesmos verificaram hemibrain e BANC). Mas os
  parâmetros do próprio Shiu não são todos medidos (`w_syn` é parâmetro livre). [OPINIÃO] Sugiro distinguir:
  - **permitido:** parâmetro medido; parâmetro de modelo publicado e validado por experimento; ajuste contra dado
    **fisiológico** (curva de Olsen, taxas espontâneas, cinemática real);
  - **proibido:** ajuste contra o **comportamento-alvo** (a mosca chegar à fruta, a mosca andar).

### Processo (vale para as próximas decisões)
- **[OPINIÃO]** O SPEC priorizou **amplitude** (4 animais, painel, larva, voo) antes de **profundidade**. A pergunta
  científica ("o comportamento vem só do conectoma?") só foi testada pela primeira vez na Fase 3, e falhou nos dois
  circuitos recorrentes que a mosca precisa.
- **[OPINIÃO]** Faltou uma revisão de literatura dirigida antes de cada fase: Pugliese (set/2025), Collie (2026) e
  fly-odor-onoff (set/2026) teriam mudado decisões.
- **Diagnóstico unificador [HIPÓTESE com evidência forte]:** o LIF do Shiu (parâmetros uniformes, basal 0, sem
  adaptação, só sinapses químicas) foi validado em vias curtas e diretas. Nos circuitos recorrentes, ele falha:
  - o lobo antenal satura (Etapas C–E e o meu teste 1);
  - o cordão não oscila (3a e o meu teste 2).

  Minhoca e larva bateriam no mesmo muro; vocês mesmos registraram que o LIF não serve para os neurônios graduados
  do C. elegans (D-102).

---

## 3. Revisão de literatura e de repositórios: o que já existe

| Trabalho | O que faz | O que NÃO faz | Confiança |
|---|---|---|---|
| **Eon Systems** (demo de mar/2026) | Shiu + Lappalainen + NeuroMechFly, sincronizados a cada 15 ms | Pelas fontes secundárias, poucos DNs escolhidos à mão acionam **controladores motores pré-treinados**; a marcha não vem do conectoma | [SECUNDÁRIA]: LessWrong "No, we haven't uploaded a fly yet", the-decoder |
| **Eon no GitHub** (`eonsystemspbc`) | `fly-brain` = modelo do Shiu em 6 backends + benchmark (rótulo `nature_2026_07`); `flybody` = fork **sem alterações** (último commit do autor original, jul/2025); `pathintegrationBPU` (RNNs com pesos do conectoma); `NEURD-sandbox` | **Não encontrei o código da integração cérebro → corpo do demo** | [VERIFICADO: repositório] |
| Shiu et al. 2024, *Nature* 634:210 | LIF do cérebro inteiro; 91 % de 164 previsões corretas (alimentação e limpeza) | Sem junções comunicantes, neuromodulação ou atividade basal | [FONTE: resumo + Métodos lidos por vocês] |
| NeuroMechFly v2 (Wang-Chen et al. 2024, *Nat Methods*) | Corpo, visão, olfato, pluma de odor, retorno ascendente | Controle por CPG/regras ou aprendizado por reforço | [FONTE: resumo] |
| flybody (Vaxenburg et al. 2025, *Nature*) | Corpo anatômico, andar e voar | Controladores treinados por reforço | [FONTE: resumo] |
| Özdil et al. 2025 (arXiv 2509.06426) | Primeiro modelo musculoesquelético 3D das pernas, com músculos tipo Hill (OpenSim/MuJoCo) | Não é controlado por conectoma; o relatório da 3a diz que a versão no FlyGym cobre só a perna anterior esquerda | [FONTE: resumo] |
| **Pugliese et al. 2025** (bioRxiv) | Ritmo gerado pelo conectoma do VNC (modelo de taxa), DNg100/DNb08, CPG de 3 neurônios, 4 conectomas, DNb08 confirmado in vivo | **Sem corpo, sem malha fechada**. Os autores citam o acoplamento ao corpo como futuro | [VERIFICADO: repositório + FONTE: resumo] |
| `Lulzx/fly-brain` (amador, 1 commit, 22/09/2026) | Cordão em LIF (MaleCNS e BANC) com varredura de mecanismos | **Sem marcha.** No BANC, um modo bilateral em fase de ~8 Hz. O autor conclui que falta propriocepção acoplada ao corpo, que ele não implementou; a marcha do app é um gerador ajustado por CMA-ES | [VERIFICADO: repositório] |
| `Fly.exe` | MaleCNS inteiro + corpo, em GPU | "The walking is engineered": `HybridTurningController` | [VERIFICADO: repositório] |
| `webgpu-fly` | FlyWire + MANC em LIF + flybody | "the connectome scales that gait; it does not generate its rhythm" | [VERIFICADO: repositório] |
| `embodied-fly-lab` | FlyWire LIF + NeuroMechFly + odor + painel 3D | Mesma interface de DNs; sem cordão | [VERIFICADO: repositório] |
| `fly-brain-minecraft` / `fly-odor-onoff` | Saturação do lobo antenal documentada; dissecção da persistência | Sem correção fisiológica | [VERIFICADO: repositório] |
| FlyGM (Jin et al. 2026, arXiv 2602.17997) | Conectoma do cérebro como grafo controlador | Dinâmica **treinada** (imitação + PPO) | [FONTE: resumo; D-105 de vocês] |
| Li et al. 2026 (bioRxiv 10.64898/2026.08.21.745055) | Modelo do cérebro inteiro ajustado a cálcio espontâneo; hubs inibitórios sustentam o repouso | Pesos **treinados**; sem cordão; sem corpo | [FONTE: resumo; vocês leram] |
| Beiran & Litwin-Kumar 2025, *Nat Neurosci* | O conectoma sozinho frequentemente não restringe a dinâmica; poucos registros resolvem | Teoria | [FONTE: resumo] |
| Awesome-fly (`cobanov/awesome-fly`) | Mais de 50 projetos amadores com FlyWire/MaleCNS | Quase todos com marcha manual ou controle por "readout" | [VERIFICADO: repositório] |

**Síntese [OPINIÃO, a confirmar com busca sua]:** na busca que fiz, **ninguém mostrou marcha gerada pelo conectoma
do cordão acionando um corpo físico**, muito menos em malha fechada com propriocepção. Pugliese tem o ritmo sem
corpo; Lulzx tem o corpo sem ritmo; Eon, Fly.exe e webgpu-fly usam marcha manual ou treinada. Isso significa "não
encontrado nesta busca", não "inédito com certeza". Peço que você repita a busca (bioRxiv, arXiv, GitHub, laboratórios
Tuthill, Brunton, Ramdya e Turaga, 2025–2026).

---

## 4. Por que vejo potencial [OPINIÃO]

1. **A lacuna é real e está nomeada pelos próprios autores do estado da arte** (Pugliese, como trabalho futuro).
2. **O projeto já tem as peças que os outros não têm:**
   - mapa MN → músculo → junta a partir das anotações do BANC;
   - 941 proprioceptores transduzidos;
   - métrica de ritmo validada contra falso positivo;
   - conectoma híbrido;
   - disciplina de pré-registro e de ablação ("o resultado precisa sumir na ablação").
3. **É visualmente impressionante e cientificamente defensável ao mesmo tempo:** um vídeo da mosca andando com as
   pernas acionadas por 391 motoneurônios do BANC, o raster ao lado, e um segundo vídeo em que silenciar o gerador
   de 3 neurônios faz a mosca parar. É o oposto do "upload" da Eon: aqui nenhuma linha diz "ande".
4. **Qualquer desfecho tem valor:**
   - se a malha fechada gerar coordenação entre pernas, é um resultado inédito (até onde achei);
   - se não gerar, é o negativo mais forte até agora sobre "conectoma + propriocepção basta para andar?", que o
     Lulzx apontou como a pergunta aberta.

**Riscos [OPINIÃO]:**
- O ritmo do Pugliese pode depender de detalhes (subgrafo T1, limiar de ≥ 5 sinapses, réplicas sorteadas,
  ajuste do estímulo) e não se transferir para o VNC inteiro do BANC. O Lulzx relata que um modelo de taxa "após
  Pugliese" deu ondas lentas no cordão inteiro, não passada.
- A coordenação entre pernas (trípode) pode não emergir.
- O mapa MN → junta é fora do conectoma.
- Laboratórios profissionais provavelmente estão fazendo o mesmo, então há risco de ser antecipado.
- O modelo de taxa não é biofísico.

---

## 5. Caminho proposto (etapas com critério de sucesso e de parada)

Todas com pré-registro, fila separada da análise e registro no NON_CONNECTOME, como vocês já fazem.
**Regra contra trapaça:** nenhum parâmetro do cordão é ajustado para a mosca andar. Usar o ensemble do Pugliese
como está e relatar **que fração das réplicas anda**.

**Etapa 0: conferir esta auditoria (1 sessão).**
- Rodar os meus dois scripts (`auditoria/`) e confirmar os números.
- Ler o Pugliese completo e confirmar ou refutar os itens marcados [FONTE].
- Repetir a busca de novidade.
- **Parar aqui** se eu estiver errado sobre o essencial (por exemplo, se alguém já publicou marcha do VNC num corpo).

**Etapa 1: reproduzir o Pugliese exatamente (a "Fase 1" do cordão).**
- Código dele + dados do Zenodo (record 22260924).
- DNg100 → ritmo no T1 do MANC; relatar a fração de réplicas rítmicas.
- Depois, a pipeline dele no **BANC T1** (os dados já estão no repositório dele).
- **Critério:** reproduzir numericamente uma figura principal, como a Fase 1 fez com o Shiu.
- **Conferir o custo em CPU:** o tutorial diz ~30–60 s por 2 s simulados de 4.604 neurônios num desktop.

**Etapa 2: do T1 para o VNC inteiro do BANC do projeto (6 pernas), em malha aberta.**
- Modelo de taxa do Pugliese no cordão do híbrido; DNg100 e DNb08 isolados.
- Métrica v2 congelada por perna; fases entre pernas registradas (sem exigir trípode ainda).
- **Critério pré-registrado:** ritmo em ≥ N pernas nas réplicas.
- **Parada:** se nada oscilar no VNC inteiro, testar a hipótese de subgrafo (T1 isolado × VNC inteiro) antes de
  qualquer outra mudança.

**Etapa 3: corpo em malha aberta.**
- Taxas dos MNs → ativação muscular → junta.
- Para fugir do problema do batente que encerrou a 3a, começar pelos **atuadores de posição padrão do FlyGym**
  (ângulo-alvo a partir da diferença flexor − extensor; mapa fora do conectoma, registrado).
- Depois, evoluir para músculos tipo Hill (Özdil 2025) ou para torque com `armature`.
- Primeiro na bolinha, depois no chão.

**Etapa 4: malha fechada com os 941 proprioceptores. É o núcleo científico.**
- Comparar malha aberta × malha fechada: a propriocepção pelo conectoma real cria alternância e coordenação
  entre pernas?
- **Controles:** VNC embaralhado com graus preservados; proprioceptores removidos; CPG de 3 neurônios silenciado;
  DN desligado.

**Etapa 5: comando pelo próprio VNC.**
- Virada pelo DNa02 (Yang et al. 2024, *Cell*: o DNa02 unilateral encurta o passo ipsilateral). [FONTE: resumo;
  o projeto leu o preprint, não a versão da *Cell*]
- Ré pelo MDN (Bidaye et al. 2014, *Science*). [NÃO VERIFICADO: o próprio projeto marcou essa fonte como não lida]
- Tudo passando pelo cordão.

**Etapa 6 (horizonte, alto risco): ligar o cérebro.**
- Primeiro por vias validadas.
- Depois, corrigir o lobo antenal contra fisiologia (curva de Olsen 2010, retorno ao basal, KCs esparsas, **com
  atividade espontânea ligada**), para chegar a uma mosca que anda até o odor com marcha **e** direção vindas do
  conectoma. Até onde encontrei, ninguém tem isso.

**Suspender:** minhocas, larva, voo, painel e o terrário decorativo. O motor, os dados e a infraestrutura da 3a ficam.

**Entregáveis "impressionantes":**
- vídeo lado a lado (corpo + raster dos 391 MNs + fases das pernas);
- vídeo da ablação (o gerador silenciado faz a mosca parar);
- comparação com a cinemática real (o `MotionSnippet` do FlyGym já está no projeto);
- repositório público e um preprint curto.

---

## 6. Alternativas para você comparar (não escolha a minha por inércia)

| Objetivo | Novidade (na minha busca) | Impacto visual | Risco | Observação |
|---|---|---|---|---|
| **A. Marcha pelo VNC num corpo, em malha fechada** (proposta) | Alta | Alto | Médio a alto | Aproveita a 3a; a lacuna foi nomeada pelo Pugliese |
| B. Olfato fisiologicamente correto no cérebro inteiro | Média a alta | Baixo | Médio | Bom preprint técnico; pouco "impressionante" em vídeo |
| C. A + B: a mosca vai ao odor com marcha e direção do conectoma | Muito alta | Muito alto | Muito alto | Horizonte; depende de A e B |
| D. Nota técnica: "o LIF do Shiu falha em circuitos recorrentes" | Média | Nulo | Baixo | Pode sair como subproduto de A e B |
| E. Voltar ao terrário | Baixa | Médio | Baixo | Reproduz o que existe |

---

## 7. O que eu peço de volta

1. Uma tabela: **item da auditoria | concorda / discorda / não verificável | por quê | evidência**.
2. Sua opinião sobre o objetivo: A, outra das alternativas ou uma que eu não vi. Com argumentos.
3. Se concordar com a direção, o prompt do Claude Code para a **Etapa 0**: rodar os meus dois scripts, ler o
   Pugliese e refazer a busca de novidade, sem construir nada ainda.
4. Com o Marcelo, a revisão dos princípios do projeto (item 10 da seção 2), antes da Etapa 1.

Obrigado. Se eu estiver errado em algo essencial, é melhor descobrir agora.
