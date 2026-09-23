"""Compara taxas por neurônio entre dois arquivos de contagens (30 trials de 1 s)."""
import sys
import numpy as np

a = np.load(sys.argv[1]) / 30
b = np.load(sys.argv[2]) / 30
act = (a > 0) | (b > 0)
print(f"ativos: {(a>0).sum()} vs {(b>0).sum()} (união {act.sum()})")
print(f"spikes/trial: {a.sum():.0f} vs {b.sum():.0f} ({100*(b.sum()/a.sum()-1):+.1f}%)")
print(f"Pearson r (taxas, ativos): {np.corrcoef(a[act], b[act])[0,1]:.4f}")
# erro-padrão de Poisson da diferença de médias, por neurônio: sqrt((ra+rb)/30)
se = np.sqrt((a + b) / 30)
z = (b - a) / np.where(se > 0, se, 1)
sig = act & (a + b >= 1)
print(f"|z|>3 (diferença > 3 erros-padrão de Poisson): {(np.abs(z[sig])>3).sum()} de {sig.sum()} neurônios com taxa >= 0,5 Hz")
top = np.argsort(-a)[:50]
rel = np.abs(b[top] - a[top]) / a[top]
print(f"top-50: dif. relativa mediana {np.median(rel):.3f}")
