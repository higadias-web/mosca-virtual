"""Vídeos curtos das cenas (requisito: 10–20 s ao fim de cada fase ou entrega, em results/).

Renderização com mujoco.Renderer (EGL) e gravação com flygym.utils.video.write_video_from_frames
(imageio + ffmpeg do imageio-ffmpeg). Cada quadro pode juntar várias câmeras lado a lado e uma
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
        from flygym.utils.video import write_video_from_frames
        write_video_from_frames(Path(path), self.frames, fps=self.fps)
        return Path(path)
