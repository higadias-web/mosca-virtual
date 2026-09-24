# Relatório da Fase 3b, Sessão 1: o odor chega aos DNs de marcha?

**Data:** 2026-09-23. **Sessão:** 1 de 4 do prazo da 3b (`docs/FASE3B_PLANO.md` (e)).
**Escopo:** só o cérebro, sem corpo. **Nenhuma interface DN → CPG foi construída.**
Pré-registros, desvios e números completos em `docs/FASE3B_PLANO.md` §F–§M; ajustes fora do conectoma em
`docs/NON_CONNECTOME.md` (Fase 3b).

## 1. Resumo
- **Viabilidade (§F1): cumprida, e específica (§H, V1).** O odor de fruta fermentada (ORNs de DM1 e VA2)
  ativa o grupo DNa01/02 em 20,75 Hz contra 0 Hz sem odor (10/10 sementes). No conectoma embaralhado
  com graus preservados, o efeito cai para 0 Hz (mediana de 5 embaralhamentos), então depende do
  cabeamento específico.
- **O grupo principal da C4, o DNp09, não é excitado pelo odor** (0 Hz), e o MDN também não. Na
  interface aprovada, o avanço vem só do DNp09, então o odor sozinho **não faria a mosca andar**.
- **Nenhum DN carrega o lado do odor (§H, V2).** A resposta é assimétrica e **fixa**: o DNa02 esquerdo
  fica em ~52 Hz e o direito em ~0,5 Hz, qualquer que seja o lado estimulado. Pelo preprint de Yang et al.
  (DNa02 unilateral → curva ipsilateral), isso preveria uma curva fixa para a esquerda da mosca, sem
  relação com a posição da fonte.
- **Origem da ativação do DNa02 esquerdo (§K–§L):** as três entradas principais do nível 1, PS013 E,
  DNae005 E e LAL081 E, silenciadas juntas, derrubam a taxa em 75 % (5/5 sementes, critério
  pré-registrado). A contribuição isolada de DNae005 e de LAL081 não foi medida. Os homólogos direitos
  estão ativos, e mesmo assim o DNa02 direito fica calado (§M); a causa da assimetria segue aberta.

## 2. O que foi feito (tudo pré-registrado em commit antes de rodar)

| Teste | Commit do pré-registro | Execuções | Resultado |
|---|---|---|---|
| Viabilidade: odor × controle, 3 grupos de DNs | 88254dd | 20 | DNa01/02 muda; DNp09 e MDN não |
| Lateralidade e especificidade: 4 condições × conectoma real + 5 embaralhados | 8398aac | 240 (`LAT_OK` 240/240) | V1 passa; V2: nenhum tipo carrega lado |
| Conectividade direta e de 2 saltos (só grafo) | — (pedido da revisão; sem simulação) | 0 | nada chega às cópias esquerdas; só caminhos mínimos até o DNa02 D |
| Recuo por atividade a partir do DNa02 E + silenciamento cumulativo | c41fbba | 5 + 15 (`ODOR_OK`, `SIL_OK`) | só as três entradas juntas passam o critério |
| Homólogos direitos e nível de atividade (spikes já salvos) | — (sem simulação) | 0 | homólogos D ativos; 6,2 % dos neurônios ativos |

Modelo: FlyWire 783 (só cérebro) e LIF de Shiu et al. 2024, com os parâmetros validados na Fase 1.
Odor = Poisson a 100 Hz nos ORNs de DM1 e VA2. 1 s por execução.

## 3. Resultados

### 3.1 Viabilidade e especificidade

| Grupo | Odor (mediana) | Controle | Wilcoxon p (α = 0,0167) | Muda |
|---|---|---|---|---|
| DNp09 (2 células) | 0 Hz | 0 Hz | 1 | não |
| MDN (4) | 0 Hz | 0 Hz | 1 | não |
| DNa01/02 (4) | 20,75 Hz | 0 Hz | 0,002 | **sim** |

Especificidade (V1): 20,75 Hz no real contra 0; 0,5; 0; 0; 0 Hz nos 5 embaralhados → **passa**
(limite de ≤ 50 %).

### 3.2 Lateralidade (V2)
ORNs estimulados: só esquerda = 69 (35 DM1 + 34 VA2); só direita = 66 (33 + 33); simétrico = 135.

| Célula | Controle | Simétrico | Só esquerda | Só direita |
|---|---|---|---|---|
| DNa02 E / D | 0 / 0 | 52 / 0,5 | 53 / 0,5 | 51,5 / 0 |
| DNa01 E / D | 0 / 0 | 21 / 8 | 19,5 / 9 | 18 / 6 |

A diferença ipsilateral − contralateral fica ≤ 1 Hz em todos os tipos (p ≥ 0,47). DNp09 e MDN ficam
em 0 Hz em todas as condições.

### 3.3 Conectividade (grafo, até 2 saltos)
- Nenhuma sinapse direta de ORNs ou PNs de DM1/VA2 em DNa01 ou DNa02.
- Em 2 saltos, nada chega às cópias esquerdas nem ao DNa01 direito. O DNa02 direito recebe caminhos
  mínimos (saldo de −5 a +7, em produtos de contagens de sinapses).
- Nos caminhos curtos, a assimetria vai no **sentido oposto** ao da simulação. A ativação do DNa02 E
  passa por caminhos mais longos.

### 3.4 Recuo por atividade e silenciamento

