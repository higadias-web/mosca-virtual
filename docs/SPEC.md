# Projeto: Terrário Virtual — organismos dirigidos por conectoma

## Objetivo
Construir uma simulação de terrário em que cada animal se comporta
exclusivamente a partir do seu conectoma e dos estímulos do ambiente. Não
programar comportamentos (nada de "se sentir cheiro, vá até a fonte"). Todo
comportamento deve emergir de sensores → neurônios → músculos/atuadores.

Inclui um painel web com visualização 3D do terrário, visualização 3D da
atividade cerebral de cada animal e replay completo.

## Elenco (fixo; ver "Regra de harmonia")
| Animal | Conectoma | Papel no terrário |
|---|---|---|
| 1 Drosophila adulta | FlyWire v783 (cérebro) + modelo LIF de Shiu et al. 2024; cordão nervoso ventral do BANC por correspondência (D-105) | Explora, chega à fruta andando, se alimenta |
| 1 larva de Drosophila | Cérebro larval (Winding et al. 2023, Science) | Vive e se alimenta na fruta e no fermento |
| 1 C. elegans hermafrodita | Cook et al. 2019 (hermafrodita adulto) | Rasteja no solo úmido e na colônia de bactérias |
| 1 C. elegans macho | Cook et al. 2019 (macho adulto) | Idem, com circuitos próprios do macho |

A mosca chega à fruta **andando**: o corpo (NeuroMechFly, FlyGym 2.1) não voa, então não há
pouso (decidido em 2026-09-23, na aprovação da Fase 2).

Ambiente vivo (sem neurônios, NON-CONNECTOME): colônia de fermento na fruta e
colônia de bactérias no solo, com crescimento e consumo.

### Fora do elenco (decisão de harmonia; não adicionar sem minha aprovação)
- Segunda mosca adulta: dobra o componente mais pesado do projeto.
- C. elegans dauer e troca de estágio de desenvolvimento: a transição exigiria
  regra programada e acrescenta complexidade sem ganho visual proporcional.
- Espécies marinhas com conectoma (Ciona, Platynereis): não pertencem ao
  ambiente.
- Espécies sem conectoma (ácaros, colêmbolos, tardígrados): exigiriam
  comportamento programado.

### Regra de harmonia
- O terrário deve parecer um ecossistema calmo e legível, não uma arena lotada.
  Cada animal tem uma "zona natural" (ver "O terrário"), e as zonas se tocam
  nas bordas, onde as interações podem acontecer.
- Nenhum animal ou elemento novo entra sem: (a) benchmark mostrando que o
  perfil `padrao` continua viável; (b) justificativa ecológica; (c) minha
  aprovação.
- Se um animal não funcionar bem (ex.: locomoção não emerge), ele sai da cena
  principal em vez de degradar o todo. Reportar e propor alternativa.

## Regras de trabalho (obrigatórias)
1. NÃO invente APIs, nomes de funções, IDs de neurônios, nomes de pacotes ou
   parâmetros. Antes de escrever código de integração, clone e leia os
   repositórios e a documentação reais. Cite o arquivo/função de origem em
   comentários. Confirme também as referências bibliográficas deste documento.
2. Fixe versões de todas as dependências (lockfile). Registre em
   docs/DECISIONS.md cada decisão técnica relevante com justificativa.
3. Tudo que NÃO vier do conectoma (CPGs, mapeamentos, pesos ajustados, ganhos,
   fricção anisotrópica, podas de rede, dinâmica de fermento/bactérias,
   consumo de alimento etc.) deve ser marcado no código com
   `# NON-CONNECTOME:` e listado em docs/NON_CONNECTOME.md. Transparência sobre
   o que é biologia e o que é engenharia é requisito do projeto.
4. Trabalhe por fases. Ao fim de cada fase, rode os testes de validação e pare
   para me mostrar os resultados antes de seguir. Não pule fases.
5. Quando houver decisão de arquitetura com trade-off relevante (marcada como
   ⚠️ DECISÃO abaixo), apresente as opções com prós/contras e uma recomendação,
   e ESPERE minha escolha.
6. Mantenha um CLAUDE.md na raiz com: estrutura do projeto, como rodar, fase
   atual, pendências e riscos conhecidos.
