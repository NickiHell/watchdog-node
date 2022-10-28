#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

readonly cmd="$*"

: "${DJANGO_DATABASE_HOST:=postgres}"
: "${DJANGO_DATABASE_PORT:=5432}"


dockerize -wait "tcp://${DJANGO_DATABASE_HOST}:${DJANGO_DATABASE_PORT}" -timeout 120s
>&2 echo 'Postgres is up - continuing...'

python /app/manage.py migrate --noinput
python /app/manage.py collectstatic --noinput --clear
python /app/manage.py compilemessages


exec "$cmd"
