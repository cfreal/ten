#!/usr/bin/env bash

DIRECTORY=$(dirname -- "$0")

cd "$DIRECTORY"

rm -rf ./pdoc
pdoc3 --html -c sort_identifiers=False --force ../tenlib --output-dir .
mkdocs build

echo
echo
echo ---------------------------------
echo Documentation is available at: $PWD/site/index.html
echo ---------------------------------
