# Relatório da Fase 1: reprodução de Shiu et al. 2024 (2026-09-23)

Objetivo (SPEC, Fase 1): reproduzir, de forma isolada, um resultado do Shiu et al. 2024
(ativação de GRNs de açúcar prevendo a atividade ligada à alimentação), comparando
**numericamente** com o artigo.

**Resultado: reproduzido.** Quatro experimentos das Figs. 1 e 3, **3.340 condições × 30 trials
= 100.200 simulações de 1 s** do cérebro inteiro (v630), comparados com as saídas publicadas pelos
autores. Não houve discrepância sistemática em nenhum deles.

## 1. O que foi construído

| Arquivo | Conteúdo |
|---|---|
| `terrario/brain/flywire.py` | carregador do conectoma (v630/v783) no formato de `model.py:create_model`, com cache CSR (RAM por processo: ~3 GB → ~0,2 GB) |
| `terrario/brain/lif.py` | motor LIF de produção (`ShiuLIF`): integra só o conjunto ativo (exato), N grupos de Poisson com taxa por neurônio, silenciamento, `get_state`/`set_state` para checkpoints |
| `tests/test_lif.py` | 5 testes (ver §2) |
| `experiments/shiu_repro.py` | experimentos das Figs. 1D/1E/1F/3A, com os mesmos parâmetros do `figures.ipynb`, trials em paralelo e sementes determinísticas |
| `experiments/compare_shiu.py` | comparação estatística com os resultados publicados |
| `experiments/overnight_phase1.sh` | fila noturna (checkpoint por frequência) |
| `tools/remote_zip.py` | extrai arquivos do `results.zip` publicado (4,5 GB) por HTTP Range, sem baixá-lo inteiro |

Resultados publicados usados como referência: `results.zip` do Edmond (doi:10.17617/3.CZODIW),
só os CSVs processados das Figs. 1 e 3 (em `data/shiu_published/`, fora do git).

## 2. Testes

`uv run pytest`: **5 de 5 passam.**
- `test_matches_brian2_deterministic[sem/com silêncio]`: numa rede aleatória com pesos excitatórios e
  inibitórios, com Poisson a 1/dt (um evento por passo, portanto determinístico), os spikes do
  `ShiuLIF` são **idênticos, spike a spike,** aos do Brian2 2.10.1, montado com o mesmo código de `model.py`.
  Isso cobre também a semântica de descarte de entradas durante o refratário.
- `test_active_equals_dense`: conjunto ativo = integração densa (v783, estímulo de açúcar).
- `test_checkpoint_roundtrip`: salvar e restaurar o estado reproduz os mesmos spikes.
- `test_silence_blocks_output`: um neurônio silenciado não transmite.

## 3. Comparação com o artigo (v630)

Método: para cada (condição, neurônio), z = (r_nosso − r_pub) / √((dp_pub² + dp_nosso²)/30).
Se as duas implementações amostram o mesmo modelo, espera-se |z| > 3 em ~0,27 % dos pares.
Os pares com r_pub + r_nosso < 1 Hz ficam fora da contagem de |z|, mas entram na correlação.
Todos os números estão em `results/phase1/*_compare.json`.

| Experimento | Condições | Pares | r de Pearson | Taxa total | \|z\|>3 (esperado) | \|z\|>4 |
|---|---|---|---|---|---|---|
| **1D** açúcar 10–200 Hz → todos os neurônios | 20 | 9.746 | 0,99975 | +0,14 % | 24 de 6.195 = 0,39 % (~17) | 1 |
| **1E** ativação de cada um do top-200 → MN9 | 1.600 | 1.600 | 0,99955 | +0,22 % | 4 de 322 (~0,9) | 0 |
| **1F** açúcar + silenciamento de cada um do top-200 → MN9 | 1.600 | 1.600 | 0,99720 | +0,07 % | 8 de 1.600 (~4,3) | 0 |
| **3A** açúcar × amargo → MN9 | 120 | 120 | 0,99951 | −0,10 % | 1 de 72 (~0,2) | 0 |

Detalhes:
- **Fig. 1D.** O **top-200 coincide em 200 de 200**. Esse top-200 define as 3.200 condições das
  Figs. 1E/1F. Com 200 Hz de açúcar: 455 (pub) contra 448 (nosso) neurônios ativos.
  Os 24 casos com |z| > 3 envolvem 24 neurônios diferentes, com sinais mistos (14+/10−).
- **Curva do MN9** (Fig. 1D, Hz; publicado → nosso): 40 Hz 4,8 → 5,7 · 50 Hz 19,4 → 17,7 ·
  60 Hz 36,4 → 37,1 · 100 Hz 65,7 → 66,8 · 150 Hz 83,7 → 84,7 · 200 Hz 93,2 → 92,5.
- **Fig. 3A** (MN9, Hz; publicado → nosso): açúcar 100 Hz com amargo 0/40/100/200 Hz =
  67,0 → 67,1 · 45,3 → 46,3 · 4,0 → 4,3 · 0,0 → 0,1. Açúcar 200 Hz: 94,9 → 92,2 ·
  80,1 → 81,5 · 55,2 → 57,3 · 11,2 → 11,4. A supressão pelo amargo foi reproduzida.
  A 121ª condição (0 × 0 Hz) não tem nenhum spike, e por isso não aparece em nenhum dos dois conjuntos.
