# Terrário Virtual

Simulação de terrário com animais dirigidos só pelo conectoma: sensores → neurônios → músculos.
A especificação completa, com regras de trabalho, fases e critérios, está em `docs/SPEC.md`. Leia antes de mudar qualquer coisa.

## Fase atual
**Fase 1 concluída, aguardando aprovação** (2026-09-23). O Shiu et al. 2024 foi reproduzido
(Figs. 1D/1E/1F/3A na v630, confirmado na v783): ver `docs/FASE1_RELATORIO.md`.
**Não iniciar a Fase 2 sem aprovação.** A Fase 0 foi aprovada em 2026-09-22 (D-003, D-006, D-008, D-101, D-102, D-104).
Nenhuma fase começa sem aprovação explícita do usuário, e nenhuma ⚠️ DECISÃO é tomada sem ele.

## Estrutura
```
docs/SPEC.md             especificação (do usuário)
docs/FASE0_RELATORIO.md  relatório da Fase 0: premissas corrigidas, ⚠️ decisões com opções
docs/FASE1_RELATORIO.md  relatório da Fase 1: reprodução do Shiu et al. 2024
docs/BENCHMARK.md        medições desta máquina e dimensionamento de episódios
docs/DECISIONS.md        decisões técnicas (D-0xx técnicas, D-1xx pendentes)
docs/NON_CONNECTOME.md   tudo que é engenharia, e não conectoma
docs/SETUP_FEDORA.md     pacotes dnf, EGL, perfis de energia
setup.sh                 recria o ambiente do zero (idempotente, sem sudo)
pyproject.toml, uv.lock  dependências fixadas (Python 3.13 via uv)
terrario/brain/flywire.py  conectoma FlyWire v630/v783 (formato do Shiu), cache CSR em data/cache
terrario/brain/lif.py    motor LIF de produção (ShiuLIF): conjunto ativo exato, Poisson, silêncio, checkpoint
tests/                   pytest (inclui comparação determinística spike a spike com o Brian2)
experiments/             Fase 1: shiu_repro.py (experimentos), compare_shiu.py, fila noturna
tools/remote_zip.py      extrai arquivos de um zip remoto por HTTP Range
results/phase1/          comparações (*_compare.json) e log da fila, versionados
runs/                    saídas brutas das simulações (fora do git)
data/                    caches e dados baixados (fora do git)
bench/                   benchmarks da Fase 0 (protótipos, não são o motor final)
  lif_engines.py         motores LIF (numba denso/ativo, numpy, torch) que replicam o Shiu/Brian2
  bench_brain.py         cérebro da mosca isolado (inclui Brian2 original como referência)
  bench_flygym.py        corpo da mosca (FlyGym 2.1), com e sem visão
  bench_worm.py          PROXY de custo de minhoca (cadeia de cápsulas)
  bench_full.py          PROXY do cenário completo num processo
  run_all.py             bateria por perfil de energia, throttling e swap
  compare_rates.py       comparação estatística das taxas entre motores
  results/*.jsonl        resultados brutos (raw/ fica fora do git)
third_party/             repositórios de referência (fora do git; commits em DECISIONS D-007)
```

## Como rodar
```bash
./setup.sh                                   # uma vez (pacotes dnf: docs/SETUP_FEDORA.md)
export MUJOCO_GL=egl PYOPENGL_PLATFORM=egl
uv run pytest                                # testes
uv run python -m experiments.shiu_repro fig1d --version 630 --workers 10   # executar como módulo, da raiz
uv run python -m experiments.compare_shiu fig1d
uv run python bench/bench_brain.py --engine numba-active --sim-ms 1000
systemd-inhibit --what=idle:sleep uv run python bench/run_all.py --profiles balanced performance
```
- Rodar sempre **na tomada** (na bateria o turbo fica desligado e a CPU trava em 1 GHz).
- Nunca `sudo pip`; `sudo` só com confirmação do usuário.
- Execuções longas: `systemd-inhibit --what=idle:sleep:handle-lid-switch`, perfil Desempenho (D-008),
  e checkpoint por partes (um arquivo por lote).
- **Esperar uma fila em segundo plano: NÃO usar `pgrep -f "<nome do script>"`.** A linha de comando
  da própria espera contém o mesmo texto, então o `pgrep` sempre a encontra e a espera nunca termina
  (aconteceu na Fase 1). Use o PID (`while kill -0 $PID`), um arquivo-sentinela/linha final do log,
  ou um padrão que não case consigo mesmo (`pgrep -f "[o]vernight_phase1.sh"`).

## Convenções
- Comentários e documentação em português.
- Tudo que não vem do conectoma leva `# NON-CONNECTOME:` no código e uma entrada em `docs/NON_CONNECTOME.md`.
- Não inventar API, ID de neurônio ou parâmetro: ler o código e os dados reais em `third_party/`
  e citar a origem (arquivo/função) em comentário.
- Unidades físicas: mm, s (padrão do FlyGym; gravidade −9810 mm/s²). Modelo neural: ms, mV.

## Pendências
- Aprovação da Fase 1; em seguida, Fase 2 (FlyGym na arena do terrário, com os sensores gerando dados).
- Fase 3: obter os IDs sensoriais nas anotações da v783 (não herdar a lista v630 do artigo; 1 dos 21 GRNs de açúcar não existe na v783).
- D-103 (larva) fica para a Fase 8.

## Riscos conhecidos
- **Física com múltiplos animais num MjModel**: custo superlinear com o Jacobiano esparso
  automático do MuJoCo; usar `mjJAC_DENSE` (medido). Minhoca com contatos por cápsula é cara (~1,2 s/s);
  a variante planar com arrasto (RFT) custa ~0,23 s/s, mas é numericamente rígida (regime sobreamortecido).
- **Custo do cérebro depende da atividade**: o conjunto ativo pode crescer com muitos sentidos ligados.
- **FlyGym 2.x não tem olfato**: a amostragem de odor nas antenas é nossa (NON-CONNECTOME).
- **Neurônios de C. elegans são majoritariamente graduados** (não disparam): o LIF não é adequado (D-102).
- **Neurônios exclusivos do macho não têm posição 3D** nos dados do OpenWorm (D-104).
- **VNC larval**: cobertura publicada ainda a confirmar na Fase 8.
- Visão da mosca é cara (8–22 s/s adicionais); desligada por padrão.
