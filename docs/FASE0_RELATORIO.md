# Relatório da Fase 0 (2026-09-22)

Escopo: leitura dos repositórios, setup do Fedora, benchmark e levantamento das ⚠️ DECISÕES.
Nenhum código de simulação foi escrito; em `bench/` há só protótipos de benchmark.

## 1. Entregas

| Item | Onde | Estado |
|---|---|---|
| Pacotes de sistema (dnf) | `docs/SETUP_FEDORA.md` | instalados e verificados |
| Ambiente isolado (uv, Python 3.13, lockfile) | `pyproject.toml`, `uv.lock` | ok |
| `setup.sh` idempotente | `setup.sh` | ok |
| MuJoCo headless com EGL (e OSMesa como alternativa) | `docs/SETUP_FEDORA.md` | ambos funcionam |
| Benchmark desta máquina | `docs/BENCHMARK.md` | completo (a larva fica para a Fase 8, como pede a SPEC) |
| Decisões técnicas | `docs/DECISIONS.md` | D-001..D-007 |
| Registro NON-CONNECTOME | `docs/NON_CONNECTOME.md` | iniciado |
| CLAUDE.md | `CLAUDE.md` | ok |

## 2. Premissas da SPEC erradas ou desatualizadas

1. **"FlyWire v783 + modelo LIF de Shiu et al. 2024"**: o artigo (Nature 634:210–219, 2024)
   usou a **v630**. O repositório tem as duas versões, mas os números publicados são da v630.
   Proposta (D-003): reproduzir na v630 e depois confirmar na v783.
2. **"O Python do Fedora 44 tende a ser mais novo do que MuJoCo/FlyGym/Brian2 suportam"**:
   não procede hoje. O FlyGym 2.1 suporta 3.12–3.14 (o repositório usa 3.14), e o Brian2 2.10
   e o MuJoCo 3.9 têm wheels cp314. Mesmo assim usamos o `uv` com 3.13, como pede a SPEC (D-001).
3. **FlyGym / NeuroMechFly v2**: foi **reescrito** em abril de 2026 (2.0), sem compatibilidade.
   A 2.x é ~10× mais rápida, mas **não tem módulo de olfato**; a `OdorArena` ficou na 1.x
   (`flygym-gymnasium`, que exige Python < 3.13). Não é um bloqueio: a SPEC já prevê um campo de
   odor próprio, e amostramos a concentração nos sites das antenas e palpos (D-002).
4. **"Avaliar Brian2 cpp_standalone vs. implementação própria"**: o `cpp_standalone` roda a
   simulação inteira num binário compilado e **não permite loop fechado passo a passo** com o
   MuJoCo. Além disso, a implementação própria em numba ficou 3,4–4× mais rápida e reproduz o
   Brian2 numericamente (D-004).
5. **"Modo debug o mais próximo possível do tempo real"**: a física do NeuroMechFly **sozinha**
   custa 2,3–2,8 s por segundo simulado nesta CPU, ou seja, nenhuma poda de cérebro leva ao
   tempo real. O "ao vivo" possível é em câmera lenta (~1/3). Alternativas para a Fase 7:
   aceitar a câmera lenta; ou, só no `debug`, relaxar o passo físico/contatos (NON-CONNECTOME,
   com perda de fidelidade da marcha); ou manter o ao vivo só com as minhocas.
6. **"LIF com o mesmo motor da mosca" para C. elegans (opção citada)**: a maioria dos neurônios
   de C. elegans **não dispara potenciais de ação** (sinalização graduada; exceções
   documentadas, como os disparos do AWA e os platôs do RMD). Um LIF distorceria a biologia.
   Consequência também para o painel e o log: para as minhocas, "acender a cada spike" vira
   "brilho proporcional à atividade graduada" (D-102).
7. **"Os DNs projetam para o VNC, ausente no FlyWire. Avaliar MANC e FANC"**: surgiram
   conectomas **de SNC inteiro (cérebro + VNC no mesmo animal)**: o **BANC** (fêmea, ~188 mil
   neurônios; Bates et al., Nature 2026) e o **Male CNS** da Janelia (~166 mil neurônios, 2025).
   Eles mudam as opções do VNC (D-101).
8. **"OSMesa como alternativa"**: o Mesa removeu o OSMesa a partir da 25.1. No Fedora 44 só
   existe o `mesa-compat-libOSMesa` 25.0.7. Funciona, mas pode sumir. O EGL funciona e é o padrão.
