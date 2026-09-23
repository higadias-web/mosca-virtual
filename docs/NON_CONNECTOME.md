# O que NÃO vem do conectoma

Tudo que é engenharia, e não biologia, aparece aqui e no código com `# NON-CONNECTOME:`.
Fase atual: 2 (concluída, aguardando aprovação). As entradas marcadas como *planejado*
são previsões a confirmar nas fases seguintes.

## Já existente (Fase 0: só benchmark, nada entra no modelo)

| Item | Onde | Observação |
|---|---|---|
| Onda senoidal de acionamento do proxy de minhoca | `bench/bench_worm.py`, `bench/bench_full.py` | só gera carga de contato para medir custo; não será usada |
| Rede densa aleatória de 400 unidades (proxy de minhoca) | idem | só carga de CPU |
| CPG de caminhada do FlyGym (`flygym_demo.complex_terrain.CPGController`) | `bench/bench_flygym.py`, `bench/bench_full.py` | só carga de contato; a ligação DN → corpo é ⚠️ DECISÃO |

## Fase 2: ambiente e sensores (já no código)

| Item | Onde | Observação |
|---|---|---|
| Arena inteira: geometria, cores, zonas do piso, paredes, atrito padrão do FlyGym | `configs/arena.yaml`, `terrario/world/terrarium.py` | cenário, não biologia |
| Pares de contato também na probóscide (`c_rostrum`, `c_haustellum`) | `terrario/world/terrarium.py:CONTACT_SEGMENTS` | o preset do FlyGym não inclui; necessário para o labelo tocar o alimento |
| Rótulo de superfície por posição no piso (solo, colônia, piso da paisagem) | `TerrariumWorld.floor_surface_at` | mapa de zonas |
| Campo de odor 2D: difusão D = 10 mm²/s, decaimento k = 0,05 /s, fontes uniformes na pegada, início em regime estacionário, mesmo valor em qualquer altura | `terrario/world/fields.py:OdorField` | física simplificada; canais por fonte (a química é da Fase 3) |
| Gradiente de temperatura linear em x; ciclo de luz cossenoidal | `fields.py:Temperature`, `Light` | ambiente |
| Amostragem de odor e temperatura no funículo (E/D) | `terrario/body/sensors.py` | o FlyGym 2.x não tem olfato (D-002) |
| Gustação = superfície tocada pelos tarsos 1–5 de cada perna e pelo haustelo, com força normal | `sensors.py:_contacts` | só o estímulo físico; a taxa dos GRNs é da Fase 3 |
| CPG de caminhada do FlyGym usado como **arnês de teste** | `experiments/phase2_demo.py`, `tests/test_world.py` | só para passar pelas superfícies; não é o controle do animal |

## D-105 (avaliação dos conectomas; `terrario/brain/banc.py`, `hybrid.py`)

| Item | Onde | Observação |
|---|---|---|
| BANC: sinal pela previsão de transmissor do neurônio (GABA, glutamato **e histamina** → −1; demais → +1) | `terrario/brain/banc.py` | mesma regra do Shiu; a histamina não existia nas previsões do FlyWire |
| BANC: `w_syn` do Shiu multiplicado por 1,9 (variante de teste) | `experiments/connectome_eval.py --wscale` | compensa a menor captura de sinapses do BANC; não é dado |
| Híbrido: costura de dois animais (cérebro FlyWire + VNC BANC); pareamento de DNs/ANs por (tipo, lado), arbitrário dentro de tipos com vários membros; sinal do FlyWire nas pontes | `terrario/brain/hybrid.py` | toda a ponte é engenharia |

## Fase 3a (cordão do BANC na bolinha), a partir da Sessão 1

Cada item conta como **um ajuste fora do conectoma** no relatório da 3a quando for usado para
obter um resultado (critério da aprovação de 2026-09-23).

| # | Item | Onde | Observação |
|---|---|---|---|
| A1 | Bola (raio 5,39 mm, 54,6 mg, atrito 1,3; junta esférica) e altura da bola sob os tarsos | `terrario/vnc/apparatus.py` | parâmetros da `Ball` do FlyGym 1.x |
| A2 | Atuadores de torque nas 42 juntas ativas; sem adesão; rigidez/amortecimento passivos de `make_locomotion_fly` | idem | biomecânica |
| A3 | Músculo → grau de liberdade do NeuroMechFly (17 músculos → 7 DOFs) e sinal de flexão medido (CTr −, FTi +, TiTa −) | `motor_map.py`, `apparatus.py` | anatomia da literatura + modelagem |
| A4 | Ativação muscular de 1ª ordem: τ = 20 ms, saturação a 200 Hz. **Ganho por junta (µN·mm): ThC 10,0; CTr 19,45; TrF 15,89; FTi 22,39; TiTa 12,22** = p95 do torque que o NeuroMechFly precisa para reproduzir a marcha real gravada (tutorial 2 do FlyGym, kp 150); fixado antes de analisar o loop fechado (Sessão 2) | `apparatus.py:MotorDrive` | critério independente do ritmo; a fila com ganho 30 (sem fonte) foi descartada sem análise |
| A5 | Transdução proprioceptiva: claw (posição FTi), hook (direção), club (|velocidade|), placas de pelos (ThC/CTr), campaniformes (força de contato); R_MAX 100 Hz, larguras e saturações; **qual neurônio é de flexão/extensão e seu limiar (pseudoaleatório, semente fixa)** | `proprio.py` | o BANC não anota o ajuste por neurônio |
| A6 | Limiares de posição dentro da faixa de ângulos da marcha do CPG (Fase 2) | `proprio.py:_R` | derivado de dado simulado, não biológico |
| A5b | (Sessão 2) Direção por TIPO celular: os dois tipos principais de claw (SNpp50/SNpp51) e de hook (SNpp39/SNpp41) são tratados como os dois sentidos, e as 4 combinações são enumeradas; o resto é sorteado | `proprio.py` | hipótese de trabalho: nenhuma fonte liga tipo a sentido |
| A7 | Pulso de flexão inicial (50 ms, CTr e FTi do trípode L1-R2-L3) para quebrar a simetria | `terrario/vnc/loop.py` | protocolo; o ritmo é avaliado depois dele |
| A8 | Aferência imposta: ângulos gravados (`flygym_demo` MotionSnippet) alimentando só a transdução | `experiments/phase3a_s2.py` | teste de reflexo; não move o corpo |
| H6-v | Sinais "verified": `neurotransmitter_verified`, preenchido pela hemilinhagem; **MNs = glutamato** | `banc.neuron_signs` | literatura (MNs glutamatérgicos; Lacin et al. 2019) |
| H6-g | Sinais "verified_gluexc": glutamato excitatório em todo o VNC | idem | teste de sensibilidade, sem base documentada |
| S | Estímulo: Poisson nos DNs (como a ativação optogenética do Shiu); grupo G3 escolhido pelo acionamento no grafo | `experiments/phase3a_s1.py` | protocolo |

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
