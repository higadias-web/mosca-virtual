# Decisões técnicas

Formato: **D-NNN — título** · status · data. "Aprovada" só depois de confirmação do usuário;
"Técnica" = decisão delegada pela SPEC ao benchmark ou à verificação; "⚠️ Pendente" = aguarda escolha.

---

## D-001 — Python 3.13, gerenciado pelo `uv` · Técnica · 2026-09-22
- FlyGym 2.1.0 exige `>=3.12,<3.15` (`third_party/flygym/pyproject.toml`); o CI testa 3.12, 3.13
  e 3.14, e o `.python-version` do repositório é 3.14.
- Brian2 2.10.1, MuJoCo 3.9, numba 0.67 e torch 2.14 têm wheels cp313.
- A escolha foi 3.13, e não 3.14: está no meio da matriz de CI do FlyGym e dá mais margem a
  dependências menos mantidas do lado das minhocas (c302/pyNeuroML/owmeta). O Python do sistema
  (3.14.7) não é usado.
- Lockfile: `uv.lock`. Torch vem do índice CPU (`download.pytorch.org/whl/cpu`).

## D-002 — FlyGym 2.1.0 (API nova), e não 1.x · Técnica · 2026-09-22
- Em março/abril de 2026 o FlyGym foi reescrito (2.0.0) sem compatibilidade. A 1.x virou
  `flygym-gymnasium` (Python `<3.13`, MuJoCo 3.2.7 fixo).
- Prós da 2.1: ~10× mais rápido em CPU (dito pelos autores; medido em `docs/BENCHMARK.md`),
  MjSpec nativo (fácil adicionar minhocas, fruta etc. ao mesmo `MjModel`), múltiplas moscas por
  `World`, visão (`Simulation.get_ommatidia_readouts`), sites e forças de contato por segmento,
  timestep padrão de 0,1 ms (`assets/model/neuromechfly/mujoco_globals.yaml`).
- Contra: **a 2.x não tem módulo de olfato** (a `OdorArena` era da 1.x, e continua em
  `flygym_gymnasium/arena/sensory_environment.py`). Como a SPEC já pede um campo de odor
  próprio, a amostragem nas antenas e palpos passa a ser nossa (posição dos sites via
  `Simulation.get_site_positions`). Será NON-CONNECTOME (transdução), como já seria.

## D-003 — FlyWire v783 no terrário; v630 para reproduzir o artigo · Aprovada · 2026-09-22
- O artigo de Shiu et al. (Nature 634:210, 2024) usou a **v630**. O repositório original traz
  a v630 e a v783 (`Completeness_783.csv`, `Connectivity_783.parquet`), e o README só explica
  como trocar.
- A v783 tem 138.639 neurônios e 15.091.983 pares pré→pós (sem duplicatas).
  Dos 21 GRNs de açúcar do exemplo, 20 existem com o mesmo ID na v783; o MN9 também existe.
- As anotações (`flyconnectome/flywire_annotations`, Supplemental_file1) são da v783 e cobrem
  99,99 % dos neurônios do modelo, com `soma_x/y/z` (ou `pos_x/y/z`), classe e tipo celular.
  Ou seja, **existem posições 3D utilizáveis** para o painel.
- Proposta para a Fase 1: comparar com os números do artigo **na v630**, que é o que foi
  publicado, e depois mostrar que as mesmas respostas aparecem na v783.
- Resultado (Fase 1): reproduzido na v630. Na v783 a resposta alimentar se mantém (mesmo limiar
  e saturação do MN9, 3–9 Hz abaixo, com 20 em vez de 21 GRNs estimulados).

## D-004 — Motor LIF próprio em numba (conjunto ativo), e não Brian2 · Técnica · 2026-09-22
- Resultado completo em `docs/BENCHMARK.md`. Resumo (cérebro inteiro, 1 s simulado, estímulo de açúcar):
  Brian2 runtime 3,4 s; Brian2 `cpp_standalone` 2,7 s (2 threads OpenMP: 3,4 s, pior);
  numba denso 2,0–2,4 s; **numba com conjunto ativo 0,6–0,7 s**.
- O conjunto ativo é **exato** (idêntico bit a bit ao denso), porque o modelo de Shiu não
  tem corrente de fundo e v_rst = v_0: um neurônio com v = v_0 e g = 0 fica exatamente assim
  até receber entrada. Integrar só os neurônios fora do repouso não muda nenhum bit.
- Reprodução contra o Brian2 original (30 trials × 1 s): r = 0,9997 nas taxas por neurônio,
  total de spikes −0,5 %, 0 de 373 neurônios com diferença > 3 erros-padrão de Poisson,
  MN9 78,4 contra 79,7 Hz.
- Achado de semântica (documentado em `bench/lif_engines.py`): no Brian2, `(unless refractory)`
  torna condicional **toda** escrita em `v` e `g`, inclusive `on_pre` sináptico e `PoissonInput`
  (`brian2/groups/neurongroup.py`, `set_conditional_write`). Entradas que chegam durante o
  refratário são **descartadas**. Sem isso, a implementação gera +21 % de spikes.