7. Peça minha confirmação antes de executar qualquer comando com `sudo`.
8. Ao fim de cada fase ou entrega, gere um vídeo curto (10–20 s) da cena em results/.
   Quando uma fase for aprovada, faça o commit dela antes de começar a seguinte.
9. Qualquer resultado de comportamento ou ritmo precisa sumir na ablação correspondente
   (critério contra resultado fabricado), e o relatório conta quantos ajustes fora do
   conectoma foram necessários, todos listados em docs/NON_CONNECTOME.md.

## Hardware e sistema (restrições obrigatórias)
Máquina alvo: ThinkPad T14 Gen 4 — Intel Core i5-1345U (2P+8E núcleos, 15 W,
sujeito a throttling térmico), Intel UHD Graphics (sem CUDA), 16 GB DDR5,
SSD NVMe 512 GB.

Sistema: Fedora 44 KDE, nativo (sem WSL, sem VM).

### Consequências de projeto
1. Modo principal = OFFLINE: simular → gravar log → assistir no replay.
   Modo ao vivo só com cenários reduzidos (ver "Perfis de execução").
2. Nada de CUDA/Brian2CUDA. Otimizar para CPU: avaliar Brian2 com
   cpp_standalone vs. implementação LIF própria com matriz esparsa
   (scipy.sparse ou PyTorch CPU). Escolher pelo benchmark, não por suposição.
   A implementação escolhida deve reproduzir numericamente o modelo original.
3. A Fase 0 inclui um BENCHMARK obrigatório, medido nesta máquina:
   - custo (tempo de parede) por 1 s simulado: cérebro da mosca isolado,
     FlyGym isolado (com e sem visão), 1 minhoca, cenário completo; a larva
     entra no benchmark na Fase 8;
   - uso de RAM de pico de cada um;
   - efeito do throttling em execução de 10+ min;
   - diferença entre os perfis de energia "Equilibrado" e "Desempenho" do KDE.
   Registrar em docs/BENCHMARK.md e usar os resultados para dimensionar os
   episódios.
4. Visão da mosca DESLIGADA por padrão; ligar só em perfil específico e com a
   menor resolução suportada. Olfato, gustação e contato têm prioridade.
5. Paralelismo: física e redes em processos separados somente se o benchmark
   mostrar ganho. Não assumir que ajuda (só 2 núcleos P).
6. Log com controle de volume: spikes completos (são esparsos), mas estados do
   corpo reduzidos para 100–200 Hz no replay (a física continua a 10 kHz
   internamente). Estimar o tamanho em disco por segundo simulado e avisar se
   um episódio passar de 5 GB.
7. Checkpoints: permitir pausar e retomar execuções longas (salvar o estado das
   redes e da física), para não perder horas de CPU por throttling, suspensão
   ou reinício.
8. Opção de nuvem documentada, mas não implementada por padrão: descrever como
   rodar o mesmo pipeline numa máquina com GPU para episódios longos do perfil
   `completo`.

### Regras específicas do Fedora
- NÃO instalar pacotes Python no Python do sistema (nada de `sudo pip`).
  O Python do Fedora 44 tende a ser mais novo do que MuJoCo/FlyGym/Brian2
  suportam. Criar um ambiente isolado com `uv`, fixando a versão do Python
  exigida pelo FlyGym (verificar no repositório; não presumir). Registrar a
  versão escolhida em DECISIONS.md.
- Dependências de sistema via `dnf`, listadas em docs/SETUP_FEDORA.md:
  compilador C/C++ para o Brian2 e bibliotecas Mesa/EGL para renderização
  headless do MuJoCo na GPU Intel. Verificar os nomes exatos dos pacotes no
  Fedora 44 e pedir minha confirmação antes de instalar.
- Renderização headless: usar `MUJOCO_GL=egl` (driver Mesa da Intel). Testar
  na Fase 0; se falhar, documentar o erro e testar `osmesa` como alternativa.
- Execuções longas: rodar com `systemd-inhibit --what=idle:sleep` para o
  notebook não suspender.
- O Fedora usa zram como swap por padrão. Monitorar se as execuções completas
  entram em swap, porque isso distorce o benchmark.
