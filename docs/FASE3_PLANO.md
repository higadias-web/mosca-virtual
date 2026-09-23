# Plano da Fase 3: malha fechada da mosca adulta (aprovado em 2026-09-23, com ajustes)

Decisões que valem aqui: **D-105 = (c)**, com o cérebro do FlyWire 783 (validado na Fase 1) e o
cordão do BANC v888 (`terrario/brain/hybrid.py`). **D-106**: Fase 3 dividida em 3a (bolinha) e
3b (terrário).
- **Prazo da 3a:** 6 sessões de trabalho ou 2 semanas a partir do início da 3a, o que vier primeiro.
- **Marco na 3ª sessão:** se nenhum estímulo de DN gerar atividade rítmica nos MNs de perna com o
  loop proprioceptivo fechado, a 3a é encerrada, o resultado negativo é documentado e a 3b segue
  com o controlador da opção (a).

## 1. Ponto de partida: sem ritmo em malha aberta

A sonda da D-105 (`results/d105/probe_*.json`) estimulou o par de DNp09 ou de DNa02 a 50–200 Hz,
por 1 s, sem corpo. Resultado: ≤ 7 dos 391 MNs de perna ativos, taxa ≤ 0,2 Hz, sem ritmo. Com o
VNC × 2: 49–63 MNs, 0,4–2,4 Hz, ainda tônico.

Achado novo, que entra como hipótese: **o BANC prevê GABA para 260 dos 391 MNs de perna**, 81
como acetilcolina e só 11 como glutamato. Os MNs de perna de *Drosophila* são glutamatérgicos
na junção neuromuscular. Nenhum dos 391 tem transmissor verificado nos metadados
(`neurotransmitter_verified` vazio). Com a regra do Shiu, as saídas centrais desses MNs viram
inibitórias por dois caminhos (GABA ou glutamato), mas a previsão errada é um sinal de que as
previsões de transmissor no VNC merecem desconfiança (H6).

## 1b. Ajustes da aprovação (2026-09-23)
1. **H6 antecipada para a Sessão 1**, junto com a H2, separando dois casos: (a) o sinal das
   sinapses **dentro do cordão** (no modelo do Shiu, glutamato é inibitório no SNC) e (b) a saída
   **motoneurônio → músculo**, que é excitatória por construção no aparato, qualquer que seja o
   transmissor previsto. Avaliar também a confiabilidade das previsões nos **interneurônios** do
   cordão, não só nos MNs.
2. **Critério contra ritmo fabricado:** um ritmo só conta se **sumir na ablação**: sem estímulo nos
   DNs **e** com os interneurônios responsáveis silenciados. O relatório informa quantos ajustes
   fora do conectoma foram necessários (H3, H4, H5 etc.), todos em `docs/NON_CONNECTOME.md`.
3. **Probóscide em paralelo à 3a**, fora do prazo das 6 sessões, como entrega separada: extensão
   com açúcar, supressão com amargo e ablação do MN9 (§4).
4. **Vídeo curto (10–20 s)** da cena em `results/` ao fim de cada fase ou entrega.
5. **Tabela de sessões** (§6) atualizada a cada sessão.
6. **Sem painel web na 3a**: a cada sessão, figuras de diagnóstico em `results/phase3a/` (raster
   dos MNs por perna e por junta, espectro da métrica de ritmo). Não contam no prazo.

## 2. Hipóteses para a falta de ritmo e como testar cada uma

**Métrica de ritmo** (fixada antes de testar, `experiments/phase3a_rhythm.py`):
- taxa populacional dos MNs de cada perna em janelas de 5 ms, durante ≥ 1 s de estímulo;
- **ritmo** = pico espectral numa banda de passada. A banda será tirada da literatura na sessão 1,
  antes de qualquer teste, e fica provisoriamente em 2–25 Hz, larga de propósito;
- o pico precisa superar o 99º percentil de 200 surrogados (deslocamentos circulares
  independentes dos trens de spike de cada MN), em pelo menos uma perna.
- Complemento: antifase entre MNs de flexor e extensor do mesmo segmento, pelos músculos-alvo
  anotados no BANC (`peripheral_target_type`, p. ex. `tibia_flexor_muscle`).

Cada hipótese traz o teste, o que conta como confirmação e em que é NON-CONNECTOME.

