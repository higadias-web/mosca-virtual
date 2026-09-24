# Plano da Fase 3b: mosca livre no terrário, DNs → controlador (APROVADO em 2026-09-23, com os ajustes de §F)

A 3a terminou como "loop fechado não testável com este aparato no prazo" (`docs/FASE3A_RELATORIO.md`).
Pela D-106, a 3b segue com a opção (a): **os DNs do cérebro FlyWire 783 modulam um controlador de marcha
do FlyGym**. O cordão do BANC sai do caminho da locomoção. O cérebro é o mesmo da Fase 1 (LIF do Shiu,
validado na Fig. 1D), e os sensores são os da Fase 2.

## 0. Peças e o que já existe (verificado no código)
- **Corpo:** `flygym_demo.complex_terrain.make_locomotion_fly`, com atuadores de POSIÇÃO (kp 45 µN·mm/rad,
  faixa ±65), passivos 0,05/0,06 e adesão tarsal. É o corpo do terrário da Fase 2
  (`terrario/body/fly.py:build_scene`). O aparato de torque da 3a não entra.
- **Controlador:** `flygym_demo.complex_terrain.turning_controller.HybridTurningController` (FlyGym 2.1).
  - Recebe um sinal descendente de 2 dimensões, `descending_signal = [δ_E, δ_D]`.
  - Para cada lado, |δ| é a amplitude do passo (ganho sobre o passo real gravado) e o sinal de δ é o
    sentido (δ < 0 inverte a frequência do lado, para trás). A frequência base é 12 Hz.
  - O modelo e as regras de correção (retração e tropeço) vêm do tutorial "turning" e do NeuroMechFly v2.
- **DNs na anotação do FlyWire** (`third_party/flywire_annotations/.../Supplemental_file1_neuron_annotations.tsv`,
  Schlegel et al. 2024):
  - DNp09, DNa01, DNa02 e DNg13: 1 célula por lado;
  - MDN: 2 por lado;
  - todos colinérgicos (`top_nt`);
  - oDN1 e BPN (Bidaye et al. 2020) **não** aparecem como tipo nessa anotação e ficam de fora.
  - Os root_ids serão casados com o conectoma carregado (`connectomes.load("783")`) antes de qualquer
    execução, **sem herdar listas de artigos** (pendência da Fase 3 no CLAUDE.md).

## (a) Como os DNs modulam o CPG

**Leitura dos DNs** (NON-CONNECTOME): taxa de disparo de cada grupo e lado, filtrada com constante de
tempo τ_r = 100 ms (escolha, sem fonte). Ela vira [δ_E, δ_D] a cada 10 ms.

| Função | Grupo (por lado) | Ligação proposta | Fonte da ligação DN → comportamento | Força da evidência |
|---|---|---|---|---|
| **Início e avanço** | DNp09 | a taxa de DNp09 dos dois lados soma no avanço: δ_E = δ_D = g_f · sat(r_E + r_D). **Parar** é a volta de δ a 0 quando a taxa cai | Bidaye et al. 2020, *Neuron* 108:469, "Two brain pathways initiate distinct forward walking programs in Drosophila": ativar P9 (= DNp09) inicia e mantém a marcha para a frente | ativação suficiente, confirmada na fonte |
| **Curva** | DNp09 unilateral + DNa02 (e DNa01) | assimetria: δ_lado = avanço × (1 − g_t · r_DNa02,lado / r_ref), o que encurta o passo de um lado. DNp09 unilateral também gera curva | DNp09: Bidaye et al. 2020, "P9 drives forward walking with ipsilateral turning". DNa02/DNa01: Yang et al. 2024, *Cell*, "Fine-grained descending control of steering in walking Drosophila": dois tipos descendentes, um que alonga o passo do lado de fora da curva e outro que encurta o do lado de dentro | DNp09: confirmada. **Qual DN alonga e qual encurta, e para que lado cada um vira: A CONFIRMAR no texto completo** (o acesso ao texto foi bloqueado nesta sessão). A ligação só entra depois de confirmada; se não for, só DNp09 controla a curva |
| **Velocidade** | DNp09 (magnitude) | a velocidade sai de \|δ\|, ou seja, da amplitude do passo. A frequência fica fixa em 12 Hz | nenhuma fonte liga a taxa de um DN específico à velocidade de passada. Mendes et al. 2013 mostram que a mosca real aumenta a frequência com a velocidade, e o controlador não faz isso | **sem fonte**: a relação taxa → amplitude (g_f, saturação) é escolha e fica toda no NON_CONNECTOME |
| **Ré** | MDN | se r_MDN > limiar, o sinal de δ inverte nos dois lados, e \|δ\| = g_b · sat(r_MDN) | Bidaye, Machacek, Wu e Dickson 2014, *Science* 344:97, "Neuronal control of Drosophila walking direction": ativar MDN basta para a marcha para trás, e bloquear MDN impede a ré diante de barreira | ativação suficiente e necessidade, confirmadas na fonte |
| **Parada ativa** | nenhum DN dedicado | não é modelada como comando: a parada é a queda da taxa dos DNs de avanço | Sapkal et al. 2024, *Nature* 634:191, "Neural circuit mechanisms underlying context-specific halting in Drosophila": um mecanismo "walk-OFF" (neurônios GABAérgicos no cérebro inibindo os DNs de marcha) e um "brake" (no cordão, sem representação aqui) | o walk-OFF já está no conectoma do cérebro; o brake fica de fora, declarado |

