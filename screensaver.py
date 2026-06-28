#!/usr/bin/env python3
"""
Kindle Screensaver Studio - a terminal interface for make_screensaver.sh.

Turn your photos into transparent KOReader sleep-screen overlays. No AI service,
no internet: bold/veil/skyline/full are pure ImageMagick; subject uses a LOCAL
neural net. Everything runs offline on this machine.

Run:  python3 screensaver.py   (or launch it from ServerHub)
Deps: ImageMagick (`magick`). subject mode also needs .venv + models/u2net.onnx.
"""

import os
import platform
import shutil
import subprocess
import sys

IS_WIN = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"


def open_file(path):
    """Open a file/folder in the OS default app (mac/Linux/Windows)."""
    try:
        if IS_MAC:
            subprocess.run(["open", path], check=False)
        elif IS_WIN:
            os.startfile(path)  # noqa: type-ignore[attr-defined]
        else:
            subprocess.run(["xdg-open", path], check=False)
    except Exception as e:
        print(f"  (couldn't open {path}: {e})")

HERE = os.path.dirname(os.path.abspath(__file__))
import generate  # pure-Python engine (no bash) — same on Windows/Mac/Linux

OUT = generate.OUTDIR
PREVIEWS = generate.PREVDIR

# ANSI colours (mirrors ServerHub)
BOLD = "\033[1m"; DIM = "\033[2m"; RESET = "\033[0m"
GREEN = "\033[32m"; RED = "\033[31m"; YELLOW = "\033[33m"; CYAN = "\033[36m"
GREY = "\033[90m"; MAG = "\033[35m"
W = 58

STYLES = [
    ("bold", "bright areas drop out, dark = ink; text shows through",
     "Landscapes / silhouettes. Top edge auto-fades. CONTRAST=med|high|max."),
    ("skyline", "dark foreground = solid ink, bright sky = veil",
     "Best for skyline shots (cliff, dawn, sunsets over land)."),
    ("veil", "whole photo as a soft semi-transparent overlay",
     "Sunsets / big skies you want to keep. VEIL=NN opacity (def 62)."),
    ("subject", "ML cutout of the subject, background transparent",
     "Portraits / busy or dark backgrounds. Uses local U2Net."),
    ("full", "opaque wallpaper, no transparency, no text behind",
     "When the scene itself is the whole picture."),
]
STYLE_NAMES = [s[0] for s in STYLES]

IMG_EXT = (".heic", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".gif", ".bmp")


def clear():
    os.system("cls" if IS_WIN else "clear")


def rule(left="├", mid="─", right="┤"):
    print(f"  {GREY}{left}{mid * W}{right}{RESET}")


def header(title, meta=""):
    print(f"  {GREY}╭{'─' * W}╮{RESET}")
    t = f" {BOLD}{CYAN}◆ {title}{RESET}"
    tvis = len(f" ◆ {title}")
    mvis = len(meta)
    gap = " " * max(1, W - tvis - mvis)
    pad = " " * max(0, W - (tvis + len(gap) + mvis))
    print(f"  {GREY}│{RESET}{t}{gap}{DIM}{meta}{RESET}{pad}{GREY}│{RESET}")
    print(f"  {GREY}╰{'─' * W}╯{RESET}")
    print()


def have_magick():
    return generate.have_magick()


def have_subject():
    return generate.venv_python() is not None


def clean_path(raw):
    """Normalise a pasted/dragged path: strip quotes, unescape Terminal drag."""
    s = raw.strip()
    if (s.startswith('"') and s.endswith('"')) or \
       (s.startswith("'") and s.endswith("'")):
        s = s[1:-1]
    # Terminal drag-and-drop backslash-escapes spaces and special chars
    s = s.replace("\\ ", " ").replace("\\(", "(").replace("\\)", ")") \
         .replace("\\&", "&").replace("\\'", "'")
    return os.path.expanduser(s.strip())


def ask(prompt, default=None):
    suffix = f" {DIM}[{default}]{RESET}" if default else ""
    try:
        v = input(f"  {prompt}{suffix} {BOLD}>{RESET} ").strip()
    except (EOFError, KeyboardInterrupt):
        return None
    return v if v else (default or "")


def list_outputs():
    if not os.path.isdir(OUT):
        return []
    return sorted(f for f in os.listdir(OUT) if f.lower().endswith(".png"))


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

def run_generate(src, style, name, env_extra):
    kwargs = {}
    if "CONTRAST" in env_extra:
        kwargs["contrast"] = env_extra["CONTRAST"]
    if "VEIL" in env_extra and str(env_extra["VEIL"]).isdigit():
        kwargs["veil"] = int(env_extra["VEIL"])
    print(f"\n  {CYAN}Generating {style} → {name or os.path.basename(src)}...{RESET}\n")
    try:
        generate.generate(src, style, name or None, **kwargs)
    except Exception as e:
        print(f"\n  {RED}Generation failed: {e}{RESET}")
        return None
    return name or f"{os.path.splitext(os.path.basename(src))[0]}_{style}"


def choose_style():
    clear()
    header("Pick a style")
    for i, (n, what, when) in enumerate(STYLES, 1):
        sub = "" if (n != "subject" or have_subject()) else \
            f"  {RED}(venv missing){RESET}"
        print(f"   {BOLD}{i}{RESET}  {CYAN}{n:<8}{RESET} {what}{sub}")
        print(f"        {DIM}{GREY}{when}{RESET}")
    print()
    while True:
        c = ask("style number (or name, blank=bold)", "bold")
        if c is None:
            return None
        c = c.lower()
        if c.isdigit() and 1 <= int(c) <= len(STYLES):
            return STYLE_NAMES[int(c) - 1]
        if c in STYLE_NAMES:
            return c
        print(f"  {RED}'{c}'? pick 1-{len(STYLES)} or a style name.{RESET}")