- **Fig. 1E.** A condição z = −3,35 (200 Hz no neurônio …630579574: 68,5 → 65,0) é a única com
  taxa alta. As outras 3 estão abaixo de 15 Hz.

### Os 8 casos com |z| > 3 da Fig. 1F

| Neurônio silenciado | Açúcar | MN9 publicado | MN9 nosso | z |
|---|---|---|---|---|
| 720575940620335269 | 110 Hz | 68,77 | 72,50 | +3,63 |
| 720575940625102692 | 110 Hz | 73,77 | 70,30 | −3,54 |
| 720575940625047484 | 80 Hz | 59,10 | 63,00 | +3,52 |
| 720575940628598121 | 70 Hz | 47,00 | 50,67 | +3,44 |
| 720575940610677828 | 120 Hz | 77,83 | 74,97 | −3,19 |
| 720575940621586854 | 50 Hz | 21,83 | 16,47 | −3,15 |
| 720575940625045180 | 110 Hz | 69,63 | 73,50 | +3,12 |
| 720575940622612749 | 60 Hz | 35,63 | 40,63 | +3,06 |

**Esses casos se concentram em algum neurônio? Não.**
- São **8 neurônios diferentes** em 7 frequências, com sinais mistos (5+/3−).
- Cada um passa de |z| > 3 em **só 1 das 8 frequências**; nas outras 7, fica em |z| ≤ 2,6.
- O z combinado de cada neurônio nas 8 frequências (Stouffer) fica entre −1,86 e +1,95 para os 8.
  No conjunto dos 200 neurônios, o maior |Z| combinado é 3,07, num neurônio que não está
  entre os 8. Com 200 testes, isso é compatível com o acaso (esperado: 0,54 casos).
- Excesso global: 8 observados contra 4,3 esperados, P(X ≥ 8) = 0,07 sob Poisson. O desvio-padrão
  de todos os 1.600 z é 1,023 (média 0,027), ou seja, só um pouco mais largo que a gaussiana,
  como é de esperar com contagens de Poisson.
- Nenhum desses 8 silenciamentos muda muito o MN9 **no próprio publicado** (±3 Hz em relação
  ao açúcar sem silêncio). Não são os neurônios que a Fig. 1F destaca como necessários.

Conclusão: flutuação estatística, sem sinal de diferença de semântica em nenhum neurônio.

## 4. Confirmação na v783 (D-003)

Fig. 1D refeita na v783. Nela existem 20 dos 21 GRNs de açúcar; o ID 720575940620900446 não existe.

| Açúcar | 30 | 40 | 50 | 60 | 80 | 100 | 150 | 200 Hz |
|---|---|---|---|---|---|---|---|---|
| MN9 v630 (nosso) | 0,4 | 5,7 | 17,7 | 37,1 | 56,2 | 66,8 | 84,7 | 92,5 |
| MN9 v783 (nosso) | 0,0 | 3,5 | 12,2 | 28,5 | 50,5 | 62,2 | 79,2 | 89,9 |

A resposta alimentar se mantém na v783: mesmo limiar (~40 Hz) e mesma saturação. O MN9 fica
sistematicamente 3–9 Hz abaixo, coerente com um GRN a menos no estímulo. Com 200 Hz: 446
neurônios ativos (contra 448); top-200 com 182 IDs em comum e 108 de 119 tipos celulares em comum.
**Portanto a v783 pode ser usada no terrário (D-003).** Detalhe para a Fase 3: os IDs dos
neurônios sensoriais precisam ser obtidos das anotações da v783, e não herdados da lista do artigo.

## 5. Custo

A fila noturna (23:39 → 06:02) levou ~6,4 h no perfil Desempenho, com 10 processos (2 núcleos P + 8 E):
1D v783 3,8 min · 1E ~76 min · 1F ~5,1 h. Antes da fila: 1D 4,9 min e 3A (~30–40 min; o início não foi registrado). Não houve falhas nem retomadas
(log em `results/phase1/overnight.log`).

## 6. Problemas encontrados e corrigidos na própria fase
- **Viés no script de comparação** (corrigido antes deste relatório): as condições eram listadas depois
  de filtrar as linhas do MN9, e as condições em que o nosso MN9 ficou em 0 Hz eram descartadas.
  Na primeira rodada, a Fig. 1E comparou só 368 das 1.600 condições, e a Fig. 3A, 86 de 120.
  Com a correção, todas entram, e os números da tabela já são os corrigidos.
- Os pickles publicados foram gerados com pandas < 2 (`Int64Index`). Um unpickler de compatibilidade
  mapeia essa classe para `pd.Index` (`experiments/shiu_repro.py:load_pub_pickle`).
- A espera em segundo plano pelo fim da fila usou `pgrep -f "overnight_phase1.sh"`, que casa com a
  própria linha de comando da espera, e por isso ela nunca terminou. O cuidado ficou registrado no CLAUDE.md.

## 7. Critério de validação da SPEC
> "Resultados reproduzidos comparados numericamente com o artigo do Shiu."

Atendido nas Figs. 1D, 1E, 1F e 3A (v630), com correlação ≥ 0,997, taxa total dentro de ±0,3 %,
sem viés sistemático e com resíduos compatíveis com ruído de Poisson. Também confirmado
qualitativamente na v783.

## 8. Próximo passo (aguarda aprovação)
Fase 2: FlyGym na arena do terrário, com os sensores gerando dados.
