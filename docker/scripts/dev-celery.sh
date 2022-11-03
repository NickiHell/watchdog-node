#!/bin/bash

set -o errexit
set -o nounset

. ./scripts/utils/graceful-exit.sh
. ./scripts/utils/prestart.sh

trap 'graceful_exit 60' TERM INT HUP

export LOG_LEVEL=${LOG_LEVEL:-INFO}
export CELERY_APP=metadata_manager
export CELERY_WORKER_CONCURRENCY=${CELERY_WORKER_CONCURRENCY:-1}

wait_db

celery beat \
& celery worker \
& echo "Celery started - press \"Ctrl-C\" to stop them"

wait

echo "Normal exit"
