# Benchmark da Fase 0: ThinkPad T14 Gen 4 (i5-1345U, 16 GB, Intel UHD)

Medido em 2026-09-22, Fedora 44, kernel 7.2.5, **na tomada**, turbo ligado (4,7 GHz P / 3,5 GHz E).
Todas as medições são de um único processo (1 thread, salvo indicação), num subprocesso próprio
(`ru_maxrss` = RAM de pico). Dados brutos: `bench/results/short.jsonl`, `bench/results/throttle.jsonl`.
Nenhuma medição entrou em swap (zram monitorado antes e depois).

Métrica: **segundos de parede por segundo simulado** (s/s). Abaixo de 1 = mais rápido que o tempo real.

## 1. Cérebro da mosca isolado (Shiu et al. 2024, FlyWire v783, 138.639 neurônios, 15,1 M conexões)

Estímulo: 20 GRNs de açúcar a 150 Hz (exemplo do repositório original). dt = 0,1 ms.
Sincronização a cada 1 ms (10 passos por chamada), como na co-simulação.

| Motor | Equilibrado | Desempenho | RAM de pico |
|---|---|---|---|
| **numba, conjunto ativo (float64)** | **0,80** | **0,64** | 3,0 GB |
| numba denso float64 | 2,34 | 1,98 | 2,9 GB |
| numba denso float32 | 2,13 | 1,75 | 2,8 GB |
| numba denso paralelo (2 threads) | 2,35 | 1,98 | 2,9 GB |
| numpy + scipy.sparse | 12,6 | 10,7 | 2,7 GB |
| PyTorch CPU (1 thread) | 16,3 | 13,7 | 2,9 GB |
| PyTorch CPU (2 threads) | 10,3 | 9,1 | 2,9 GB |
| Brian2 2.10.1 runtime (Cython), código original | 3,38 | 2,78 | 3,0 GB |
| Brian2 `cpp_standalone` (1 thread) | 2,90 | 2,41 | 3,1 GB |
| Brian2 `cpp_standalone` (2 threads OpenMP) | 3,31 | 2,89 | 3,1 GB |

Tempos fixos (não entram no s/s): carga do conectoma ~1,1 s; compilação JIT do numba em
cache; Brian2 `cpp_standalone` compila 4–6 s por execução; Brian2 runtime recompila Cython a
cada rede nova (em 30 trials seguidos: 38 s por trial, contra 3,4 s isolado).

A RAM de pico (~3 GB) vem da leitura do Parquet via pandas. O estado da simulação em si é
pequeno (CSR de 15 M pesos ≈ 180 MB). Dá para reduzir com um cache `.npz` da matriz CSR.

### Reprodução numérica (requisito da SPEC)
Numba com conjunto ativo contra o Brian2 original (`third_party/Drosophila_brain_model/model.py`),
30 trials × 1 s cada, mesmo estímulo (`bench/compare_rates.py`):

| Métrica | Resultado |
|---|---|
| Neurônios ativos | 433 (Brian2) × 435 (numba) |
| Spikes por trial | 12.841 × 12.775 (−0,5 %) |
| Correlação de Pearson das taxas por neurônio | **0,9997** |
| Neurônios (taxa ≥ 0,5 Hz) com diferença > 3 erros-padrão de Poisson | **0 de 373** |
| MN9 (motoneurônio da probóscide) | 78,4 × 79,7 Hz |
| Numba denso × conjunto ativo (mesma semente) | **idênticos bit a bit** |

A primeira versão deu +21 % de spikes. A causa foi uma semântica do Brian2: com
`(unless refractory)`, entradas sinápticas e de Poisson que chegam durante o refratário são
**descartadas** (`set_conditional_write`). Isso foi verificado empiricamente e corrigido.

Paralelismo: nenhuma forma testada ganhou com 2 threads (numba `prange`, OpenMP do Brian2),
exceto o torch, que continua 14× mais lento que o numba com conjunto ativo. A rede é esparsa
demais por passo para compensar a sincronização entre threads.

## 2. Corpo da mosca isolado (FlyGym 2.1.0, NeuroMechFly v2, dt = 0,1 ms)

Caminhada com o CPG de demonstração, em chão plano, com adesão (≈14 mm/s de deslocamento).

| Configuração | Equilibrado | Desempenho | RAM |
|---|---|---|---|
| Sem visão | 2,83 | 2,31 | 0,3 GB |
| Visão a 100 Hz (omatídeos) | 8,23 | 6,76 | 0,5 GB |
| Visão a 500 Hz (padrão do FlyGym 1.x) | 22,1 | 14,6 | 0,5 GB |

