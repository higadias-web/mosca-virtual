# Terrário Virtual

Simulação de terrário com animais dirigidos só pelo conectoma: sensores → neurônios → músculos.
A especificação completa, com regras de trabalho, fases e critérios, está em `docs/SPEC.md`. Leia antes de mudar qualquer coisa.

## Fase atual
**Fase 2 aprovada** (2026-09-23). Decididas: **D-105 = (c)** FlyWire 783 no cérebro + cordão do
BANC; **D-106**: Fase 3 em 3a (bolinha, marcha pelo cordão) e 3b (terrário). Prazo da 3a: 6 sessões
ou 2 semanas (o que vier primeiro); marco na 3ª sessão (sem ritmo nos MNs de perna com loop
proprioceptivo fechado → encerrar 3a, documentar, 3b com o controlador (a)).
**Plano aprovado; Fase 3a em andamento: Sessões 1 e 2 concluídas (2026-09-23).** S1: sem ritmo em
malha aberta. S2: aferência imposta sem ritmo (nem reflexo); loop fechado INCONCLUSIVO (acionamento
quase nulo + aparato sem limites/rigidez nas juntas); inibição recíproca funcional confirmada.
Sessão 3 só depois de aprovar a proposta de `docs/FASE3_PLANO.md` §7.3. Registro de sessões e resultados em `docs/FASE3_PLANO.md` §6–7. Prazo: 2026-10-07
ou 6 sessões. A entrega paralela "P" (probóscide) ainda não começou.
Ao fim de cada fase ou entrega: vídeo WebM de 10–20 s em results/. A cada sessão: figuras em results/phase3a/.
Fase 1 aprovada em 2026-09-23; Fase 0 em 2026-09-22 (D-003, D-006, D-008, D-101, D-102, D-104).
Nenhuma fase começa sem aprovação explícita do usuário, e nenhuma ⚠️ DECISÃO é tomada sem ele.

