# Relatório da Fase 3a: marcha pelo cordão do BANC na bolinha

**Resultado: loop fechado não testável com este aparato no prazo. A pergunta do loop fechado ficou ABERTA: não foi respondida como ausência de ritmo.**
A 3a é encerrada na Sessão 3 (2026-09-23), a 3ª de 6 sessões do prazo, pela regra de teto aprovada
(FASE3_PLANO §7.8.1 e §7.10). A validação do aparato falhou nas três tentativas de batente, então o loop
fechado nunca rodou com um corpo válido. A 3b segue com o controlador da opção (a).

Detalhes e números por sessão: `docs/FASE3_PLANO.md` §6–7. Ajustes fora do conectoma:
`docs/NON_CONNECTOME.md` (Fase 3a).

## 1. O que ficou demonstrado

Tudo abaixo vale para o híbrido FlyWire 783 + cordão BANC v888, com o LIF de Shiu et al. 2024 e a
métrica de ritmo v2 congelada (Sessão 1).

| # | Resultado | Evidência | Onde |
|---|---|---|---|
| D1 | **Sem ritmo em malha aberta** | 18 condições (4 grupos de DNs, de 2 a 159 DNs × modos de sinal × taxas) × 5 sementes: 0 de 108 pares perna × condição rítmicos. Populações maiores recrutam até 70 % dos MNs, mas o espectro fica plano (proeminência máxima 5,8 numa única semente; p95 3,6) | S1, §7.1; `results/phase3a/s1_h2_h6_v2.csv` |
| D2 | **Aferência imposta negativa nas 3 variantes** | Marcha real gravada (~11 Hz) aplicada aos 941 proprioceptores, nas variantes sinais `verified`, fundo H5 (5 Hz) e glutamato excitatório (H6-g), com e sem G3, 4 combinações de direção × 5 sementes: **0 pernas com geração e 0 com reflexo**. A potência na frequência imposta fica igual à do controle sem aferência (mediana 1,31–2,11 contra 1,37). Os sensores carregam o ritmo (hook da L1 com pico em 11 Hz, proeminência 7,6); o caminho até os MNs, não | S2, §7.2; `s2_imposed*.csv` |
| D3 | **Acionamento dos MNs de perna quase nulo** | Com os DNs de marcha ligados, a ativação mediana dos grupos musculares foi 0,0016 no loop fechado da S2 (73 % dos MNs em 0 Hz). Em malha aberta, sem corpo, o quadro é o mesmo: G2 0,0000 e G4 0,0002; o G3 fica na fronteira (0,054 em malha aberta, 0,044 no loop). **Não depende do aparato** | S2, §7.2 |
| D4 | **Inibição recíproca funcional nos dois sentidos** | **Flexor → extensor: 12 de 12** pares perna × junta, com os extensores caindo de 44 % a 96 % e os flexores subindo em todos (S2). **Extensor → flexor: 11 de 12** pelo critério pré-registrado (≥ 9 pares com os flexores caindo ≥ 25 % e os extensores subindo); os 11 caem de 35 % a 61 %, e a **exceção é a FTi da L1 (−14 %)** (S3). Números conferidos nos CSVs em 2026-09-23. O efeito é assimétrico: extensor → flexor é mais fraco | S2 §7.2, S3 §7.5; `results/phase3a/s3/diagnostico_s3.png` |
| D5 | **O saldo do caminho proprioceptor → MN é inibitório** | Nas vias de 2 sinapses, o saldo (E − I)/(E + I) de claw, hook e club fica entre −0,49 e −0,52; a via direta, pequena, é excitatória. Com a H6-g, claw e hook seguem negativos (leitura pré-registrada **não cumprida**); placas de pelos (+0,12) e campaniformes (+0,17) passam a positivos, o que fica **só como hipótese** | S3 §7.5; `s3_ei_balance.csv` |

## 1b. Indícios e inferências (não demonstrados)

