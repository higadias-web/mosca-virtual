# Fase 3b, Etapa B: sensibilidade à taxa dos ORNs e homólogos (relatório curto)

**Data:** 2026-09-23/24. Sem corpo, **sem interface, sem vídeo**. Pré-registro em `docs/FASE3B_PLANO.md` §N
(commit 0c2e639, antes de rodar). Fila: 380/380 (`RATES_OK`), análise só com a fila completa.
Figura: `results/phase3b/s1/diagnostico_etapaB.png`. Dados: `results/phase3b/rates.json`, `rates_runs.csv`,
`homologs_weights.json`.

## 1. Fonte para a taxa dos ORNs: encontrada
- Faucher CP, Hilker M, de Bruyne M 2013, *PLoS ONE* 8(2):e56361, "Interactions of Carbon Dioxide and Food
  Odours in *Drosophila*: Olfactory Hedonics and Sensory Neuron Properties".
- Registro de sensila única com vinagre de maçã. Os valores são o **aumento sobre a taxa pré-estímulo**,
  lidos visualmente da Fig. 2C (±3 spikes/s).
- **Condição de referência "vin5":** fêmeas, vinagre a 5 %; ORN_DM1 (ab1A, Or42b) = 42 Hz e ORN_VA2 (ab1B,
  Or92a) = 22 Hz.
- **Escolhas sem fonte que sobram:** a concentração de 5 %, a curva das fêmeas e a leitura da figura.

## 2. Critérios pré-registrados (conectoma real, 10 sementes pareadas)

| Critério | Resultado | Números |
|---|---|---|
| (a) O DNp09 é excitado em alguma taxa | **NÃO** | 0 Hz em 20, 50, 100 Hz e vin5 (p = 1 em todas) |
| (b) O viés do DNa02 esquerdo se mantém em todas as taxas | **SIM** | DNa02 E/D no bilateral: 50/1 (20 Hz), 54,5/0 (vin5), 52,5/0,5 (50 Hz), 55/0 Hz (100 Hz); p = 0,002 em todas (α = 0,0125) |
| (c) Algum DN distingue o lado | **NÃO** | \|Δ ipsi − contra\| ≤ 1,75 Hz, p ≥ 0,29 nos 16 pares tipo × taxa (α = 0,003) |
| (d) Regime de atividade na faixa plausível (**faixa sem fonte**: ≤ 3,1 % de neurônios ativos, 10× o regime validado da Fase 1) | **NÃO, em todas as taxas** | ativos no bilateral: 6,14 % (20 Hz), 6,16 % (vin5), 6,18 % (50 Hz), 6,20 % (100 Hz) |

O MDN fica em 0 Hz em todas as condições. O DNa01 E/D fica em ~17–22,5 / 7,5–9 Hz, sem lado.

## 3. Nível de atividade: real × embaralhados (mediana; bilateral)

| Taxa | Real: spikes em 1 s | Real: % ativos | Embaralhados: spikes | Embaralhados: % ativos |
|---|---|---|---|---|
| 20 Hz | 470.720 | 6,14 | ~2.720 | ~0,12 |
| vin5 (42/22 Hz) | 474.799 | 6,16 | ~4.630 | ~0,17 |
| 50 Hz | 480.194 | 6,18 | ~7.220 | ~0,19 |
| 100 Hz | 492.716 | 6,20 | ~15.600 | ~0,28 |
| sem odor | 0 | 0 | 0 | 0 |

- **No conectoma real, o regime alto não depende da taxa dos ORNs.** Com só ~2.700 spikes de entrada (135
  ORNs a 20 Hz), a rede chega a ~470 mil spikes e ~6,1 % de neurônios ativos, quase o mesmo que a 100 Hz.
  É uma resposta de tudo ou nada, não graduada.
- **Nos embaralhados**, a atividade quase não passa dos próprios ORNs (135 × 20 Hz ≈ 2.700 spikes) e cresce
  com a entrada.
- A limitação da S1, "o caminho pode depender dos 100 Hz", fica respondida **dentro de 20–100 Hz e vin5**:
  o regime e o viés do DNa02 E são os mesmos em todas as taxas, **inclusive na taxa com fonte**. O regime
  continua **fora da faixa declarada**, que não tem fonte.
- **Não testado:** se a atividade se sustenta depois que o estímulo é desligado (autossustentação), nem
  taxas abaixo de 20 Hz, onde a transição para o regime alto poderia aparecer.

## 4. Homólogos e entradas do DNa02 (só grafo e spikes já salvos; odor bilateral a 100 Hz)
- **Os pesos diretos dos homólogos são simétricos**, sem ligação cruzada:
  - PS013 → DNa02 do mesmo lado: 178 (E) e 162 (D);
  - DNae005: 196 e 240;
  - LAL081: 93 e 99.
- **O saldo de entrada ativa (peso × taxa) no DNa02 D é negativo:** E 43,5 mil contra I 57,8 mil. No DNa02 E
  é positivo: E 53,0 mil contra I 36,5 mil.
- **A maior inibição isolada sobre o DNa02 D vem do AOTU019 esquerdo** (GABA, 126 Hz, peso −216,
  contribuição −27,2 mil). O espelho sobre o DNa02 E, o AOTU019 D, é mais fraco (81 Hz, peso −121, −9,8
  mil). Seguem MBON32 E (−6,6 mil) e CB0083 E (−3,2 mil).
- **Leitura, só descritiva:** a assimetria acompanha uma inibição contralateral mais forte vinda do AOTU019
  E (mais taxa e mais peso). **Não houve teste causal** (silenciar o AOTU019 E).

## 5. O que isso implica para a S2
1. **O avanço pelo DNp09 não acontece com odor**, em nenhuma taxa testada, inclusive a com fonte. Com a
   interface aprovada, o odor não faria a mosca andar, e C4(i) no grupo principal daria negativo.
2. **O odor gera um viés fixo e robusto para o DNa02 esquerdo**, que pelo preprint de Yang et al. seria uma
   curva para a esquerda, sem relação com o lado da fonte. Uma interface por esse caminho não levaria a
   mosca à fruta.
3. **O regime de atividade do modelo está fora da faixa declarada (sem fonte) e responde em tudo ou nada.**
   Isso pesa contra usar essas respostas de DNs como base do comportamento sem entender antes o regime. A
   causa não foi investigada: pode ser um ciclo recorrente excitatório no caminho olfativo do LIF do Shiu.
4. Pelos princípios do projeto (o comportamento vem da mosca, o mínimo fora do conectoma), construir a
   interface agora exigiria compensar esses três pontos com engenharia (outro grupo de avanço, correção do
   viés), o que contraria os princípios. **Recomendação: não construir a interface na S2 sem antes decidir
   o que fazer com o regime** (p. ex., testar autossustentação e taxas < 20 Hz, e testar causalmente o
   AOTU019 E). A decisão é do usuário.

## 6. Desvios e ressalvas
- **Tempo:** a fila levou ~30 min, contra a estimativa de 15 min (teto declarado de 25). As taxas baixas não
  custaram menos, porque a rede real entra no mesmo regime alto em todas elas.
- A condição r100 bilateral **não** repete bit a bit a viabilidade (a ordem dos alvos de Poisson mudou), mas
  os números coincidem de perto (DNa02 E 55 contra 52 Hz; ~4,9×10⁵ spikes).
- A faixa de (d) não tem fonte, e a referência (435 ativos) soma 30 trials, o que torna o limite mais
  frouxo; mesmo assim, o real passa dele em ~2×.
