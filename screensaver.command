#!/bin/bash
# Double-clickable macOS launcher: opens the studio in a Terminal window.
# Checks for Python 3 first (the studio is a Python program, so it can't
# install Python from inside itself) and offers to install it via Homebrew.
cd "$(dirname "$0")"
clear

if ! command -v python3 >/dev/null 2>&1; then
  echo "  Python 3 isn't installed — the studio needs it to run."
  echo
  if command -v brew >/dev/null 2>&1; then
    read -p "  Install Python now with Homebrew? [Y/n] " a
    if [[ "$a" != "n" && "$a" != "N" ]]; then
      brew install python
    fi
  else
    echo "  Install Homebrew first (one paste from https://brew.sh), then run:"
    echo "      brew install python imagemagick"
    echo
    read -p "  Press enter to close. "
    exit 1
  fi
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "  Python still not found — open a new Terminal and try again."
  read -p "  Press enter to close. "
  exit 1
fi

python3 screensaver.py