| # | Inferência | Base | Ressalva |
|---|---|---|---|
| I1 | **A coativação flexor × extensor vem do acionamento paralelo pelos DNs, e não da falta de substrato de alternância** | Coativação na S1: r de +0,1 a +0,37 em CTr e FTi. **Estrutura:** a excitação pré-motora compartilhada entre flexores e extensores é baixa (5–15 %), a inibição pré-motora é seletiva (0,84–0,89) e os DNs de G3 acionam os dois lados (razão flexor/extensor de 0,9 a 8×; `s2_coactivation_structure.csv`). **Função:** a inibição recíproca existe nos dois sentidos (D4) | **Não houve manipulação direta** (p. ex., acionar os pré-motores de um lado só a partir dos DNs, ou remover a entrada dos DNs num dos lados). É uma inferência, não um resultado demonstrado |
| I2 | Com glutamato excitatório (H6-g), placas de pelos e campaniformes passam a um saldo positivo até os MNs | T1 (S3) | A H6-g não tem base documentada. Hipótese apenas |

## 2. O que ficou sem teste

| Pergunta | Por que ficou sem teste |
|---|---|
| **Loop fechado (H1-ii):** o ritmo aparece com a realimentação proprioceptiva real? A pergunta do marco | S2: inconclusivo (acionamento quase nulo + juntas sem limite nem rigidez). S3: o aparato não passou na validação, então a fila não rodou |
| H3 (escala do VNC) em loop fechado | depende do loop fechado |
| H5 (tônus) em loop fechado, com fundo sublimiar | depende do loop fechado; o fundo da S2 era supralimiar (limitação registrada) |
| Sensibilidade à rigidez (k/16) e à F_SAT | a fila da F_SAT da S2 rodou num aparato inválido e não foi analisada; a de k/16 não rodou |
| H7 (BANC puro, sem costura) | a ordem de trabalho a previa para a S3, condicionada ao loop fechado |
| H4 (parâmetros do LIF no VNC) e H8 (propriedades intrínsecas) | previstas para as sessões 4–6, só se o marco passasse |
| Critérios de marcha (alternância, trípode, bola, virada, ablação) | idem |

**O marco da 3ª sessão não foi decidido como "ausência" nem como "ritmo".** A 3a termina pelo teto
do aparato, não por um negativo do loop fechado.

## 3. O aparato: por que não passou

Corpo: NeuroMechFly com atuadores de torque nas 42 juntas ativas das pernas, sobre a bola do NeuroMechFly v1.

| Tentativa | (a) réplica | (b) repouso | (c) limites | (d) faixa dinâmica | (e) controle negativo | Instabilidade |
|---|---|---|---|---|---|---|
| 1. Limite com o `solref` padrão (0,02 s) | passou | passou | **66/66 > Y**, até 36,6 rad | falhou | passou (com batentes inoperantes; refeito depois) | não medida |
| 2. `std2dt` (0,2 ms) | passou | passou | **31/66**, até 0,22 rad | falhou | passou | — |
| 3. `direct_dt` (formato direto, ≡ 0,1 ms) | passou | passou | **8/66**, até 0,11 rad | falhou (18 não monotônicos) | passou | **nenhuma** (0 avisos, 0 NaN, energia sem aumento) |

Diagnóstico, pelas métricas gravadas na tentativa 3, sem nova execução:
- **O batente segura na sustentação.** A violação média em 100–200 ms fica ≤ 0,021 rad nos 66 grupos
  (mediana 0,0014), sempre abaixo de Y.
- **O que passa de Y é o impacto.** O pico nos primeiros ~1 ms passa de Y em 46 grupos (até 0,20 rad) e
  aparece na leitura a 1 kHz em 8 deles.
