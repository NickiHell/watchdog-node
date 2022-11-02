#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail


echo "DJANGO_ENV is $DJANGO_ENV"
if [ "$DJANGO_ENV" != 'prod' ]; then
  echo 'Error: DJANGO_ENV is not set to "prod".'
  echo 'Application will not start.'
  exit 1
fi

export DJANGO_ENV

python /app/manage.py migrate --noinput
python /app/manage.py collectstatic --noinput --clear
python /app/manage.py compilemessages

find /var/www/django/static -type f \
  ! -regex '^.+\.\(jpg\|jpeg\|png\|gif\|webp\|zip\|gz\|tgz\|bz2\|tbz\|xz\|br\|swf\|flv\|woff\|woff2\)$' \
  -exec brotli --force --best {} \+ \
  -exec gzip --force --keep --best {} \+

gunicorn --config python:docker.django.gunicorn_config server.asgi.app