- O `cpp_standalone` também não serve para loop fechado: compila e roda a simulação inteira
  num binário, sem devolver o controle ao Python a cada passo de sincronização.
- Riscos: o custo do conjunto ativo cresce com a atividade (muitos sentidos ligados ao mesmo
  tempo). Isso será remedido na Fase 3 com o acoplamento sensorial real.
- Fase 1: promovido a `terrario/brain/lif.py` (`ShiuLIF`), idêntico spike a spike ao Brian2
  (teste determinístico) e com as Figs. 1D/1E/1F/3A do artigo reproduzidas
  (`docs/FASE1_RELATORIO.md`).

## D-005 — Renderização headless: EGL · Técnica · 2026-09-22
- `MUJOCO_GL=egl` funciona na Intel UHD (Mesa 26). OSMesa só via `mesa-compat-libOSMesa`
  25.0.7 (o Mesa removeu o OSMesa na 25.1). Também funciona, mas fica como alternativa.

## D-006 — Passos de tempo · Aprovada · 2026-09-22
- Física (MuJoCo): 0,1 ms, o padrão do NeuroMechFly, necessário para contatos e adesão estáveis.
- Cérebro da mosca: 0,1 ms, o dt do modelo de Shiu (padrão do Brian2). Mudar o dt muda a dinâmica.
- **Sincronização cérebro ↔ corpo: a cada 1 ms.** O atraso sináptico do modelo é 1,8 ms, então
  a troca de 1 ms fica abaixo da menor latência da rede. Sincronizar a cada 0,1 ms custaria
  10× mais chamadas Python↔numba sem ganho biológico. (A Eon Systems usou 15 ms.)
- Campo de odor e ambiente vivo: 10 ms (difusão lenta em escala de mm).
- Minhocas: a definir na Fase 4 (o proxy sugere que 0,1 ms é caro; ver BENCHMARK).

## D-007 — Repositórios de referência fixados por commit · Técnica · 2026-09-22
`setup.sh` clona em `third_party/` (fora do git):

| Repositório | Commit | Uso |
|---|---|---|
| philshiu/Drosophila_brain_model | 91bdd1e | modelo LIF e conectomas v630/v783 |
| NeLy-EPFL/flygym | 38c8ec6 (v2.1.0) | leitura do código (o pacote vem do PyPI, 2.1.0) |
| NeLy-EPFL/flygym-gymnasium | d285260 | referência do olfato da 1.x |
| flyconnectome/flywire_annotations | 8587524 | anotações v783 e posições de soma |
| openworm/c302 | 6cd861f | referência para C. elegans |
| openworm/ConnectomeToolbox (cect) | b9c0b4a | leitores do Cook 2019 (herm/macho); pacote `cect==0.3.4` |
| mwinding/connectome_tools | bfdc691 | ferramentas do conectoma larval |
| htem/BANC-project | e31a2e2 | documentação e tabelas de captura do BANC (D-105); opcional (`BANC_REPO=0`) |

Dados do BANC (não são repositório): Harvard Dataverse doi:10.7910/DVN/7WTH1N, versão 3
(2026-07-01), materialização v888; `setup.sh` baixa os 6 arquivos usados para `data/banc/`.

---

## D-008 — Perfil de energia Desempenho nas execuções longas · Aprovada · 2026-09-22
15–20 % mais rápido que o Equilibrado, sem throttling em 12 min (84 °C de pico). Ver BENCHMARK §5.

## D-009 — Arena e sensores da Fase 2 · Técnica (Fase 2 aprovada em 2026-09-23) · 2026-09-23
- Arena em `configs/arena.yaml` (80 × 60 mm), montada com a API de mundos do FlyGym 2.1
  (`BaseWorld` + `_GroundContactMixin`, como `complex_terrain.py`): cada sólido é um geom de chão
  com pares de contato próprios. A superfície tocada vem do geom e, no piso, da posição.
- Contato também na probóscide (`c_rostrum`, `c_haustellum`), que o preset do FlyGym não inclui:
  o labelo precisa tocar o alimento.
- Sensores lidos a cada 1 ms (D-006) e gravados a 200 Hz (SPEC: 100–200 Hz), em Parquet zstd.
- Odor: grade 2D de 0,5 mm, D = 10 mm²/s, k = 0,05 /s, passo de 10 ms com 2 subpassos
  (estabilidade), início em regime estacionário (solução esparsa). Custo < 0,1 s/s.
- Jacobiano denso por padrão (7 % mais lento que o esparso com uma mosca só; mais rápido com vários
  animais, BENCHMARK §3–4). Rever na Fase 5.
- Resultados: `docs/FASE2_RELATORIO.md`.
- Na aprovação: a mosca chega à fruta **andando** (o NeuroMechFly não voa); registrado na SPEC.