- Criar um script `setup.sh` idempotente que recrie o ambiente do zero.

## Perfis de execução (config YAML)
- `debug`: mosca adulta com cérebro reduzido (só os circuitos de interesse,
  extraídos do conectoma por caminhos que partem dos neurônios sensoriais usados
  e chegam aos DNs; a poda é NON-CONNECTOME), demais animais com conectoma
  completo (são baratos), sem visão, episódios curtos. Alvo: o mais próximo
  possível do tempo real. Usado para o painel ao vivo e para testar a
  infraestrutura. NÃO serve para conclusões sobre comportamento emergente,
  porque a poda altera a dinâmica da rede.
- `padrao`: todos os conectomas completos, sem visão, offline.
- `completo`: tudo ligado, incluindo visão; offline, com checkpoints; pode
  exigir execução noturna ou nuvem.
- Cada perfil permite ligar/desligar animais individualmente (para testes
  isolados e para a regra de harmonia).

## Componentes de referência (verificar e confirmar cada um)
### Drosophila adulta
- Cérebro: conectoma FlyWire v783 + modelo LIF de Shiu et al. 2024 (Nature),
  repositório original do modelo (Brian2). Verificar se existe implementação
  alternativa no próprio repositório ou em forks confiáveis.
- Corpo: NeuroMechFly v2 / FlyGym (MuJoCo). Usar os sensores já existentes
  (visão com olhos compostos, olfato, contato/tarsos) sempre que possível.
- VNC: o FlyWire cobre só o cérebro. Os DNs projetam para o cordão nervoso
  ventral, ausente no FlyWire. Avaliar MANC (Janelia) e FANC.
  ⚠️ DECISÃO: (a) DNs → comandos de alto nível num controlador FlyGym;
  (b) integrar o conectoma do VNC até os motoneurônios; (c) híbrido.
  Considerar o custo computacional de cada opção nesta máquina.
  (D-101, aprovada na Fase 0: híbrido, começando por (a).)
- Conectoma de cérebro + cordão (atualizado em 2026-09-23): o **BANC** (Bates, Phelps,
  Kim, Yang et al., "Distributed control circuits across a brain-and-cord connectome",
  Nature 2026; código github.com/htem/BANC-project; dados no Harvard Dataverse
  doi:10.7910/DVN/7WTH1N, no flywire.ai e no Codex) une cérebro e VNC da mesma mosca.
  Referência relacionada, não dependência: arXiv 2602.17997 (FlyGM), que usa o FlyWire
  v783 como grafo de um controlador treinado por imitação + RL.
  D-105 (aprovada em 2026-09-23: opção (c)). Opções avaliadas: (a) FlyWire 783 + controlador; (b) BANC inteiro
  (cérebro + cordão); (c) FlyWire no cérebro + cordão do BANC por correspondência entre
  datasets. Para cada uma: benchmark nesta máquina (RAM, tempo por trial, quantos workers
  cabem), revalidação (refazer a Fig. 1D no BANC e comparar com o FlyWire), cobertura de
  revisão dos circuitos de alimentação e locomoção e impacto da lâmina ausente na visão.
  Levantamento e recomendação em docs/D105_CONECTOMA.md.
- Qualquer troca de conectoma do cérebro exige refazer a Fig. 1D do Shiu e comparar com o
  resultado da Fase 1 antes de usar.

### Larva de Drosophila
- Cérebro: conectoma larval de Winding et al. 2023 (Science). Verificar o
  formato de distribuição dos dados, as anotações de tipos celulares e o que
  existe publicado sobre o cordão nervoso ventral larval (há circuitos
  parciais em outros trabalhos; confirmar cobertura).
- Modelo neuronal: LIF com o mesmo motor da mosca adulta, para uniformidade.
  Documentar a origem dos parâmetros (não há um modelo equivalente ao do Shiu
  para a larva, até onde se sabe; verificar).
- Corpo: avaliar modelos biomecânicos existentes de larva (ex.: Loveless,
  Lagogiannis e Webb 2019; verificar se há código disponível). Alternativa:
  corpo segmentado próprio em MuJoCo, com locomoção peristáltica.
  ⚠️ DECISÃO: ligação cérebro → locomoção, com as mesmas opções (a)/(b)/(c)
  da mosca adulta, conforme a cobertura do VNC larval.