O que o conectoma decide: **se** e **quando** esses DNs disparam em resposta aos sentidos. O que a
engenharia decide: a tradução das taxas em amplitude e sentido do passo.

## (b) O que entra no `docs/NON_CONNECTOME.md`
1. **O CPG inteiro:** 6 osciladores acoplados, frequência de 12 Hz, vieses de fase do trípode e
   convergência (`cpg_controller.py`); passos pré-programados a partir da cinemática gravada
   (`preprogrammed.py`); regras de correção do controlador híbrido (retração, tropeço; limiares e taxas).
2. **O mapeamento DN → CPG:** a escolha dos grupos (pela literatura acima), a leitura da taxa
   (τ_r = 100 ms), os ganhos g_f, g_t, g_b, a saturação, o limiar do MDN, a regra de curva e a
   frequência fixa.
3. **O corpo com atuadores de posição** (kp 45), a adesão e os passivos de `make_locomotion_fly`.
4. **A transdução sensorial** da Fase 2 para taxas de Poisson nos ORNs, GRNs e mecanorreceptores (IDs da
   v783; a pendência da Fase 3 continua).
5. **A ausência** de atividade de fundo no LIF: sem estímulo, os DNs ficam calados e a mosca fica
   parada. É declarado como propriedade do modelo, não como comportamento.

Os ganhos (g_f, g_t, g_b, r_ref, limiar do MDN) são fixados **uma vez**, antes de qualquer teste
sensorial, por um critério independente: a estimulação direta de cada grupo a 100 Hz (a taxa dos
experimentos do Shiu) deve dar |δ| = 1 no controlador (o passo real gravado). Nenhum ajuste depois de
ver o comportamento sensorial.

## (c) Ablação: o comportamento tem de vir do conectoma
- **A1, silenciar o grupo de DNs** (DNp09; DNa02/DNa01; MDN) no LIF, com o mesmo estímulo sensorial:
  a modulação correspondente precisa sumir.
  - *Ressalva:* com esta arquitetura, isso é quase garantido por construção, porque sem taxa no DN
    lido não há δ. Por isso a A1 prova o caminho, não a origem.
- **A2, silenciar os neurônios sensoriais do estímulo** (p. ex., os ORNs do odor da fruta; os GRNs de
  açúcar), com os DNs intactos: a mudança nas taxas dos DNs **e** no comportamento precisa sumir. **É
  esta a ablação que mostra que o comportamento vem da rede.**
- **A3, conectoma embaralhado** (controle; proposta opcional): pesos do cérebro permutados preservando
  os graus de entrada e saída de cada neurônio, com o mesmo estímulo. Se a resposta dos DNs se mantiver,
  ela não depende do cabeamento específico. Custo: 1 execução por semente e condição.

## (d) Critérios de sucesso (fixados antes; o que não tem fonte está marcado)

