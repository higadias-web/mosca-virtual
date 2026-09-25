#!/usr/bin/env bash
# Recria o ambiente do Terrário Virtual do zero (idempotente).
# Pré-requisito: pacotes de sistema de docs/SETUP_FEDORA.md (este script NÃO usa sudo).
set -euo pipefail

cd "$(dirname "$0")"
ROOT="$PWD"

# ---------------------------------------------------------------- 1. dependências de sistema
missing=()
for pkg in gcc gcc-c++ make uv git-lfs mesa-libEGL-devel libglvnd-devel; do
    rpm -q "$pkg" >/dev/null 2>&1 || missing+=("$pkg")
done
if ((${#missing[@]})); then
    echo "Faltam pacotes de sistema: ${missing[*]}"
    echo "Instale com (pede senha):"
    echo "  sudo dnf install -y ${missing[*]}"
    exit 1
fi

# ---------------------------------------------------------------- 2. Python isolado (uv)
# A versão vem de .python-version (3.13, ver docs/DECISIONS.md). Nunca usa o Python do sistema.
uv python install "$(cat .python-version)"
uv sync --frozen

# ---------------------------------------------------------------- 3. repositórios de referência
# Versões fixadas por commit (ver docs/DECISIONS.md, D-007). Só leitura e dados.
mkdir -p third_party
clone_at() {  # clone_at <url> <dir> <commit>
    local url=$1 dir=third_party/$2 rev=$3
    if [[ ! -d $dir/.git ]]; then
        git clone -q --filter=blob:none "$url" "$dir"
    fi
    if [[ $(git -C "$dir" rev-parse HEAD) != "$rev"* ]]; then
        git -C "$dir" fetch -q --depth 1 origin "$rev" 2>/dev/null || git -C "$dir" fetch -q origin
        git -C "$dir" checkout -q "$rev"
    fi
}
clone_at https://github.com/philshiu/Drosophila_brain_model.git Drosophila_brain_model 91bdd1e
clone_at https://github.com/NeLy-EPFL/flygym.git                flygym                 38c8ec6
clone_at https://github.com/NeLy-EPFL/flygym-gymnasium.git      flygym-gymnasium       d285260
clone_at https://github.com/flyconnectome/flywire_annotations.git flywire_annotations  8587524
clone_at https://github.com/openworm/c302.git                   c302                   6cd861f
clone_at https://github.com/openworm/ConnectomeToolbox.git      ConnectomeToolbox      b9c0b4a
clone_at https://github.com/mwinding/connectome_tools.git       connectome_tools       bfdc691
# BANC (D-105): só documentação e tabelas pequenas (data/synapse_capture). ~2,8 GB; opcional.
if [[ ${BANC_REPO:-1} == 1 ]]; then
    clone_at https://github.com/htem/BANC-project.git           BANC-project           e31a2e2
fi

# ---------------------------------------------------------------- 3b. dados do BANC v888 (D-105)
# Harvard Dataverse doi:10.7910/DVN/7WTH1N, versão 3 (2026-07-01). Só os arquivos usados
# (~0,8 GB). ?format=original devolve o arquivo como depositado.
mkdir -p data/banc
dv_get() {  # dv_get <id> <nome>
    [[ -s data/banc/$2 ]] || curl -sfL -o "data/banc/$2" \
        "https://dataverse.harvard.edu/api/access/datafile/$1?format=original"
}
dv_get 14033740 banc_888_meta.feather
dv_get 13992792 banc_888_edgelist_simple_v2.feather
dv_get 13918810 banc_888_edgelist_simple_v3.feather
dv_get 13994485 banc_fafb_reviewed_matches.csv.gz
dv_get 13994489 banc_manc_reviewed_matches.csv.gz
dv_get 13916443 banc_problem_regions.csv

# ---------------------------------------------------------------- 4. checagens rápidas
export MUJOCO_GL=egl PYOPENGL_PLATFORM=egl
uv run python - <<'EOF'
import mujoco, brian2, flygym, numba
m = mujoco.MjModel.from_xml_string('<mujoco><worldbody><light pos="0 0 3"/><geom type="sphere" size=".2"/></worldbody></mujoco>')
d = mujoco.MjData(m); r = mujoco.Renderer(m, 64, 64); mujoco.mj_forward(m, d); r.update_scene(d)
assert r.render().mean() > 0; r.close()
print(f"ok: mujoco {mujoco.__version__} (EGL), brian2 {brian2.__version__}, flygym, numba {numba.__version__}")
EOF
echo "Ambiente pronto em $ROOT/.venv"
