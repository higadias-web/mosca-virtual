# Auditoria do Terrário Virtual (2026-09-25)

Teste feito na auditoria, com o motor do próprio projeto (`terrario/brain/lif.py`, ShiuLIF, FlyWire 783,
parâmetros da Fase 1). Rodar da raiz do projeto `terrario-virtual`.

**Pergunta:** sem odor, com só uma atividade espontânea baixa em todos os 2.275 ORNs, o modelo entra no
estado alto e persistente da Etapa C?

**Taxas:** varredura de 0,5 a 5 Hz, sem fonte. É um teste de sensibilidade, não um valor fisiológico.

**Sanidade:** vin5, semente 1000 → 474.799 spikes, idêntico ao `rates_runs.csv` da Etapa B.

| Condição (sem odor) | Neurônios ativos | PN de DM1 (mediana) | KCs ativas | Média dos ALPNs |
|---|---|---|---|---|
| Referência: vin5 (odor) | 6,1 % | 252 Hz | 65 % | 83 Hz |
| ORNs a 0,5 Hz | 6,6 % | 209–218 Hz | 65 % | 78–80 Hz |
| ORNs a 1 Hz | 6,9 % | 222–223 Hz | 65 % | 81–82 Hz |
| ORNs a 2 Hz | 7,3 % | 223–227 Hz | 65 % | 82–83 Hz |
| ORNs a 5 Hz | 7,5 % | 227–228 Hz | 66 % | 84 Hz |

3 sementes por taxa (1000–1002), 1 s cada. Dados brutos em `teste_espontanea_resultado.jsonl`.

**Conclusão:** qualquer entrada espontânea nos ORNs, a partir de 0,5 Hz, liga o mesmo estado que o odor.
O controle "sem odor = 0 spikes" das Etapas B a D só existe porque o modelo tem basal 0.
