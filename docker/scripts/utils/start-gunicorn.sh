#!/bin/bash

start_gunicorn() {
    GUNICORN_WORKERS="${WEB_CONCURRENCY:=4}"
    GUNICORN_MAX_REQUESTS="${GUNICORN_MAX_REQUESTS:-2000}"
    GUNICORN_MAX_REQUESTS_JITTER="${GUNICORN_MAX_REQUESTS_JITTER:-400}"
    GUNICORN_WORKER_TIMEOUT="${GUNICORN_WORKER_TIMEOUT:-60}"
    GUNICORN_WORKER_GRACEFUL_TIMEOUT="${GUNICORN_WORKER_GRACEFUL_TIMEOUT:-30}"

    exec /usr/local/bin/gunicorn metadata_manager.wsgi \
      --workers=$GUNICORN_WORKERS \
      --max-requests=$GUNICORN_MAX_REQUESTS \
      --max-requests-jitter=$GUNICORN_MAX_REQUESTS_JITTER \
      --timeout=$GUNICORN_WORKER_TIMEOUT \
      --graceful-timeout=$GUNICORN_WORKER_GRACEFUL_TIMEOUT \
      --bind='0.0.0.0:9001' \
      --worker-tmp-dir='/dev/shm' \
      --logger-class=gunicorn_logger.DjangoLogger \
      --access-logfile=- \
      --error-logfile=- \
      ${GUNICORN_RELOAD:+'--reload'}
}
