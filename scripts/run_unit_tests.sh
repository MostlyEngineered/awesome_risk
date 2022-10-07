#!/bin/bash
set -euox pipefail  # if anything fails throw error
BASEDIR=$(dirname $0)
cd ${BASEDIR}
cd ..
echo "Run unit tests"
python3 -m unittest discover
echo "Completed unit tests"