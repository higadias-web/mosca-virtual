# Setup no Fedora 44 (ThinkPad T14 Gen 4)

Verificado em 2026-09-22: Fedora 44 KDE, kernel 7.2.5-200.fc44, Mesa 26.1.8/26.2.2,
Intel UHD (RPL-U, `/dev/dri/renderD128`).

## 1. Pacotes de sistema (`dnf`, precisa de sudo)

```bash
sudo dnf install -y gcc gcc-c++ make uv git-lfs mesa-libEGL-devel libglvnd-devel \
                    mesa-compat-libOSMesa stress-ng
```

| Pacote | Versão verificada | Para quê |
|---|---|---|
| `gcc`, `gcc-c++`, `make` | 16.2.1 | Brian2 (codegen Cython e `cpp_standalone`) |
| `uv` | 0.12.15 | ambiente Python isolado (nunca `sudo pip`) |
| `git-lfs` | 3.7.1 | datasets distribuídos via LFS (reserva; os atuais não usam) |
| `mesa-libEGL-devel`, `libglvnd-devel` | 26.2.2 / 1.7.0 | renderização headless do MuJoCo (`MUJOCO_GL=egl`) |
| `mesa-compat-libOSMesa` | 25.0.7 | alternativa `MUJOCO_GL=osmesa` (ver abaixo) |
| `stress-ng` | 0.22.00 | opcional: teste de throttling |

Já vinham instalados: `mesa-libEGL`, `mesa-dri-drivers`, `libglvnd-egl`, `lm_sensors`, `tuned-ppd`.

**OSMesa:** o Mesa removeu o OSMesa a partir da série 25.1. No Fedora 44 só existe o pacote
`mesa-compat-libOSMesa`, congelado na 25.0.7. Ele funciona (testado), mas é software
rendering e pode sumir numa versão futura do Fedora. O caminho principal é o EGL.

## 2. Ambiente Python

```bash
./setup.sh
```

O `setup.sh` é idempotente e não usa sudo. Ele:
1. confere os pacotes de sistema e, se faltar algum, imprime o comando `dnf`;
2. instala o CPython 3.13 gerenciado pelo `uv` (em `~/.local/share/uv`, não no sistema) e roda
   `uv sync --frozen` com o `uv.lock`;
3. clona os repositórios de referência em `third_party/`, nos commits fixados;
4. testa o MuJoCo com EGL.

## 3. Renderização headless

```bash
export MUJOCO_GL=egl PYOPENGL_PLATFORM=egl
```

Testado em 2026-09-22: `mujoco.Renderer` com EGL renderiza na GPU Intel
(`GL_RENDERER = Mesa Intel(R) Graphics (RPL-U)`). Na saída do interpretador aparece um
`EGLError` inofensivo no `__del__` do `Renderer` quando ele não é fechado; chame
`renderer.close()` explicitamente.

Alternativa testada: `MUJOCO_GL=osmesa PYOPENGL_PLATFORM=osmesa` (funciona, na CPU).

## 4. Energia e execuções longas

- **Rodar sempre na tomada.** Na bateria, o perfil `power-saver` desliga o turbo
  (`/sys/devices/system/cpu/intel_pstate/no_turbo = 1`) e limita a CPU a 1,0 GHz (P) / 0,8 GHz (E).
  Com o turbo ligado: 4,7 GHz (P) / 3,5 GHz (E).
- O KDE usa o `tuned-ppd` (API `org.freedesktop.UPower.PowerProfiles`). Os perfis mapeiam para o
  `tuned` assim (`/etc/tuned/ppd.conf`): power-saver → `powersave`,
  Equilibrado (`balanced`) → `balanced`, Desempenho (`performance`) → `throughput-performance`.
- Trocar o perfil sem sudo:
  ```bash
  busctl set-property org.freedesktop.UPower.PowerProfiles /org/freedesktop/UPower/PowerProfiles \
      org.freedesktop.UPower.PowerProfiles ActiveProfile s performance
  ```
- Execuções longas:
  ```bash
  systemd-inhibit --what=idle:sleep --why="terrario" uv run python ...
  ```
- **Swap:** o Fedora usa zram (`/dev/zram0`, 8 GB). Os benchmarks registram `SwapFree` antes e
  depois; se a execução entrar em swap, o resultado é marcado como inválido.
