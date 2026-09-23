# Plano da Fase 3: malha fechada da mosca adulta (2026-09-23; aguarda aprovação)

Decisões que valem aqui: **D-105 = (c)**, com o cérebro do FlyWire 783 (validado na Fase 1) e o
cordão do BANC v888 (`terrario/brain/hybrid.py`). **D-106**: Fase 3 dividida em 3a (bolinha) e
3b (terrário).
- **Prazo da 3a:** 6 sessões de trabalho ou 2 semanas a partir do início da 3a, o que vier primeiro.
- **Marco na 3ª sessão:** se nenhum estímulo de DN gerar atividade rítmica nos MNs de perna com o
  loop proprioceptivo fechado, a 3a é encerrada, o resultado negativo é documentado e a 3b segue
  com o controlador da opção (a).

## 1. Ponto de partida: sem ritmo em malha aberta

A sonda da D-105 (`results/d105/probe_*.json`) estimulou o par de DNp09 ou de DNa02 a 50–200 Hz,
por 1 s, sem corpo. Resultado: ≤ 7 dos 391 MNs de perna ativos, taxa ≤ 0,2 Hz, sem ritmo. Com o
VNC × 2: 49–63 MNs, 0,4–2,4 Hz, ainda tônico.

Achado novo, que entra como hipótese: **o BANC prevê GABA para 260 dos 391 MNs de perna**, 81
como acetilcolina e só 11 como glutamato. Os MNs de perna de *Drosophila* são glutamatérgicos
na junção neuromuscular. Nenhum dos 391 tem transmissor verificado nos metadados
(`neurotransmitter_verified` vazio). Com a regra do Shiu, as saídas centrais desses MNs viram
inibitórias por dois caminhos (GABA ou glutamato), mas a previsão errada é um sinal de que as
previsões de transmissor no VNC merecem desconfiança (H6).

## 2. Hipóteses para a falta de ritmo e como testar cada uma

**Métrica de ritmo** (fixada antes de testar, `experiments/phase3a_rhythm.py`):
- taxa populacional dos MNs de cada perna em janelas de 5 ms, durante ≥ 1 s de estímulo;
- **ritmo** = pico espectral numa banda de passada. A banda será tirada da literatura na sessão 1,
  antes de qualquer teste, e fica provisoriamente em 2–25 Hz, larga de propósito;
- o pico precisa superar o 99º percentil de 200 surrogados (deslocamentos circulares
  independentes dos trens de spike de cada MN), em pelo menos uma perna.
- Complemento: antifase entre MNs de flexor e extensor do mesmo segmento, pelos músculos-alvo
  anotados no BANC (`peripheral_target_type`, p. ex. `tibia_flexor_muscle`).

Cada hipótese traz o teste, o que conta como confirmação e em que é NON-CONNECTOME.

| # | Hipótese | Teste | Confirma se… |
|---|---|---|---|
| **H1** | **Propriocepção ausente.** Em insetos, o ritmo de marcha depende da realimentação dos sensores das pernas (cordotonais, campaniformes, placas de pelos). Sem ela, o VNC não alterna. | (i) **Aferência imposta**: pernas movidas pela cinemática de marcha gravada que vem com o FlyGym (`flygym_demo.spotlight_data.MotionSnippet`), gerando entrada nos proprioceptores do BANC, com ou sem DN estimulado. (ii) **Loop fechado**: MNs → juntas → proprioceptores → VNC, na bolinha. | há ritmo nos MNs com a aferência imposta (i), ou com o loop fechado (ii) e não em malha aberta |
| **H2** | **Estímulo insuficiente.** Um par de DNs não basta; a marcha real recruta populações de DNs. | Estimular grupos crescentes: DNp09; + DNa01/DNa02; os DNs mais ligados a MNs de perna (influência calculada no conectoma); todos os DNs de um cluster funcional do BANC (`banc_neck_functional_classes`). Taxas de 50–300 Hz. | o recrutamento de MNs cresce com a população e aparece ritmo |
| **H3** | **Sinapses subcontadas no BANC.** O BANC tem ~0,5× as sinapses do FlyWire por par de neurônios (captura pós-sináptica ~0,2), e o `w_syn` do Shiu foi calibrado no FlyWire. | Varrer `vnc_scale` (1; 1,5; 2; 2,5; 3) só nas arestas do VNC, com o cérebro intacto; checar que a Fig. 1D não muda e que não surge atividade autossustentada sem estímulo. | há uma faixa de escala com ritmo e sem descontrole; ou só descontrole (negativo) |
| **H4** | **Parâmetros do LIF calibrados para o cérebro.** O `w_syn` do Shiu foi ajustado no cérebro, e muitos interneurônios locais do VNC de insetos são não disparadores (graduados). O LIF não os representa. | (i) Limiar e constante de membrana só no VNC, dentro das faixas publicadas; (ii) interneurônios locais inibitórios do VNC como graduados (o modelo de taxa já previsto para as minhocas, D-102), só se (i) falhar. | o ritmo aparece com parâmetros dentro das faixas medidas |
| **H5** | **Falta de modulação / estado.** In vivo, o VNC recebe tônus descendente e octopamina (há 30 neurônios octopaminérgicos intrínsecos no VNC do BANC). O modelo do Shiu não tem atividade de fundo. | Entrada tônica de Poisson de baixa taxa (i) nos DNs em geral ou (ii) nos neurônios octopaminérgicos e seus alvos, com o DN de marcha por cima. | o ritmo depende do tônus: some sem ele e aparece com ele |
| **H6** | **Sinais errados no VNC.** Previsão de transmissor duvidosa nos MNs (GABA em 260 de 391); glutamato tratado sempre como inibitório; 197 discordâncias de sinal nas pontes. | (i) Refazer com os sinais das previsões do MANC para os tipos casados (`banc_manc_reviewed_matches`); (ii) MNs como glutamatérgicos; (iii) sensibilidade: inverter o sinal de classes inteiras (nunca neurônio a neurônio). | o ritmo aparece ao corrigir sinais com base documentada |
| **H7** | **Costura entre animais.** DNs pareados por tipo (87 %), sinapses ponte→ponte descartadas. | Mesmo teste no BANC puro (cordão e DNs do mesmo animal), estimulando os DNs direto, e no híbrido com as sinapses ponte→ponte incluídas via `synapse_neuropil_lookup_v2` (2,2 GB). | o BANC puro tem ritmo e o híbrido não |
| **H8** | **Falta de propriedades intrínsecas** (rebote pós-inibitório, platôs, adaptação), que os osciladores de meio-centro usam. | Só se H1–H7 falharem: adaptação e rebote nos interneurônios do VNC (NON-CONNECTOME explícito). | o ritmo aparece só com a propriedade intrínseca |