| # | Hipótese | Teste | Confirma se… |
|---|---|---|---|
| **H1** | **Propriocepção ausente.** Em insetos, o ritmo de marcha depende da realimentação dos sensores das pernas (cordotonais, campaniformes, placas de pelos). Sem ela, o VNC não alterna. | (i) **Aferência imposta**: pernas movidas pela cinemática de marcha gravada que vem com o FlyGym (`flygym_demo.spotlight_data.MotionSnippet`), gerando entrada nos proprioceptores do BANC, com ou sem DN estimulado. (ii) **Loop fechado**: MNs → juntas → proprioceptores → VNC, na bolinha. | há ritmo nos MNs com a aferência imposta (i), ou com o loop fechado (ii) e não em malha aberta |
| **H2** | **Estímulo insuficiente.** Um par de DNs não basta; a marcha real recruta populações de DNs. | Estimular grupos crescentes: DNp09; + DNa01/DNa02; os DNs mais ligados a MNs de perna (influência calculada no conectoma); todos os DNs de um cluster funcional do BANC (`banc_neck_functional_classes`). Taxas de 50–300 Hz. | o recrutamento de MNs cresce com a população e aparece ritmo |
| **H3** | **Sinapses subcontadas no BANC.** O BANC tem ~0,5× as sinapses do FlyWire por par de neurônios (captura pós-sináptica ~0,2), e o `w_syn` do Shiu foi calibrado no FlyWire. | Varrer `vnc_scale` (1; 1,5; 2; 2,5; 3) só nas arestas do VNC, com o cérebro intacto; checar que a Fig. 1D não muda e que não surge atividade autossustentada sem estímulo. | há uma faixa de escala com ritmo e sem descontrole; ou só descontrole (negativo) |
| **H4** | **Parâmetros do LIF calibrados para o cérebro.** O `w_syn` do Shiu foi ajustado no cérebro, e muitos interneurônios locais do VNC de insetos são não disparadores (graduados). O LIF não os representa. | (i) Limiar e constante de membrana só no VNC, dentro das faixas publicadas; (ii) interneurônios locais inibitórios do VNC como graduados (o modelo de taxa já previsto para as minhocas, D-102), só se (i) falhar. | o ritmo aparece com parâmetros dentro das faixas medidas |
| **H5** | **Falta de modulação / estado.** In vivo, o VNC recebe tônus descendente e octopamina (há 30 neurônios octopaminérgicos intrínsecos no VNC do BANC). O modelo do Shiu não tem atividade de fundo. | Entrada tônica de Poisson de baixa taxa (i) nos DNs em geral ou (ii) nos neurônios octopaminérgicos e seus alvos, com o DN de marcha por cima. | o ritmo depende do tônus: some sem ele e aparece com ele |
| **H6** | **Sinais errados no VNC.** Previsão de transmissor duvidosa nos MNs (GABA em 260 de 391); glutamato tratado sempre como inibitório; 197 discordâncias de sinal nas pontes. | (i) Refazer com os sinais das previsões do MANC para os tipos casados (`banc_manc_reviewed_matches`); (ii) MNs como glutamatérgicos; (iii) sensibilidade: inverter o sinal de classes inteiras (nunca neurônio a neurônio). | o ritmo aparece ao corrigir sinais com base documentada |
| **H7** | **Costura entre animais.** DNs pareados por tipo (87 %), sinapses ponte→ponte descartadas. | Mesmo teste no BANC puro (cordão e DNs do mesmo animal), estimulando os DNs direto, e no híbrido com as sinapses ponte→ponte incluídas via `synapse_neuropil_lookup_v2` (2,2 GB). | o BANC puro tem ritmo e o híbrido não |
| **H8** | **Falta de propriedades intrínsecas** (rebote pós-inibitório, platôs, adaptação), que os osciladores de meio-centro usam. | Só se H1–H7 falharem: adaptação e rebote nos interneurônios do VNC (NON-CONNECTOME explícito). | o ritmo aparece só com a propriedade intrínseca |

H1, H2 e H3 são as mais prováveis e as mais baratas. H8 é a última porque é a que mais adiciona
engenharia ao modelo.

## 3. Ordem de trabalho da 3a (por sessão)

