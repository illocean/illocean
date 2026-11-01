#!/usr/bin/env python3
"""Fail CI unless output.gif is a plausible animated GIF."""

import argparse
import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError

MIN_WIDTH = 320
MIN_HEIGHT = 200
MIN_FRAMES = 2
MIN_COLORS = 2


def validate_gif(path: Path) -> tuple[int, int, int, int]:
    if not path.is_file():
        raise ValueError(f"missing GIF: {path}")

    try:
        with Image.open(path) as image:
            if image.format != "GIF":
                raise ValueError(f"not a GIF: {path} ({image.format or 'unknown format'})")

            width, height = image.size
            frames = getattr(image, "n_frames", 1)
            if frames < MIN_FRAMES:
                raise ValueError(
                    f"GIF has too few frames: {path} ({frames}; minimum {MIN_FRAMES})"
                )
            if width < MIN_WIDTH or height < MIN_HEIGHT:
                raise ValueError(
                    f"implausibly small GIF: {path} ({width}x{height}; "
                    f"minimum {MIN_WIDTH}x{MIN_HEIGHT})"
                )

            for frame_index in range(frames):
                try:
                    image.seek(frame_index)
                    frame = image.convert("RGB")
                    frame.load()
                    colors = frame.getcolors(maxcolors=width * height)
                except (EOFError, OSError, SyntaxError, UnidentifiedImageError, ValueError) as exc:
                    raise ValueError(
                        f"cannot load GIF frame {frame_index}: {path} ({exc})"
                    ) from exc
                if colors is None or len(colors) < MIN_COLORS:
                    raise ValueError(f"GIF frame {frame_index} is blank: {path}")
    except (EOFError, OSError, SyntaxError, UnidentifiedImageError, ValueError) as exc:
        raise ValueError(f"invalid GIF: {path} ({exc})") from exc

    return width, height, frames, path.stat().st_size


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=Path("output.gif"))
    args = parser.parse_args()

    try:
        width, height, frames, byte_count = validate_gif(args.path)
    except ValueError as exc:
        print(f"Invalid GIF: {exc}", file=sys.stderr)
        return 1

    print(
        f"Valid GIF: {args.path} ({width}x{height}, {frames} frames, "
        f"{byte_count} bytes)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