| Silenciados (cumulativo, ordem pré-registrada) | DNa02 E | Queda mediana | Sementes ≥ 50 % | Passa |
|---|---|---|---|---|
| nenhum | 51 Hz | — | — | — |
| PS013 E | 35 Hz | 31 % | 0/5 | não |
| + DNae005 E | 28 Hz | 45 % | 1/5 | não |
| + LAL081 E | 13 Hz | 75 % | 5/5 | **sim** |

- **As três juntas passam o critério; a contribuição isolada de DNae005 e LAL081 não foi medida.**
- A queda mede a **contribuição total numa rede recorrente**, não só a sinapse direta no DNa02 E.
- Mais acima na árvore aparecem MBONs, SMP177, CRE011 e LHPV10b1, dos dois lados, a 110–240 Hz.

### 3.5 Homólogos direitos e nível de atividade
- Com odor bilateral: PS013 E/D 46/19 Hz, DNae005 E/D 19/17 Hz, LAL081 E/D 40/45 Hz. **Os homólogos
  direitos estão ativos**, e o DNa02 D fica em 0–2 Hz.
- Conectoma real: ~4,92×10⁵ spikes em 1 s, **6,2 % dos neurônios ativos**, ~57 Hz em média entre os
  ativos.
- A mesma medida nos embaralhados **não está disponível**, porque os spikes de todos os neurônios não
  foram salvos.

## 4. Fontes verificadas e não verificadas

| Ligação ou convenção | Estado | Fonte e trecho |
|---|---|---|
| DM1 e VA2 mediam a atração ao vinagre | verificada | Semmelhack & Wang 2009, *Nature*: DM1 e VA2 necessários; ativar cada um basta |
| DNa02 unilateral → curva ipsilateral; encurta o passo do lado de dentro | verificada (**preprint**) | Yang, Brezovec, Serratosa Capdevila, Vanderbeck, Adachi, Mann e Wilson, bioRxiv v2 (30/10/2023), PMC10614758, Fig. 4A e 4G. A versão da *Cell* 2024 não foi lida |
| Sentido do DNa01 | **não verificado** | Rayshubskiy, Holtz, Bates, Vanderbeck, Serratosa Capdevila, Rockwell e Wilson, *eLife* 2025 (10.7554/eLife.102230): só a correlação com a diferença D − E das taxas, sem a convenção de sinal no trecho lido |
| `side = left` é o lado esquerdo da mosca | verificada | documentação do `fafbseg` ("the official `side` labels … are biologically correct"), com base em Schlegel P, Yin Y, Bates AS, Dorkenwald S, … Jefferis GSXE, "Whole-brain annotation and multi-connectome cell typing of Drosophila", *Nature* 634:139–152 (2024) |
| `side` nos ORNs = lado de entrada do nervo | verificada | README de `flywire_annotations` (commit 8587524, versão ≥ 3.1.0, materialização 783) |
| DNp09 inicia a marcha para a frente; MDN, a ré | verificada | Bidaye et al. 2020, *Neuron*; Bidaye, Machacek, Wu e Dickson 2014, *Science* |

## 5. Ajustes fora do conectoma usados na S1
B-odor (modelo de odor: taxa de 100 Hz sem fonte), B-10Hz (limiar descritivo sem fonte, retirado da
conclusão), B-lat (2 Hz de diferença mínima, sem fonte), B-shuf (controle embaralhado) e S (estímulo de
Poisson). Os itens da interface (B-filtro, B-ganho, B-mag, B-cpg) estão registrados, mas **não foram
usados**, porque a interface não foi construída.

## 6. Limitações
- **Regime de atividade muito alto:** com os ORNs a 100 Hz (sem fonte), ~6 % dos neurônios disparam a
  ~57 Hz em média. **O caminho identificado pode depender desse regime.**
- **A ausência de lado pode vir do modelo de estímulo:** taxa uniforme nos ORNs de um lado, sem
  gradiente entre as antenas nem diferença de tempo, e sinapses tratadas só pela contagem.
- **A inibição não é detectável:** sem atividade espontânea, DNp09, MDN e as cópias caladas ficam em 0
  Hz também sem odor.
- **O silenciamento cumulativo não separa a contribuição de DNae005 e de LAL081.**
- **Ablação em rede recorrente:** a queda inclui efeitos indiretos.

## 7. Pendências (não executadas)
- Sensibilidade à taxa dos ORNs (p. ex., 25–200 Hz).
- Nível de atividade (total de spikes e fração ativa) nos 5 embaralhados, que exige simulação nova com
  os spikes salvos.
- A causa da assimetria: por que o DNa02 D fica calado com os homólogos direitos ativos.
- Contribuição isolada de DNae005 E e de LAL081 E.

## 8. Implicações para a S2 (decisão do usuário)
Com a interface como aprovada, o odor produziria só um viés fixo de curva para a esquerda, sem avanço, e
o critério C4(i) no grupo principal (DNp09) daria negativo. Qualquer mudança na interface depois destes
resultados (p. ex., outro grupo de avanço) precisa de fonte nova e fica declarada como decisão posterior
ao resultado. Nada foi construído.

## 9. Arquivos
- Resultados: `results/phase3b/{viability,laterality,connectivity,backtrace_tree,backtrace_silence,homologs_activity}.json`
  e CSVs; figura `results/phase3b/s1/diagnostico_s1.png`.
- Brutos (fora do git): `runs/phase3b/` (`laterality_runs.csv`, `backtrace/*.npz`).
- Scripts: `experiments/phase3b_{viability,laterality,connectivity,backtrace,s1_figs}.py`; embaralhamento
  em `terrario/brain/shuffle.py`.
