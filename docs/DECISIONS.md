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

---

## D-008 — Perfil de energia Desempenho nas execuções longas · Aprovada · 2026-09-22
15–20 % mais rápido que o Equilibrado, sem throttling em 12 min (84 °C de pico). Ver BENCHMARK §5.

## D-101 — Mosca adulta, VNC: híbrido, começando por DNs → controlador FlyGym · Aprovada · 2026-09-22
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

As opções completas estão em `docs/FASE0_RELATORIO.md` §3.
