#!/usr/bin/env sh

set -o errexit
set -o nounset

readonly cmd="$*"

export poetry=$HOME/.poetry/bin/poetry

poetry shell

exec $cmd