- A causa é mecânica. Com a rigidez medida por Wang et al. (0,1–3 µN·mm/rad) e o torque máximo do A4
  (10–22 µN·mm), a junta chega ao batente a centenas de rad/s. A rigidez do limite macio do MuJoCo
  escala com a inércia da junta (~10⁻⁵), inclusive no formato "direto" (verificado no código do MuJoCo
  3.9.0), e o formato padrão tem uma trava de 2× o passo.
- A falha de (d) na tentativa 3 tem a mesma origem: a junta já está no batente desde a ativação de 0,2
  e oscila ±0,01–0,03 rad ali.

**Checagem da unidade de Wang et al. 2025** (preprint): a leitura mN·m/° falhou na checagem
pré-registrada. O limiar de sustentação ficou em m* = 2,5, contra a faixa [10, 160] em torno do ×40 do
artigo (discrepância de 16×). As outras leituras ficam a ≥ 62×. A leitura foi mantida como valor
principal por decisão do usuário (opção (i)).

## 3b. Caminhos não testados para o loop fechado (só descritos; nada foi executado)

O loop fechado esbarrou em dois problemas independentes: (1) o aparato, com o impacto no batente acima
de Y (§3); (2) o acionamento quase nulo dos MNs (D3), que não depende do aparato. Os caminhos abaixo
atacam um ou outro. Custos estimados nesta máquina a partir da fila do loop fechado da S2: 120 execuções
de 5,7 s em ~107 min com 10 processos, ou seja, ~9 min de parede por execução (~95 s/s por processo
com a CPU dividida).

| Caminho | O que resolveria | Custo estimado | O que fica fora do conectoma |
|---|---|---|---|
| **Músculo tipo Hill** (força-comprimento-velocidade; atuadores `muscle` do MuJoCo com tendões) | (1): a força cai com a velocidade de encurtamento, então a junta não chega ao batente a centenas de rad/s. O impacto some na origem, sem batente artificialmente rígido. Também daria uma F_SAT com sentido físico | Computacional: pequeno (os atuadores `muscle` são baratos perto do contato). **Engenharia: alto**. O único modelo pronto (FlyMimic, Ozdil et al. 2026, no FlyGym) tem 15 músculos só na perna anterior esquerda; as outras 5 pernas exigiriam geometria de tendões e parâmetros sem fonte. Estimativa: 2–4 sessões antes do primeiro loop | força máxima, comprimento ótimo, v_max e curvas de cada músculo; geometria dos tendões; ativação MN → músculo (substitui o A4) |
| **Passo de tempo menor** (0,05 ou 0,025 ms) | (1), em parte: com o `refsafe` o batente pode ficar mais rígido (tc = 2·dt), e o pico no impacto cai ~∝ dt. Pela extrapolação das 3 tentativas: ~0,1 rad a 0,05 ms e ~0,05 rad a 0,025 ms, na fronteira de Y | ×2 a ×4 no custo da física. A fila de 120 execuções passaria de ~1,8 h para ~3,5–7 h. O loop teria de rodar 20–40 passos de física por ms do LIF | nada novo além do batente (numérico) |
| **Armature** (inércia adicional nas juntas; o `flybody` do FlyGym usa 10⁻⁴ nas pernas, contra 10⁻⁶ aqui) | (1): com inércia ~10× maior, o batente fica ~10× mais rígido em força (a rigidez do limite ∝ inércia) e a velocidade no impacto cai (~4× pela estimativa) | computacional: nulo | inércia fictícia, não fisiológica. Ela desacelera a perna (constante mecânica I/c ≈ 12 ms, corte perto de 13 Hz, dentro da banda de passada de 3–20 Hz). Teria de repassar no teste (a) e ser declarada como filtro possível do ritmo |
| **Neurônios graduados no cordão** (modelo de taxa para os interneurônios locais não disparadores; H4-ii, D-102) | (2): muitos interneurônios locais do VNC de insetos não disparam, e o LIF do Shiu os trata como disparadores. Isso pode explicar o acionamento quase nulo e a falta de ritmo. **Não resolve o aparato** | Computacional: baixo a moderado (modelo de taxa para alguns milhares de neurônios, junto do LIF). **Engenharia e fonte: alto**. O BANC não anota quem é não disparador; seria preciso fixar a atribuição por hemilinhagem com base na literatura, que em *Drosophila* é escassa. Estimativa: 2–3 sessões | quais neurônios são graduados, a constante de tempo, o ganho e o limiar deles, e a conversão sinapse → corrente graduada |

