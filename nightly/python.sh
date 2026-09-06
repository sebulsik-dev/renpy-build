#!/bin/bash

set -e

pushd $BASE/renpy

uv sync

. $VENV/bin/activate

# Delete the generated files.
rm -Rf renpy/module/gen

./run.sh launcher quit
popd
