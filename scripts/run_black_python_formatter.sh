#!/bin/bash

set -eoux pipefail  # fail and exit if any command throws an error

BASEDIR=$(dirname $0)
cd ${BASEDIR}
cd ..
echo "Running black formatter"

black -l 120 . --exclude=venv

echo "Done formatting"
