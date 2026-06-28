#!/usr/bin/env python3
"""
Screensaver generator engine — pure Python, drives ImageMagick (`magick`).

No bash required, so it behaves identically on Windows, macOS and Linux. The
only external dependency is ImageMagick; `subject` mode additionally needs the
local venv + U2Net model (see setup_subject.sh / setup_subject.bat).

CLI:   python generate.py PHOTO [style] [out_name]
       style = bold | veil | skyline | subject | full   (default: bold)
       env knobs:  CONTRAST=med|high|max   VEIL=NN   SKY=lo,hi

API:   generate(src, style="bold", name=None, contrast="high", veil=62,
                sky="40%,68%") -> (output_png, preview_png)
"""
import os
import platform
import shutil
import subprocess
import sys
import tempfile

W, H = 1072, 1448  # older Paperwhite; change for other models
HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "screensavers")
PREVDIR = os.path.join(HERE, "previews")
IS_WIN = platform.system() == "Windows"

# Preview font: first that exists (macOS, common Linux, then Windows).
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Georgia.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "/usr/share/fonts/TTF/DejaVuSerif.ttf",
    r"C:\Windows\Fonts\georgia.ttf",
    r"C:\Windows\Fonts\times.ttf",
]

# bold: (sigmoidal-contrast, level, alpha-mask level)
CONTRAST = {
    "med":  ("3x55%", "0%,95%", "20%,80%"),
    "high": ("5x58%", "0%,92%", "30%,80%"),
    "max":  ("7x55%", "0%,88%", "45%,82%"),
}

PREVIEW_TEXT = (
    "Vin nodded in agreement, but Kelsier just shook his head. I do not work "
    "that way, Yeden. I invited Clubs to a meeting where I outlined a dangerous "
    "plan, one some people might even call stupid. I am not going to have him "
    "followed because he decided it was too dangerous. If you invite someone to "
    "one of these meetings and then have them followed, pretty soon nobody will "
    "come listen to your plans. Impossible, Vin thought. He had to be bluffing."
)


def _magick(*args):
    subprocess.run(["magick", *[str(a) for a in args]], check=True)


def _identify_h(path):
    out = subprocess.run(["magick", "identify", "-format", "%h", path],
                         capture_output=True, text=True, check=True)
    return int(out.stdout.strip())


def _find_font():
    for f in FONT_CANDIDATES:
        if os.path.isfile(f):
            return f
    return None


def venv_python():
    """Path to the subject-mode venv interpreter, or None (cross-platform)."""
    for c in (os.path.join(HERE, ".venv", "Scripts", "python.exe"),
              os.path.join(HERE, ".venv", "bin", "python")):
        if os.path.exists(c):
            return c
    return None


def _tmp_png():
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)  # close so Windows lets magick write it
    return path


def have_magick():
    return shutil.which("magick") is not None