9. **Perfis "Equilibrado/Desempenho"**: no Fedora 44 KDE, quem responde é o `tuned-ppd`
   (Desempenho = `throughput-performance`). **Na bateria**, o perfil de economia desliga o turbo
   e trava a CPU em 1 GHz (era o estado da máquina no início da Fase 0).
10. **Atividade espontânea**: o modelo de Shiu **não tem ruído nem corrente de fundo**. Sem
    entrada sensorial, o cérebro inteiro fica em silêncio absoluto (é isso que torna exata a
    otimização de conjunto ativo). Para o terrário, isso significa que exploração espontânea não
    vai emergir sozinha: a mosca só se mexe se algum sentido estiver sendo estimulado. Será
    preciso decidir (na Fase 3) se haverá entrada sensorial tônica (ex.: mecanossensação dos
    tarsos em contato, luz ambiente) e documentá-la como codificação sensorial NON-CONNECTOME.
    Nenhuma "corrente de exploração" inventada.
11. **"~139 mil pontos"**: correto (138.639 na v783). Há posições 3D de soma para 99,99 % deles
    (`flywire_annotations`, Supplemental_file1: `soma_x/y/z`).
12. **Posições 3D das minhocas**: o hermafrodita tem os 302 neurônios com coordenadas (NeuroML do
    OpenWorm/c302). O **macho tem 380 neurônios no Cook 2019, e 89 deles (exclusivos do macho:
    CA*, CP*, R*, SPV* etc.) não têm posição** nesses dados (D-104).
13. **Larva**: o Winding et al. 2023 (Science 379:eadd9330) cobre o **cérebro** (3.016 neurônios,
    548 mil sinapses). As matrizes estão nos Data S1/S2 e no CATMAID público da Virtual Fly Brain
    (l1em.catmaid.virtualflybrain.org). O código do Loveless, Lagogiannis e Webb 2019 existe
    (github.com/janeloveless/mechanics-of-exploration; Zenodo 1014807). Se já existe um
    conectoma completo do VNC larval publicado, **não consegui confirmar** (fica para a Fase 8).

Referências confirmadas: Shiu et al. 2024 (Nature, doi:10.1038/s41586-024-07763-9);
Winding et al. 2023 (Science, doi:10.1126/science.add9330); Loveless et al. 2019 (PLoS Comput
Biol, doi:10.1371/journal.pcbi.1006635); Cook et al. 2019 (Nature 571:63; lido pelo
`cect.readers.Cook2019*Reader`); NeuroMechFly v2 (Wang-Chen et al., Nature Methods 2024);
MANC (Takemura et al. 2024; Marin et al. 2024, eLife). Neurônios do bombeamento faríngeo:
MC (inicia a contração e define a taxa), M3 (fim da contração) e M4 (peristalse do istmo)
(Avery & Horvitz 1987; Avery 1993; Raizen & Avery 1994; WormBook "C. elegans feeding").

Trabalhos prévios semelhantes, **não verificados nem usados como dependência**: Eon Systems
(Shiu + NeuroMechFly com interface DN → controladores escolhida à mão, sincronização a cada
15 ms), `erojasoficial-byte/fly-brain`, `statsleelab/embodied-fly-lab`, `Fly.exe` (Male CNS na GPU).

## 3. ⚠️ DECISÕES (preciso da sua escolha)

### ⚠️ D-101: Mosca adulta, VNC (DNs → corpo)

| Opção | Como | Custo nesta máquina | Prós | Contras |
|---|---|---|---|---|
| **(a)** DNs → controlador FlyGym | Taxas de DNs identificados no FlyWire → sinal descendente do `HybridTurningController` (2D: esquerda/direita) + MN9 → probóscide | ~0 (o controlador é trivial) | Robusto; é a abordagem do NeuroMechFly v2 e da Eon; marcha estável garantida | Os CPGs, os reflexos e o mapeamento DN → comando são NON-CONNECTOME; baixa dimensão (poucos DNs usados) |
| **(b)** Conectoma do VNC até os motoneurônios | Trocar o FlyWire pelo **BANC** ou pelo **Male CNS** (cérebro + VNC no mesmo animal), LIF em tudo, motoneurônios → atuadores | +20–35 % no cérebro (~0,9–1,1 s/s, estimado pelo número de neurônios) | Máximo de conectoma; os DNs se ligam a MNs reais | Não há evidência de que um LIF sem propriocepção nem propriedades intrínsecas gere marcha; o mapeamento MN → torque de junta também é NON-CONNECTOME; o Shiu não foi validado nesses datasets; risco alto de "não anda" |
| **(c)** Híbrido | Locomoção por (a); circuitos que não dependem de ritmo (alimentação/probóscide, e depois grooming) pelo conectoma até os MNs | Pequeno | Transparência onde é viável e marcha garantida | Dois caminhos para manter; é preciso escolher os datasets |

