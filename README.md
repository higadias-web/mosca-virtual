# Terrário Virtual: versão enxuta para leitura

Projeto de simulação de *Drosophila* dirigida pelo conectoma (FlyWire 783 + LIF de Shiu et al. 2024; cordão
nervoso do BANC; corpo NeuroMechFly/FlyGym). Esta é a **versão enxuta**: só os arquivos que o próprio projeto
versiona, com o **histórico original de commits** preservado. Os commits de pré-registro vêm antes dos resultados,
e as datas provam isso.

## Por onde começar

| Arquivo | O que é |
|---|---|
| `CLAUDE.md` | Estado atual do projeto, fase atual, pendências e riscos |
| `docs/SPEC.md` | Especificação original (objetivo antigo: terrário com 4 animais) |
| `docs/FASE0_RELATORIO.md` … `docs/FASE3B_ETAPA_E_RELATORIO.md` | Relatórios de cada fase, em ordem |
| `docs/FASE3_PLANO.md`, `docs/FASE3B_PLANO.md` | Planos com os pré-registros e o registro das sessões |
| `docs/DECISIONS.md`, `docs/NON_CONNECTOME.md`, `docs/BENCHMARK.md`, `docs/D105_CONECTOMA.md` | Decisões, o que não vem do conectoma, custos, escolha do conectoma |
| `auditoria/PROMPT_PARA_A_CONVERSA.md` | **Auditoria externa (Fase 0 → 3b), revisão de literatura e proposta do novo objetivo (C)** |
| `auditoria/README.md` | Números dos três testes da auditoria |

## Estrutura do código

`terrario/` (motor LIF, conectomas, corpo, cordão), `experiments/` (scripts de cada fase), `tests/`, `configs/`,
`bench/` (benchmarks da Fase 0), `results/` (resumos, figuras e vídeos versionados).

## O que NÃO está aqui (grande demais, ou recriável)

`.venv/`, `third_party/` (repositórios de referência fixados por commit, recriados pelo `setup.sh`), `data/`
(conectomas e caches, baixados pelo `setup.sh`), `runs/` (saídas brutas das simulações) e `bench/results/raw/`.
Para **rodar** algo é preciso o projeto completo na máquina do Marcelo; para **ler e auditar**, esta versão basta.