## Estrutura
```
docs/SPEC.md             especificação (do usuário)
docs/FASE0_RELATORIO.md  relatório da Fase 0: premissas corrigidas, ⚠️ decisões com opções
docs/FASE1_RELATORIO.md  relatório da Fase 1: reprodução do Shiu et al. 2024
docs/FASE2_RELATORIO.md  relatório da Fase 2: arena, sensores, custo
docs/D105_CONECTOMA.md   ⚠️ D-105/D-106: FlyWire × BANC × híbrido, com benchmark e revalidação
docs/BENCHMARK.md        medições desta máquina e dimensionamento de episódios
docs/DECISIONS.md        decisões técnicas (D-0xx técnicas, D-1xx pendentes)
docs/NON_CONNECTOME.md   tudo que é engenharia, e não conectoma
docs/SETUP_FEDORA.md     pacotes dnf, EGL, perfis de energia
setup.sh                 recria o ambiente do zero (idempotente, sem sudo)
pyproject.toml, uv.lock  dependências fixadas (Python 3.13 via uv)
terrario/brain/flywire.py  conectoma FlyWire v630/v783 (formato do Shiu), cache CSR em data/cache
terrario/brain/lif.py    motor LIF de produção (ShiuLIF): conjunto ativo exato, Poisson, silêncio, checkpoint
terrario/brain/banc.py   BANC v888 (cérebro + VNC) no formato do Shiu; cache em data/cache
terrario/brain/hybrid.py FlyWire 783 + VNC do BANC (pontes DN/AN pareadas por tipo e lado)
terrario/brain/connectomes.py  load("783" | "banc888" | "banc888v3" | "fw783+bancvnc")
terrario/world/          arena do terrário (FlyGym 2.1 BaseWorld) e campos (odor 2D, temperatura, luz)
terrario/body/           cena (build_scene), sensores da mosca (1 kHz), gravação Parquet (200 Hz)
terrario/vnc/            Fase 3a: motor_map (MN → músculo → junta), apparatus (bola, torque), proprio, rhythm
terrario/video.py        vídeos curtos das cenas (results/)
configs/arena.yaml       disposição da arena (mm)
tests/                   pytest (inclui comparação determinística spike a spike com o Brian2)
experiments/             Fase 1: shiu_repro.py, compare_shiu.py, fila noturna; Fase 2: phase2_demo.py;
                         D-105: connectome_eval.py (bench/fig1d/probe), compare_d105.py
tools/remote_zip.py      extrai arquivos de um zip remoto por HTTP Range
results/phase1/          comparações (*_compare.json) e log da fila, versionados
results/phase2/, results/d105/  resumos, imagem da arena, benchmarks e comparações (versionados)
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
uv run python -m experiments.phase2_demo --sim-s 2.5 --render          # travessia no terrário
uv run python -m experiments.connectome_eval fig1d --version fw783+bancvnc --workers 10
uv run python -m experiments.compare_d105
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
- **Vídeos: sempre WebM (VP9)** (`terrario/video.py:write_webm`); nada de MP4/H.264, que o Fedora
  não toca sem codecs extras. Ao fim de cada fase ou entrega: vídeo de 10–20 s em results/.
- Métrica de ritmo da 3a (`terrario/vnc/rhythm.py`, v2) **congelada**: mudar só com aprovação do usuário.
- Unidades físicas: mm, s (padrão do FlyGym; gravidade −9810 mm/s²). Modelo neural: ms, mV.

## Pendências
- Fase 3a, Sessão 3 (aguarda aprovação de §7.3): validar o aparato (limites e rigidez das juntas com fonte) antes de qualquer fila; regra pré-definida para ativação perto de 0.
- Filas: rodar com `systemd-inhibit`, gravar `FILA_OK` com a contagem, analisar só com a fila completa, execução separada da análise.
- Entrega P (paralela, fora do prazo): juntas da probóscide, extensão com açúcar, supressão com amargo, ablação do MN9, vídeo.
- Fase 3: obter os IDs sensoriais nas anotações da v783 (não herdar a lista v630 do artigo; 1 dos 21 GRNs de açúcar não existe na v783).
- Fase 3: dar juntas e atuadores à probóscide (o corpo de locomoção padrão não tem); MN9 → probóscide.
- Fase 3a (se aprovada): bola simulada (o FlyGym 2.1 não tem), mapeamento MN → músculo → torque
  (o BANC anota o músculo-alvo de cada MN de perna), transdução proprioceptiva.
- D-103 (larva) fica para a Fase 8.

## Riscos conhecidos
- **BANC não reproduz a Fig. 1D** (GRNs de açúcar com 15× menos sinapses de saída que no FlyWire);
  compensar `w_syn` globalmente deixa a rede autossustentada. Ver D-105.
- **Marcha pelo VNC não é garantida**: com os parâmetros do Shiu, DNs de marcha quase não ativam
  MNs de perna (BANC e híbrido). É a pergunta da Fase 3a.
- **Híbrido costura dois animais**: 87 % dos DNs e 58 % dos ANs pareados; o BANC tem ~0,5× as
  sinapses do FlyWire por par de neurônios.
- **Física com múltiplos animais num MjModel**: custo superlinear com o Jacobiano esparso
  automático do MuJoCo; usar `mjJAC_DENSE` (medido). Minhoca com contatos por cápsula é cara (~1,2 s/s);
  a variante planar com arrasto (RFT) custa ~0,23 s/s, mas é numericamente rígida (regime sobreamortecido).
- **Custo do cérebro depende da atividade**: o conjunto ativo pode crescer com muitos sentidos ligados.
- **FlyGym 2.x não tem olfato**: a amostragem de odor nas antenas é nossa (NON-CONNECTOME).
- **Neurônios de C. elegans são majoritariamente graduados** (não disparam): o LIF não é adequado (D-102).
- **Neurônios exclusivos do macho não têm posição 3D** nos dados do OpenWorm (D-104).
- **VNC larval**: cobertura publicada ainda a confirmar na Fase 8.
- Visão da mosca é cara (8–22 s/s adicionais; +4,2 s/s a 100 Hz no terrário); desligada por padrão.
- Terrário: 798 pares de contato com o relevo (+36 % na física da mosca, 3,4 s/s com sensores).
- O NeuroMechFly não voa: a mosca chega à fruta andando (registrado na SPEC).
