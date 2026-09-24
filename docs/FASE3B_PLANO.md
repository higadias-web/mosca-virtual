# Plano da Fase 3b: mosca livre no terrário, DNs → controlador (APROVADO em 2026-09-23, com os ajustes de §F)

A 3a terminou como "loop fechado não testável com este aparato no prazo" (`docs/FASE3A_RELATORIO.md`).
Pela D-106, a 3b segue com a opção (a): **os DNs do cérebro FlyWire 783 modulam um controlador de marcha
do FlyGym**. O cordão do BANC sai do caminho da locomoção. O cérebro é o mesmo da Fase 1 (LIF do Shiu,
validado na Fig. 1D), e os sensores são os da Fase 2.

## 0. Peças e o que já existe (verificado no código)
- **Corpo:** `flygym_demo.complex_terrain.make_locomotion_fly`, com atuadores de POSIÇÃO (kp 45 µN·mm/rad,
  faixa ±65), passivos 0,05/0,06 e adesão tarsal. É o corpo do terrário da Fase 2
  (`terrario/body/fly.py:build_scene`). O aparato de torque da 3a não entra.
- **Controlador:** `flygym_demo.complex_terrain.turning_controller.HybridTurningController` (FlyGym 2.1).
  - Recebe um sinal descendente de 2 dimensões, `descending_signal = [δ_E, δ_D]`.
  - Para cada lado, |δ| é a amplitude do passo (ganho sobre o passo real gravado) e o sinal de δ é o
    sentido (δ < 0 inverte a frequência do lado, para trás). A frequência base é 12 Hz.
  - O modelo e as regras de correção (retração e tropeço) vêm do tutorial "turning" e do NeuroMechFly v2.
- **DNs na anotação do FlyWire** (`third_party/flywire_annotations/.../Supplemental_file1_neuron_annotations.tsv`,
  Schlegel et al. 2024):
  - DNp09, DNa01, DNa02 e DNg13: 1 célula por lado;
  - MDN: 2 por lado;
  - todos colinérgicos (`top_nt`);
  - oDN1 e BPN (Bidaye et al. 2020) **não** aparecem como tipo nessa anotação e ficam de fora.
  - Os root_ids serão casados com o conectoma carregado (`connectomes.load("783")`) antes de qualquer
    execução, **sem herdar listas de artigos** (pendência da Fase 3 no CLAUDE.md).

## (a) Como os DNs modulam o CPG

**Leitura dos DNs** (NON-CONNECTOME): taxa de disparo de cada grupo e lado, filtrada com constante de
tempo τ_r = 100 ms (escolha, sem fonte). Ela vira [δ_E, δ_D] a cada 10 ms.

| Função | Grupo (por lado) | Ligação proposta | Fonte da ligação DN → comportamento | Força da evidência |
|---|---|---|---|---|
| **Início e avanço** | DNp09 | a taxa de DNp09 dos dois lados soma no avanço: δ_E = δ_D = g_f · sat(r_E + r_D). **Parar** é a volta de δ a 0 quando a taxa cai | Bidaye et al. 2020, *Neuron* 108:469, "Two brain pathways initiate distinct forward walking programs in Drosophila": ativar P9 (= DNp09) inicia e mantém a marcha para a frente | ativação suficiente, confirmada na fonte |
| **Curva** | DNp09 unilateral + DNa02 (e DNa01) | assimetria: δ_lado = avanço × (1 − g_t · r_DNa02,lado / r_ref), o que encurta o passo de um lado. DNp09 unilateral também gera curva | DNp09: Bidaye et al. 2020, "P9 drives forward walking with ipsilateral turning". DNa02/DNa01: Yang et al. 2024, *Cell*, "Fine-grained descending control of steering in walking Drosophila": dois tipos descendentes, um que alonga o passo do lado de fora da curva e outro que encurta o do lado de dentro | DNp09: confirmada. **Qual DN alonga e qual encurta, e para que lado cada um vira: A CONFIRMAR no texto completo** (o acesso ao texto foi bloqueado nesta sessão). A ligação só entra depois de confirmada; se não for, só DNp09 controla a curva |
| **Velocidade** | DNp09 (magnitude) | a velocidade sai de \|δ\|, ou seja, da amplitude do passo. A frequência fica fixa em 12 Hz | nenhuma fonte liga a taxa de um DN específico à velocidade de passada. Mendes et al. 2013 mostram que a mosca real aumenta a frequência com a velocidade, e o controlador não faz isso | **sem fonte**: a relação taxa → amplitude (g_f, saturação) é escolha e fica toda no NON_CONNECTOME |
| **Ré** | MDN | se r_MDN > limiar, o sinal de δ inverte nos dois lados, e \|δ\| = g_b · sat(r_MDN) | Bidaye, Machacek, Wu e Dickson 2014, *Science* 344:97, "Neuronal control of Drosophila walking direction": ativar MDN basta para a marcha para trás, e bloquear MDN impede a ré diante de barreira | ativação suficiente e necessidade, confirmadas na fonte |
| **Parada ativa** | nenhum DN dedicado | não é modelada como comando: a parada é a queda da taxa dos DNs de avanço | Sapkal et al. 2024, *Nature* 634:191, "Neural circuit mechanisms underlying context-specific halting in Drosophila": um mecanismo "walk-OFF" (neurônios GABAérgicos no cérebro inibindo os DNs de marcha) e um "brake" (no cordão, sem representação aqui) | o walk-OFF já está no conectoma do cérebro; o brake fica de fora, declarado |

O que o conectoma decide: **se** e **quando** esses DNs disparam em resposta aos sentidos. O que a
engenharia decide: a tradução das taxas em amplitude e sentido do passo.

## (b) O que entra no `docs/NON_CONNECTOME.md`
1. **O CPG inteiro:** 6 osciladores acoplados, frequência de 12 Hz, vieses de fase do trípode e
   convergência (`cpg_controller.py`); passos pré-programados a partir da cinemática gravada
   (`preprogrammed.py`); regras de correção do controlador híbrido (retração, tropeço; limiares e taxas).
2. **O mapeamento DN → CPG:** a escolha dos grupos (pela literatura acima), a leitura da taxa
   (τ_r = 100 ms), os ganhos g_f, g_t, g_b, a saturação, o limiar do MDN, a regra de curva e a
   frequência fixa.
3. **O corpo com atuadores de posição** (kp 45), a adesão e os passivos de `make_locomotion_fly`.
4. **A transdução sensorial** da Fase 2 para taxas de Poisson nos ORNs, GRNs e mecanorreceptores (IDs da
   v783; a pendência da Fase 3 continua).
5. **A ausência** de atividade de fundo no LIF: sem estímulo, os DNs ficam calados e a mosca fica
   parada. É declarado como propriedade do modelo, não como comportamento.

