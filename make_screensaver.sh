#!/bin/bash
# Turn a photo into a transparent Kindle (KOReader) screensaver overlay.
# Bright areas (sky) -> transparent so the book page shows through;
# darker areas -> your photo as e-ink "ink".
#
# Usage:  ./make_screensaver.sh PHOTO [style] [out_basename]
#   style: bold | veil | skyline | subject | full   (default: bold)
#     bold    : bright areas (sky/snow/pale wall) go transparent, dark = ink,
#               page text shows through. Free, instant.
#               CONTRAST=med|high|max controls aggressiveness (default high).
#     subject : ML cutout of the subject, background transparent. Any photo.
#               Needs the .venv + models/u2net.onnx in this folder.
#     full    : whole image as an opaque wallpaper (NO transparency). For when
#               the sky/scene itself is the subject (sunsets, big skies).
#
# Output: <name>.png         -> copy to your Kindle screensaver folder
#         <name>_preview.png -> shows it over mock book text
#
# Target: Paperwhite (older, PW3/PW4) = 1072x1448. Change W/H for other models.

set -e
SRC="$1"; STYLE="${2:-bold}"; NAME="${3:-$(basename "${1%.*}")_$STYLE}"
W=1072; H=1448
DIR="$(cd "$(dirname "$0")" && pwd)"
OUTDIR="$DIR/screensavers"; PREVDIR="$DIR/previews"
mkdir -p "$OUTDIR" "$PREVDIR"

# Preview font: first one that exists (macOS Georgia, then common Linux fonts).
FONT=""
for f in \
  "/System/Library/Fonts/Supplemental/Georgia.ttf" \
  "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf" \
  "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf" \
  "/usr/share/fonts/TTF/DejaVuSerif.ttf" ; do
  [ -f "$f" ] && { FONT="$f"; break; }
done

[ -z "$SRC" ] && { echo "usage: $0 PHOTO [bold|photo|layered] [out]"; exit 1; }

base="$(mktemp -t ss).png"
magick "$SRC" -auto-orient -colorspace Gray -resize ${W}x "$base"

