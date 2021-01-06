#!/bin/sh

code_dir="mkdocstrings/handlers/crystal/"

set -eEx

cd "$(dirname "$0")/.."

git diff --quiet "$code_dir"

# https://github.com/pawamoy/pytkdocs/issues/86
git ls-files "$code_dir" | xargs sed -i 's/@cached_property/@property/'

trap 'git checkout -- "$code_dir"' EXIT

python -m mkdocs build