Nenhum destes caminhos foi testado. Um teste do loop fechado precisaria de pelo menos um da linha (1)
**e** de uma resposta para (2); se o acionamento continuar quase nulo, um aparato perfeito ainda daria
um negativo inconclusivo.

## 4. Ajustes fora do conectoma usados na 3a

14 itens, todos em `docs/NON_CONNECTOME.md`:
- aparato e corpo: A1 (bola), A2 (passivos originais, defeituosos), A2' (rigidez de Wang et al.,
  amortecimento pelo critério, limites);
- mapeamento e acionamento: A3 (MN → músculo → junta), A4 (ganho muscular, F_SAT);
- propriocepção: A5 (transdução), A5b (direção por tipo), A6 (limiares);
- protocolo: A7 (pulso inicial), A8 (aferência imposta), S (estímulo de Poisson nos DNs);
- sinais e fundo: H5-bg (fundo de 5 Hz), H6-v (sinais `verified`), H6-g (glutamato excitatório).

**Nenhum resultado positivo de ritmo foi obtido**, com ou sem eles. D4 e I1 usam H6-v e S.

## 5. Para a 3b

- **Controlador:** opção (a), DNs → comandos de alto nível num controlador do FlyGym.
- **Corpo confirmado:** `flygym_demo.complex_terrain.make_locomotion_fly`, com **atuadores de POSIÇÃO**
  (kp = 45 µN·mm/rad, faixa ±65 µN·mm), rigidez/amortecimento passivos 0,05/0,06 e adesão tarsal.
  É o mesmo corpo que o terrário da Fase 2 já usa (`terrario/body/fly.py:build_scene`). O CPG do
  `flygym_demo` (`complex_terrain/cpg_controller.py:CPGController`) atua nesse corpo. **O aparato de
  torque da 3a (`terrario/vnc/apparatus.py`) não é usado na 3b.**
- A 3b precisa de um plano aprovado antes de começar. Ele deve dizer como os DNs do cérebro FlyWire
  modulam o controlador, o que fica de fora do conectoma (o CPG inteiro é NON-CONNECTOME) e a ablação
  correspondente.
- O cordão do BANC continua disponível para estudo, fora do caminho da locomoção. Os achados D2–D5
  valem como caracterização do VNC no LIF do Shiu.

## 6. Pendências de fechamento
- **Vídeo de fechamento (aprovado; conteúdo fixado antes de gerar):** `results/phase3a/video_fechamento_3a.webm`,
  30 fps, com o corpo da última tentativa (`passive="wang2025"`, `limit="direct_dt"`), câmera lateral e
  bola quadriculada (só visual). Roteiro:
  1. cartela (1 s);
  2. **teste (a):** os torques da marcha real (servo kp 150 gravado e tocado em malha aberta, igual ao
     teste) por 2 s simulados a 0,25× = 8 s;
  3. cartela (1 s);
  4. **teste (c), pior caso:** o grupo com a maior violação pelo critério do teste (1 kHz) na tentativa
     `direct_dt`, **LF FTi extensor (0,111 rad)**, identificado como o pior caso. Ativação 1 por 200 ms,
     bola afastada (−5 mm), a 0,025× = 8 s, com o ângulo, o limite e a violação na legenda.
  Total de ~18 s. Script: `experiments/video_phase3a_close.py`.
- Figuras da sessão: `results/phase3a/s3/diagnostico_s3.png`.