### C. elegans (hermafrodita e macho)
- Sistema nervoso: conectomas de Cook et al. 2019 (hermafrodita e macho
  adultos, incluindo junções neuromusculares). Avaliar c302 (OpenWorm,
  NeuroML) vs. reimplementar os conectomas em LIF com o mesmo motor da mosca.
  Verificar se o c302 suporta o conectoma do macho; se não, a reimplementação
  tende a ser necessária.
  ⚠️ DECISÃO: qual fonte e qual simulador.
- Corpo: Sibernetic (SPH) está fora do escopo (pesado demais e sem GPU
  adequada). Propor um corpo simplificado em MuJoCo (cadeia de segmentos com
  músculos nos 4 quadrantes, mapeados às células musculares da parede do
  corpo), com fricção anisotrópica ou modelo de força resistiva para rastejar
  em superfície úmida. Mesmo corpo para os dois sexos, salvo diferença
  morfológica relevante (a cauda do macho pode ser simplificada).
  RISCO CONHECIDO: a locomoção ondulatória pode não emergir só do conectoma
  (depende de propriocepção). Plano B, marcado como NON-CONNECTOME:
  acoplamento proprioceptivo mínimo, documentado.
- Comportamento reprodutivo do macho: a cópula está FORA do escopo (o corpo
  simplificado não a reproduz). Aproximação e busca podem emergir ou não; não
  forçar. Se houver sinal químico entre os sexos, ele entra como campo químico
  emitido pelo hermafrodita, documentado.

## O terrário ("paradisíaco", mas fisicamente coerente)
Arena única no MuJoCo, em escala real (milímetros), organizada em zonas que se
tocam nas bordas:

| Zona | Elementos | Habitante natural |
|---|---|---|
| Fruta | Fatia de fruta em decomposição (ex.: banana) com colônia de fermento na superfície | Larva (dentro/sobre a fruta); mosca chega andando para se alimentar |
| Solo úmido | Substrato tipo ágar/solo com colônia de bactérias, gradiente químico | C. elegans |
| Borda fruta–solo | Bactérias também crescem na fruta que encosta no solo | Zona de encontro de todos |
| Paisagem | Pedrinhas, um pedaço de musgo, uma gotícula de água, relevo suave | Mosca (caminha) |

- Gradiente de temperatura suave (termotaxia das minhocas via AFD) e ciclo de
  luz dia/noite.
- Campo de odores: modelo de difusão simples (2D ou 3D, decidir pelo custo),
  com fontes na fruta, no fermento e nas bactérias, atualizado em passo
  próprio e amostrado pelos sensores de cada animal.
- Ambiente vivo (NON-CONNECTOME): fermento e bactérias com crescimento
  logístico simples e consumo local. Consumo acontece por acoplamento físico,
  não por regra de comportamento: ex.: a mosca consome quando os motoneurônios
  da probóscide estão ativos e há contato com alimento; a minhoca consome
  quando a cabeça está na colônia e os neurônios do bombeamento faríngeo estão
  ativos (confirmar os neurônios na literatura).
- Composição visual: poucos elementos, bem iluminados, com espaço livre entre
  as zonas. Priorizar legibilidade da cena sobre quantidade de objetos.

## Acoplamento sensorial (sempre mapear para neurônios anotados reais)
- Mosca adulta: olfato (antena → ORNs correspondentes), gustação (contato com
  alimento → GRNs de açúcar), mecanossensação (tarsos/corpo) e, no perfil
  `completo`, visão (olhos compostos do FlyGym → fotorreceptores). Identificar
  os neurônios pelas anotações do FlyWire. Se a visão vier de um dataset sem
  lâmina (BANC), R1–R6 não existem e a entrada vai direto para L1–L3, com uma
  "lâmina virtual" NON-CONNECTOME (D-105).
- Larva: olfato (órgão dorsal → ORNs larvais), gustação e mecanossensação
  (contato com fruta, com outros animais e com obstáculos). Identificar pelas
  anotações do conectoma larval.