A visão consome 62–81 % do tempo. A resolução bruta é fixa em 512 × 450 px por olho, porque é
definida pelo mapa de omatídeos `compound_eye.npz` (721 omatídeos por olho). O que se pode
baixar é a taxa de atualização. Sozinha, a física da mosca já é **2,3–2,8× mais lenta que o
tempo real** nesta CPU.

## 3. Uma minhoca (PROXY; não é o modelo do projeto)

Cadeia de 24 cápsulas em escala real (1 mm × 60 µm), 4 atuadores por segmento, onda senoidal,
rede densa de 400 unidades (`bench/bench_worm.py`).

| Variante | 1 minhoca | 2 minhocas |
|---|---|---|
| Contato com o chão, Jacobiano automático (esparso) | 1,57 | 6,49 |
| Contato com o chão, Jacobiano **denso** | 1,48 | 3,23 |
| Contato, denso, sem autocolisão | 1,21 | 2,74 |
| **Planar sem contato, arrasto anisotrópico (RFT) via `xfrc_applied`** | **0,23** | **0,43** |

Lições: (1) o MuJoCo escolhe o Jacobiano esparso quando nv ≥ 60, e aqui ele é 2× mais lento;
com o denso, o custo fica linear; (2) os contatos por cápsula dominam o custo; (3) a variante
RFT é ~5× mais barata, mas é **numericamente rígida**: com massas reais (~10⁻⁷ na unidade do
modelo) e arrasto realista, o passo explícito de 0,1 ms diverge (regime sobreamortecido). Isso
precisa de tratamento na Fase 4 (integração implícita do arrasto ou formulação quase estática).
O custo da rede neural é irrelevante (~0,1–0,2 s/s mesmo em numpy passo a passo).

## 4. Cenário completo (PROXY do perfil `padrao`)

Mosca FlyGym + 2 minhocas-proxy com contato **no mesmo MjModel** + cérebro inteiro (numba ativo)
+ 2 redes-proxy + campo de odor 2D 256² a cada 10 ms (`bench/bench_full.py`).

| Configuração | Equilibrado | Desempenho | RAM |
|---|---|---|---|
| Jacobiano automático | 15,3 | 12,9 | 3,0 GB |
| **Jacobiano denso** | **9,0–9,2** | **7,65** | 3,0 GB |

Divisão do tempo (denso): física 75 %, cérebro 12 %, minhocas 12 %, odor 0,4 %.
**Estimativa** (soma das partes medidas, não medida integrada) com minhocas RFT:
~4,5–5 s/s no Equilibrado.

## 5. Throttling (execução contínua > 10 min)

Cenário completo (denso) em blocos de 20 s simulados, 12 min por perfil, 2 min de pausa entre perfis.

| Perfil | s/s por bloco (início → fim) | Frequência P | Temp. máx. |
|---|---|---|---|
| Equilibrado | 9,07 · 9,04 · 9,07 · 9,00 | ~3,0–3,6 GHz | 55 °C |
| Desempenho | 7,65 · 7,66 · 7,62 · 7,66 · 7,69 | ~4,5–4,7 GHz | 84 °C |

**Não houve throttling mensurável** com carga de 1 processo: a variação entre blocos foi < 1 %.
O Desempenho é ~15–20 % mais rápido que o Equilibrado em todas as medições, ao custo de
~30 °C a mais. Com 2 processos pesados em paralelo o comportamento térmico pode mudar (não testado).

## 6. Tamanho do log (estimativa por segundo simulado, perfil `padrao`)

| Fluxo | Hipótese | Volume |
|---|---|---|
| Spikes da mosca | 13 k spikes/s (açúcar) a 50 k/s (vários sentidos); 8 B por spike | 0,1–0,4 MB/s |
| Corpo da mosca a 200 Hz | qpos + qvel + forças de contato ≈ 170 float32 | 0,14 MB/s |
| Atividade graduada das minhocas a 200 Hz | 2 × (380 + 147) valores, float16 | 0,42 MB/s (0,21 a 100 Hz) |
| Corpo das minhocas a 200 Hz | 2 × ~26 DoF × (qpos + qvel), float32 | 0,08 MB/s |
| Campo de odor | 128² float16 a 5 Hz | 0,16 MB/s |
| **Total, sem compressão** | | **~0,9–1,2 MB/s** |