| # | Critério | Números | Origem dos números |
|---|---|---|---|
| C1 | **Interface, avanço:** estimulação direta de DNp09 bilateral a 100 Hz por 2 s | velocidade ≥ 5 mm/s durante o estímulo; < 1 mm/s 0,5 s depois de desligar; 5 de 5 sementes | a velocidade do CPG do FlyGym com δ = 1 é ~14 mm/s (BENCHMARK, Fase 0). O limite de 5 mm/s é **escolha** |
| C2 | **Interface, curva:** DNp09 unilateral (e DNa02, se confirmado) | velocidade angular média ≥ 30°/s, com o sentido previsto pela fonte, em ≥ 4 de 5 sementes | o sentido vem da fonte (DNp09: ipsilateral). 30°/s é **escolha** |
| C3 | **Interface, ré:** MDN bilateral a 100 Hz | deslocamento para trás ≥ 1 mm em 2 s, em ≥ 4 de 5 sementes | o sentido vem da fonte; 1 mm é **escolha** |
| C4 | **Comportamento sensorial, o critério central:** mosca no terrário, com o campo de odor da fruta ligado contra desligado, 10 sementes pareadas, 20 s | (i) a taxa de pelo menos um grupo de DNs difere entre odor e sem odor (Wilcoxon pareado, p < 0,05); (ii) a distância mínima até a fruta é menor com odor (Wilcoxon pareado, p < 0,05) | teste e α são **escolha**. É o critério da SPEC: "mudança de comportamento com estímulo olfativo/gustativo, sem regra programada" |
| C5 | **Ablações:** A2 elimina o efeito de C4 (nem (i) nem (ii) com p < 0,05, com o efeito mediano reduzido em ≥ 50 %); A1 elimina a modulação correspondente | — | 50 % é **escolha** |

C1–C3 validam a interface; eles **não** são comportamento emergente. O resultado da 3b é C4 + C5. Se o
odor não mudar a taxa dos DNs no LIF do Shiu, C4 dá negativo, e esse é um resultado legítimo a relatar.
Os ganhos não são reajustados para "fazer funcionar".

## (e) Prazo, marco e saída
- **Prazo: 4 sessões** (as figuras de diagnóstico de cada sessão não contam).
  - S1: IDs dos DNs e dos sensores na v783; confirmação da ligação DNa02/DNa01 no texto completo de
    Yang et al.; implementação do mapeamento e dos ganhos pelo critério de (b); C1–C3.
  - S2: C4 (odor).
  - S3: C5 (ablações) e, se sobrar prazo, gustação nos tarsos (GRNs → DNs), sem a probóscide (essa é da
    entrega P).
  - S4: relatório e vídeo.
- **Marco na S2:** se **C1–C3 não passarem** com os ganhos fixados, o problema é da interface, não do
  conectoma. É permitida **uma** revisão da ligação, e só com fonte; se falhar de novo, a 3b encerra
  como "interface DN → CPG não validada", com relatório.
- **Saída:**
  - Sucesso (C1–C5): relatório da 3b, vídeo de 10–20 s (WebM) da mosca indo à fruta com odor, e o
    controle com os ORNs silenciados. A mosca entra na Fase 5.
  - C1–C3 passam e C4 dá negativo: relatório com o negativo (o odor não modula os DNs de marcha no
    modelo). A mosca anda no terrário só por estimulação direta, o que **não** é comportamento emergente.
    Pela regra de harmonia da SPEC, o usuário decide se ela fica na cena principal.
- **Custo estimado:** terrário com sensores ~3,4 s/s mais o cérebro ~0,7 s/s (BENCHMARK), ~4–5 s/s
  por processo sozinho. Um episódio de 20 s leva ~1,5 min, e C4 + C5 (≈ 10 sementes × 4 condições) cabe
  em < 1 h com 10 processos.