Os ganhos (g_f, g_t, g_b, r_ref, limiar do MDN) são fixados **uma vez**, antes de qualquer teste
sensorial, por um critério independente: a estimulação direta de cada grupo a 100 Hz (a taxa dos
experimentos do Shiu) deve dar |δ| = 1 no controlador (o passo real gravado). Nenhum ajuste depois de
ver o comportamento sensorial.

## (c) Ablação: o comportamento tem de vir do conectoma
- **A1, silenciar o grupo de DNs** (DNp09; DNa02/DNa01; MDN) no LIF, com o mesmo estímulo sensorial:
  a modulação correspondente precisa sumir.
  - *Ressalva:* com esta arquitetura, isso é quase garantido por construção, porque sem taxa no DN
    lido não há δ. Por isso a A1 prova o caminho, não a origem.
- **A2, silenciar os neurônios sensoriais do estímulo** (p. ex., os ORNs do odor da fruta; os GRNs de
  açúcar), com os DNs intactos: a mudança nas taxas dos DNs **e** no comportamento precisa sumir. **É
  esta a ablação que mostra que o comportamento vem da rede.**
- **A3, conectoma embaralhado** (controle; proposta opcional): pesos do cérebro permutados preservando
  os graus de entrada e saída de cada neurônio, com o mesmo estímulo. Se a resposta dos DNs se mantiver,
  ela não depende do cabeamento específico. Custo: 1 execução por semente e condição.

## (d) Critérios de sucesso (fixados antes; o que não tem fonte está marcado)

| # | Critério | Números | Origem dos números |
|---|---|---|---|
| C1 | **Interface, avanço:** estimulação direta de DNp09 bilateral a 100 Hz por 2 s | velocidade ≥ 5 mm/s durante o estímulo; < 1 mm/s 0,5 s depois de desligar; 5 de 5 sementes | a velocidade do CPG do FlyGym com δ = 1 é ~14 mm/s (BENCHMARK, Fase 0). O limite de 5 mm/s é **escolha** |
| C2 | **Interface, curva:** DNp09 unilateral (e DNa02, se confirmado) | velocidade angular média ≥ 30°/s, com o sentido previsto pela fonte, em ≥ 4 de 5 sementes | o sentido vem da fonte (DNp09: ipsilateral). 30°/s é **escolha** |
| C3 | **Interface, ré:** MDN bilateral a 100 Hz | deslocamento para trás ≥ 1 mm em 2 s, em ≥ 4 de 5 sementes | o sentido vem da fonte; 1 mm é **escolha** |
| C4 | **Comportamento sensorial, o critério central:** mosca no terrário, com o campo de odor da fruta ligado contra desligado, 10 sementes pareadas, 20 s | (i) a taxa de pelo menos um grupo de DNs difere entre odor e sem odor (Wilcoxon pareado, p < 0,05); (ii) a distância mínima até a fruta é menor com odor (Wilcoxon pareado, p < 0,05) | teste e α são **escolha**. É o critério da SPEC: "mudança de comportamento com estímulo olfativo/gustativo, sem regra programada" |
| C5 | **Ablações:** A2 elimina o efeito de C4 (nem (i) nem (ii) com p < 0,05, com o efeito mediano reduzido em ≥ 50 %); A1 elimina a modulação correspondente | — | 50 % é **escolha** |

C1–C3 validam a interface; eles **não** são comportamento emergente. O resultado da 3b é C4 + C5. Se o
odor não mudar a taxa dos DNs no LIF do Shiu, C4 dá negativo, e esse é um resultado legítimo a relatar.
Os ganhos não são reajustados para "fazer funcionar".

## (e) Prazo, marco e saída
- **Prazo: 4 sessões** (as figuras de diagnóstico de cada sessão não contam).
  - S1: IDs dos DNs e dos sensores na v783; confirmação da ligação DNa02/DNa01 no texto completo de
    Yang et al.; implementação do mapeamento e dos ganhos pelo critério de (b); C1–C3.
  - S2: C4 (odor).
  - S3: C5 (ablações) e, se sobrar prazo, gustação nos tarsos (GRNs → DNs), sem a probóscide (essa é da
    entrega P).
  - S4: relatório e vídeo.
- **Marco na S2:** se **C1–C3 não passarem** com os ganhos fixados, o problema é da interface, não do
  conectoma. É permitida **uma** revisão da ligação, e só com fonte; se falhar de novo, a 3b encerra
  como "interface DN → CPG não validada", com relatório.
- **Saída:**
  - Sucesso (C1–C5): relatório da 3b, vídeo de 10–20 s (WebM) da mosca indo à fruta com odor, e o
    controle com os ORNs silenciados. A mosca entra na Fase 5.
  - C1–C3 passam e C4 dá negativo: relatório com o negativo (o odor não modula os DNs de marcha no
    modelo). A mosca anda no terrário só por estimulação direta, o que **não** é comportamento emergente.
    Pela regra de harmonia da SPEC, o usuário decide se ela fica na cena principal.
- **Custo estimado:** terrário com sensores ~3,4 s/s mais o cérebro ~0,7 s/s (BENCHMARK), ~4–5 s/s
  por processo sozinho. Um episódio de 20 s leva ~1,5 min, e C4 + C5 (≈ 10 sementes × 4 condições) cabe
  em < 1 h com 10 processos.

## Fontes
- Bidaye et al. 2020, *Neuron* 108:469 (P9 = DNp09).
- Bidaye, Machacek, Wu e Dickson 2014, *Science* 344:97 (MDN).
- Yang et al. 2024, *Cell* (DNa02 e outro tipo descendente na curva; o detalhe está a confirmar).
- Sapkal et al. 2024, *Nature* 634:191 (parada).
- Mendes et al. 2013, *eLife* 2:e00231 (frequência × velocidade).
- FlyGym 2.1: `flygym_demo/complex_terrain/{turning_controller,hybrid_controller,cpg_controller,common}.py`;
  o tutorial "turning" (`third_party/flygym-gymnasium/doc/source/tutorials/turning.rst`).

## F. Ajustes da aprovação (2026-09-23, commitados antes de executar)

**F1. A S1 começa com um teste de viabilidade sem corpo** (`experiments/phase3b_viability.py`). Se ele
der negativo, a 3b vai direto ao relatório, **sem construir a interface**.
- Conectoma: FlyWire 783, só o cérebro (`connectomes.load("783")`), com o LIF do Shiu (os parâmetros
  da Fase 1).