def flow_generate():
    clear()
    header("New screensaver")
    print(f"  Drag a photo into this window (or paste/type its path).")
    print(f"  {DIM}{GREY}HEIC, JPG, PNG... all fine.{RESET}\n")
    raw = ask("photo")
    if not raw:
        return
    src = clean_path(raw)
    if not os.path.isfile(src):
        print(f"  {RED}No file at: {src}{RESET}")
        ask("enter to go back")
        return

    style = choose_style()
    if style is None:
        return
    if style == "subject" and not have_subject():
        print(f"  {RED}subject mode needs the .venv. Pick another style.{RESET}")
        ask("enter to go back")
        return

    default_name = os.path.splitext(os.path.basename(src))[0].lower()
    name = ask("output name", default_name)

    env_extra = {}
    if style in ("bold",):
        lvl = ask("contrast: med / high / max", "high").lower()
        if lvl in ("med", "high", "max"):
            env_extra["CONTRAST"] = lvl
    if style in ("veil", "skyline"):
        op = ask("veil opacity % (higher = photo more dominant)", "62")
        if op.isdigit():
            env_extra["VEIL"] = op

    out = run_generate(src, style, name, env_extra)
    if out is None:
        ask("enter to continue")
        return
    print(f"\n  {GREEN}✓ wrote screensavers/{out}.png{RESET}")
    print(f"  {DIM}{GREY}preview: previews/{out}_preview.png{RESET}\n")
    if ask("open preview now? y/n", "y").lower().startswith("y"):
        pv = os.path.join(PREVIEWS, f"{out}_preview.png")
        if os.path.isfile(pv):
            open_file(pv)
        else:
            open_file(os.path.join(OUT, f"{out}.png"))
    ask("enter to continue")


def flow_browse():
    while True:
        clear()
        outs = list_outputs()
        header("Your screensavers", f"{len(outs)} saved")
        if not outs:
            print(f"  {DIM}{GREY}Nothing yet — generate one from the main menu.{RESET}\n")
            ask("enter to go back")
            return
        for i, f in enumerate(outs, 1):
            print(f"   {BOLD}{i:>2}{RESET}  {f}")
        print()
        rule("╭", "─", "╮")
        print(f"  {GREY}│{RESET}  {BOLD}#{RESET}{DIM} open preview   "
              f"{BOLD}f{RESET}{DIM} open folder   "
              f"{BOLD}q{RESET}{DIM} back{RESET}")
        rule("╰", "─", "╯")
        c = ask("")
        if c is None or c.lower() in ("q", ""):
            return
        if c.lower() == "f":
            open_file(OUT)
            continue
        if c.isdigit() and 1 <= int(c) <= len(outs):
            base = os.path.splitext(outs[int(c) - 1])[0]
            pv = os.path.join(PREVIEWS, f"{base}_preview.png")
            target = pv if os.path.isfile(pv) else os.path.join(OUT, outs[int(c) - 1])
            open_file(target)


def flow_kindle_help():
    clear()
    header("Load onto the Kindle")
    steps = [
        "Connect the device by USB.",
        "Copy screensavers/*.png into  koreader/screensavers/  on the device.",
        "KOReader ▸ ⚙ ▸ Screen ▸ Sleep screen ▸ set the wallpaper folder",
        "   to that screensavers/ folder.",
        "Sleep screen ▸ 'Border fill, rotation and fit' ▸ set Fill to 'No fill'",
        "   ← the key step; with no fill KOReader doesn't repaint the page, so",
        "   the book text shows through the transparent areas.",
        "Optional: 'Random image' so it rotates through them.",
    ]
    for s in steps:
        print(f"  {GREEN}•{RESET} {s}")
    print()
    if ask("open the screensavers folder now? y/n", "n").lower().startswith("y"):
        open_file(OUT)
    ask("enter to go back")


def main_menu():
    if not have_magick():
        clear()
        print(f"  {RED}ImageMagick not found.{RESET} Install it with:  brew install imagemagick")
        sys.exit(1)
    while True:
        clear()
        n = len(list_outputs())
        header("Kindle Screensaver Studio", f"{n} saved")
        print(f"  {BOLD}{GREY}WHAT NOW{RESET}\n")
        items = [
            ("1", "New screensaver", "pick a photo + style, generate + preview"),
            ("2", "Browse / open existing", "view what you've made"),
            ("3", "Style guide", "what bold / veil / skyline / subject do"),
            ("4", "Load onto Kindle", "copy + KOReader settings"),
        ]
        for k, name, desc in items:
            print(f"   {BOLD}{k}{RESET}  {name:<24}  {DIM}{GREY}{desc}{RESET}")
        print()
        rule("╭", "─", "╮")
        print(f"  {GREY}│{RESET}  {BOLD}1-4{RESET}{DIM} choose      "
              f"{BOLD}q{RESET}{DIM} quit{RESET}")
        rule("╰", "─", "╯")
        c = ask("")
        if c is None or c.lower() in ("q", "quit", "exit"):
            break
        if c == "1":
            flow_generate()
        elif c == "2":
            flow_browse()
        elif c == "3":
            choose_style()  # reuses the annotated list; returns on selection
        elif c == "4":
            flow_kindle_help()
    clear()
    print("bye 👋")


if __name__ == "__main__":
    main_menu()