## Fontes
- Bidaye et al. 2020, *Neuron* 108:469 (P9 = DNp09).
- Bidaye, Machacek, Wu e Dickson 2014, *Science* 344:97 (MDN).
- Yang et al. 2024, *Cell* (DNa02 e outro tipo descendente na curva; o detalhe está a confirmar).
- Sapkal et al. 2024, *Nature* 634:191 (parada).
- Mendes et al. 2013, *eLife* 2:e00231 (frequência × velocidade).
- FlyGym 2.1: `flygym_demo/complex_terrain/{turning_controller,hybrid_controller,cpg_controller,common}.py`;
  o tutorial "turning" (`third_party/flygym-gymnasium/doc/source/tutorials/turning.rst`).

## F. Ajustes da aprovação (2026-09-23, commitados antes de executar)

**F1. A S1 começa com um teste de viabilidade sem corpo** (`experiments/phase3b_viability.py`). Se ele
der negativo, a 3b vai direto ao relatório, **sem construir a interface**.
- Conectoma: FlyWire 783, só o cérebro (`connectomes.load("783")`), com o LIF do Shiu (os parâmetros
  da Fase 1).
- **Odor (modelo, NON-CONNECTOME):** Poisson a **100 Hz** em todos os ORNs dos glomérulos **DM1 e VA2**,
  nos dois lados (135 neurônios: 68 ORN_DM1 e 67 ORN_VA2, pela anotação do FlyWire; todos os root_ids
  existem na v783).
  - Os glomérulos vêm de Semmelhack & Wang 2009 (*Nature*, "Select Drosophila glomeruli mediate innate
    olfactory attraction and aversion"): no vinagre de maçã em concentração baixa, DM1 e VA2 são
    necessários para a atração, e ativar cada um basta. É a referência para odor de fruta fermentada.
  - Os **100 Hz** são **sem fonte**: é a convenção de estímulo do Shiu, dentro da faixa de 10–200 Hz da
    Fase 1.
- Controle: sem estímulo, com a **mesma semente** (pareado). 10 sementes (1000–1009), 1 s por
  execução, como os trials do Shiu.
- Medida: taxa média por célula de cada grupo durante o estímulo:
  - **DNp09** (2 células);
  - **MDN** (4);
  - **DNa01/02** (DNa01 + DNa02, 4 células).
- **Critério (fixado agora):** um grupo **muda** se o Wilcoxon pareado bilateral (odor × controle, 10
  sementes) der p < 0,05/3 (Bonferroni sobre os 3 grupos) **e** a diferença mediana for ≥ 1 Hz.
  - A 3b segue para a interface se **pelo menos um** grupo mudar; se nenhum mudar, relatório.
  - Os limiares de 1 Hz e α = 0,05 são **escolha**.
- Descritivo, que não decide: se a diferença mediana chega a **≥ 10 Hz**. Pelo critério de ganho (100 Hz
  → |δ| = 1), 10 Hz dá |δ| ≈ 0,1, cerca de 1,4 mm/s. Abaixo disso a interface andaria perto de parada,
  e C4(ii) fica improvável.
- Nota: sem estímulo, o LIF do Shiu não tem atividade de fundo, então o controle deve ficar em 0 Hz.

**F2. C4 com grupo principal fixado:** o **DNp09** é o grupo principal de C4(i) (α = 0,05). MDN e
DNa01/02 entram com Bonferroni (α = 0,05/2 cada). C4(ii), a distância até a fruta, não muda.

**F3. Conectoma embaralhado obrigatório (A3 deixa de ser opcional):**
- Pesos do cérebro reorganizados por trocas duplas de arestas (a→b, c→d ⇒ a→d, c→b). Isso preserva o
  grau de saída e de entrada de cada neurônio. O peso e o sinal viajam com a aresta, então o sinal
  continua sendo o do pré-sináptico.
- Número de trocas: 10× o número de arestas. 5 embaralhamentos independentes.
- **Critério em C5:** no conectoma embaralhado, o efeito do odor em C4(i) (DNp09) **e** em C4(ii) precisa
  cair ≥ 50 % (efeito mediano) em relação ao conectoma real. Se não cair, a resposta não depende do
  cabeamento específico, e isso é relatado como tal.

**F4. Registrados no NON_CONNECTOME.md como sem fonte:** o modelo de odor (a taxa de 100 Hz e, na
C4, a relação concentração → taxa), o filtro da taxa dos DNs antes do CPG (τ_r = 100 ms) e os 100 Hz
do critério de ganho.
