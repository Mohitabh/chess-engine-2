#!/bin/bash

# Check if pypy3 is installed on the system, otherwise fall back to python3
if command -v pypy3 >/dev/null 2>&1; then
    INTERPRETER="pypy3"
else
    INTERPRETER="python3"
fi

# Direct execution based on the first argument
case "$1" in
    benchmark)
        shift
        exec "$INTERPRETER" benchmark.py "$@"
        ;;
    perft)
        shift
        exec "$INTERPRETER" perft.py "$@"
        ;;
    test)
        shift
        exec "$INTERPRETER" -m unittest discover -s tests "$@"
        ;;
    *)
        exec "$INTERPRETER" cli.py "$@"
        ;;
esac
