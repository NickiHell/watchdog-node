#!/usr/bin/env bash

echo "!!!ENTRYPOINT!!!"

set -o errexit
set -o nounset
set -o pipefail

. ./docker/django/prestart.sh
readonly cmd="$*"


wait_db
sync

exec "$cmd"