case "$STYLE" in
  bold)    # solid: dark = opaque ink, bright = transparent.
           # Visible ink = natural luminance grayscale; transparency = brightness
           # (max channel) so CLEAR BLUE skies (dark in luminance, bright in
           # brightness) drop out too, not just white/grey skies.
           # CONTRAST=med|high|max controls how hard mid-tones go transparent.
    case "${CONTRAST:-high}" in
      med)  SIG="3x55%"; LVL="0%,95%"; AMASK="20%,80%" ;;
      high) SIG="5x58%"; LVL="0%,92%"; AMASK="30%,80%" ;;
      max)  SIG="7x55%"; LVL="0%,88%"; AMASK="45%,82%" ;;
    esac
    # The photo is bottom-anchored, so fade its top edge to transparent over the
    # top ~18% of the photo height — otherwise it cuts off as a hard line.
    baseH=$(magick identify -format '%h' "$base")
    fadeH=$(awk "BEGIN{printf \"%d\", $baseH*0.18}"); restH=$((baseH - fadeH))
    magick "$base" -sigmoidal-contrast $SIG -level $LVL \
      \( "$SRC" -auto-orient -resize ${W}x -grayscale Brightness -negate -level $AMASK \
         \( -size ${W}x${fadeH} gradient:black-white -size ${W}x${restH} xc:white -append \) \
         -compose multiply -composite \) \
      -alpha off -compose CopyOpacity -composite \
      -background none -gravity South -extent ${W}x${H} "$OUTDIR/$NAME.png" ;;
  subject) # cut the subject out with U2Net; background -> transparent.
           # Works on ANY background (busy/dark), unlike bold. Needs the venv.
    PY="$DIR/.venv/bin/python"
    [ -x "$PY" ] || { echo "subject mode needs the venv at $PY (run the rembg-free install)"; exit 1; }
    rgb="$(mktemp -t ssrgb).png"; mask="$(mktemp -t ssmask).png"
    magick "$SRC" -auto-orient "$rgb"
    "$PY" "$DIR/subject_mask.py" "$rgb" "$mask"
    # Build masked subject (grayscale + gentle contrast, sharpened matte as alpha),
    # then composite onto a transparent canvas. Two stages: -extent on an
    # alpha-bearing image blackens the colour channel, so we use -compose over.
    magick -size ${W}x${H} xc:none \
      \( "$base" -sigmoidal-contrast 3x50% \
         \( "$mask" -resize ${W}x -level 20%,80% \) \
         -alpha off -compose CopyOpacity -composite \) \
      -gravity South -compose over -composite "$OUTDIR/$NAME.png"
    rm -f "$rgb" "$mask" ;;
  veil)    # whole image fills the screen as a SEMI-TRANSPARENT overlay, so the
           # sky/scene stays visible AND the page text shows through it. Best for
           # sunsets/big skies you want to see but still keep the text-behind look.
           # VEIL=NN sets opacity percent (default 62; higher = photo more dominant).
    op="${VEIL:-62}"
    magick "$SRC" -auto-orient -colorspace Gray -normalize -sigmoidal-contrast 3x50% \
      -resize ${W}x${H}^ -gravity center -extent ${W}x${H} \
      -alpha set -channel A -evaluate set ${op}% +channel \
      "$OUTDIR/$NAME.png" ;;
  skyline) # HYBRID of bold + veil: dark foreground/land becomes SOLID opaque ink
           # that fully obscures the text, while the bright sky stays as a veil
           # (text shows through). The handoff sits at the skyline and auto-adapts
           # per photo (brightness is normalized first).
           # VEIL=NN sky opacity (default 62). SKY=lo,hi skyline band (default 40%,68%).
    op="${VEIL:-62}"; band="${SKY:-40%,68%}"
    frac=$(awk "BEGIN{printf \"%.3f\", (100-$op)/100}")
    magick \( "$SRC" -auto-orient -colorspace Gray -normalize -sigmoidal-contrast 6x55% \
               -resize ${W}x${H}^ -gravity center -extent ${W}x${H} \) \
           \( "$SRC" -auto-orient -grayscale Brightness -normalize \
               -resize ${W}x${H}^ -gravity center -extent ${W}x${H} \
               -level ${band} -evaluate multiply ${frac} -negate \) \
           -alpha off -compose CopyOpacity -composite "$OUTDIR/$NAME.png" ;;
  full)    # whole image as an opaque e-ink WALLPAPER (no transparency).
           # For photos where the sky/scene itself is the subject (sunsets,
           # big skies) and you do NOT want the page showing through.
           # -normalize stretches the tonal range; sigmoidal adds punch.
           # Portrait shots fill the screen; wide shots get black letterbox bars.
    magick "$SRC" -auto-orient -colorspace Gray \
      -normalize -sigmoidal-contrast 3x50% \
      -resize ${W}x${H} -background black -gravity center -extent ${W}x${H} \
      "$OUTDIR/$NAME.png" ;;
  *) echo "unknown style: $STYLE"; exit 1 ;;
esac

# preview over mock book text
T="Vin nodded in agreement, but Kelsier just shook his head. I do not work that way, Yeden. I invited Clubs to a meeting where I outlined a dangerous plan, one some people might even call stupid. I am not going to have him followed because he decided it was too dangerous. If you invite someone to one of these meetings and then have them followed, pretty soon nobody will come listen to your plans. Impossible, Vin thought. He had to be bluffing."
page="$(mktemp -t sspage).png"
fontopt=(); [ -n "$FONT" ] && fontopt=(-font "$FONT")
magick -size $((W-120))x${H} -background white -fill gray25 "${fontopt[@]}" \
  -pointsize 33 -interline-spacing 18 caption:"$T $T $T" \
  -gravity North -background white -extent ${W}x${H} "$page"
magick "$page" "$OUTDIR/$NAME.png" -gravity South -compose over -composite "$PREVDIR/${NAME}_preview.png"
rm -f "$base" "$page"
echo "wrote: $OUTDIR/$NAME.png  (+ previews/${NAME}_preview.png)"