## D-101 — Mosca adulta, VNC: híbrido, começando por DNs → controlador FlyGym · Aprovada · 2026-09-22
(Complementada pelas D-105 e D-106, aprovadas em 2026-09-23: cordão do BANC na 3a; (a) continua como saída.)
Opção (c) do relatório da Fase 0. A Fase 3 começa por (a): taxas de DNs anotados no FlyWire →
sinal descendente do `HybridTurningController` do FlyGym (NON-CONNECTOME), e MN9 → probóscide.
Os nomes dos DNs serão confirmados nas anotações antes do uso. BANC/Male CNS ficam como
experimento separado, para (b).

## D-102 — C. elegans: Cook 2019 via `cect`, modelo graduado próprio, corpo planar RFT · Aprovada · 2026-09-22
Hermafrodita (302 neurônios) e macho (380), 95 músculos da parede do corpo e JNMs pelo
`cect.readers.Cook2019{Herm,Male}Reader`. O modelo neuronal graduado (dinâmica tipo c302 /
Wicks 1996 / Kunert 2014, parâmetros a confirmar na Fase 4) é NON-CONNECTOME. Corpo: cadeia
planar com arrasto anisotrópico (RFT); a rigidez numérica é tratada na Fase 4.

## D-103 — Larva: registrada, decisão na Fase 8 · Adiada · 2026-09-22

## D-104 — Posições dos 89 neurônios exclusivos do macho · Aprovada · 2026-09-22
Primeiro buscar coordenadas publicadas; se não houver, posicionar no gânglio anatômico
correto e marcar como aproximação (NON-CONNECTOME).

## D-105 — Conectoma da mosca adulta: FlyWire 783, BANC ou híbrido · Aprovada: opção (c) · 2026-09-23
Relatório completo: `docs/D105_CONECTOMA.md`. Opções: (a) FlyWire 783 + controlador; (b) BANC v888
inteiro (cérebro + cordão da mesma mosca); (c) FlyWire 783 no cérebro + cordão do BANC por pareamento
de DNs/ANs.
- Revalidação (Fig. 1D, 30 trials): **(b) falha**. O MN9 fica em 0 Hz em todas as variantes
  (edgelist v2 e v3, dois conjuntos de GRNs, `w_syn` × 1,9 e × 1,3). Os GRNs de açúcar do labelo
  no BANC têm mediana de 21 sinapses de saída, contra 325 no FlyWire. Com peso compensado, a rede
  entra em atividade autossustentada antes de o MN9 responder. **(c) reproduz a v783** (MN9 dentro
  de ±1 Hz; r = 0,98 por tipo).
- Custo por trial de 1 s (1 processo): (a) 0,68 s; (c) 0,89 s; (b) 0,05 s sem propagação, 11,6 s
  compensado. RAM por processo 0,56–0,73 GB, então 17–22 cabem na RAM; na prática, 10 (CPU).
- Cobertura: pós-sináptica ~0,2 no BANC contra ~0,38 no FlyWire (GNG); o VNC do BANC tem captura
  pré-sináptica de 0,83–0,84, como o MANC. Lâmina: o BANC não tem R1–R6 nem Lai; o FlyWire tem.
- Sonda: com os parâmetros do Shiu, DNs de marcha a 200 Hz quase não ativam MNs de perna, em (b)
  e em (c). A marcha pelo VNC é uma pergunta de pesquisa em aberto.
- **Escolha do usuário: (c)**, FlyWire 783 no cérebro + cordão do BANC (`terrario/brain/hybrid.py`), com (a) como saída.
- Técnico, qualquer que seja a escolha: edgelist v2 (padrão do BANC-project); sinal com histamina
  → −1 (NON-CONNECTOME); pareamento de pontes por (tipo FAFB, lado), porque `fafb_match` aponta
  para um representante e em ~40 % dos casos está do lado oposto.

## D-106 — Dividir a Fase 3 em 3a (bolinha) e 3b (terrário) · Aprovada · 2026-09-23
Só faz sentido com (b) ou (c). **3a**: mosca presa (`TetheredWorld` + bola simulada, nossa)
e marcha gerada pelo VNC do BANC: MNs de perna → músculos-alvo anotados → torques; propriocepção
pelos neurônios sensoriais do VNC; estímulo em DNp09/DNa02. Critérios de ritmo, coordenação,
direção e ablação, com prazo; se não passar, **3b usa o controlador de (a)**. **3b**: mosca livre
no terrário, com sensores da Fase 2 → neurônios sensoriais da v783. Detalhes em
`docs/D105_CONECTOMA.md` §9.
- **Prazo da 3a** (definido pelo usuário): 6 sessões de trabalho ou 2 semanas, o que vier primeiro.
- **Marco na 3ª sessão**: se nenhum estímulo de DN gerar atividade rítmica nos MNs de perna com o
  loop proprioceptivo fechado, a 3a é encerrada, o resultado negativo é documentado e a 3b segue
  com o controlador da opção (a).
- Plano, hipóteses e juntas da probóscide: `docs/FASE3_PLANO.md` (aguarda aprovação).

As opções completas da Fase 0 estão em `docs/FASE0_RELATORIO.md` §3.