| Sessão | Construção | Testes | Saída |
|---|---|---|---|
| 1 | **H6 (a) e (b)** e confiabilidade das previsões nos interneurônios; aparato: `TetheredWorld` + bola livre (massa e inércia de bola sustentada por ar, da literatura); MNs de perna → músculo-alvo (BANC) → junta do NeuroMechFly (mapa documentado por músculo); transdução proprioceptiva: cordotonais (posição/direção pelo `cell_function_detailed`), placas de pelos (ângulo), campaniformes (carga); banda de ritmo tirada da literatura | métrica de ritmo validada num controle positivo sintético; **H2 × H6** em malha aberta | aparato + métrica; tabelas de H2 e H6; figuras |
| 2 | Loop fechado corpo ↔ híbrido | **H1** (aferência imposta e loop fechado); **H3** | ritmo? (sim/não por teste) |
| 3 | — | **H5**, **H7**; combinações das que mostraram efeito. **Marco:** algum estímulo de DN produz ritmo nos MNs com o loop fechado? | **se não:** encerrar a 3a, escrever `docs/FASE3A_RELATORIO.md` (negativo, com todas as hipóteses) e seguir para a 3b com (a) |
| 4–6 | (só se o marco passou) | alternância flexor/extensor, coordenação entre pernas, bola para a frente com DNp09, virada com DNa02, ablação (silenciar DNs e propriocepção), **H4/H8** só se o ritmo for fraco; custo em s/s | relatório da 3a; se os critérios de marcha não fecharem na 6ª sessão, 3b com (a) |

Cada sessão termina com uma linha no registro abaixo (prazo) e com o resultado em `results/phase3a/`.

## 4. Juntas da probóscide (MN9 → alimentação): proposta de subfase

**O que existe:** o FlyGym 2.1 já define as juntas `c_head–c_rostrum` e `c_rostrum–c_haustellum`
(3 graus de liberdade cada, `JointPreset.ALL_BIOLOGICAL`, `flygym/anatomy.py`). O corpo de
locomoção padrão só não as inclui. Os MNs da probóscide estão no cérebro, que nesta opção é o
FlyWire; o MN9 está validado na Fase 1. O BANC anota o músculo-alvo de 13 tipos de MN da
probóscide (MN1–MN9 → músculos m1–m9, etc.), o que ajuda a mapear MN → músculo → junta
(NON-CONNECTOME; a anatomia muscular será tirada da literatura, p. ex. Schwarz et al. 2017,
*eLife*, "Motor control of Drosophila feeding behavior", a confirmar).

**Decisão (2026-09-23): em paralelo à 3a, fora do prazo, como entrega separada "P"** (extensão
com açúcar, supressão com amargo, ablação do MN9; vídeo ao final). A proposta original está abaixo.

**Proposta original: primeira etapa da 3b (3b.1), antes de soltar a mosca no terrário.**
- **3b.1, extensão da probóscide na mosca presa** (reaproveita o aparato da 3a): açúcar no labelo
  ou nos tarsos → GRNs (IDs da v783) → MN9 e demais MNs → juntas pitch do rostro e do haustelo.
  Critérios: extensão com açúcar, com limiar e saturação coerentes com a Fig. 1D; supressão por
  amargo (análogo à Fig. 3A); silenciar o MN9 elimina a extensão; consumo só quando o labelo
  toca o alimento com a probóscide estendida (acoplamento físico, SPEC).
- **3b.2, mosca livre no terrário**: marcha (VNC, se a 3a passou, senão o controlador (a)) +
  olfato, gustação e mecanossensação da Fase 2 → neurônios sensoriais da v783 + probóscide.

Por que não na 3a: a probóscide não depende do cordão nem da pergunta da 3a, e colocá-la lá
consumiria o prazo das 6 sessões. Por que não no fim da 3b: a extensão é o comportamento
alimentar central da SPEC e é validável isolada, na mosca presa, como no experimento clássico.
Alternativa, se preferir: fazê-la em paralelo na 3a, fora da contagem do prazo.

## 5. NON-CONNECTOME previsto na Fase 3
Bola e aparato; mapa MN → músculo → torque (pernas e probóscide); transdução proprioceptiva e
gustativa/olfativa → taxas de Poisson; `vnc_scale` e qualquer parâmetro testado em H3–H8; o
controlador (a), se usado. Tudo entra em `docs/NON_CONNECTOME.md` quando for implementado.

