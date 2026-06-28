# koreader-screensavers

Turn your own photos into **transparent e-ink sleep-screen overlays** for
[KOReader](https://github.com/koreader/koreader). KOReader keeps the last book
page on screen and only paints the *opaque* pixels of your screensaver — so your
photo floats over the text, with the page showing through wherever the image is
transparent.

It's a tiny ImageMagick pipeline plus a no-dependency terminal UI. **No AI
service, no internet, no account** — the default styles are pure ImageMagick;
the optional `subject` cutout runs a *local* neural net. Everything works
offline.

![styles](docs/styles.png)

## Why

E-ink screensavers are usually full, opaque images. The fun trick KOReader
allows is **"Leave screen unchanged"** as the sleep background: it doesn't blank
the page, so a partly-transparent PNG layers *over your book*. A silhouette
skyline, a faded sunset, a cut-out portrait — drifting over the last paragraph
you read.

## Styles

| style | what it does | best for |
|-------|--------------|----------|
| `bold` | bright areas (sky/snow) go transparent, dark = solid ink; text shows through. Top edge auto-fades. | landscapes, silhouettes |
| `skyline` | hybrid: dark foreground = solid ink, bright sky = soft veil | skyline shots, sunsets over land |
| `veil` | the whole photo as a soft semi-transparent overlay | big skies / sunsets you want to keep |
| `subject` | ML cutout of the subject, background transparent (local U2Net) | portraits, busy/dark backgrounds |
| `full` | opaque wallpaper, no transparency | when the scene *is* the whole picture |

E-ink is 16-level grayscale, so colour (e.g. sunset hues) is lost — only tone
survives. `veil` and `skyline` are the nicest compromise for colourful skies.

## Requirements

- **[ImageMagick 7](https://imagemagick.org)** (`magick` on your PATH) — that's
  it for `bold`/`veil`/`skyline`/`full`.
- For `subject` mode only: Python 3.10–3.13 + the U2Net model. Run
  `./setup_subject.sh` once (creates a `.venv`, downloads the ~176MB model).

## Usage

### Terminal UI (easiest)

```bash
python3 screensaver.py
```

Drag a photo into the window, pick a style, get an instant preview. The UI also
browses what you've made and shows the exact KOReader settings to use.

On macOS you can double-click `screensaver.command` instead.

### One-shot CLI

```bash
./make_screensaver.sh PHOTO [style] [out_name]

./make_screensaver.sh ~/Pictures/cliff.heic skyline cliff
CONTRAST=max ./make_screensaver.sh ~/Pictures/trail.jpg bold
VEIL=70     ./make_screensaver.sh ~/Pictures/sunset.jpg veil
```

Outputs land in `screensavers/<name>.png` (copy to the device) and a
`previews/<name>_preview.png` showing it over mock book text.

Knobs: `CONTRAST=med|high|max` (bold), `VEIL=NN` opacity (veil/skyline),
`SKY=lo,hi` skyline handoff band.

## Putting them on your reader

1. Copy `screensavers/*.png` into `koreader/screensavers/` on the device.
2. KOReader ▸ ⚙ ▸ **Screen ▸ Sleep screen** ▸ set the wallpaper folder to that
   folder.
3. **Sleep screen ▸ Background ▸ "Leave screen unchanged"** — the key step; this
   is what lets the book text show through the transparent areas.
4. Optional: "Random image" to rotate through them.

Default geometry targets an older Paperwhite (**1072×1448**). Change `W`/`H` at
the top of `make_screensaver.sh` for other models.

## Platform notes

- **macOS / Linux**: works directly (needs `bash` + `magick`; on Linux the
  preview falls back to DejaVu/Liberation serif fonts).
- **Windows**: run it under **WSL** or **Git Bash** — `make_screensaver.sh` is a
  bash script. The Python UI itself is cross-platform.

## How `subject` works

`subject_mask.py` runs the U2Net model (the one
[rembg](https://github.com/danielgatis/rembg) uses) directly via `onnxruntime`,
producing a matte that becomes the alpha channel. No rembg package, no cloud.

## License

MIT — see [LICENSE](LICENSE).
