"""Vídeos curtos das cenas (requisito: 10–20 s ao fim de cada fase ou entrega, em results/).

Renderização com mujoco.Renderer (EGL). Gravação SEMPRE em WebM/VP9 (padrão do projeto, CLAUDE.md:
o Fedora não toca H.264 sem codecs extras), com o ffmpeg do pacote imageio-ffmpeg. Cada quadro pode juntar várias câmeras lado a lado e uma
legenda de texto.
"""

from __future__ import annotations

from pathlib import Path

import mujoco as mj
import numpy as np
from PIL import Image, ImageDraw


class Recorder:
    def __init__(self, sim, cameras: list[str], size=(360, 480), fps: int = 30,
                 playback: float = 0.25):
        self.sim = sim
        self.cams = cameras
        self.r = mj.Renderer(sim.mj_model, height=size[0], width=size[1])
        self.frames: list[np.ndarray] = []
        self.period = playback / fps          # segundos simulados entre quadros
        self.fps = fps
        self._next = 0.0

    def maybe_capture(self, caption: str = "") -> None:
        t = self.sim.mj_data.time
        if t + 1e-12 < self._next:
            return
        self._next = t + self.period
        imgs = []
        for c in self.cams:
            self.r.update_scene(self.sim.mj_data, camera=c)
            imgs.append(self.r.render().copy())
        frame = np.concatenate(imgs, axis=1)
        if caption:
            im = Image.fromarray(frame)
            d = ImageDraw.Draw(im)
            d.rectangle([0, 0, im.width, 22], fill=(252, 252, 251))
            d.text((8, 5), caption, fill=(11, 11, 11))
            frame = np.asarray(im)
        self.frames.append(frame)

    def save(self, path: Path) -> Path:
        return write_webm(Path(path), self.frames, self.fps)


def write_webm(path: Path, frames: list[np.ndarray], fps: int = 30, crf: int = 32) -> Path:
    """Grava quadros RGB uint8 em WebM (VP9). Dimensões arredondadas para pares (yuv420p)."""
    import imageio_ffmpeg

    path = Path(path).with_suffix(".webm")
    path.parent.mkdir(parents=True, exist_ok=True)
    h, w = frames[0].shape[:2]
    h2, w2 = h - h % 2, w - w % 2
    wr = imageio_ffmpeg.write_frames(str(path), (w2, h2), fps=fps, codec="libvpx-vp9",
                                     pix_fmt_out="yuv420p", macro_block_size=1,
                                     output_params=["-b:v", "0", "-crf", str(crf), "-row-mt", "1"])
    wr.send(None)
    for f in frames:
        wr.send(np.ascontiguousarray(f[:h2, :w2]))
    wr.close()
    return path
