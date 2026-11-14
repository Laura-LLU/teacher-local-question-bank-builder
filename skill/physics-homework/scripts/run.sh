#!/bin/bash
# First-run bootstrap is confined to this tool's own workspace; no shell profile edits or sudo.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORK="${PHYSICS_HOME:-$HOME/codex/physics-homework}"
mkdir -p "$WORK/.tools" "$WORK/.cache" "$WORK/tmp"
export UV_CACHE_DIR="$WORK/.cache/uv"
export UV_PYTHON_INSTALL_DIR="$WORK/.python"
export UV_PYTHON_BIN_DIR="$WORK/.tools"
export TMPDIR="$WORK/tmp"
PY="$WORK/.venv/bin/python"
if [ ! -x "$PY" ] || ! "$PY" -c 'import PIL,pypdf,pdfplumber,reportlab,pypdfium2' >/dev/null 2>&1; then
  echo '首次使用：正在自动准备独立运行环境，不修改系统Python，也不需要API Key。' >&2
  UV="$WORK/.tools/uv"
  if [ ! -x "$UV" ]; then
    if command -v uv >/dev/null 2>&1; then
      UV="$(command -v uv)"
    else
      curl --fail --silent --show-error --location --retry 2 https://astral.sh/uv/install.sh -o "$WORK/tmp/install-uv.sh"
      env UV_INSTALL_DIR="$WORK/.tools" UV_NO_MODIFY_PATH=1 sh "$WORK/tmp/install-uv.sh" >&2
    fi
  fi
  if [ ! -x "$PY" ]; then "$UV" venv --python 3.12 "$WORK/.venv" >&2; fi
  "$UV" pip install --python "$PY" -r "$SCRIPT_DIR/requirements.txt" >&2
fi
if [ "${1:-}" = "qa" ]; then
  shift
  exec "$PY" "$SCRIPT_DIR/qa_pdf.py" "$@"
fi
exec "$PY" "$SCRIPT_DIR/homework.py" --workspace "$WORK" "$@"
