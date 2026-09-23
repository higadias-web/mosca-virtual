# O que NÃO vem do conectoma

Tudo que é engenharia, e não biologia, aparece aqui e no código com `# NON-CONNECTOME:`.
Fase atual: 0. Ainda não há código de simulação. As entradas marcadas como *planejado*
são previsões a confirmar nas fases seguintes.

## Já existente (Fase 0: só benchmark, nada entra no modelo)

| Item | Onde | Observação |
|---|---|---|
| Onda senoidal de acionamento do proxy de minhoca | `bench/bench_worm.py`, `bench/bench_full.py` | só gera carga de contato para medir custo; não será usada |
| Rede densa aleatória de 400 unidades (proxy de minhoca) | idem | só carga de CPU |
| CPG de caminhada do FlyGym (`flygym_demo.complex_terrain.CPGController`) | `bench/bench_flygym.py`, `bench/bench_full.py` | só carga de contato; a ligação DN → corpo é ⚠️ DECISÃO |

## Planejado (a confirmar por fase)

| Item | Animal | Fase | Por que não vem do conectoma |
|---|---|---|---|
| Parâmetros LIF (v_0, v_th, τ, w_syn etc.) | mosca | 1 | vêm de Shiu et al. 2024 (literatura + parâmetro livre `w_syn`), não do EM |
| Sinal das sinapses por neurotransmissor previsto | mosca | 1 | predição por ML (Eckstein et al. 2024) usada por Shiu, não observação direta |
| Codificação estímulo → taxa de Poisson nos neurônios sensoriais | todos | 1–5 | a transdução sensorial não está no conectoma |
| Interface DN → comando motor (depende da ⚠️ DECISÃO do VNC) | mosca | 3 | o FlyWire não inclui o VNC |
| Poda de rede do perfil `debug` | mosca | 7 | altera a dinâmica; só para infraestrutura |
| Modelo de neurônio graduado (não LIF) para C. elegans | minhocas | 4 | escolha de modelo; parâmetros da literatura (c302/Kunert et al.) |
| Corpo segmentado MuJoCo, mapeamento célula muscular → atuador, fricção anisotrópica / RFT | minhocas | 4 | biomecânica simplificada |
| Plano B: acoplamento proprioceptivo mínimo | minhocas | 4 | só se a ondulação não emergir |
| Posições 3D dos neurônios exclusivos do macho | minhoca macho | 6 | sem coordenadas publicadas no NeuroML do OpenWorm (ver DECISIONS) |
| Campo de odor (difusão), gradiente térmico, ciclo dia/noite | ambiente | 5 | física do ambiente |
| Crescimento logístico de fermento/bactérias e taxa de consumo | ambiente | 5 | ecologia simplificada |
| Sinal químico hermafrodita → macho (se usado) | minhocas | 5 | só com base documentada |