def generate(src, style="bold", name=None, contrast="high", veil=62,
             sky="40%,68%"):
    if not have_magick():
        raise RuntimeError("ImageMagick not found — install it and ensure "
                           "`magick` is on your PATH.")
    os.makedirs(OUTDIR, exist_ok=True)
    os.makedirs(PREVDIR, exist_ok=True)
    if not name:
        name = f"{os.path.splitext(os.path.basename(src))[0]}_{style}"
    out = os.path.join(OUTDIR, f"{name}.png")

    base = _tmp_png()
    _magick(src, "-auto-orient", "-colorspace", "Gray", "-resize", f"{W}x", base)

    try:
        if style == "bold":
            sig, lvl, amask = CONTRAST.get(contrast, CONTRAST["high"])
            baseH = _identify_h(base)
            fadeH = int(baseH * 0.18)
            restH = baseH - fadeH
            _magick(
                base, "-sigmoidal-contrast", sig, "-level", lvl,
                "(", src, "-auto-orient", "-resize", f"{W}x",
                     "-grayscale", "Brightness", "-negate", "-level", amask,
                     "(", "-size", f"{W}x{fadeH}", "gradient:black-white",
                          "-size", f"{W}x{restH}", "xc:white", "-append", ")",
                     "-compose", "multiply", "-composite", ")",
                "-alpha", "off", "-compose", "CopyOpacity", "-composite",
                "-background", "none", "-gravity", "South", "-extent",
                f"{W}x{H}", out)

        elif style == "veil":
            _magick(
                src, "-auto-orient", "-colorspace", "Gray", "-normalize",
                "-sigmoidal-contrast", "3x50%",
                "-resize", f"{W}x{H}^", "-gravity", "center", "-extent",
                f"{W}x{H}",
                "-alpha", "set", "-channel", "A", "-evaluate", "set",
                f"{veil}%", "+channel", out)

        elif style == "skyline":
            frac = (100 - veil) / 100.0
            _magick(
                "(", src, "-auto-orient", "-colorspace", "Gray", "-normalize",
                     "-sigmoidal-contrast", "6x55%",
                     "-resize", f"{W}x{H}^", "-gravity", "center", "-extent",
                     f"{W}x{H}", ")",
                "(", src, "-auto-orient", "-grayscale", "Brightness",
                     "-normalize", "-resize", f"{W}x{H}^", "-gravity", "center",
                     "-extent", f"{W}x{H}", "-level", sky, "-evaluate",
                     "multiply", f"{frac:.3f}", "-negate", ")",
                "-alpha", "off", "-compose", "CopyOpacity", "-composite", out)

        elif style == "subject":
            py = venv_python()
            if not py:
                raise RuntimeError("subject mode needs the venv — run "
                                   "setup_subject.sh (or .bat on Windows).")
            rgb, mask = _tmp_png(), _tmp_png()
            _magick(src, "-auto-orient", rgb)
            subprocess.run([py, os.path.join(HERE, "subject_mask.py"), rgb,
                            mask], check=True)
            _magick(
                "-size", f"{W}x{H}", "xc:none",
                "(", base, "-sigmoidal-contrast", "3x50%",
                     "(", mask, "-resize", f"{W}x", "-level", "20%,80%", ")",
                     "-alpha", "off", "-compose", "CopyOpacity", "-composite",
                     ")",
                "-gravity", "South", "-compose", "over", "-composite", out)
            os.unlink(rgb)
            os.unlink(mask)

        elif style == "full":
            _magick(
                src, "-auto-orient", "-colorspace", "Gray", "-normalize",
                "-sigmoidal-contrast", "3x50%", "-resize", f"{W}x{H}",
                "-background", "black", "-gravity", "center", "-extent",
                f"{W}x{H}", out)

        else:
            raise ValueError(f"unknown style: {style}")

        # preview over mock book text
        prev = os.path.join(PREVDIR, f"{name}_preview.png")
        page = _tmp_png()
        font = _find_font()
        fontopt = ["-font", font] if font else []
        _magick(
            "-size", f"{W - 120}x{H}", "-background", "white", "-fill",
            "gray25", *fontopt, "-pointsize", "33", "-interline-spacing", "18",
            f"caption:{PREVIEW_TEXT} {PREVIEW_TEXT} {PREVIEW_TEXT}",
            "-gravity", "North", "-background", "white", "-extent", f"{W}x{H}",
            page)
        _magick(page, out, "-gravity", "South", "-compose", "over",
                "-composite", prev)
        os.unlink(page)
    finally:
        if os.path.exists(base):
            os.unlink(base)

    return out, prev


def _cli():
    if len(sys.argv) < 2:
        print("usage: python generate.py PHOTO [bold|veil|skyline|subject|full]"
              " [out_name]")
        print("  env: CONTRAST=med|high|max  VEIL=NN  SKY=lo,hi")
        sys.exit(1)
    src = sys.argv[1]
    style = sys.argv[2] if len(sys.argv) > 2 else "bold"
    name = sys.argv[3] if len(sys.argv) > 3 else None
    try:
        out, prev = generate(
            src, style, name,
            contrast=os.environ.get("CONTRAST", "high"),
            veil=int(os.environ.get("VEIL", "62")),
            sky=os.environ.get("SKY", "40%,68%"))
    except Exception as e:
        print(f"error: {e}")
        sys.exit(1)
    print(f"wrote: {out}")
    print(f"   (+ {prev})")


if __name__ == "__main__":
    _cli()
