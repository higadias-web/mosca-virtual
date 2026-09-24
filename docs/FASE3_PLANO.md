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
| 2 | 2026-09-23 | Direção dos proprioceptores por tipo (4 combinações); aferência imposta (marcha gravada) com sinais `verified`, H5 (fundo 5 Hz) e H6-g; ganho muscular fixado por critério (A4); loop fechado com H3 (×1, ×2); diagnóstico sem ajuste; inibição recíproca funcional; sensibilidade F_SAT; §7.2 | H1 (i e ii), H3, H5, H6-g | **Não** (aferência imposta: 0, nem reflexo). **Loop fechado: INCONCLUSIVO** por duas causas: (b) acionamento quase nulo, independente do aparato, e (a) juntas sem limite nem rigidez (§7.2). Sensibilidade F_SAT inválida, não analisada |
| 3 | 2026-09-23 | (em andamento) Pré-registro §7.4 e §7.6 (marco pela métrica congelada; A2' com Wang et al. 2025); T1 e T2; checagem da unidade (**leitura mN·m/° caiu**: m* = 2,5 contra 40); validação: (a), (b) e (e) passaram, **(c) e (d) falharam** (limites macios do MuJoCo não seguram); nenhuma fila (§7.7) | — | pendente (validação falhou) |

Marco da 3ª sessão: ainda pendente. O loop fechado da Sessão 2 foi inconclusivo. A Sessão 3 foi aprovada com
ajustes, e a regra do marco (em taxa) e o pré-registro estão em §7.4.

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


### 7.2 Sessão 2 (2026-09-23): propriocepção (H1), escala (H3), fundo (H5), glutamato (H6-g)

**Procedimento e desvios, registrados antes do resultado.**
- **Resultados vistos antes das instruções de bloqueio.** O resumo da primeira aferência imposta e
  a figura de uma execução do loop fechado com ganho 30 foram abertos antes de o usuário pedir que
  nada fosse aberto antes do `FILA_OK`. Os dois são declarados aqui.
- **Ganho muscular (A4).** A primeira fila usou 30 em todas as juntas, sem fonte. Ela foi
  interrompida e as 40 execuções prontas foram descartadas sem análise
  (`runs/phase3a/s2_gain30_descartado/`). O novo ganho foi fixado por critério independente no
  commit e50c4f5, antes de qualquer resultado: p95 do |τ| que o NeuroMechFly precisa para
  reproduzir a marcha real. A taxa de referência F_SAT = 200 Hz é uma suposição **sem fonte**
  (commit de3573c).
- Pré-registros nos commits 87ef624 e de3573c:
  - regra de inconclusivo;
  - sensibilidade a F_SAT = 100 e 400 Hz;
  - fundo da H5 (5 Hz de entrada, extrapolado do flexor da tíbia);
  - configuração do vídeo.
- **Fila:** 210/210 execuções (`runs/phase3a/s2/FILA_OK`), sob `systemd-inhibit`, com execução
  separada da análise. A análise se recusa a rodar sem `FILA_OK` completo.
- **Métrica congelada:** v2 da Sessão 1, sem mudança.

**Direção dos proprioceptores (item 2 da instrução).**
- Nenhuma fonte classifica claw/hook por sentido em tipos do MANC, FANC ou BANC. Foram verificados
  Mamiya et al. 2018, Lee et al. 2025 (FANC, tabela suplementar não publicada em forma utilizável)
  e Dallmann et al. 2025.
- Como claw e hook se concentram em dois tipos principais cada (claw SNpp50/51; hook SNpp39/41),
  a direção foi atribuída **por tipo**, com as 4 combinações enumeradas. A hipótese de que os dois
  tipos são os dois sentidos **não está verificada**.
- Ritmo conta só se aparecer em ≥ 3 das 4 combinações.

**H1-i, aferência imposta** (marcha real gravada, ~11 Hz; sinais `verified`; 4 combinações × 5
sementes; `results/phase3a/s2_imposed*.csv`, `s2_imposed_entrainment.csv`):

| Condição | Geração (≥ 3/4) | Reflexo na freq. imposta | Potência na freq. imposta / mediana do espectro (mediana; p90) |
|---|---|---|---|
| Sem DNs | 0 de 6 pernas | 0 | 1,55; 2,82 |
| Com G3 | 0 | 0 | 1,31; 2,43 |
| H5 (fundo 5 Hz), sem DNs | 0 | 0 | 1,50; 2,34 |
| H5, com G3 | 0 | 0 | 1,45; 1,94 |
| **Controle H5** (só fundo, sem aferência) | 0 | 0 | 1,37; 2,04 |
| Controle H5 + G3 | 0 | 0 | 1,37; 1,81 |
| H6-g (glutamato excitatório), sem DNs | 0 | 0 | **2,11; 4,53** |
| H6-g, com G3 | 0 | 0 | 1,34; 2,16 |

- **Nem reflexo:** os MNs não acompanham a marcha imposta, e a potência na frequência imposta fica
  igual à do controle sem aferência.
- **Os sensores carregam o ritmo** (hook da L1 com pico em 11 Hz, proeminência 7,6), mas o caminho
  de 2 sinapses dos claw até os MNs é inibitório no saldo (−260 mil contra +265 direto).
- A H6-g sem DNs é o único caso com elevação (p90 4,5). Continua abaixo do limiar e não conta;
  fica como indício para a Sessão 3.
- **Limitação da H5 (pré-registrada):** o Poisson é supralimiar no LIF do Shiu. O fundo faz os
  neurônios dispararem em vez de só despolarizá-los, então não testa bem a "inibição sem o que modular".

**H1-ii + H3, loop fechado:** 3 grupos × 2 escalas × 4 combinações × 5 sementes = 120 execuções.
**Ritmo que conta: 0 em todas as condições** (janela A: 0/4 combinações em todas as pernas).

**Diagnóstico sem ajuste (pré-registro 2)** (`results/phase3a/s2_diag_closed.json`,
`s2/diag_closed.png`):

| Medida (janela A, 120 execuções) | Valor |
|---|---|
| MNs em 0 Hz | 73 % |
| Taxa por MN: mediana / p90 | 0 / 22,8 Hz |
| Ativação média dos grupos musculares: mediana entre execuções (regra) | **0,0016** (p90 dos grupos 0,13) |
| Grupos saturados (≥ 0,95 em > 50 % do tempo) | 0 % |
| Amplitude das juntas / marcha real (mediana) | ThC 5,9×; CTr 12,5×; FTi 15,2× |

**O loop fechado é inconclusivo por duas causas independentes:**

**(b) Acionamento quase nulo. Não depende do aparato e sozinho já torna o loop inconclusivo.**
Com os DNs ligados, a taxa mediana dos MNs é 0 Hz, 73 % ficam parados e a ativação mediana dos
grupos é 0,0016, 30× abaixo do limite pré-registrado de 0,05. O corpo quase não é acionado, então
não há movimento gerado pela rede que os proprioceptores possam realimentar.
*Evidência de que não depende do aparato:* a mesma medida nas execuções em malha aberta da Sessão 1
(sem corpo; sinais `verified`, 200 Hz, 5 sementes) dá o mesmo quadro:

| Grupo | Malha aberta (S1, sem aparato) | Loop fechado ×1 (S2) | Loop fechado ×2 (S2) |
|---|---|---|---|
| G2 | 0,0000 | 0,0000 | 0,0009 |
| G3 | 0,0541 | 0,0443 | 0,0362 |
| G4 | 0,0002 | 0,0007 | 0,0028 |

(mediana entre sementes da ativação média dos grupos). G2 e G4 ficam perto de 0 com ou sem corpo.
O G3 fica na fronteira do limite (0,05) nos dois casos: o aparato baixou pouco (0,054 → 0,044) e não
criou o problema.

**(a) Defeito do aparato: juntas sem limite nem rigidez.** As juntas giram várias voltas: ThC da L1
até 46 rad, FTi da L2 até −71 rad, contra 0,4–1,3 rad na marcha real. O vídeo mostra pernas em
posições impossíveis. Os proprioceptores leram ângulos impossíveis, então o loop fechado não
testa a H1-ii nem a H3.

*Por que a rigidez e o amortecimento passivos do A2 não atuaram:*
- Eles vêm de `make_locomotion_fly`: rigidez 0,05 µN·mm/rad e amortecimento 0,06. Nesse corpo, a
  rigidez efetiva vem dos atuadores de POSIÇÃO (kp = 45 µN·mm/rad, ~900× maior), e a passiva é só
  um resíduo. Ao trocar por torque puro, tirei esse "mola" sem pôr outra no lugar.
- Com o ganho de 10–22 µN·mm, uma ativação de apenas 0,13 (p90) dá ~1,3–2,9 µN·mm. O equilíbrio
  com a rigidez de 0,05 fica a τ/k ≈ 26–58 rad do neutro.
- O amortecimento só atrasa a chegada; não limita a amplitude.
- As juntas do `add_joints` do FlyGym não têm `range` (limites). No uso normal os atuadores de
  posição mantêm as juntas dentro da faixa, e aqui nada as mantinha.

Juntas, as duas causas tornam o **negativo da Sessão 2 inconclusivo**: nem ausência nem presença de
ritmo no loop fechado foi demonstrada.

**Sensibilidade a F_SAT (100 e 400 Hz) registrada como INVÁLIDA.** O pré-registro exigia um
negativo válido do loop fechado. Ele saiu inválido e a sensibilidade rodou no mesmo aparato com
defeito. As duas filas terminaram, mas **não foram analisadas como evidência**. Os arquivos ficam
em `runs/phase3a/s2/closed_fsat*` e não foram apagados. O contador da fila de sensibilidade
(`FILA_OK3`) tem um defeito conhecido: o padrão `^closed_` também conta os arquivos `closed_fsat*`.
Isso não importa, já que ela não será analisada.

**Declaração sobre a figura com ganho 30.** A figura de uma execução do loop fechado (G2, ×1,
combinação 00, semente 7000, ganho 30) foi vista por volta das 12:30. **F_SAT = 200 Hz já estava
fixado antes**: está no código desde o commit da Sessão 1 (7f17e7b, 11:50) e não mudou depois. **O
ganho, sim, foi fixado depois de ver essa figura** (e50c4f5, 12:53). O critério adotado (torque da
marcha real) não usa nada da figura, mas a ordem fica declarada.

**Hipótese da coativação e como foi testada (item 4 da instrução da Sessão 2).**
- *Hipótese:* a coativação flexor × extensor da Sessão 1 (r de +0,1 a +0,37) não vem da falta de
  substrato. Vem de os DNs acionarem em paralelo os pré-motores excitatórios dos DOIS lados, sem um
  sinal fásico (proprioceptivo) que engaje a inibição recíproca.
- *Teste estrutural* (`results/phase3a/s2_coactivation_structure.csv`): o substrato de alternância
  existe. A excitação pré-motora compartilhada entre flexores e extensores é baixa (5–15 % por
  junta e perna), e a inibição pré-motora é seletiva (0,84–0,89). Os DNs de G3 acionam os dois
  lados (flexor/extensor de 0,9× a 8×).
- *Teste funcional* (`results/phase3a/s2_reciprocal_inhibition.csv`): com G3 ligado, acionar os
  20 pré-motores excitatórios mais seletivos dos flexores e medir a mudança nos extensores.
  **A inibição recíproca FUNCIONA no modelo:** nas 12 combinações de perna e junta, os flexores sobem
  2–5× (p. ex. FTi da L1: 5,3 → 26,3 Hz) e os extensores **caem 44–96 %** (FTi da L1: 7,2 → 0,3 Hz;
  CTr da L1: 16,9 → 2,8 Hz). A média é de 5 sementes por combinação (60 execuções, CSV gravado só
  ao fim). Leitura: a coativação da Sessão 1 não vem da falta de inibição recíproca, e sim do
  acionamento paralelo dos dois lados pelos DNs. Falta testar a direção oposta (extensores →
  flexores).
- *Loop fechado:* r flexor × extensor da FTi perto de 0 (−0,07 a +0,23), mas com acionamento quase
  nulo. Não é evidência de alternância.

**Figuras e vídeo** (`results/phase3a/s2/`): `diag_closed.png`; `closed_G3_top20_drive_s1_c00_7000.png`
(execução pré-registrada: raster, bola e espectros A e B); vídeo WebM/VP9
`/home/sine/terrario-virtual/results/phase3a/s2/video_closed_G3_top20_drive_s1_c00_7000.webm`
(5,00 s, 840 × 360, 30 fps, 150 quadros). A reexecução é **idêntica** à da fila: 21.968 spikes de
MNs, sha256 80d9d5851cb58d26… nas duas.

**Ajustes fora do conectoma nesta sessão:** A1–A8, A5b (direção por tipo), sinal `verified`,
H5-bg e H6-g (ver `docs/NON_CONNECTOME.md`). Nenhum resultado positivo foi obtido com eles.

### 7.3 Proposta para a Sessão 3 (aprovada com ajustes em 2026-09-23; ajustes em §7.4)

**(a) Validação do aparato antes de qualquer fila.** São 5 testes automáticos, e todos precisam
passar antes da primeira execução com o LIF:
1. **Limites:** cada junta ativa ganha um `range` (proposta: faixa da marcha real gravada ± 30 %,
   ou limites anatômicos da literatura, se houver). Teste: torque máximo por 200 ms não ultrapassa
   o limite.
2. **Rigidez e amortecimento passivos com fonte.** Proposta: medições de rigidez passiva de juntas
   de perna de inseto, se existir fonte para Drosophila; senão, o valor que faz o tempo de relaxação
   passiva ficar na ordem medida, com fonte a buscar. Teste: sem ativação, a perna volta ao neutro
   e fica parada (amplitude < 0,05 rad).
3. **Faixa dinâmica:** com ativação de 0 a 1 em cada grupo, a junta varre de 0 a ~100 % da
   amplitude da marcha real, sem ultrapassar os limites.
4. **Réplica da marcha real** com torques equivalentes: os ângulos ficam na faixa real (razão de
   amplitude de 0,5 a 2).
5. **Repouso:** 5 s sem estímulo nem ativação, sem drift da bola nem das juntas.

**(b) Se, com o aparato corrigido, a ativação continuar perto de 0.** Definido antes de rodar,
contando para o marco:
- Regra: se a mediana da ativação média dos grupos na janela A ficar < 0,05 **em todas** as
  condições (3 grupos × 2 escalas) do loop fechado corrigido, **o resultado da Sessão 3 é
  "sem acionamento motor suficiente"**. Isso conta para o marco como **ausência de ritmo com loop
  proprioceptivo fechado**: a 3a é encerrada, o negativo é documentado (com esta causa) e a 3b segue
  com o controlador (a).
- A única exceção seria uma causa de acionamento baixo pré-registrada e testável DENTRO da
  Sessão 3, sem estourar o prazo do marco. Hoje: a F_SAT sem fonte (200 Hz).
- Proposta: fixar a F_SAT com fonte antes de rodar. Se não houver fonte, manter 200 Hz e aceitar a
  regra acima. Nenhum ajuste de ganho ou de F_SAT depois de ver o resultado.

### 7.4 Sessão 3: ajustes da aprovação e pré-registro (2026-09-23, antes de rodar qualquer coisa)

Commitado antes de qualquer execução da Sessão 3. O que diverge de §7.3 vale como está aqui.

**1. Regra do marco, em taxa (substitui §7.3 (b)). SUBSTITUÍDA em §7.6.1; não vale mais.**
- Se a mediana entre sementes da taxa média dos MNs por grupo ficar **abaixo de 10 Hz** (equivalente
  a 0,05 × 200 Hz) **em todas as condições**, o resultado conta como ausência de ritmo com o loop
  fechado. A 3a é encerrada e a 3b segue com o controlador (a).
- **A exceção da F_SAT foi removida.** A F_SAT continua em 200 Hz só para mover o corpo
  (`MotorDrive`) e não entra na decisão do marco.
- Operacionalização, fixada agora:
  - janela A = 450–3450 ms, como na Sessão 2;
  - para cada execução, r_g = taxa média dos MNs do grupo muscular g (perna × junta × papel,
    `leg_mn_table.csv`, MNs em 0 Hz incluídos);
  - estatística da execução = mediana de r_g entre os grupos, o mesmo agregador da regra de ativação
    da Sessão 2;
  - condição = grupo de DNs × escala do VNC × combinação de direção;
  - valor da condição = mediana das 5 sementes;
  - a regra dispara se todas as condições ficarem abaixo de 10 Hz.
- **Na fronteira:** a decisão usa a mediana das 5 sementes, olhada **uma única vez**. Não entram
  novas sementes nem rodada extra para desempatar.
- O ritmo continua avaliado pela métrica v2 congelada. Um ritmo só conta se sumir na ablação (§1b.2).

**2. Parâmetros passivos das juntas (correção do defeito A2), com fonte.**
Fonte: Wang, Babski, Perdomo, McMahan, Ramakrishnan, Biswas e Bhandawat 2025, "Passive muscle forces
in *Drosophila* are large but insufficient to support a fly's weight", bioRxiv
10.1101/2025.04.29.651225 v2 (**preprint, sem revisão por pares**; PMC12324252).
- Método da fonte: MNs inativados geneticamente, com o torque passivo estimado pela configuração da
  perna. O torque é linear no desvio do ângulo de repouso; n = 20 moscas; o IQR indica uma faixa de
  ~2× entre moscas.
- Tabela 1 (mediana). A unidade vem impressa como "mN/°". A leitura dimensionalmente coerente é
  **mN·m/°**, que fecha com duas afirmações do artigo: o torque passivo é muito maior que o peso da
  própria perna e 70× menor que o necessário para sustentar a mosca.
- Conversão para a unidade do modelo (µN·mm/rad = mN·m × 10⁶ × 57,296):

| DOF do NeuroMechFly (grau de liberdade da fonte) | Anterior | Média | Posterior |
|---|---|---|---|
| CTr pitch (levação-depressão) | 0,859 | 0,493 | 1,547 |
| ThC pitch (retração-protração) | 0,109 | 0,630 | 3,209 |
| FTi pitch (extensão-flexão) | 0,974 | 1,432 | 0,974 |
| ThC roll (pronação-supinação, na ThC pela fonte) | 0,859 | 0,573 | 2,693 |
| **Sem medida** (ThC yaw, TrF roll, TiTa pitch): mediana dos 4 valores da mesma perna, **escolha sem fonte** | 0,859 | 0,602 | 2,120 |

- **Repouso das molas:** a pose neutra do NeuroMechFly (`springref` atual). A fonte só dá os ângulos
  de repouso em figura. **Escolha sem fonte.**
- **Amortecimento: a fonte não mede, então vale um critério fixado agora, sem ajuste depois.** Para
  cada junta, c = max(k · 8 ms, 2·√(k·I)):
  - 8 ms = 1/(2π · 20 Hz): a junta passiva não pode filtrar a banda de passada (3–20 Hz, Mendes et
    al. 2013, a mesma da métrica);
  - 2·√(k·I) é o amortecimento crítico, com I = diagonal da matriz de massa do MuJoCo na pose
    neutra. É um piso para a junta não oscilar sozinha;
  - estabilidade com dt = 0,1 ms: 2·√(I/k) ≥ 1,5 ms ≫ 0,1 ms (I ~ 2×10⁻⁶ a 1,5×10⁻⁵ no modelo). O
    integrador Euler do MuJoCo trata o amortecimento de forma implícita.
- Tarsos passivos (7,5 / 0,01): sem mudança.
- **Limites de amplitude** (`range`): para cada DOF ativo, [mín − 0,3·s, máx + 0,3·s] da marcha
  real gravada (MotionSnippet, 2 s), com s = máx − mín. Se o repouso da mola cair fora, a faixa é
  estendida até ele. A fonte não dá a amplitude máxima de movimento. **Escolha sem fonte.**
- Consequência, calculada antes de rodar: com k ~ 0,1–3 µN·mm/rad e ganho de 10–22 µN·mm (A4,
  congelado), uma ativação líquida de 1 num grupo leva o equilíbrio a dezenas de rad, bem além dos
  limites. Com a rigidez medida, **o que segura a junta é o balanço entre antagonistas e os
  limites**, não a mola. Isso é coerente com a fonte (torque passivo 70× menor que o de
  sustentação). O teste 3 de §7.3 ("varre até ~100 % da amplitude real") não pode passar e é
  reformulado abaixo. **Nenhum ganho muda por causa disso.**

**3. Validação do aparato: tolerâncias PROPOSTAS (aguardam aprovação; nada roda antes).**
Referência medida na marcha real gravada (MotionSnippet, 2 s, 18 pares perna × {ThC pitch, CTr,
FTi}):
- amplitude p5–p95 de 0,25 a 1,47 rad;
- CV da amplitude entre passadas: mediana 0,25, máximo 0,41;
- diferença da própria medida p5–p95 entre as duas metades de 1 s: mediana 9 %, **máximo 34 %**.

| Teste | Tolerância proposta | Justificativa |
|---|---|---|
| (a) Réplica com torques | Réplica por servo (kp = 150, como no tutorial 2 e na calibração do A4) **na bola, com as juntas novas**; os torques dos atuadores são gravados e tocados em malha aberta como MOTOR, no mesmo aparato. **Cada uma das 18 amplitudes p5–p95 fica dentro de ±35 % da marcha real** (X = 35 %) | É o máximo que a mesma medida varia na mosca real entre duas metades do registro (34 %). Uma tolerância menor reprovaria a mosca real contra ela mesma. Ainda é 17–40× mais apertada que o defeito da Sessão 2 (5,9–15×). O valor vem dos dados; a regra "a pior metade da mosca real" é escolha |
| (b) Repouso | Sem estímulo nem ativação, por **Z = 5,7 s** (a duração de uma execução do loop). Depois de 0,5 s de acomodação, **cada junta ativa fica a menos de Y = 0,05 rad** do seu ângulo em 0,5 s, e a superfície da bola percorre < 0,2 mm | Y = 1/3 da largura da sigmoide de posição dos claw (W_RAD = 0,15 rad, A5), para a deriva de repouso não varrer os sensores de posição, e 1/5 da menor amplitude real (0,25 rad). Z cobre uma execução inteira. **Bola (0,2 mm): escolha sem fonte.** Os 0,5 s de acomodação também são escolha |
| (c) Limites | Ativação 1 (torque = ganho) em cada grupo, sozinho, por 200 ms: a junta não passa do `range` em mais de 0,05 rad (limite macio do MuJoCo) | a mesma tolerância Y |
| (d) Faixa dinâmica (reformulado) | Ativação de 0 a 1 em 5 degraus, em cada grupo: o ângulo varia de forma monotônica, no sentido do papel (flexor/extensor etc.), e respeita (c) | não exige cobrir a amplitude real, que depende do balanço dos antagonistas (item 2) |

Os testes (b) a (d) usam o aparato da bola, com as mesmas pernas e a mesma pose. Se qualquer teste
falhar, **nenhuma fila roda**, e a falha é relatada sem ajuste do critério.

**4. Dois testes baratos (independentes do aparato; malha aberta ou só grafo).**
- **T1, saldo E/I do caminho sensor → MN na H6-g.** Grafo do híbrido, vnc_scale 1, nos modos
  `verified` e `verified_gluexc`.
  - Para cada perna e cada classe proprioceptiva (claw, hook, club, placas de pelos, campaniformes),
    calcular a soma com sinal das sinapses diretas até os MNs da mesma perna (1 sinapse) e a soma de
    W₁·W₂ nos caminhos de 2 sinapses (produto dos pesos com sinal; a desinibição conta como
    positiva, o que é uma linearização).
  - Relatar E, I e (E − I)/(E + I), também separando MNs flexores e extensores da FTi.
  - **Leitura pré-registrada:** se o saldo de 2 sinapses de claw/hook passar de negativo (`verified`)
    a positivo (`gluexc`), isso é coerente com a elevação da H6-g sem DNs na Sessão 2 (p90 = 4,5).
    Como a H6-g não tem base documentada, isso gera **só uma hipótese**, nunca ritmo nem resultado
    positivo.
- **T2, inibição recíproca no sentido extensores → flexores.** Espelho exato do teste da Sessão 2
  (`experiments/phase3a_recip.py`):
  - estímulo nos 20 pré-motores excitatórios mais seletivos para os extensores (entrada em E > 0 e
    em F = 0) a 100 Hz, de 1000 a 2000 ms;
  - G3 a 200 Hz o tempo todo; sinais `verified`, escala 1; sementes 9000–9004 (as mesmas); 12
    pares perna × junta (CTr, FTi).
  - **Critério pré-registrado:** a inibição recíproca E → F funciona se, na média das 5 sementes,
    os flexores caírem ≥ 25 % em pelo menos 9 dos 12 pares, com os extensores subindo. Os limiares
    25 % e 9/12 são **escolha sem fonte**. Um par com flexores em 0 Hz antes do estímulo é "não
    avaliável" e conta contra.

### 7.5 Sessão 3: resultados (parcial; a validação do aparato aguarda aprovação das tolerâncias)

**T1, saldo E/I proprioceptor → MN** (`experiments/phase3a_s3_ei.py`, `results/phase3a/s3_ei_balance.csv`;
agregado nas 6 pernas, alvo = todos os MNs da perna):

| Classe | 1 sinapse (ambos os modos) | 2 sinapses, `verified` | 2 sinapses, `gluexc` (H6-g) |
|---|---|---|---|
| claw | +0,996 | −0,52 | −0,21 |
| hook | +1,000 | −0,52 | −0,22 |
| club | +1,000 | −0,49 | −0,25 |
| placas de pelos | +0,98 | −0,49 | **+0,12** |
| campaniformes | +0,88 | −0,20 | **+0,17** |

- **Leitura pré-registrada: NÃO cumprida para claw e hook.** O saldo de 2 sinapses fica menos negativo
  com glutamato excitatório (de −0,52 para −0,21/−0,22), mas continua negativo em 11 de 12 pares
  perna × classe. A única exceção é o claw da L1: +0,03.
- Achado fora da leitura pré-registrada, que vale só como hipótese: com a H6-g, as placas de pelos e
  os campaniformes passam a saldo positivo nos caminhos de 2 sinapses. Na aferência imposta da Sessão
  2, as placas de pelos eram acionadas e os campaniformes ficavam em 0 (sem força de contato). Essa é
  uma via possível para a elevação da H6-g sem DNs. A H6-g continua sem base documentada.
- A via direta (1 sinapse) é excitatória e pequena. O saldo negativo vem dos interneurônios. As somas
  de 1 e de 2 sinapses não são comparáveis em escala (produto de contagens).

**T2, inibição recíproca extensores → flexores** (`experiments/phase3a_recip.py --direction E2F`,
`results/phase3a/s3_reciprocal_inhibition_E2F.csv`; 60 execuções, sementes 9000–9004):
- **Funciona pelo critério pré-registrado: 11 de 12 pares** (critério ≥ 9). Os extensores sobem de
  15 % a 1.700 % e os flexores caem de 35 % a 61 %.
- A exceção é a FTi da L1 (flexores −14 %).
- Com a Sessão 2 (flexores → extensores: 12 de 12, com os extensores caindo 44–96 %), a inibição
  recíproca é funcional **nos dois sentidos**. O efeito é assimétrico: os extensores inibem os flexores
  menos do que o contrário.

### 7.6 Sessão 3: segunda rodada de ajustes (2026-09-23, commitada antes de rodar a validação)

Tolerâncias (a)–(d) de §7.4.3 **aprovadas como propostas**.

**1. Regra do marco (substitui a regra por taxa de §7.4.1).**
- Com o aparato validado, o loop fechado roda **uma única vez**, no mesmo desenho da Sessão 2:
  - 3 grupos de DNs (G2, G3, G4) × 2 escalas (×1, ×2) × 4 combinações de direção × 5 sementes;
  - sinais `verified`, F_SAT 200 Hz, janela A = 450–3450 ms;
  - corpo `passive="wang2025"`.
- O marco é decidido pela **métrica de ritmo congelada (v2)**. Numa combinação, uma perna é rítmica se
  a v2 passar (≥ 3 de 5 sementes). Para cada condição (grupo × escala) e cada perna, conta-se em
  quantas das 4 combinações ela é rítmica:
  - **0/4 em todas** as condições e pernas → **ausência de ritmo**;
  - **≥ 3/4** em alguma condição e perna → **ritmo**. Continua valendo §1b.2: o ritmo só se sustenta
    se sumir na ablação;
  - **1–2/4** (e nenhum ≥ 3/4) → **ausência para o marco**, registrada como **hipótese**, porque a
    direção por tipo (A5b) não está verificada.
- A taxa dos MNs entra **só como diagnóstico** (a regra por taxa de §7.4.1 foi retirada).
- Se a validação do aparato falhar: relatar e parar.
- **Juntas no limite:** fração do tempo, na janela A, em que cada DOF ativo fica a ≤ 0,02 rad de um
  dos limites ou além deles (a margem de 0,02 rad é escolha: a folga do limite macio do MuJoCo). Um
  ritmo numa perna em que algum DOF ativo fica no limite **> 50 % do tempo** é marcado como
  **suspeito de artefato**, e a decisão do marco sobre ele espera a sua revisão, sem nova rodada.

**2. Rigidez de Wang et al. 2025: valor bruto, unidade e conversão.**
Fonte: bioRxiv 10.1101/2025.04.29.651225 v2, **PREPRINT** (sem revisão por pares); PMC12324252,
Tabela 1. A legenda diz, textualmente: "Median stiffness for each of the measured joints in **mN/°**".
Um valor em mN/° é dimensionalmente uma **força** por ângulo, não um torque. A unidade impressa está
incompleta, e a leitura **mN·m/°** é uma **hipótese nossa**, a ser checada (item 3).

| Grau de liberdade (fonte) | Anterior | Média | Posterior |
|---|---|---|---|
| Lev-Dep | 1,5×10⁻⁸ | 8,6×10⁻⁹ | 2,7×10⁻⁸ |
| Ret-Pro | 1,9×10⁻⁹ | 1,1×10⁻⁸ | 5,6×10⁻⁸ |
| Ext-Flex | 1,7×10⁻⁸ | 2,5×10⁻⁸ | 1,7×10⁻⁸ |
| Pro-sup | 1,5×10⁻⁸ | 1×10⁻⁸ | 4,7×10⁻⁸ |

Conversão, exemplo com Ext-Flex anterior = 1,7×10⁻⁸ mN·m/°:
1. mN·m → N·m: × 10⁻³ → 1,7×10⁻¹¹ N·m/°.
2. N → µN: × 10⁶; m → mm: × 10³ → 1,7×10⁻¹¹ × 10⁹ = 1,7×10⁻² µN·mm/°.
3. ° → rad: 1 rad = 57,296°, então (por °) × 57,296 = (por rad) → 1,7×10⁻² × 57,296 =
   **0,974 µN·mm/rad**.
Fator total: × 10⁶ × 57,296 = × 5,7296×10⁷. O modelo usa g, mm e s. A força sai em g·mm/s² = 10⁻⁶ N
= µN, e o torque em µN·mm (o kp = 150 µN·mm/rad do tutorial 2 do FlyGym está na mesma unidade).
As outras leituras possíveis deslocam tudo por potências de 10³: mN·mm/° → 0,000974;
µN·m/° → 0,000974; N·m/° → 974.

**3. Checagem da leitura (reproduz um número do próprio artigo).**
Número escolhido: "a **40-fold increase** implemented uniformly across all leg joints was necessary
to support the fly" (e, com a rigidez medida, a mosca simulada cai: "fell within 20 milliseconds").
O multiplicador que sustenta a mosca muda por 10³ entre as leituras, então ele discrimina a leitura.
- **Protocolo** (`experiments/phase3a_s3_unitcheck.py`):
  - NeuroMechFly com `passive="wang2025"` e toda a rigidez das pernas × m, com o amortecimento pelo
    mesmo critério;
  - mosca livre no chão plano, sem torque e sem adesão, por 1 s;
  - "sustenta" = tórax, abdome e cabeça sem contato com o chão em ≥ 95 % do tempo entre 0,5 e 1 s;
  - grade m ∈ {1; 2,5; 5; 10; 20; 40; 80; 160; 320; 640; 1000}; m* = o menor que sustenta.
- **Critério:**
  - m* ∈ [10, 160] (fator 4 em torno de 40, para cobrir as diferenças entre o modelo OpenSim deles e
    o NeuroMechFly: massas, geometria, pose, definição de "sustentar") → a leitura se mantém;
  - m* fora dessa faixa → **a leitura "mN·m/°" cai**, e voltamos a discutir;
  - sanidade: m = 1000 precisa sustentar, senão a checagem é inválida.
- Descritivo: tempo até o primeiro contato do corpo com m = 1 (no artigo, < 20 ms).
- Os ângulos de repouso e a constante de tempo não servem: o artigo só dá os ângulos em figura, e os
  ~100 ms são o decaimento da força ativa (inativação dos MNs + músculo), não a mecânica passiva.

**4. Limites anatômicos: procurados, nenhum utilizável.**
- NeuroMechFly (FlyGym 2.1 e 1.x): as juntas não têm `range`.
- `flybody` (FlyGym, `assets/model/flybody/joints.yaml`): tem faixas, mas em outra referência de
  ângulo. A FTi vai de −1,35 a 1,3 rad, contra 0,2–2,5 na marcha do NeuroMechFly. Não é transferível.
- FlyMimic (Ozdil et al. 2026, ICLR; `assets/model/musculoskeletal/`, convertido do OpenSim): tem a
  mesma convenção do NeuroMechFly, mas só na perna anterior esquerda. Só 2 DOFs têm limite ativo (ThC
  roll 0,14–0,62; FTi 0,48–2,50); os demais têm `limited="false"`, e nada documenta a origem das faixas.
- **Mantemos a marcha ± 30 %** e relatamos a fração do tempo no limite (item 1). Para comparação, a
  FTi da L1 fica em 0,03–2,72 com o nosso critério, contra 0,48–2,50 no FlyMimic.

**5. Teste (e), controle negativo mecânico.**
- Sem conectoma. Cada MN de perna dispara Poisson tônico na **sua taxa média da Sessão 2** (janela A,
  média das 120 execuções do loop fechado; média entre MNs 8,9 Hz, máximo 92 Hz).
- Mesmo protocolo do loop: pulso A7, 5,7 s, 5 sementes, corpo novo.
- A métrica congelada é aplicada aos **ângulos** (cada DOF ativo) e aos **proprioceptores** (Poisson
  da transdução, população por perna, 4 combinações). Detalhe em `experiments/phase3a_s3_validate.py`:
  - para os ângulos, só a parte espectral da v2 mais a reprodutibilidade. O teste de surrogados não
    se define para um sinal único; sem ele o critério fica mais sensível, o que é o lado conservador
    num controle negativo;
  - a cópia da parte espectral é conferida contra `rhythm.welch_peak`.
- **Qualquer pico na banda de 3–20 Hz que passe pela métrica = o aparato gera ritmo sozinho, e nenhuma
  fila roda.**

**Ordem:** este commit; depois a checagem da unidade (item 3) e a validação (a)–(e); depois parar
para revisão.

### 7.7 Sessão 3: resultado da checagem da unidade e da validação (2026-09-23). VALIDAÇÃO FALHOU; nenhuma fila rodou

**Checagem da unidade** (`results/phase3a/s3_unitcheck.json`): **a leitura "mN·m/°" CAIU pelo critério
pré-registrado.**

| m (× rigidez da fonte) | 1 | 2,5 | 5 | 10 | 20 | 40 | 80 | 160 | 1000 |
|---|---|---|---|---|---|---|---|---|---|
| Sustenta (corpo sem tocar o chão) | não (1º contato em 53 ms) | sim | sim | sim | sim | sim | sim | sim | sim |
| Altura do tórax em 1 s (mm) | 0,43 | 0,63 | 0,64 | 0,62 | 0,61 | 0,83 | 1,01 | 1,09 | 1,15 |

- Resultado: m* = 2,5, fora de [10, 160] (no artigo, 40). A referência ×1000 sustenta, e a resposta é
  monotônica, então a checagem é válida. A massa do modelo é 1,02 mg.
- Direção da discrepância: o nosso modelo precisa de **menos** rigidez que o do artigo para não
  encostar o corpo.
- Para a discussão, e não como critério: as leituras vizinhas (mN·mm/° ou µN·m/°, 10³× menores)
  levariam m* para ~2.500; N·m/° (10³× maior) levaria para ~0,0025. As duas ficam mais longe de 40 que
  mN·m/°.
- A definição de "sustentar" usada aqui (corpo sem contato) é frouxa. Entre m = 2,5 e 20 o tórax fica
  a ~55 % da altura da referência rígida. A definição do artigo não foi verificada.
- Defeito menor, só no campo descritivo: `thorax_z0` foi lido antes do primeiro passo e saiu 0.

**Validação do aparato** (`results/phase3a/s3_validation*.{json,csv}`):

| Teste | Resultado | Números |
|---|---|---|
| (a) Réplica com torques | **passou** | razão da amplitude de 0,95 a 1,00 (mediana 0,99), 0 de 18 fora de ±35 % |
| (b) Repouso | **passou** | deriva máxima 0,003 rad (CTr da R1); bola 0,015 mm |
| (c) Limites | **FALHOU** | 66 de 66 grupos; violação de 2,3 a 36,6 rad |
| (d) Faixa dinâmica | **FALHOU** (por (c)) | 0 de 66 não monotônicos; todos passam do limite |
| (e) Controle negativo mecânico | **passou** | 0 positivos em 66 (42 ângulos + 24 proprioceptores); proeminência máxima 6,1 (ângulo; sem reprodutibilidade) e 4,9 (proprioceptores) |

**Causa de (c), diagnosticada só lendo o modelo compilado, sem nova simulação:**
- Os limites estão ativos: `jnt_limited` = 1 e nenhum `mjDSBL_LIMIT`.
- Eles usam o `solref` padrão do MuJoCo (0,02 s, amortecimento 1). No MuJoCo, a rigidez de um
  limite macio escala com a massa efetiva da junta: k ≈ I/τ². Com I ~ 10⁻⁵ e τ = 20 ms, k ≈ 0,025
  µN·mm/rad. Um torque de 10–22 µN·mm atravessa o limite como se ele não existisse. O ângulo andou o
  que dava torque/rigidez em 200 ms (FTi ~21 rad, ThC pitch da perna anterior ~37 rad).
- (a) e (b) passaram porque não chegam perto dos limites.
- É um defeito de implementação do aparato (parâmetro numérico do limite), não dos critérios.
  **Nenhuma fila roda.** A correção precisa de aprovação (ver o relato da sessão).
