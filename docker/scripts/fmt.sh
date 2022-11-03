#!/bin/bash

set -o errexit
set -o nounset

isort .
black -l 90 -S .
flake8 || true
