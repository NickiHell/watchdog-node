#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

. ./docker/django/prestart.sh
readonly cmd="$*"

while ! /usr/bin/pg_isready -h $DB_HOST -p ${DB_PORT:-5432} >/dev/null 2>/dev/null; do
  echo "I'm waiting DB (Host: $DB_HOST, port: ${DB_PORT:-5432})"
  sleep 1
done
echo -e "\n### Migrate DB ###\n" && python manage.py migrate

exec "$cmd"
