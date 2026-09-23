"""Campos do ambiente: odor (difusão 2D), temperatura e luz. Tudo NON-CONNECTOME.

Odor: um canal por FONTE (fruta, fermento, bactérias), em unidades arbitrárias. A identidade
química dos odores e o mapeamento para ORNs ficam para a Fase 3 (acoplamento sensorial).
Modelo: dc/dt = D ∇²c − k c + S(x, y), grade 2D no plano do piso, bordas sem fluxo (paredes).
  - D e k em configs/arena.yaml; comprimento característico √(D/k).
  - Estado inicial = regime estacionário (resolvido uma vez, esparso): o terrário "já existe" há
    tempo quando o episódio começa. Depois, passo explícito a cada `dt_s` (D-006: 10 ms), com
    subpassos para respeitar a estabilidade dt·D/dx² ≤ 1/4.
  - O campo é o mesmo em qualquer altura (aproximação 2D): as antenas amostram (x, y).
Fontes: solid → pegada (x, y) do sólido; disk → disco no piso. Taxa uniforme na pegada.
Consumo e crescimento do fermento/bactérias (ambiente vivo) são da Fase 5: aqui S é fixo, mas
`set_source_rate` já permite alterá-lo.
"""

from __future__ import annotations

import math

import numpy as np


class OdorField:
    def __init__(self, cfg: dict, world) -> None:
        oc = cfg["odor"]
        hx, hy = cfg["arena"]["half_size"]
        self.h = float(oc["cell_mm"])
        self.D = float(oc["diffusion_mm2_s"])
        self.k = float(oc["decay_1_s"])
        self.dt = float(oc["dt_s"])
        self.x0, self.y0 = -hx, -hy
        self.nx, self.ny = int(round(2 * hx / self.h)), int(round(2 * hy / self.h))
        xc = self.x0 + (np.arange(self.nx) + 0.5) * self.h
        yc = self.y0 + (np.arange(self.ny) + 0.5) * self.h
        X, Y = np.meshgrid(xc, yc, indexing="ij")
        self.channels = list(oc["sources"])
        self.masks, self.rates = [], []
        for ch in self.channels:
            src = oc["sources"][ch]
            if "solid" in src:
                s = cfg["solids"][src["solid"]]
                r = s["radii"] if s["shape"] == "ellipsoid" else [s["radius"]] * 3
                c = s["center"]
                # pegada no plano do piso: onde o sólido está acima de z = 0
                q = ((X - c[0]) / r[0]) ** 2 + ((Y - c[1]) / r[1]) ** 2
                zt = c[2] + r[2] * np.sqrt(np.clip(1 - q, 0, None))
                mask = (q < 1) & (zt > 0)
            else:
                d = cfg["zones"][src["disk"]]
                mask = (X - d["center"][0]) ** 2 + (Y - d["center"][1]) ** 2 <= d["radius"] ** 2
            m = mask.astype(float)
            self.masks.append(m / max(m.sum(), 1.0))  # taxa total = rate, qualquer que seja a área
            self.rates.append(float(src["rate"]))
        self.nsub = max(1, math.ceil(self.dt * self.D / self.h ** 2 / 0.2))
        self._S = None
        self.c = self.steady_state()
        self.t = 0.0

    # ------------------------------------------------------------------ dinâmica
    def source(self) -> np.ndarray:
        return np.stack([r * m for r, m in zip(self.rates, self.masks)]) / self.h ** 2

    def steady_state(self) -> np.ndarray:
        import scipy.sparse as sp
        import scipy.sparse.linalg as spla

        def lap1(n):
            main = -2 * np.ones(n)
            main[0] = main[-1] = -1  # Neumann (sem fluxo) nas bordas
            return sp.diags([np.ones(n - 1), main, np.ones(n - 1)], [-1, 0, 1])
        L = (sp.kron(lap1(self.nx), sp.eye(self.ny)) + sp.kron(sp.eye(self.nx), lap1(self.ny)))
        A = (self.D / self.h ** 2) * L - self.k * sp.eye(self.nx * self.ny)
        S = self.source()
        lu = spla.splu(A.tocsc())
        return np.stack([-lu.solve(s.ravel()).reshape(self.nx, self.ny) for s in S])

    def step(self) -> None:
        """Avança `dt` (chamar a cada 10 ms de simulação)."""
        if self._S is None:
            self._S = self.source()
            self._lap = np.empty_like(self.c)
        ds = self.dt / self.nsub
        a = self.D * ds / self.h ** 2
        c, lap = self.c, self._lap
        for _ in range(self.nsub):
            # laplaciano de 5 pontos com borda sem fluxo (Neumann: vizinho fora = a própria célula)
            np.multiply(c, -4.0, out=lap)
            lap[:, 1:, :] += c[:, :-1, :]
            lap[:, 0, :] += c[:, 0, :]
            lap[:, :-1, :] += c[:, 1:, :]
            lap[:, -1, :] += c[:, -1, :]
            lap[:, :, 1:] += c[:, :, :-1]
            lap[:, :, 0] += c[:, :, 0]
            lap[:, :, :-1] += c[:, :, 1:]
            lap[:, :, -1] += c[:, :, -1]
            lap *= a
            c *= 1.0 - ds * self.k
            c += lap
            c += ds * self._S
        self.t += self.dt

    def set_source_rate(self, channel: str, rate: float) -> None:
        self.rates[self.channels.index(channel)] = float(rate)
        self._S = None

    # ------------------------------------------------------------------ amostragem
    def sample(self, xy: np.ndarray) -> np.ndarray:
        """Concentração (bilinear) nos pontos xy (n, 2) → (n, canais)."""
        xy = np.atleast_2d(xy)
        fx = np.clip((xy[:, 0] - self.x0) / self.h - 0.5, 0, self.nx - 1.0001)
        fy = np.clip((xy[:, 1] - self.y0) / self.h - 0.5, 0, self.ny - 1.0001)
        i, j = fx.astype(int), fy.astype(int)
        u, v = fx - i, fy - j
        c = self.c
        out = (c[:, i, j] * (1 - u) * (1 - v) + c[:, i + 1, j] * u * (1 - v)
               + c[:, i, j + 1] * (1 - u) * v + c[:, i + 1, j + 1] * u * v)
        return out.T


class Temperature:
    """Gradiente linear em x (°C)."""

    def __init__(self, cfg: dict) -> None:
        self.t0 = float(cfg["temperature"]["t0_c"])
        self.g = float(cfg["temperature"]["grad_c_per_mm"])

    def sample(self, xy: np.ndarray) -> np.ndarray:
        return self.t0 + self.g * np.atleast_2d(xy)[:, 0]


class Light:
    """Ciclo dia/noite: intensidade relativa, cossenoidal entre night_level e 1."""

    def __init__(self, cfg: dict) -> None:
        self.period = float(cfg["light"]["period_s"])
        self.night = float(cfg["light"]["night_level"])

    def level(self, t: float) -> float:
        return self.night + (1 - self.night) * 0.5 * (1 + math.cos(2 * math.pi * t / self.period))


class Environment:
    """Os três campos juntos, avançados pelo orquestrador."""

    def __init__(self, cfg: dict, world) -> None:
        self.odor = OdorField(cfg, world)
        self.temperature = Temperature(cfg)
        self.light = Light(cfg)
        self._next_odor_t = self.odor.dt

    def advance_to(self, t: float) -> None:
        while t + 1e-12 >= self._next_odor_t:
            self.odor.step()
            self._next_odor_t += self.odor.dt
