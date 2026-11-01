import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from scripts.validate_gif import main


class ValidateGifTests(unittest.TestCase):
    def run_validator(self, path: Path | None) -> tuple[int, str]:
        stdout = io.StringIO()
        with patch("sys.argv", ["validate_gif.py", *([] if path is None else [str(path)])]):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stdout):
                result = main()
        return result, stdout.getvalue()

    def test_missing_gif_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result, output = self.run_validator(Path(temp_dir) / "missing.gif")
        self.assertEqual(result, 1)
        self.assertIn("missing GIF", output)

    def test_non_gif_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "output.gif"
            path.write_bytes(b"not an image")
            result, output = self.run_validator(path)
        self.assertEqual(result, 1)
        self.assertIn("invalid GIF", output)

    def test_tiny_gif_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "output.gif"
            tiny = Image.new("RGB", (319, 200), "red")
            tiny.save(
                path,
                "GIF",
                save_all=True,
                append_images=[Image.new("RGB", (319, 200), "blue")],
            )
            result, output = self.run_validator(path)
        self.assertEqual(result, 1)
        self.assertIn("implausibly small", output)

    def test_one_frame_gif_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "output.gif"
            image = Image.new("RGB", (320, 200), "white")
            image.paste((0, 0, 0), (0, 0, 32, 32))
            image.save(path, "GIF")
            result, output = self.run_validator(path)
        self.assertEqual(result, 1)
        self.assertIn("too few frames", output)

    def test_later_blank_frame_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "output.gif"
            image = Image.new("RGB", (320, 200), "white")
            image.paste((0, 0, 0), (0, 0, 32, 32))
            blank = Image.new("RGB", image.size, "white")
            image.save(path, "GIF", save_all=True, append_images=[blank])
            result, output = self.run_validator(path)
        self.assertEqual(result, 1)
        self.assertIn("frame 1 is blank", output)

    def test_later_corrupt_frame_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "output.gif"
            image = Image.new("RGB", (320, 200), "white")
            image.paste((0, 0, 0), (0, 0, 32, 32))
            second = image.copy()
            second.paste((32, 0, 0), (32, 0, 64, 32))
            image.save(path, "GIF", save_all=True, append_images=[second])
            data = bytearray(path.read_bytes())
            image_bytes = Image.open(path)
            image_bytes.seek(1)
            image_bytes.close()
            frame_start = data.rfind(b"\x2c")
            data[frame_start + 9] ^= 0x80
            path.write_bytes(data)
            result, output = self.run_validator(path)
        self.assertEqual(result, 1)
        self.assertIn("cannot load GIF frame 1", output)

    def test_valid_gif_passes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "output.gif"
            image = Image.new("RGB", (320, 200), "white")
            image.paste((0, 0, 0), (0, 0, 32, 32))
            second = image.copy()
            second.paste((32, 0, 0), (32, 0, 64, 32))
            image.save(path, "GIF", save_all=True, append_images=[second])
            result, output = self.run_validator(path)
        self.assertEqual(result, 0)
        self.assertIn("Valid GIF:", output)
        self.assertIn("2 frames", output)


if __name__ == "__main__":
    unittest.main()