- C. elegans: quimiossensação (ex.: AWC, ASE e ASH, conforme o estímulo),
  termossensação (AFD), toque (ALM, AVM e PLM). Confirmar funções e as
  diferenças do macho na literatura/WormBase antes de ligar.
- Interação entre animais: apenas física (contato/colisão) e química (odores
  do ambiente e, se documentado, sinais químicos entre os vermes). Nenhuma
  regra de interação programada.

### Interações que podem emergir (observar; NÃO forçar)
- Mosca e larva convergindo para a fruta e o fermento.
- Minhocas encontrando a borda fruta–solo pelo gradiente das bactérias.
- Toques entre animais na zona de encontro, gerando respostas de fuga ou
  reversão (ex.: reversão da minhoca por toque anterior).
- Macho se aproximando do hermafrodita.
Registrar no log os eventos de encontro, para análise e para os marcadores do
replay.

## Arquitetura de co-simulação
- Orquestrador com relógio global e passos de sincronização definidos
  (física MuJoCo ~0,1 ms; redes neurais em passo próprio, ex.: 0,1–1 ms;
  campo de odor e ambiente vivo em passo mais lento). Justificar os valores em
  DECISIONS.md.
- Sem GPU dedicada: tempo real só no perfil `debug`. Os demais perfis são
  offline, com replay. Tempo real NÃO é requisito se comprometer a fidelidade.
- Log unificado: spikes (animal, neuron_id, t), estados do corpo, contatos,
  consumo, populações de fermento/bactérias e campos sensoriais amostrados, em
  formato colunar (Parquet ou HDF5), com metadados de versão, perfil e seed.
  Execuções devem ser reproduzíveis.

## Painel web
### Terrário
- Vista 3D do terrário (three.js) sincronizada com a física. Renderização
  bonita no painel (iluminação, materiais), separada da física. Leve o
  suficiente para a GPU integrada.
- Clicar num animal seleciona o cérebro dele no painel de atividade cerebral.

### Atividade cerebral (requisito central)
- Um cérebro 3D por animal, com neurônios posicionados pelas coordenadas reais
  dos datasets (somas ou centroides; verificar a disponibilidade de posições
  em cada dataset: FlyWire, conectoma larval e C. elegans). Se algum dataset
  não tiver posições utilizáveis, propor alternativa e registrar.
- Neurônios como pontos (geometria instanciada / shader de pontos) que acendem
  a cada spike e apagam com decaimento, com cor por classe (sensorial,
  interneurônio, DN/motor). O cérebro da mosca adulta (~139 mil pontos) deve
  rodar fluido na GPU integrada; pré-computar a atividade por quadro para o
  replay em vez de processar spikes brutos no navegador.
- Visões: (a) grade com os 4 cérebros lado a lado, sincronizados com a
  timeline; (b) foco em um cérebro, com rotação/zoom.
- Ao selecionar um neurônio: nome/anotação, tipo, taxa de disparo e, opcional,
  as conexões mais fortes (limitar o número de arestas desenhadas).
- Complementos 2D por animal: raster de spikes e taxa de disparo por grupo.
- Destaque automático das regiões mais ativas em eventos (ex.: quando a mosca
  toca a fruta, realçar os circuitos gustativos).

### Atividade motora (requisito adicionado em 2026-09-23; construir na Fase 6)
- Um painel de atividade motora por animal, sincronizado com a timeline do replay.
- Mosca: vista do corpo em que cada perna e a probóscide acendem conforme disparam os
  motoneurônios de cada junta, pelo mapa motoneurônio → músculo → junta do BANC
  (músculo-alvo anotado por MN), sincronizada com o movimento das juntas no replay.
  Clicar numa junta mostra os motoneurônios dela e o músculo-alvo de cada um.
- O cordão nervoso ventral aparece na vista 3D do cérebro da mosca, ligado a ele
  (posições do BANC registradas ao espaço do FlyWire, ou lado a lado com a ligação
  pelos DNs/ANs; decidir na Fase 6).
- Minhocas: vista da "onda motora", com os motoneurônios agrupados pelos quadrantes
  musculares ao longo do corpo. Larva: equivalente, se ela entrar no elenco.
