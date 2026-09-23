# Terrário Virtual

Simulação de terrário com animais dirigidos só pelo conectoma: sensores → neurônios → músculos.
A especificação completa, com regras de trabalho, fases e critérios, está em `docs/SPEC.md`. Leia antes de mudar qualquer coisa.

## Fase atual
**Fase 1 em andamento** (reproduzir um resultado do Shiu et al. 2024, isolado). A Fase 0 foi
aprovada em 2026-09-22, com todas as recomendações (D-003, D-006, D-008, D-101, D-102, D-104).
Nenhuma fase começa sem aprovação explícita do usuário, e nenhuma ⚠️ DECISÃO é tomada sem ele.

## Estrutura
```
docs/SPEC.md             especificação (do usuário)
docs/FASE0_RELATORIO.md  relatório da Fase 0: premissas corrigidas, ⚠️ decisões com opções
docs/BENCHMARK.md        medições desta máquina e dimensionamento de episódios
docs/DECISIONS.md        decisões técnicas (D-0xx técnicas, D-1xx pendentes)
docs/NON_CONNECTOME.md   tudo que é engenharia, e não conectoma
docs/SETUP_FEDORA.md     pacotes dnf, EGL, perfis de energia
setup.sh                 recria o ambiente do zero (idempotente, sem sudo)
pyproject.toml, uv.lock  dependências fixadas (Python 3.13 via uv)
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
uv run python bench/bench_brain.py --engine numba-active --sim-ms 1000
systemd-inhibit --what=idle:sleep uv run python bench/run_all.py --profiles balanced performance
```
- Rodar sempre **na tomada** (na bateria o turbo fica desligado e a CPU trava em 1 GHz).
- Nunca `sudo pip`; `sudo` só com confirmação do usuário.

## Convenções
- Comentários e documentação em português.
- Tudo que não vem do conectoma leva `# NON-CONNECTOME:` no código e uma entrada em `docs/NON_CONNECTOME.md`.
- Não inventar API, ID de neurônio ou parâmetro: ler o código e os dados reais em `third_party/`
  e citar a origem (arquivo/função) em comentário.
- Unidades físicas: mm, s (padrão do FlyGym; gravidade −9810 mm/s²). Modelo neural: ms, mV.

## Pendências
- Fase 1: reproduzir o Shiu na v630 (números do artigo) e depois na v783.
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