**Recomendação: (c), começando por (a) na Fase 3.** Uso DNs anotados no FlyWire (os nomes
exatos, como DNa01/DNa02/oDN1, serão confirmados nas anotações antes de usar) e o MN9 → probóscide.
Deixo a porta aberta para (b) com BANC/Male CNS como experimento separado. Justificativa: a
SPEC exige que a marcha seja estável, e uma marcha a partir de um VNC LIF é pergunta de pesquisa em aberto.

### ⚠️ D-102: C. elegans, fonte, modelo neuronal e simulador

| Opção | Prós | Contras |
|---|---|---|
| **(1)** c302 (NeuroML) + jNeuroML/NEURON | Modelos já publicados; ecossistema OpenWorm | Roda em lote (Java/NEURON), sem passo a passo com o MuJoCo; o padrão é o hermafrodita (o leitor do macho existe no `cect`, mas o c302 assume músculos e posições do hermafrodita); mais dependências |
| **(2)** Cook 2019 via `cect` + **modelo graduado próprio** em numba (dinâmica tipo c302 / Wicks et al. 1996 / Kunert et al. 2014, a confirmar na Fase 4), mesmo orquestrador e log da mosca | Hermafrodita **e macho** (302 e 380 neurônios, 95 músculos da parede do corpo, JNMs); passo a passo; custo desprezível | Os parâmetros neuronais vêm da literatura (NON-CONNECTOME), e o sinal das sinapses químicas é incerto |
| **(3)** Cook 2019 + LIF do motor da mosca | Uniformidade total | Biologicamente inadequado (neurônios graduados) |

**Recomendação: (2).** E para o corpo, **cadeia planar com arrasto anisotrópico (RFT)**, e não
contatos por cápsula: 0,23 contra 1,2 s/s por minhoca, e RFT é o regime físico do rastejar em ágar
(Boyle, Berri & Cohen 2012 usam essa formulação num modelo neuromecânico de C. elegans).
O custo: tratar a rigidez numérica (item 3 do BENCHMARK) e fazer o contato mosca–minhoca por
geometria sem fricção. O Plano B proprioceptivo segue a SPEC.

### ⚠️ D-103: Larva, cérebro → locomoção (decisão só na Fase 8)
Mesmas opções (a)/(b)/(c). Com o VNC larval ainda sem cobertura confirmada, a tendência é
(a)/(c): cérebro Winding (LIF, mesmo motor, parâmetros do Shiu por falta de modelo larval
equivalente, NON-CONNECTOME) → comandos de peristalse/virada num corpo segmentado (avaliar o
código do Loveless 2019). Nada a decidir agora; registrado para não se perder.

### ⚠️ D-104: Posições 3D dos 89 neurônios exclusivos do macho

| Opção | Prós | Contras |
|---|---|---|
| (a) Buscar coordenadas publicadas (atlas do macho, WormAtlas/Cook 2019 SI) antes de decidir | Seria o dado real | Talvez não exista em formato utilizável |
| (b) Neurônios compartilhados com as coordenadas do hermafrodita; exclusivos do macho posicionados no gânglio anatômico correto (pré-anal, dorsorretal, raios da cauda), marcados como aproximação (NON-CONNECTOME) | Visualização legível e honesta | Posição aproximada |
| (c) Layout 2D esquemático para o macho | Simples | Quebra a uniformidade 3D do painel |

**Recomendação: (a) com fallback (b).**

### Confirmações menores (padrão proposto, basta responder "ok")
- **D-003**: Fase 1 reproduz na v630 (números do artigo) e depois confirma na v783.
- **D-006**: física a 0,1 ms; cérebro a 0,1 ms; sincronização a cada 1 ms (abaixo do atraso sináptico de 1,8 ms); odor e ambiente a 10 ms.
- **Perfil de energia**: usar o **Desempenho** nas execuções longas (15–20 % mais rápido, sem throttling em 12 min, 84 °C de pico).

## 4. Riscos que continuam abertos
- Custo do cérebro com muitos sentidos ativos ao mesmo tempo (o conjunto ativo cresce): remedir na Fase 3.
- Rigidez numérica do corpo RFT das minhocas: Fase 4.
- Emergência da ondulação só pelo conectoma: Fase 4 (o Plano B está previsto na SPEC).
- Log de ~1 MB/s simulado sem compressão: o aviso de 5 GB deve disparar em episódios de ~1 h+.
