@echo off
REM Optional setup for `subject` mode only (the ML cutout). The other styles
REM need NOTHING but ImageMagick. Creates a venv + downloads the U2Net model
REM (~176MB). Needs Python 3.10-3.13 (3.14 has no onnxruntime wheels yet).
cd /d "%~dp0"

python -m venv .venv
call .venv\Scripts\python.exe -m pip install --upgrade pip
call .venv\Scripts\python.exe -m pip install -r requirements.txt

if not exist models mkdir models
if not exist models\u2net.onnx (
  echo Downloading U2Net model ^(~176MB^)...
  curl -L -o models\u2net.onnx https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx
)

echo Done. subject mode is ready.
pause