- **Odor (modelo, NON-CONNECTOME):** Poisson a **100 Hz** em todos os ORNs dos glomérulos **DM1 e VA2**,
  nos dois lados (135 neurônios: 68 ORN_DM1 e 67 ORN_VA2, pela anotação do FlyWire; todos os root_ids
  existem na v783).
  - Os glomérulos vêm de Semmelhack & Wang 2009 (*Nature*, "Select Drosophila glomeruli mediate innate
    olfactory attraction and aversion"): no vinagre de maçã em concentração baixa, DM1 e VA2 são
    necessários para a atração, e ativar cada um basta. É a referência para odor de fruta fermentada.
  - Os **100 Hz** são **sem fonte**: é a convenção de estímulo do Shiu, dentro da faixa de 10–200 Hz da
    Fase 1.
- Controle: sem estímulo, com a **mesma semente** (pareado). 10 sementes (1000–1009), 1 s por
  execução, como os trials do Shiu.
- Medida: taxa média por célula de cada grupo durante o estímulo:
  - **DNp09** (2 células);
  - **MDN** (4);
  - **DNa01/02** (DNa01 + DNa02, 4 células).
- **Critério (fixado agora):** um grupo **muda** se o Wilcoxon pareado bilateral (odor × controle, 10
  sementes) der p < 0,05/3 (Bonferroni sobre os 3 grupos) **e** a diferença mediana for ≥ 1 Hz.
  - A 3b segue para a interface se **pelo menos um** grupo mudar; se nenhum mudar, relatório.
  - Os limiares de 1 Hz e α = 0,05 são **escolha**.
- Descritivo, que não decide: se a diferença mediana chega a **≥ 10 Hz**. Pelo critério de ganho (100 Hz
  → |δ| = 1), 10 Hz dá |δ| ≈ 0,1, cerca de 1,4 mm/s. Abaixo disso a interface andaria perto de parada,
  e C4(ii) fica improvável.
- Nota: sem estímulo, o LIF do Shiu não tem atividade de fundo, então o controle deve ficar em 0 Hz.

**F2. C4 com grupo principal fixado:** o **DNp09** é o grupo principal de C4(i) (α = 0,05). MDN e
DNa01/02 entram com Bonferroni (α = 0,05/2 cada). C4(ii), a distância até a fruta, não muda.

**F3. Conectoma embaralhado obrigatório (A3 deixa de ser opcional):**
- Pesos do cérebro reorganizados por trocas duplas de arestas (a→b, c→d ⇒ a→d, c→b). Isso preserva o
  grau de saída e de entrada de cada neurônio. O peso e o sinal viajam com a aresta, então o sinal
  continua sendo o do pré-sináptico.
- Número de trocas: 10× o número de arestas. 5 embaralhamentos independentes.
- **Critério em C5:** no conectoma embaralhado, o efeito do odor em C4(i) (DNp09) **e** em C4(ii) precisa
  cair ≥ 50 % (efeito mediano) em relação ao conectoma real. Se não cair, a resposta não depende do
  cabeamento específico, e isso é relatado como tal.

**F4. Registrados no NON_CONNECTOME.md como sem fonte:** o modelo de odor (a taxa de 100 Hz e, na
C4, a relação concentração → taxa), o filtro da taxa dos DNs antes do CPG (τ_r = 100 ms) e os 100 Hz
do critério de ganho.

## G. S1: resultado do teste de viabilidade (2026-09-23)

`results/phase3b/viability.json`, `viability_runs.csv`: 10 sementes pareadas, 1 s. Os ORNs de DM1+VA2
dispararam a 99 Hz (mediana).

| Grupo | Odor (mediana) | Controle | Diferença mediana (mín–máx) | Wilcoxon p | Muda (p < 0,0167 e ≥ 1 Hz) | ≥ 10 Hz |
|---|---|---|---|---|---|---|
| **DNp09** (principal de C4) | 0 Hz | 0 Hz | 0 (0–0) | 1 | **não** | não |
| MDN | 0 Hz | 0 Hz | 0 (0–0) | 1 | **não** | não |
| **DNa01/02** | 20,75 Hz | 0 Hz | 20,75 (18,75–22,75) | 0,002 | **sim** | sim |

**Veredito "viável": PENDENTE** (decisão do usuário, 2026-09-23), até o controle com conectoma
embaralhado (§H, V1). O critério de §F1 foi cumprido por um grupo (DNa01/02), mas falta o critério
obrigatório de especificidade (§F3).

Notas (corrigidas na revisão):
- **99 × 100 Hz:** 100 Hz é a taxa de ENTRADA pré-registrada; 99,2 ± 0,9 Hz é a taxa de SAÍDA medida
  (média de 135 ORNs em 1 s, entre as 10 sementes). A dispersão bate com o sorteio de Poisson (~0,86 Hz
  esperado), e o déficit médio de 0,8 Hz não foi investigado.
- **DNp09 e MDN ficam em 0 Hz também sem odor:** o modelo não tem atividade espontânea, então **uma
  inibição desses grupos pelo odor não é detectável neste teste**. "Não muda" quer dizer "não é
  excitado", não "não é afetado".
- **O sentido da ligação do DNa01/02 com a curva está NÃO VERIFICADO.** Yang et al. 2024 (*Cell*) só
  entra na interpretação com a referência completa e o trecho lido. Na revisão, o texto não abriu
  (bioRxiv 429, Cell 403).
- **Os "10 Hz"** saem da conclusão. Eles estavam em §F1 como descritivo, antes de rodar, mas a
  leitura "relevante para mover a mosca" depende do critério de ganho (B-ganho), que não tem fonte.
  Registrado no NON_CONNECTOME.md (B-10Hz).
- A continuação aguarda a revisão do usuário. Nada da interface foi construído.

## H. S1: lateralidade e especificidade, opção (2) (pré-registro, commitado antes de rodar)

`experiments/phase3b_laterality.py`; embaralhamento em `terrario/brain/shuffle.py` (trocas duplas de
arestas, 10 × E trocas bem-sucedidas, sementes 0–4, com verificação de grau de entrada igual, sem
arestas repetidas e sem autolaços novos; o grau e a força de saída ficam iguais por construção).
- Conectomas: **real** e **5 embaralhados** (§F3).
- Condições:
  - **controle** (sem estímulo);
  - **simétrico** (ORNs de DM1+VA2 dos dois lados, 100 Hz);
  - **só esquerda** (ORNs com `side == left`);
  - **só direita**.
- 10 sementes pareadas (1000–1009), 1 s. A condição simétrica no conectoma real repete o teste de
  viabilidade (mesmas sementes, então resultado idêntico esperado).
- Medida: **taxa por célula** de DNp09 (E, D), MDN (2 E, 2 D), DNa01 (E, D) e DNa02 (E, D).

**V1, especificidade da viabilidade (critério de §F3, aplicado ao DNa01/02):**
- efeito_real = mediana entre as sementes de [taxa do grupo DNa01/02 no simétrico − controle], no
  conectoma real;
- efeito_emb = mediana, entre os 5 embaralhamentos, da mesma medida;
- **específico se efeito_emb ≤ 0,5 × efeito_real.** Se não for, a resposta ao odor não depende do
  cabeamento específico, e isso é relatado como tal.

**V2, "carrega lado"** (fixado agora), para cada tipo T ∈ {DNa01, DNa02, DNp09, MDN}:
- por semente, Δ_T = ½[(r_E − r_D | só esquerda) + (r_D − r_E | só direita)], ou seja, ipsilateral −
  contralateral ao lado estimulado. No MDN, a taxa do lado é a média das 2 células;
- teste: **Wilcoxon pareado bilateral de Δ_T contra 0**, com **α = 0,05/4 = 0,0125** (Bonferroni
  sobre os 4 tipos);
- diferença mínima: **|mediana Δ_T| ≥ 2 Hz** (**escolha, sem fonte**);
- T "carrega lado" se as duas condições valerem. O sinal (ipsi > contra ou o contrário) é relatado,
  **sem** interpretação de sentido de curva (a ligação não está verificada);
- especificidade lateral (só para os tipos que carregam lado): |Δ| mediana dos 5 embaralhamentos ≤
  0,5 × |Δ_real|.

Execução separada da análise: `run` grava `runs/phase3b/laterality_runs.csv` e `LAT_OK` com a contagem
(240 = 6 conectomas × 4 condições × 10 sementes); `analyze` se recusa a rodar sem `LAT_OK` completo.

## I. S1: resultado de lateralidade e especificidade (2026-09-23)

`results/phase3b/laterality.json`; brutos em `runs/phase3b/laterality_runs.csv` (`LAT_OK` 240/240). Análise
rodada só com a fila completa.

**V1, especificidade: cumprida.**
- DNa01/02, simétrico − controle: **20,75 Hz no conectoma real**, idêntico ao teste de viabilidade
  (mesmas sementes).
- Nos 5 embaralhados: 0; 0,5; 0; 0; 0 Hz (mediana 0), bem abaixo do limite de 0,5 × 20,75.
- **Pelos critérios de §F1 e §F3, o veredito "viável" fica confirmado**: a resposta do DNa01/02 ao odor
  depende do cabeamento específico.

**V2, "carrega lado": nenhum tipo carrega lado.**

| Tipo | Δ ipsi − contra (mediana) | p (α = 0,0125) | Carrega lado |
|---|---|---|---|
| DNp09 | 0 | 1 | não (0 Hz em todas as condições) |
| MDN | 0 | 1 | não (0 Hz em todas as condições) |
| DNa01 | −1,0 Hz | 0,47 | não |
| DNa02 | +0,75 Hz | 0,64 | não |

Taxas por célula no conectoma real (mediana, E / D), descritivas:

| Tipo | Controle | Simétrico | Só esquerda | Só direita |
|---|---|---|---|---|
| DNa01 | 0 / 0 | 21 / 8 | 19,5 / 9 | 18 / 6 |
| DNa02 | 0 / 0 | 52 / 0,5 | 53 / 0,5 | 51,5 / 0 |

**Achado descritivo, fora dos critérios:** a resposta é **assimétrica e fixa**. A célula esquerda de
DNa02 (e, em menor grau, a de DNa01) responde forte, e a direita quase não responde, **qualquer que
seja o lado dos ORNs estimulados**.
- Leitura: o modelo não codifica o lado do odor nesses DNs. Nele, o odor ativa sobretudo os DNs de
  curva do lado esquerdo.
- A causa não foi investigada. Hipóteses: assimetria real do caminho no conectoma ou diferença de
  reconstrução entre os hemisférios.
- O sentido da curva que isso produziria: ver §J (verificado depois, no preprint de Yang et al.).
- Consequência para a interface aprovada: o odor não gera avanço (o DNp09 fica em 0) e geraria um
  **viés fixo de curva para um lado**, sem informação sobre onde está a fonte.

A continuação aguarda a revisão do usuário. Nada da interface foi construído.

## J. S1: revisão de V1/V2, sem novas simulações (2026-09-23)

V1 e V2 foram aceitos pelo usuário. Esta revisão só lê o que já existe: fontes, anotações e o grafo.

**J1. Yang et al.: o sentido da ligação do DNa02, agora verificado.**
- Referência lida: Helen H. Yang, Luke E. Brezovec, Laia Serratosa Capdevila, Quinn X. Vanderbeck,
  Atsuko Adachi, Richard S. Mann e Rachel I. Wilson, "Fine-grained descending control of steering in
  walking *Drosophila*", **preprint bioRxiv v2 (30/10/2023), PMC10614758**. A versão revisada por pares
  (*Cell* 2024) **não foi lida**.
- Trecho, na legenda da Fig. 4A, sobre o estímulo optogenético unilateral do DNa02: "a brief pulse of
  light (200 ms) triggered a turn in the direction of the stimulated cell, with no change in forward
  velocity" → **curva ipsilateral**.
- Legenda da Fig. 4G: "DNa02 shortens steps on the inside of a turn, while DNg13 lengthens steps on the
  outside of a turn".
- O preprint **não descreve o efeito de ativar o DNa01** (só que ele se correlaciona com a velocidade
  de rotação, Fig. 2). O sentido do DNa01 continua **não verificado**.
- **Interpretação atualizada do viés:** o odor ativa sobretudo o DNa02 **esquerdo** (52 contra 0,5 Hz).
  Pelo trecho acima, isso preveria uma **curva para a esquerda da mosca** (ver J2 sobre a convenção de
  lado), sem avanço (o DNp09 fica em 0) e **independente do lado do odor**. Pelo trecho da Fig. 4G, a
  regra "encurtar o passo do lado ipsilateral ao DNa02 ativo" do plano (a) passa a ter fonte, no preprint.

**J2. ORNs estimulados e convenção de lado.**
- Contagens: **só esquerda = 69 ORNs** (35 ORN_DM1 + 34 ORN_VA2); **só direita = 66** (33 + 33); simétrico = 135.
- Campo usado: `side` de `Supplemental_file1_neuron_annotations.tsv` (repositório `flywire_annotations`,
  commit 8587524, versão ≥ 3.1.0, materialização `783`; a v2.1.0 era a de Schlegel et al. 2024: Schlegel P,
  Yin Y, Bates AS, Dorkenwald S, Eichler K, Brooks P, … Costa M, Seung HS, Murthy M, Hartenstein V, Bock DD,
  Jefferis GSXE, "Whole-brain annotation and multi-connectome cell typing of Drosophila", *Nature* 634:139–152
  (2024), doi:10.1038/s41586-024-07686-5).
  Segundo o README das tabelas, `side` é "the soma side for brain-intrinsic neurons and the nerve-entry
  side for sensory/ascending neurons", ou seja, nos ORNs, **o lado do nervo antenal por onde entram**.
- **Convenção:** a documentação do `fafbseg` ("Mirroring FlyWire neurons", com base em Schlegel et al. 2024, acima)
  diz que "the FAFB image dataset underlying it was accidentally flipped along the left-right (i.e. "x")
  axis" e que "the official `side` labels we provide for FlyWire are biologically correct". Portanto
  **`left` = lado esquerdo da mosca**.

**J3. Conectividade de DM1/VA2 até DNa01/DNa02** (`experiments/phase3b_connectivity.py`,
`results/phase3b/connectivity.{csv,json}`). Pesos com sinal do conectoma do LIF, produtos de contagens
de sinapses nos caminhos de 2 saltos:
- **Direto:** nenhuma sinapse de ORN_DM1, ORN_VA2, DM1_lPN ou VA2_adPN, de nenhum lado, em DNa01 ou
  DNa02, de nenhum lado.
- **2 saltos:** **nada chega às cópias esquerdas** de DNa01 e DNa02 **nem ao DNa01 direito**. Só o
  **DNa02 direito** recebe caminhos, todos mínimos:
  - ORN_DM1 esquerdo +5 e direito +2 (1 intermediário);
  - DM1_lPN direito: E 1, I 6, saldo −5 (via DNb09, glutamatérgico, portanto inibitório no modelo, e
    via M_spPN5t10);
  - VA2_adPN direito +1.
- **Comparação das duas cópias:** nos caminhos de até 2 saltos, a assimetria vai no sentido **oposto**
  ao da simulação (o direito recebe um pouco, o esquerdo nada). **A forte ativação do DNa02 esquerdo
  vem de caminhos com 3 ou mais saltos, que não foram analisados.** A causa da assimetria continua
  aberta.

**J4. O que o embaralhamento preservou** (verificado nos 5):
- conjunto de pesos (com sinal) idêntico;
- fração de arestas inibitórias idêntica (0,3997);
- grau de saída, força de saída com sinal (portanto o sinal E/I de cada neurônio pré-sináptico) e grau
  de entrada idênticos em todos os neurônios;
- menos de 0,003 % das arestas ficou no lugar.
- **O que não se preserva:** a força de entrada E e I de cada neurônio (correlação com a original de
  0,77 e 0,75), que muda com a troca dos parceiros. É uma consequência esperada do método pré-registrado.

**J5. Ressalvas para o relatório:**
- **A ausência de lado pode vir do modelo de estímulo.** Os ORNs de um lado recebem a mesma taxa (100
  Hz) em todos os neurônios, sem gradiente de concentração entre as antenas nem diferença de tempo, e
  o LIF trata cada sinapse só pela contagem, sem propriedades de liberação que possam ser assimétricas.
  O teste mostra que, **com este estímulo e este modelo**, os DNs não carregam o lado. Isso não prova
  que o conectoma não tenha a informação.
- **A inibição não é detectável:** DNp09 e MDN ficam em 0 Hz também sem odor (o modelo não tem
  atividade espontânea), e o mesmo vale para as cópias silenciosas de DNa01/02. Uma inibição pelo odor
  não apareceria neste teste.

## K. S1: de onde vem a ativação do DNa02 esquerdo (pré-registro, commitado antes de rodar; teto: esta sessão)

Pedido do usuário: **não** analisar caminhos de 3 saltos no grafo estático. Em vez disso, usar a atividade
simulada (`experiments/phase3b_backtrace.py`):
1. **odor:** odor bilateral (ORNs de DM1+VA2 a 100 Hz), conectoma real, **5 sementes** (1000–1004), 1 s,
   salvando os spikes de **todos** os neurônios.
2. **tree:**
   - r_j = taxa média de cada neurônio nas 5 sementes;
   - contribuição de j para k = W(j→k) · r_j, com W = contagem de sinapses com sinal, a mesma do LIF;
   - a partir do **DNa02 esquerdo**, os **3 pré-sinápticos de maior contribuição positiva**, e recua do
     mesmo jeito até **3 níveis** (≤ 3 + 9 + 27 nós);
   - os 3 maiores inibitórios de cada nó entram só como descritivo;
   - tipo, lado, superclasse e transmissor vêm da anotação.
3. **silence:** silencia os **1, 2 e 3 principais do nível 1**, de forma cumulativa (top1; top1+2;
   top1+2+3). As sinapses de saída são zeradas, como em `model.py:silence` do Shiu. Mesmo odor e mesmas
   sementes. A escolha dos neurônios é algorítmica (a ordem do passo 2), sem escolha manual.
4. **evaluate:** **critério de QUEDA** (fixado agora): a mediana da queda relativa do DNa02 esquerdo
   contra o intacto da mesma semente precisa ser **≥ 50 %**, e a queda precisa ser **≥ 50 % em ≥ 4 de 5
   sementes**. Com 5 sementes, um Wilcoxon não alcança p < 0,05 bilateral, por isso o critério é de
   magnitude. DNa02 direito, DNa01 E/D e o total de spikes entram como descritivos.

Cada etapa exige a anterior completa (`ODOR_OK`, `tree_OK.json`, `SIL_OK`).

**Fontes da interface, atualizadas:**
- **DNa01:** Rayshubskiy A, Holtz SL, Bates AS, Vanderbeck QX, Serratosa Capdevila L, Rockwell V, Wilson
  RI, "Neural circuit mechanisms for steering control in walking Drosophila", *eLife* 2025,
  doi:10.7554/eLife.102230 (lido no PMC12279373). O texto lido **não afirma o sentido do DNa01**. Há o
  registro pareado ("rotational velocity is related to the right-left firing rate difference in this
  DNa01 paired recording", Fig. 3, suplemento 2), sem a convenção de sinal no trecho, e a Discussão diz
  que "inhibiting DNa01 produced only small defects in steering". O sentido do DNa01 continua **não
  verificado**, e ele fica fora da regra de curva até haver fonte.
- **A magnitude taxa → encurtamento do passo não tem fonte**: Yang et al. 2023 só dão o sentido.
  Registrado no NON_CONNECTOME.md (B-mag).

## L. S1: resultado do recuo e do silenciamento (2026-09-23)

`results/phase3b/backtrace_tree.json`, `backtrace_silence.json`; spikes em `runs/phase3b/backtrace/`
(`ODOR_OK` 5/5, `SIL_OK` 15/15).

**Árvore (resumo; contribuição = peso × taxa)**, a partir do DNa02 esquerdo (52,4 Hz com odor):

| Nível 1 (principais) | Taxa | Peso | Principais entradas (nível 2 → nível 3) |
|---|---|---|---|
| **PS013 E** (central, ACh) | 45,8 Hz | +178 | CB0359 E (← MBON12 E, CB1245 E); LAL023 E ×2 (← SMP177 E/D, LHPV5e3 E, CRE011 E) |
| **DNae005 E** (descendente, ACh) | 19,2 Hz | +196 | CB0316 E (← AL-AST1 E, LHCENT11 E, LT86 E); DNbe007 E; PVLP141 D (← PVLP076 D, LHAV1a1 D) |
| **LAL081 E** (central, ACh) | 40,0 Hz | +93 | CRE011 E e D (← SMP177, LHPV10b1, MBON35, MBON05); LAL030b E |

- Maiores inibitórios diretos do DNa02 E: AOTU019 D (−121), CB0083 D (−80), LAL051 E (−70).
- Os três principais do nível 1 ficam do lado **esquerdo**. Mais acima aparecem neurônios dos dois
  lados, com taxas altas (MBONs, SMP177, CRE011, LHPV10b1, de 110 a 240 Hz).
- Com odor, a rede inteira fica muito ativa: ~4,9×10⁵ spikes em 1 s, ~3,5 Hz em média por neurônio.

**Silenciamento cumulativo do nível 1** (5 sementes pareadas; critério: queda mediana ≥ 50 % e ≥ 50 % em ≥ 4/5):

| Silenciados | DNa02 E (mediana) | Queda mediana | Sementes com ≥ 50 % | QUEDA |
|---|---|---|---|---|
| — (intacto) | 51 Hz | — | — | — |
| PS013 E | 35 Hz | 31 % | 0/5 | não |
| + DNae005 E | 28 Hz | 45 % | 1/5 | não |
| + LAL081 E | 13 Hz | **75 %** | **5/5** | **sim** |

- Descritivos: o DNa02 direito fica em 0–2 Hz em todas as condições. O DNa01 esquerdo só cai
  (20 → 8 Hz) quando o LAL081 E é silenciado. O total de spikes da rede não muda (±0,2 %).

**Leitura (corrigida na revisão do usuário, 2026-09-23):**
- **As três juntas passam o critério** (PS013 E + DNae005 E + LAL081 E: queda de 75 %, 5/5). Só o PS013 E
  foi silenciado sozinho (31 %, não passa). **A contribuição isolada de DNae005 e de LAL081 não foi
  medida**: o desenho cumulativo não a separa. A frase anterior, "convergência, não neurônio único",
  foi retirada porque o teste não sustenta essa conclusão.
- **A ordem do silenciamento estava no pré-registro** (commit c41fbba, §K passo 3 e o cabeçalho do
  script): cumulativo top1; top1+2; top1+2+3, na ordem de contribuição (peso × taxa) calculada no passo 2,
  sem escolha manual.
- **A queda mede a contribuição TOTAL numa rede recorrente**, e não só a sinapse direta desses neurônios
  no DNa02 E. Silenciar um neurônio remove também o efeito dele em qualquer caminho que chega ao DNa02 E,
  inclusive através dos outros nós da árvore.
- O critério foi aplicado uma vez, sem novas sementes.

## M. S1: homólogos direitos e nível de atividade, só com spikes já salvos (2026-09-23)

`results/phase3b/homologs_activity.json`, a partir de `runs/phase3b/backtrace/odor_s*.npz` (odor bilateral,
conectoma real, 5 sementes). Nenhuma simulação nova.

**(a) Os homólogos direitos estão ativos com odor bilateral:**

| Tipo | Esquerdo (mediana) | Direito (mediana) |
|---|---|---|
| PS013 | 46 Hz | 19 Hz |
| DNae005 | 19 Hz | 17 Hz |
| LAL081 | 40 Hz | 45 Hz |

O DNa02 D fica em 0–2 Hz mesmo com esses homólogos ativos. Então a assimetria não vem de os
homólogos direitos estarem calados; o que a produz fica em aberto (p. ex., a ligação deles com o DNa02 D
ou uma inibição maior sobre ele). Nada disso foi testado.

**(b) Nível de atividade da rede:**
- **Conectoma real**, com odor bilateral: **~4,92×10⁵ spikes em 1 s** (491.339–493.169 entre as
  sementes), com **6,2 % dos neurônios ativos** (~8.600 de 138.639). Os ativos disparam, em média, ~57 Hz.
- **Embaralhados: não é possível responder sem simulação nova.** A fila de lateralidade (§H) gravou
  só as taxas das células de DN (`laterality_runs.csv`), não os spikes de todos os neurônios. Fica
  como pendência.

**Limitações registradas:**
- **Regime de atividade muito alto:** com os ORNs de DM1+VA2 a 100 Hz (taxa **sem fonte**, B-odor),
  a rede entra num regime em que ~6 % dos neurônios disparam a ~57 Hz em média. **O caminho
  identificado (PS013/DNae005/LAL081 → DNa02 E) pode depender desse regime.**
- **A sensibilidade à taxa dos ORNs fica como pendência, não executada.**
- **A queda na ablação mede a contribuição total na rede recorrente** (ver §L).
- **A ausência de lado pode vir do modelo de estímulo, e a inibição não é detectável sem atividade
  espontânea** (§J5).

## N. Etapa B: sensibilidade à taxa dos ORNs e homólogos (pré-registro, commitado antes de rodar)

Sem corpo e sem interface. Princípios do projeto: o comportamento vem da mosca, o mínimo fora do conectoma
e, quando houver opção, parâmetro com fonte.

**N1. Fonte para a taxa dos ORNs: ENCONTRADA.**
- Faucher CP, Hilker M, de Bruyne M 2013, "Interactions of Carbon Dioxide and Food Odours in
  *Drosophila*: Olfactory Hedonics and Sensory Neuron Properties", *PLoS ONE* 8(2):e56361,
  doi:10.1371/journal.pone.0056361.
  - Registro de sensila única com vinagre de maçã orgânico (puro ou diluído em água destilada), 10 µl
    em papel de filtro, estímulo de 500 ms.
  - Nos Métodos: "Pre-stimulus activity was then subtracted from the response during stimulation to get
    an increase (or decrease) in the spike frequency relative to the pre-stimulus frequency". Ou seja,
    os valores são o **aumento sobre a taxa espontânea**.
  - A Fig. 2C mostra a dose-resposta de ab1A (Or42b → DM1) e ab1B (Or92a → VA2). Os valores só aparecem
    na figura; a leitura foi **visual**, com precisão de ~±3 spikes/s.
- Valores lidos, fêmeas (linha contínua), escolhidas porque o FlyWire é o cérebro de uma fêmea:

| Vinagre | ab1A → ORN_DM1 | ab1B → ORN_VA2 |
|---|---|---|
| 0,5 % | ~12 Hz | ~9 Hz |
| **5 %** | **~42 Hz** | **~22 Hz** |
| 50 % | ~88 Hz | ~43 Hz |

- **Condição de referência (com fonte): "vin5"**, com ORN_DM1 a 42 Hz e ORN_VA2 a 22 Hz. Como o LIF não
  tem atividade de fundo, a taxa de Poisson é o próprio aumento medido.
- **Escolhas sem fonte que sobram:** a concentração (5 %; nenhuma fonte diz a concentração que chega à
  antena perto da fruta), a curva das fêmeas e a leitura visual da figura.

**N2. Desenho** (`experiments/phase3b_rates.py`):
- Taxas: **20, 50 e 100 Hz** em todos os ORNs de DM1 e VA2 (varredura, sem fonte) e **vin5** (com fonte).
- Condições:
  - conectoma **real**: sem odor, bilateral, só esquerda e só direita;
  - **5 embaralhados** (os mesmos de §H): sem odor e bilateral.
- 10 sementes pareadas (1000–1009), 1 s; **380 execuções**.
- Salva os spikes de **todos** os neurônios (`runs/phase3b/rates/*.npz`) e, no fim, `RATES_OK` com a
  contagem.
- A análise (`analyze`) se recusa a rodar sem `RATES_OK` completo.
- Nota: com várias chamadas de `set_poisson` (uma por tipo de ORN), a ordem dos alvos muda o sorteio. A
  condição r100 bilateral **não** é uma repetição bit a bit da viabilidade.

**N3. Critérios (fixados agora):**
- **(a) O DNp09 é excitado em alguma taxa:** no conectoma real, bilateral × sem odor, média das 2 células,
  Wilcoxon pareado com p < 0,05/4 (Bonferroni sobre as 4 taxas) **e** diferença mediana ≥ 1 Hz, em
  pelo menos uma taxa.
- **(b) O viés do DNa02 esquerdo se mantém em todas as taxas:** no bilateral, d = DNa02 E − DNa02 D por
  semente; em **cada** uma das 4 taxas, Wilcoxon com p < 0,05/4 **e** mediana de d ≥ +2 Hz. Uma taxa
  em que o DNa02 fica calado conta como "não se mantém".
- **(c) Algum DN distingue o lado:** Δ ipsi − contra (como em §H), por tipo (4) e por taxa (4), com
  Wilcoxon p < 0,05/16 **e** |mediana| ≥ 2 Hz, em pelo menos um par tipo × taxa.
- **(d) O regime de atividade da rede está numa faixa plausível: SEM FONTE.** Não há medida publicada
  da fração de neurônios ativos no cérebro inteiro da mosca que sirva de comparação para um LIF.
  - Faixa declarada sem fonte: a fração de neurônios ativos (≥ 1 spike em 1 s) no bilateral deve ficar
    **≤ 10× a do regime em que o modelo foi validado na Fase 1**: 20 GRNs de açúcar a 150 Hz, 435
    ativos em 138.639 (0,31 %), portanto limite de **3,1 %**.
  - Ressalva: os 435 somam 30 trials; por trial, a fração é menor, o que torna o limite mais frouxo.

**N4. Estimativa de tempo** (medida nesta máquina, na mesma sessão):
- a fila de lateralidade (240 execuções de 1 s, 10 processos) levou ~17 min, incluindo ~1,5–2 min de
  geração de cada embaralhamento, que agora estão em cache;
- isso dá ~24 s de parede por execução e por processo, com atividade alta (100 Hz);
- **380 execuções ≈ 15 min** (teto de ~25 min). As taxas mais baixas devem custar menos. Sob
  `systemd-inhibit`, no perfil Desempenho, na tomada.

**N5. Só grafo e spikes já salvos, sem simulação** (`experiments/phase3b_homologs.py`): pesos diretos
de PS013, DNae005 e LAL081 (E e D) em DNa02 E e D; e, com os spikes do odor bilateral a 100 Hz (§K),
as entradas ativas (peso × taxa) sobre DNa02 D e E, com as somas excitatória e inibitória e as 10
maiores inibitórias sobre o DNa02 D. É descritivo, sem critério.

## O. Etapa B: resultado (2026-09-24). Relatório em `docs/FASE3B_ETAPA_B_RELATORIO.md`
- `RATES_OK` 380/380, análise só com a fila completa.
- **Critérios:**
  - (a) DNp09 excitado: **não** (0 Hz em todas as taxas, inclusive vin5);
  - (b) viés do DNa02 E em todas as taxas: **sim** (50–55 Hz contra 0–1 Hz; p = 0,002);
  - (c) algum DN distingue o lado: **não**;
  - (d) regime na faixa sem fonte (≤ 3,1 %): **não** (6,1–6,2 % em todas as taxas).
- **Real × embaralhados:** o conectoma real entra num regime alto de tudo ou nada já a 20 Hz (~470 mil
  spikes); os embaralhados ficam em ~0,1–0,3 %.
- **Homólogos:** pesos simétricos; o saldo no DNa02 D é negativo, com a maior inibição vinda do AOTU019 E
  (descritivo, sem teste causal).
- **Desvio:** a fila levou ~30 min, contra os 15 estimados.

## P. Etapa C: o regime de atividade alta (pré-registro, commitado antes de rodar)

Sem corpo, sem interface, sem vídeo. `experiments/phase3b_regime.py`.

**P0. Correção da leitura de Faucher et al. 2013, Fig. 2C** (releitura ampliada, 3,76 px/Hz):
- a 0,5 %, fêmeas, ab1A ≈ **16 Hz** e ab1B ≈ **11 Hz** (em §N estava ~12/9);
- a 0,1 % há **um único ponto** por neurônio, sem separação por sexo: ab1A ≈ **7 Hz** e ab1B ≈ **0 Hz**;
- os pontos de 5 % (42/22) e de 50 % (88/42) se confirmam;
- existem pontos com fonte abaixo de 20 Hz, então **não** foram acrescentados os 5 e 10 Hz sem fonte.

**P1. Condições** (odor sempre bilateral, ORNs de DM1+VA2; 10 sementes pareadas, 1000–1009):
- **Persistência:** vinagre a 5 % (42/22 Hz) em [0, 200) ms, depois desligado até 1000 ms. Conectoma real
  e 5 embaralhados.
- **Dose:** vinagre a 0,1 % (7/0 Hz) e a 0,5 % (16/11 Hz), contínuos por 1 s. Conectoma real e 5
  embaralhados. O vinagre a 5 % contínuo e o sem odor são **reaproveitados da Etapa B** (mesmo código,
  mesma ordem de chamadas, mesmas sementes).
  - Nota: a 0,1 %, os ORNs de VA2 entram como alvos de Poisson a 0 Hz, o que, pela convenção do Shiu,
    zera o refratário deles (sem outra consequência).
- **Causal:** vinagre a 5 % contínuo com o **AOTU019 esquerdo silenciado** (sinapses de saída zeradas,
  como `model.py:silence`). Só o conectoma real. Pareado com o vinagre a 5 % da Etapa B.
- Total: **190 execuções novas** (real 40, embaralhados 150). Spikes de todos os neurônios salvos;
  `REGIME_OK` com a contagem; análise separada.

**P2. Critérios (fixados agora):**
- **Persistência:** a atividade "se mantém sozinha" se a mediana entre as sementes da razão [taxa de
  spikes da rede em 400–1000 ms] / [taxa em 100–200 ms] for **≥ 0,10** (escolha, sem fonte). Descritivos:
  instante do último spike e spikes em 900–1000 ms.
- **Limiar e resposta graduada:**
  - uma semente está em **"estado alto"** se a fração ativa for ≥ 3,14 % (o limite (d) da Etapa B, sem
    fonte);
  - **existe limiar** se alguma dose baixa (0,1 % ou 0,5 %) tiver ≤ 2/10 sementes em estado alto **e** o
    vinagre a 5 % tiver ≥ 8/10;
  - **graduada abaixo do limiar** se, com as duas doses baixas abaixo do limiar, o total de spikes a 0,1 %
    for menor que a 0,5 %;
  - uma dose com 3–7 sementes em estado alto é registrada como **"mista"** (sinal de biestabilidade).
- **Causal:** o AOTU019 esquerdo **contribui** para o silêncio do DNa02 direito se a mediana do aumento
  pareado do DNa02 D for **≥ 5 Hz** e o Wilcoxon der **p < 0,05**. Descritivo: o viés some se o DNa02 D
  chegar a ≥ 50 % do DNa02 E.

**P3. Estimativa de tempo:**
- na Etapa B (380 execuções, 10 processos, ~30 min), o custo foi dominado pelas 130 execuções do
  conectoma real em regime alto (~14 s de parede por execução com 10 processos). As 250 dos embaralhados
  foram baratas;
- aqui: 40 do real (a persistência deve ser mais barata se a atividade cair) + 150 dos embaralhados + 6
  inicializações de pool ≈ **10–15 min**. O log agora grava o tempo por conectoma.

**P4. Regra da causa:** se a causa apontar para uma limitação conhecida do modelo, **nada é corrigido**.
A limitação é descrita com fonte, e as opções são listadas com prós, contras e o quanto cada uma
interfere no conectoma.

## Q. Etapa C: resultado (2026-09-24). Relatório em `docs/FASE3B_ETAPA_C_RELATORIO.md`
- `REGIME_OK` 190/190, em ~9 min.
- **Persistência: sim** no conectoma real (razão de 0,98; não desliga); não nos embaralhados.
- **Dose com fonte: nenhum limiar** (0,1 %, 0,5 % e 5 %: 10/10 sementes em estado alto).
- **Causal: o AOTU019 E cala o DNa02 D** (0 → 44,5 Hz, p = 0,002; o viés some).
- **Núcleo da persistência:** alça química excitatória de LNs colinérgicos ↔ PNs no lobo antenal
  (inferência pelas fontes de excitação). É a limitação L1: na mosca, a excitação eLN → PN é elétrica
  (Yaksi & Wilson 2010).
- APL não disparador na mosca (Amin et al. 2020) e disparando a ~340 Hz no modelo (L2).
- Opções O0–O6 listadas; **nada foi corrigido**.

## R. Etapa D: ablações diagnósticas (pré-registro, commitado antes de rodar)

**Não são correções: o modelo oficial não muda.** As sinapses são zeradas numa cópia do conectoma, só dentro
de `experiments/phase3b_ablation.py`. Sem corpo, sem interface, sem vídeo.

**R0. O que os terminais dos ORNs recebem na mosca real** (fontes lidas antes de definir B):
- Olsen SR, Wilson RI 2008, *Nature* 452:956–960: "a substantial portion of this inter-glomerular inhibition
  acts at a presynaptic locus, and our results imply this is mediated by both GABAA and GABAB receptors on
  the same nerve terminal". Os terminais dos ORNs recebem **inibição GABAérgica pré-sináptica**.
- Horne JA et al. 2018, *eLife* 7:e37550 (glomérulo VA1v): "ORNs are predominantly presynaptic" (razão
  pré/pós de 3,9 ± 0,6 nos ipsilaterais), e "some ORN synapses are made between an ORN and its neighbouring
  olfactory receptor neurons".
- **Nenhuma fonte lida mostra que entradas excitatórias nos terminais façam o ORN inteiro disparar.** A
  hipótese de B (um modelo de neurônio pontual transforma sinapses no terminal em excitação do ORN inteiro,
  inclusive dos que não recebem odor) continua **hipótese**.
- No modelo: os ORNs recebem 95.001 sinapses excitatórias (76 % de LNs, 20 % de outros ORNs, 4 % de PNs) e
  66.477 inibitórias.

**R1. Conjuntos** (definidos no código antes de rodar):
- **A (eLN → PN):** eLN = LN do lobo antenal (`cell_class == ALLN`) com saída excitatória no modelo (sinal do
  arquivo do Shiu) e `known_nt` que não seja GABA, glutamato ou octopamina. São **148 eLNs**; a ablação remove
  **18.618 arestas (142.287 sinapses)** de eLN para PN.
- **B (entradas excitatórias nos ORNs):** toda sinapse de peso > 0 que chega a um ORN (`ORN_*`): **51.695
  arestas (95.001 sinapses)**.
- **C:** A + B.
- **Achado registrado à parte:** 18 LNs são excitatórios no modelo mas têm `known_nt` GABA, glutamato ou
  octopamina na anotação (p. ex., 12 com "gaba, MIP; acetylcholine-negative"). É um erro de sinal do modelo
  para esses neurônios. **Não é corrigido aqui.**

**R2. Condições:**
- A, B e C: sem odor, vinagre a 0,1 % (7/0 Hz), 0,5 % (16/11) e 5 % (42/22) (Faucher et al. 2013), com o
  odor ligado em [0, 200) ms e observação até 1000 ms.
- Intacto: persistência a 0,1 % e 0,5 % (novas); a 5 % vem da Etapa C.
- 10 sementes pareadas; **140 execuções novas**.

**R3. Critérios (fixados agora):**
- **A atividade volta ao basal?** Basal = sem odor (0 spikes, sem atividade de fundo). "Volta ao basal" se a
  mediana da razão [taxa da rede em 400–1000 ms] / [taxa em 100–200 ms] for **≤ 0,01**. "Persistente" se
  **≥ 0,10**; entre os dois, "parcial".
- **A resposta cresce com a dose?** Total de spikes durante o odor (0–200 ms): as medianas crescem
  0,1 % < 0,5 % < 5 %, **e** o Wilcoxon pareado de cada passo dá **p < 0,025** (Bonferroni para 2 passos).
- **Fração de neurônios ativos durante o odor (0–200 ms):** relatada no total e por classe (células de Kenyon,
  PNs, LNs), comparada com o limite de 3,14 % da Etapa B (sem fonte). É descritiva.

**R4. Estimativa de tempo:** as execuções em regime alto custaram ~100 s cada (Etapa C: 40 em 430 s com 10
processos). Aqui são até ~110 em regime alto + 30 controles baratos ≈ **10–20 min**, e menos se as
ablações apagarem o regime.

**R5. Propostas pedidas (nada rodado com elas):** referência olfativa para reprodução e resposta sobre
ligações elétricas nos conectomas. Ver `docs/FASE3B_ETAPA_D_RELATORIO.md`.