## 6. Registro de sessões da 3a (prazo: 6 sessões ou 2 semanas; início 2026-09-23, limite 2026-10-07)

| Sessão | Data | Feito | Hipóteses testadas | Ritmo? |
|---|---|---|---|---|
| 1 | 2026-09-23 | Métrica de ritmo (v1 → v2, §7.1); H6: confiabilidade dos transmissores; H2 × H6 em malha aberta (18 condições × 5 sementes); aparato: bola, torque, MN → músculo → junta (sinais de flexão medidos), transdução proprioceptiva (941 sensores); figuras em `results/phase3a/s1/` | H2, H6 (a) e (b) | **Não** (0 de 108 pernas×condições; malha aberta) |

Marco da 3ª sessão: ainda pendente (exige o loop proprioceptivo fechado, Sessão 2).

**Pré-registro (Sessão 2, antes de abrir resultados):** configuração principal para o vídeo =
loop fechado, G3 (20 DNs de maior acionamento), vnc_scale 1, combinação de direção 00, semente
7000. Escolhida por ser o grupo de referência da Sessão 1 e por não usar escala fora do conectoma.

**Pré-registro 2 (Sessão 2, antes de abrir resultados; pedido do usuário):**
1. *Diagnóstico sem ajuste do loop fechado* (janela A, todas as execuções):
   - distribuição das taxas por MN de perna;
   - ativação muscular por grupo, recalculada dos spikes com a mesma dinâmica de `MotorDrive`
     (τ = 20 ms, F_SAT);
   - amplitude das juntas (percentis 5–95) comparada com a marcha real gravada (MotionSnippet),
     por perna, em ThC pitch, CTr e FTi.

   Regra de inconclusivo, fixada agora:
   - ativação "perto de 0" = mediana da ativação média dos grupos < 0,05;
   - "saturada" = mais da metade dos grupos com ativação ≥ 0,95 em mais da metade do tempo.

   Em qualquer um dos dois casos, um negativo é marcado como **inconclusivo**. A amplitude entra
   no relatório; ela não reclassifica sozinha.
2. *Sensibilidade à taxa de referência (F_SAT)*: se o loop fechado der negativo, rodar a combinação 00
   com as 5 sementes a **F_SAT = 100 Hz e 400 Hz**, nos mesmos 3 grupos × 2 escalas (60 execuções),
   dentro do prazo da Sessão 2. Só testa se o negativo se mantém. Ritmo que apareça só a 100 ou
   400 Hz **não conta como positivo**: vira hipótese para a Sessão 3.

## 7. Resultados por sessão

### 7.1 Sessão 1 (2026-09-23): H2 e H6 em malha aberta, aparato

**Métrica de ritmo: correção antes de qualquer teste em malha fechada.** A v1 (pico na banda
3–20 Hz acima do p99 de surrogados por deslocamento circular) dá **falso positivo com entrada
comum sem periodicidade**. Os surrogados destroem a correlação entre neurônios, e qualquer
sincronia passa, em qualquer frequência. Isso está demonstrado num controle sintético
(`tests/test_rhythm.py::test_v1_false_positive_shared_broadband`) e apareceu nos dados: a v1
marcou até 6 pernas "rítmicas" onde as figuras mostram espectros planos. A **v2**
(`terrario/vnc/rhythm.py`) exige, além da v1:
- um máximo local na banda, com proeminência ≥ 5 sobre os flancos (espectro de Welch, bins de 1 Hz).
  O limiar vem da distribuição nula: 200 sementes de entrada comum de Ornstein-Uhlenbeck, p99 = 4,79;
- reprodutibilidade em ≥ 3 de 5 sementes, a ±1 Hz.

Controles: 4, 8 e 16 Hz detectados nas 5 sementes; ruído comum rejeitado. A banda de 3–20 Hz vem de
Mendes et al. 2013 (eLife): período de passada mínimo ~60 ms (~16 Hz). A mudança só torna o
critério mais estrito.

**H6: confiabilidade dos transmissores previstos** (`results/phase3a/s1_nt_reliability.csv`):

