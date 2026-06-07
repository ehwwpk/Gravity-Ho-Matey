from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from pathlib import Path


def _gif_frame_delay_ms(frame: tk.PhotoImage) -> int:
    try:
        delay = int(frame.info().get("delay", 100))  # type: ignore[attr-defined]
    except (tk.TclError, ValueError, TypeError, AttributeError):
        delay = 100
    return max(20, delay)


def _fit_subsample(frame: tk.PhotoImage, max_w: int, max_h: int) -> tk.PhotoImage:
    width = frame.width()
    height = frame.height()
    if width <= 0 or height <= 0:
        return frame
    factor = max(1, (width + max_w - 1) // max_w, (height + max_h - 1) // max_h)
    if factor <= 1:
        return frame
    return frame.subsample(factor, factor)


def _load_gif_tk(
    path: Path,
    *,
    max_width: int,
    max_height: int,
    master: tk.Misc | None,
) -> "AnimatedImageSequence":
    raw_frames: list[tk.PhotoImage] = []
    delays: list[int] = []
    index = 0
    while True:
        try:
            frame = tk.PhotoImage(
                master=master,
                file=str(path),
                format=f"gif -index {index}",
            )
        except tk.TclError:
            break
        raw_frames.append(frame)
        delays.append(_gif_frame_delay_ms(frame))
        index += 1
    if not raw_frames:
        raise ValueError(f"No GIF frames in {path}")
    frames = [_fit_subsample(frame, max_width, max_height) for frame in raw_frames]
    return AnimatedImageSequence(frames=frames, delays_ms=delays)


def _load_gif_pillow(
    path: Path,
    *,
    max_width: int,
    max_height: int,
    master: tk.Misc | None,
) -> "AnimatedImageSequence":
    from PIL import Image, ImageSequence, ImageTk

    frames: list[tk.PhotoImage] = []
    delays: list[int] = []
    with Image.open(path) as image:
        for frame_im in ImageSequence.Iterator(image):
            rgba = frame_im.convert("RGBA")
            width, height = rgba.size
            scale = max(width / max_width, height / max_height, 1.0)
            if scale > 1.0:
                new_size = (max(1, int(width / scale)), max(1, int(height / scale)))
                rgba = rgba.resize(new_size, Image.Resampling.LANCZOS)
            frames.append(ImageTk.PhotoImage(rgba, master=master))
            delay = frame_im.info.get("duration", 100)
            try:
                delay_ms = max(20, int(delay))
            except (TypeError, ValueError):
                delay_ms = 100
            delays.append(delay_ms)
    if not frames:
        raise ValueError(f"No GIF frames in {path}")
    return AnimatedImageSequence(frames=frames, delays_ms=delays)


@dataclass(slots=True)
class AnimatedImageSequence:
    """Frame sequence for narrative intros — GIF via Pillow (preferred) or Tk."""

    frames: list[tk.PhotoImage]
    delays_ms: list[int]

    @classmethod
    def load(
        cls,
        path: Path,
        *,
        max_width: int,
        max_height: int,
        master: tk.Misc | None = None,
    ) -> AnimatedImageSequence:
        suffix = path.suffix.lower()
        if suffix == ".gif":
            try:
                return _load_gif_pillow(
                    path,
                    max_width=max_width,
                    max_height=max_height,
                    master=master,
                )
            except ImportError:
                return _load_gif_tk(
                    path,
                    max_width=max_width,
                    max_height=max_height,
                    master=master,
                )
        raw_frames = [_load_static_image(path, master=master)]
        return cls(frames=raw_frames, delays_ms=[100])

    @property
    def frame_count(self) -> int:
        return len(self.frames)

    def duration_seconds(self) -> float:
        return sum(self.delays_ms) / 1000.0

    def frame(self, index: int) -> tk.PhotoImage:
        return self.frames[index % len(self.frames)]

    def delay_seconds(self, index: int) -> float:
        return self.delays_ms[index % len(self.delays_ms)] / 1000.0


def _load_static_image(path: Path, *, master: tk.Misc | None = None) -> tk.PhotoImage:
    try:
        return tk.PhotoImage(master=master, file=str(path))
    except tk.TclError:
        pass
    try:
        from PIL import Image, ImageTk
    except ImportError as exc:
        raise ValueError(
            f"Tk cannot load {path.suffix} and Pillow is not installed; use GIF narrative assets."
        ) from exc
    image = Image.open(path)
    return ImageTk.PhotoImage(image.convert("RGBA"), master=master)
