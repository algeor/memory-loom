#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_directory="${1:-$repo_root/dist}"
temporary_directory="$(mktemp -d)"
trap 'rm -rf "$temporary_directory"' EXIT

mkdir -p "$output_directory"
UV_CACHE_DIR="${UV_CACHE_DIR:-$temporary_directory/uv-cache}" \
  uv build --out-dir "$output_directory"

wheel="$(find "$output_directory" -maxdepth 1 -name 'memory_loom-*.whl' -print | sort | tail -1)"
if [[ -z "$wheel" ]]; then
  echo "error: wheel was not created" >&2
  exit 1
fi

uv venv --python 3.14 "$temporary_directory/venv"
UV_CACHE_DIR="${UV_CACHE_DIR:-$temporary_directory/uv-cache}" \
  uv pip install --python "$temporary_directory/venv/bin/python" "$wheel"

cd "$temporary_directory"
"$temporary_directory/venv/bin/python" \
  "$repo_root/scripts/smoke-installed-package.py" \
  --bin-dir "$temporary_directory/venv/bin"
