#!/bin/bash
# Shell convenience wrapper around the Python engine (generate.py).
# The real logic lives in generate.py so there's a single implementation that
# also runs natively on Windows. Usage is unchanged:
#
#   ./make_screensaver.sh PHOTO [bold|veil|skyline|subject|full] [out_name]
#   CONTRAST=max ./make_screensaver.sh photo.jpg bold
#   VEIL=70      ./make_screensaver.sh sunset.jpg veil
#
exec python3 "$(dirname "$0")/generate.py" "$@"
