#!/usr/bin/env bash
# Fila noturna da Fase 1 (2026-09-22). Log: runs/phase1/overnight.log
set -u
cd "$(dirname "$0")/.."
LOG=runs/phase1/overnight.log
mkdir -p runs/phase1
busctl set-property org.freedesktop.UPower.PowerProfiles /org/freedesktop/UPower/PowerProfiles \
    org.freedesktop.UPower.PowerProfiles ActiveProfile s performance
log() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }
run() { log "INÍCIO $*"; uv run python -m experiments.shiu_repro "$@" >>"$LOG" 2>&1; log "FIM ($?) $*"; }
cmp() { uv run python -m experiments.compare_shiu "$@" >>"$LOG" 2>&1; }

# 1. espera a Fig. 3A que já está rodando
while pgrep -f "experiments.shiu_repro fig3a" >/dev/null; do sleep 30; done
cmp fig3a
# 2. D-003: Fig. 1D na v783 (a comparação com a v630 é feita no relatório)
run fig1d --version 783 --workers 10
# 3. Fig. 1E completa (8 frequências), uma frequência por arquivo
for f in 25 50 75 100 125 150 175 200; do run fig1e --version 630 --workers 10 --freqs $f; done
cmp fig1e
# 4. Fig. 1F completa (8 frequências), uma frequência por arquivo
for f in 50 60 70 80 90 100 110 120; do run fig1f --version 630 --workers 10 --freqs $f; done
cmp fig1f
log "FILA CONCLUÍDA"