| Classe | n | Score mediano | Concordância previsto × verificado |
|---|---|---|---|
| Interneurônios do cordão | 12.835 | 0,95 | **99,3 %** (9.949 verificados); 96,4 % de consistência dentro da hemilinhagem |
| ANs | 1.849 | 0,92 | 98,4 % (1.306) |
| DNs | 1.316 | 0,92 | 85,2 % (155) |
| Sensoriais do cordão | 7.593 | 0,86 | 86,8 % (859) |
| **Motoneurônios (todos)** | 805 | **0,46** | **6,7 %** (30 verificados) |

Os interneurônios são confiáveis. A previsão falha nos motoneurônios: 260 dos 391 MNs de perna
saem como GABA, e eles são glutamatérgicos.
- H6 (a), sinal **dentro do cordão**: três modos (`banc.neuron_signs`):
  - `predicted`;
  - `verified`: verificado → hemilinhagem → previsto; MNs = glutamato; muda 903 neurônios do VNC;
  - `verified_gluexc`: como `verified`, com glutamato excitatório em todo o VNC; muda 3.832
    neurônios; teste de sensibilidade.
- H6 (b), **MN → músculo**: excitatório por construção em `MotorDrive`. O transmissor previsto do
  MN não entra nesse caminho, só nas saídas centrais do MN.

**H2 × H6 em malha aberta** (1 execução de 1,5 s por condição com a v1 e 5 sementes de 3,25 s com a
v2; `results/phase3a/s1_h2_h6.csv`, `s1_h2_h6_v2.csv`):

| Grupo de DNs (n) | MNs ativos (de 391): predicted / verified / gluexc | Pernas rítmicas (v2) |
|---|---|---|
| G1 DNp09 (2) | 0–4 / 0–4 / 11–38 | 0 |
| G2 DNp09 + DNa01 + DNa02 (6) | 11–25 / 19–35 / 106–118 | 0 |
| G3 20 DNs de maior acionamento (20) | 145–162 / 116–127 / 256–278 | 0 |
| G4 cluster "walking" do BANC (159) | 108–115 / 76–78 / 198–216 | 0 |

- **H2 confirmada para recrutamento, não para ritmo.** Populações maiores de DNs recrutam até 70 %
  dos MNs, mas o espectro fica plano: a proeminência máxima em 540 espectros foi 5,8 (uma única
  semente, na borda da banda), e o p95 foi 3,6.
- **H6 não produz ritmo.** Corrigir os sinais (`verified`) reduz um pouco o recrutamento, e o
  glutamato excitatório aumenta muito (mais MNs, mais atividade). Nenhum dos dois gera ritmo.
- **Sem alternância:** flexores e extensores da mesma junta estão **coativados** (r de +0,1 a +0,37
  em CTr e FTi; `results/phase3a/s1/checks.csv`), como uma co-contração tônica.
- Ajustes fora do conectoma usados nesta tabela: sinal `verified` (1) e `verified_gluexc` (2);
  estímulo de Poisson nos DNs (protocolo). Ver `docs/NON_CONNECTOME.md` (Fase 3a).

**Aparato construído** (testado; `tests/test_apparatus.py`):
- Bola do NeuroMechFly v1 portada para o FlyGym 2.1.
- Mosca com torque nas 42 juntas ativas.
- Mapa de 391 MNs → 17 músculos → 7 graus de liberdade por perna.
- Sinais de flexão medidos com torque imposto, iguais nas 6 pernas: CTr −, FTi +, TiTa −.
- Ativação muscular de 1ª ordem.
- Transdução de 941 proprioceptores do BANC: 162 claw, 142 hook, 341 club, 234 placas de pelos e
  62 campaniformes. Os limiares ficam na faixa de ângulos da marcha da Fase 2.

**Figuras** (`results/phase3a/s1/`):
- `raster_*.png`: MNs por perna e por junta;
- `spectrum_*.png`: v1, com o p99 dos surrogados;
- `spectrum_v2_*.png`: Welch, 5 sementes.

**Para a Sessão 2:** fechar o loop (MNs → torque → juntas → proprioceptores → VNC). Testar H1, com
aferência imposta pela cinemática gravada e com loop fechado, e H3 (escala do VNC). Testar também a
sensibilidade à atribuição flexão/extensão dos proprioceptores. A malha aberta já descarta H2 e H6
como causa **suficiente**. O marco depende do loop fechado.