- Antes da Fase 6 não se constrói painel web: nas fases anteriores, só figuras de
  diagnóstico em results/ (ex.: na 3a, raster dos MNs por perna e por junta e o espectro
  da métrica de ritmo, a cada sessão).

### Replay
- Timeline com play/pause/velocidade/scrub e marcadores de eventos (contato,
  chegada à fruta, consumo, encontros entre animais).
- Modo ao vivo apenas no perfil `debug`; modo replay para todos os perfis,
  usando o mesmo formato de log.

## Fases
0. Leitura dos repositórios, setup do ambiente no Fedora (`setup.sh`),
   benchmark desta máquina e levantamento das ⚠️ DECISÕES com recomendação.
   Apontar qualquer premissa deste documento que esteja errada ou
   desatualizada. Nenhum código de simulação antes da minha aprovação.
1. Reproduzir um resultado do Shiu et al. 2024 (ex.: ativação de GRNs de
   açúcar prevendo a atividade relacionada à alimentação) de forma isolada.
2. FlyGym rodando na arena do terrário, com os sensores gerando dados.
3. Loop fechado da mosca adulta: cérebro FlyWire 783 + cordão do BANC (D-105, opção (c)).
   Dividida em duas subfases (D-106, aprovada em 2026-09-23; plano em docs/FASE3_PLANO.md):
   3a. Mosca presa sobre bolinha virtual: validar a marcha gerada pelo cordão
       nervoso (DNs → VNC → motoneurônios → juntas, com propriocepção pelos
       neurônios sensoriais do VNC). Prazo: 6 sessões de trabalho ou 2 semanas, o
       que vier primeiro. Marco: se até a 3ª sessão nenhum estímulo de DN gerar
       atividade rítmica nos MNs de perna com o loop proprioceptivo fechado, a 3a
       é encerrada, o resultado negativo é documentado e a 3b segue com DNs →
       controlador FlyGym (opção (a)).
   3b. Mosca livre no terrário, em malha fechada com os sensores da Fase 2.
4. Um C. elegans hermafrodita isolado: conectoma + corpo simplificado. Validar
   a ondulação e a reversão ao toque anterior. Se falhar, reportar e propor o
   Plano B. Depois, repetir com o macho.
5. Terrário com mosca adulta + 2 C. elegans + campos químico e térmico +
   ambiente vivo (fermento e bactérias), perfil `padrao`.
6. Log unificado e painel com terrário, atividade cerebral 3D dos animais e
   replay.
7. Painel ao vivo com o perfil `debug`; documentar a execução em nuvem para o
   perfil `completo`.
8. Larva de Drosophila: primeiro isolada (conectoma + corpo + validação),
   depois benchmark com o elenco completo e, se viável e aprovado, entrada no
   terrário e no painel.

## Critérios de validação (por fase)
- Resultados reproduzidos comparados numericamente com o artigo do Shiu.
- C. elegans: frequência e comprimento de onda da ondulação em faixa plausível
  para rastejamento em superfície; resposta de reversão ao toque anterior;
  comparação qualitativa entre macho e hermafrodita documentada.
- Mosca adulta: marcha estável no terreno; mudança de comportamento com
  estímulo olfativo/gustativo, sem regra programada.
- Fase 3a: na bolinha, alternância rítmica flexor/extensor por perna,
  coordenação entre pernas (trípode/tetrápode), bola girando para a frente com DNs de
  marcha e virada lateralizada com DNs de virada; silenciar os DNs ou a propriocepção
  muda ou elimina a marcha. Faixas numéricas fixadas pela literatura antes de começar.
- Larva: locomoção peristáltica reconhecível; resposta a gradiente de odor
  (quimiotaxia) se emergir; documentar se não emergir.
- Teste de ablação para cada animal: zerar os neurônios sensoriais relevantes
  deve eliminar a resposta correspondente. Isso prova que o comportamento vem
  da rede.
- Perfil `debug` vs. `padrao`: comparar respostas equivalentes e documentar as
  diferenças causadas pela poda.
- Harmonia: revisão visual de um episódio completo no replay antes de
  considerar a Fase 5 e a Fase 8 concluídas (cena legível, sem aglomeração,
  interações visíveis).

Comece pela Fase 0.