H1, H2 e H3 são as mais prováveis e as mais baratas. H8 é a última porque é a que mais adiciona
engenharia ao modelo.

## 3. Ordem de trabalho da 3a (por sessão)

| Sessão | Construção | Testes | Saída |
|---|---|---|---|
| 1 | Aparato: `TetheredWorld` + bola livre (massa e inércia de bola sustentada por ar, da literatura); MNs de perna → músculo-alvo (BANC) → junta do NeuroMechFly (mapa documentado por músculo); transdução proprioceptiva: cordotonais (posição/direção pelo `cell_function_detailed`), placas de pelos (ângulo), campaniformes (carga); banda de ritmo tirada da literatura | métrica de ritmo validada num controle positivo sintético; **H2** em malha aberta | aparato + métrica; tabela de H2 |
| 2 | Loop fechado corpo ↔ híbrido | **H1** (aferência imposta e loop fechado); **H3** | ritmo? (sim/não por teste) |
| 3 | — | **H5**, **H6**, **H7**; combinações das que mostraram efeito. **Marco:** algum estímulo de DN produz ritmo nos MNs com o loop fechado? | **se não:** encerrar a 3a, escrever `docs/FASE3A_RELATORIO.md` (negativo, com todas as hipóteses) e seguir para a 3b com (a) |
| 4–6 | (só se o marco passou) | alternância flexor/extensor, coordenação entre pernas, bola para a frente com DNp09, virada com DNa02, ablação (silenciar DNs e propriocepção), **H4/H8** só se o ritmo for fraco; custo em s/s | relatório da 3a; se os critérios de marcha não fecharem na 6ª sessão, 3b com (a) |

Cada sessão termina com uma linha no registro abaixo (prazo) e com o resultado em `results/phase3a/`.

## 4. Juntas da probóscide (MN9 → alimentação): proposta de subfase

**O que existe:** o FlyGym 2.1 já define as juntas `c_head–c_rostrum` e `c_rostrum–c_haustellum`
(3 graus de liberdade cada, `JointPreset.ALL_BIOLOGICAL`, `flygym/anatomy.py`). O corpo de
locomoção padrão só não as inclui. Os MNs da probóscide estão no cérebro, que nesta opção é o
FlyWire; o MN9 está validado na Fase 1. O BANC anota o músculo-alvo de 13 tipos de MN da
probóscide (MN1–MN9 → músculos m1–m9, etc.), o que ajuda a mapear MN → músculo → junta
(NON-CONNECTOME; a anatomia muscular será tirada da literatura, p. ex. Schwarz et al. 2017,
*eLife*, "Motor control of Drosophila feeding behavior", a confirmar).

**Proposta: primeira etapa da 3b (3b.1), antes de soltar a mosca no terrário.**
- **3b.1, extensão da probóscide na mosca presa** (reaproveita o aparato da 3a): açúcar no labelo
  ou nos tarsos → GRNs (IDs da v783) → MN9 e demais MNs → juntas pitch do rostro e do haustelo.
  Critérios: extensão com açúcar, com limiar e saturação coerentes com a Fig. 1D; supressão por
  amargo (análogo à Fig. 3A); silenciar o MN9 elimina a extensão; consumo só quando o labelo
  toca o alimento com a probóscide estendida (acoplamento físico, SPEC).
- **3b.2, mosca livre no terrário**: marcha (VNC, se a 3a passou, senão o controlador (a)) +
  olfato, gustação e mecanossensação da Fase 2 → neurônios sensoriais da v783 + probóscide.

Por que não na 3a: a probóscide não depende do cordão nem da pergunta da 3a, e colocá-la lá
consumiria o prazo das 6 sessões. Por que não no fim da 3b: a extensão é o comportamento
alimentar central da SPEC e é validável isolada, na mosca presa, como no experimento clássico.
Alternativa, se preferir: fazê-la em paralelo na 3a, fora da contagem do prazo.

## 5. NON-CONNECTOME previsto na Fase 3
Bola e aparato; mapa MN → músculo → torque (pernas e probóscide); transdução proprioceptiva e
gustativa/olfativa → taxas de Poisson; `vnc_scale` e qualquer parâmetro testado em H3–H8; o
controlador (a), se usado. Tudo entra em `docs/NON_CONNECTOME.md` quando for implementado.

## 6. Registro de sessões da 3a (prazo: 6 sessões ou 2 semanas)

| Sessão | Data | Feito | Hipóteses testadas | Ritmo? |
|---|---|---|---|---|
| — | — | (a 3a ainda não começou; aguarda aprovação deste plano) | — | — |
