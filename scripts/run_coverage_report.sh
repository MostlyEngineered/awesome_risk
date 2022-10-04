#!/bin/bash
# set -eoux pipeline # fail pipeline if anything fails

BASEDIR=$(dirname $0)
#cd BASEDIR
#cd ..
echo "Run coverage test"
coverage erase
rm -rf htmlcov
pwd
coverage run --source=.. --omit=testing/*,*__init__.py -m unittest

coverage html -i
ls -a

echo "Coverage report completed"