Portanto 5 GB equivalem a ~70–90 min simulados sem compressão. A compressão colunar do
Parquet/zstd deve render ~2× (não medido). O aviso de 5 GB precisa existir, mas só dispara
em episódios longos.

## 7. Dimensionamento de episódios

| Perfil | Custo | 1 min simulado | Numa noite (8 h) |
|---|---|---|---|
| `debug` (mosca sem cérebro completo, minhocas RFT) | ≥ 2,5–3 s/s (a física da mosca sozinha já custa 2,3–2,8) | ~3 min | — |
| `padrao` (proxy medido, minhocas com contato) | 7,7–9 s/s | 8–9 min | ~55–60 min simulados |
| `padrao` (estimado, minhocas RFT) | ~4,5–5 s/s | ~5 min | ~1,6 h simulada |
| `completo` (padrao + visão a 100 Hz) | ~+5–6 s/s → 10–15 s/s | 10–15 min | ~30–45 min simulados |

**Consequência:** nesta máquina, nem o perfil `debug` roda em tempo real, porque a física
do NeuroMechFly sozinha já custa 2,3–2,8 s/s. O "ao vivo" possível é em câmera lenta (~1/3
da velocidade real). Ver o relatório da Fase 0 para as alternativas.

## 8. Paralelismo

- Dentro do cérebro: sem ganho com 2 threads (medido).
- Entre componentes: o cérebro é só 12 % do tempo total, então separá-lo num processo daria
  no máximo ~12 % de ganho. A física domina e é um único `mj_step`. Separar as minhocas num
  MjModel/processo próprio perderia o contato físico mosca–minhoca (a SPEC pede interação física).
- **Conclusão: um processo só**, por enquanto. Reavaliar na Fase 5 com o cenário real.

## 9. Fase 2: mosca no terrário (2026-09-23)

Perfil Desempenho, na tomada, máquina ociosa, 1 processo (`experiments/phase2_demo.py`,
`results/phase2/bench_raw.txt`).

| Configuração | s/s |
|---|---|
| Chão plano (referência; Fase 0: 2,31) | 2,25 |
| Terrário, só física, Jacobiano denso / esparso | 3,07 / 2,87 |
| Terrário + sensores (1 kHz) + campos + gravação (200 Hz) | **3,38** (sensores e campos: 0,15) |
| Idem + visão a 100 Hz | 7,29 |

O relevo e os sólidos acrescentam 798 pares de contato (+36 % na física). Log: 235 kB por segundo
simulado (zstd), ou seja, 5 GB em ~5,9 h simuladas.

## 10. D-105: conectomas candidatos (2026-09-23)

Um processo, açúcar a 200 Hz, 1 s em chamadas de 1 ms, mediana de 3 trials
(`experiments/connectome_eval.py bench`, `results/d105/bench.jsonl`).

| Conectoma | Neurônios | Arestas | s/s | RAM de pico | Processos pela RAM |
|---|---|---|---|---|---|
| FlyWire 783 | 138.639 | 15,1 M | 0,68 | 0,66 GB | 19 |
| BANC v888 (v2) | 155.858 | 11,4 M | 0,05 (sinal não se propaga) | 0,56 GB | 22 |
| BANC v888, `w_syn` × 1,9 | idem | idem | 11,6 (atividade autossustentada) | ~0,6 GB | 22 |
| FlyWire 783 + VNC do BANC | 162.197 | 17,7 M | 0,89 | 0,73 GB | 17 |

Na prática, o limite é a CPU (10 processos, como na Fase 1). Fig. 1D completa (600 trials, 10
processos): v783 3,8 min (Fase 1); híbrido 8,7 min, mas dividindo a CPU com os testes da Fase 2.
Análise em `docs/D105_CONECTOMA.md`.

## Custo do LIF no regime de atividade alta (Fase 3b, 2026-09-24)

O custo do cérebro depende da atividade (conjunto ativo). Com odor nos ORNs de DM1+VA2, o conectoma real
entra num regime alto (~6 % dos neurônios ativos, ~4,7×10⁵ spikes em 1 s) **qualquer que seja a taxa dos
ORNs entre 20 e 100 Hz**. Nesse regime, **o custo da fila dobra**: a Etapa B (380 execuções de 1 s, 10
processos, perfil Desempenho) levou ~30 min, contra os ~15 min estimados pela fila anterior. As taxas
baixas não custaram menos, porque a rede entra no mesmo regime. Os embaralhados (0,1–0,3 % ativos) são
baratos. Para estimar uma fila, conte as execuções do conectoma real com odor como as caras
(~14 s de parede por execução com 10 processos).
