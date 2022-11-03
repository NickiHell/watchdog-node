#!/bin/bash

set -o errexit
set -o nounset

. ./scripts/utils/graceful-exit.sh
. ./scripts/utils/prestart.sh

trap 'graceful_exit 60' TERM INT HUP
wait_db

export LOG_LEVEL=${LOG_LEVEL:-INFO}
export CELERY_APP=metadata_manager

eventler -A metadata_manager.eventler:event_bus outbox syncsequences
exec celery worker --pool solo -c 1 -Q eventler-django-send-messages
